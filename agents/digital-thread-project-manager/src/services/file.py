import asyncio
from io import BytesIO
import logging
import os
import tempfile
from typing import Optional, Set, List, Dict, Any
from fastapi import UploadFile
import httpx
from src.models.entities.file import FileRepository
from src.utils.exceptions import CustomException, ExceptionEnum
from motor.motor_asyncio import AsyncIOMotorGridFSBucket, AsyncIOMotorGridOut
try:
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.StlAPI import StlAPI_Writer
    from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
    from OCC.Core.IFSelect import IFSelect_RetDone
    _OCC_AVAILABLE = True
except ImportError:
    STEPControl_Reader = None
    StlAPI_Writer = None
    BRepMesh_IncrementalMesh = None
    IFSelect_RetDone = None
    _OCC_AVAILABLE = False
from dotenv import load_dotenv
from bson.objectid import ObjectId, InvalidId
import gridfs
import logging
import asyncio
import xmltodict

load_dotenv()


class FileService:
    """
    파일 업로드/다운로드, 변환, 삭제 등 파일 관련 모든 핵심 로직을 담당하는 서비스 클래스.
    MongoDB GridFS, 외부 DLL 변환 서버(http API), OpenCASCADE 파이썬 바인딩 사용.
    """

    DLL_URI = os.getenv(
        "DLL_URI", "http://dll-server:8010"
    )  # 외부 DLL 변환 서버 API 주소

    def __init__(self, grid_fs: AsyncIOMotorGridFSBucket):
        # 파일 저장/조회 등 실제 DB 작업은 FileRepository가 담당 (의존성 주입)
        self.repository = FileRepository(grid_fs)

    async def delete_project_dt_files(self, project: dict) -> List[str]:
        """
        프로젝트 XML(dt_asset)에서 모든 dt_file 요소를 찾아,
        그 안에 들어있는 Mongo ObjectId(보통 <value>에 저장)를 전부 삭제한다.
        - 중복 ID는 한 번만 삭제 시도
        - 존재하지 않는 파일은 무시(로그만)
        - 문제 발생 시 안전 로깅
        반환: 실제 삭제 시도한 file_id(ObjectId 문자열) 리스트
        """
        # 1) XML 파싱
        raw = project.get("data")
        if raw is None:
            logging.warning("[delete_project_dt_files] project.data 없음")
            return []

        if isinstance(raw, (bytes, str)):
            xml_dict = xmltodict.parse(
                raw,
                process_namespaces=True,
                namespaces={
                    "http://digital-thread.re/dt_asset": None,
                    "http://www.w3.org/2001/XMLSchema-instance": "xsi",
                },
                attr_prefix="@",
                cdata_key="#text",
            )
        elif isinstance(raw, dict):
            xml_dict = raw
        else:
            logging.error(
                f"[delete_project_dt_files] 지원하지 않는 data 타입: {type(raw)}"
            )
            return []

        # 2) dt_file 노드들 수집
        dt_file_nodes = self._collect_dt_file_nodes(xml_dict)

        # 3) 각 dt_file에서 삭제 대상 ObjectId 추출
        to_delete: Set[str] = set()
        for node in dt_file_nodes:
            # (a) 기본: <value>에 저장된 OID
            val = node.get("value")
            if self._is_valid_objectid(val):
                to_delete.add(val)
            elif val:
                logging.debug(f"[delete_project_dt_files] value가 OID 아님: {val}")

            # (b) 선택: keys 안에 들어간 추가 OID가 있을 수 있음 (예: log_doc_id 등)
            keys = node.get("keys")
            if isinstance(keys, list):
                for kv in keys:
                    if isinstance(kv, dict):
                        k = kv.get("key")
                        v = kv.get("value")
                        # 보수적으로: 키가 *_id 이거나 value가 OID로 유효하면 삭제 대상으로 간주
                        if (
                            k and k.endswith("_id") and self._is_valid_objectid(v)
                        ) or self._is_valid_objectid(v):
                            to_delete.add(v)
            elif isinstance(keys, dict):
                # 단일 <keys>일 수도 있음
                k = keys.get("key")
                v = keys.get("value")
                if (
                    k and k.endswith("_id") and self._is_valid_objectid(v)
                ) or self._is_valid_objectid(v):
                    to_delete.add(v)

        if not to_delete:
            logging.info(
                "[delete_project_dt_files] 삭제할 파일 ID 없음 (dt_file 존재 X 또는 OID 없음)"
            )
            return []

        # 4) 안전 삭제
        async def safe_delete(file_id: str):
            try:
                await self.repository.delete_file_by_id(file_id)
            except gridfs.errors.NoFile:
                logging.info(f"[delete_file_by_id] 파일이 존재하지 않음: {file_id}")
            except Exception as e:
                logging.error(f"[delete_file_by_id] 삭제 중 에러: {file_id} / {e}")

        await asyncio.gather(*(safe_delete(fid) for fid in to_delete))
        return list(to_delete)

    # ----------------- 내부 유틸 -----------------

    def _is_valid_objectid(self, value: Any) -> bool:
        try:
            ObjectId(str(value))
            return True
        except (InvalidId, TypeError):
            return False

    def _collect_dt_file_nodes(self, xml_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        xmltodict 파싱 결과에서 모든 dt_file 노드(dict)를 리스트로 수집.
        - @xsi:type == 'dt_file' 또는 'xsi:type' == 'dt_file' 둘 다 지원
        - dt_elements가 단일/리스트 모두 지원
        """
        try:
            dt_asset = xml_dict.get("dt_asset") or xml_dict.get(
                "{http://digital-thread.re/dt_asset}dt_asset"
            )
            if not isinstance(dt_asset, dict):
                return []

            elems = dt_asset.get("dt_elements")
            if elems is None:
                return []

            if isinstance(elems, dict):
                elems = [elems]

            out: List[Dict[str, Any]] = []
            for el in elems:
                if not isinstance(el, dict):
                    continue
                xtype = (
                    el.get("@xsi:type")
                    or el.get("xsi:type")
                    or el.get("@{http://www.w3.org/2001/XMLSchema-instance}type")
                )
                if xtype == "dt_file":
                    out.append(el)
            return out
        except Exception as e:
            logging.error(f"[_collect_dt_file_nodes] 수집 중 에러: {e}")
            return []

    async def delete_project_files(self, project: dict):
        """
        프로젝트 정보 내 연결된 파일 ObjectId 리스트를 추출해 전부 삭제.
        (프로젝트 내 여러 파일 종류별로 관리)
        """

        def is_valid_objectid(value):
            try:
                ObjectId(value)
                return True
            except (InvalidId, TypeError):
                return False

        file_ids = []
        for key, value in project.items():
            if key not in ["_id", "data"]:
                vals = value if isinstance(value, list) else [value]
                for v in vals:
                    if is_valid_objectid(v):
                        file_ids.append(v)
                    else:
                        logging.warning(
                            f"[delete_project_files] 무시되는 잘못된 파일ID: {v} (field: {key})"
                        )

        # 각 파일 삭제시, 없는 파일은 무시 (NoFile 예외 개별 처리)
        async def safe_delete(file_id):
            try:
                await self.repository.delete_file_by_id(file_id)
            except gridfs.errors.NoFile:
                logging.info(f"[delete_file_by_id] 파일이 존재하지 않음: {file_id}")
            except Exception as e:
                logging.error(
                    f"[delete_file_by_id] 삭제 중 알 수 없는 에러: {file_id} / {e}"
                )

        delete_tasks = [safe_delete(file_id) for file_id in file_ids]
        await asyncio.gather(*delete_tasks)
        return

    async def delete_file_by_id(self, file_id: str):
        """파일 ObjectId로 해당 파일을 삭제."""
        await self.repository.delete_file_by_id(file_id)
        return

    async def process_upload(self, file: UploadFile, metadata: Optional[dict] = None):
        """
        업로드 파일(UploadFile)을 읽어 GridFS에 저장, file_id 반환.
        """
        step_content = await file.read()
        filename = file.filename
        file_id = await self.repository.insert_file(
            step_content, filename, metadata=metadata
        )
        return file_id

    async def file_exist(self, file_id: str):
        """
        파일 존재 여부 확인. 없으면 예외 발생.
        """
        exists = await self.repository.file_exists(file_id)
        if not exists:
            raise CustomException(ExceptionEnum.NC_NOT_EXIST)
        return

    async def get_file_stream(self, file_id: str) -> str:
        """파일 ObjectId로 GridFS에서 파일 스트림 조회."""
        return await self.repository.get_file(file_id)

    async def stp_upload(self, step_file: UploadFile):
        """
        STEP 파일 업로드 후 STL로 변환, 둘 다 GridFS에 저장.
        변환된 파일 ID(dict) 반환: {"step_id": step_file_id, "stl_id": stl_file_id}
        """
        step_content = await step_file.read()
        filename = step_file.filename

        stl_filename = await self.stl_convert(step_content)  # STEP → STL 변환
        step_file_id = await self.repository.insert_file(step_content, filename)

        with open(stl_filename, "rb") as stl_file:
            stl_content = stl_file.read()
            stl_file_id = await self.repository.insert_file(
                stl_content, filename.replace(".STEP", ".stl")
            )

        os.remove(stl_filename)  # 임시 STL 파일 삭제

        return {"step_id": step_file_id, "stl_id": stl_file_id}

    async def stl_convert(self, step_content: bytes) -> str:
        """
        STEP 파일 바이너리를 STL 파일로 변환 (OpenCASCADE).
        변환된 임시 STL 파일 경로 반환 (호출부에서 직접 삭제 필요).
        """
        if not _OCC_AVAILABLE:
            raise RuntimeError(
                "OCC (pythonocc-core) is not installed. "
                "STEP-to-STL conversion is unavailable on this platform."
            )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".stp") as tmp_step:
            tmp_step.write(step_content)
            tmp_step_path = tmp_step.name

        reader = STEPControl_Reader()
        status = reader.ReadFile(tmp_step_path)

        if status == IFSelect_RetDone:
            reader.TransferRoots()
            shape = reader.Shape()

            mesh = BRepMesh_IncrementalMesh(shape, 0.1)
            mesh.Perform()

            stl_path = tmp_step_path.replace(".stp", ".stl")
            stl_writer = StlAPI_Writer()
            stl_writer.Write(shape, stl_path)

            os.remove(tmp_step_path)

            return stl_path

    async def convert_stp_to_cad(self, step_id: str, type: str) -> bytes:
        """
        STEP 파일을 CAD/GD&T 포맷(json)으로 변환.
        내부적으로 외부 DLL API 서버에 HTTP로 전달.
        type = "cad" or "gdt"
        """
        file_stream = await self.repository.get_file_byteio(step_id)
        filename = f"{step_id}.stp"
        result = await self._send_to_conversion_api(file_stream, filename, type)
        return result

    async def _send_to_conversion_api(
        self, file_bytes: BytesIO, filename: str, type: str
    ) -> bytes:
        """
        외부 DLL 서버에 파일을 POST로 전송하여 CAD/GD&T 변환 결과(json) 받기.
        실패시 예외 발생.
        """
        file_bytes.seek(0)
        files = {"file": (filename, file_bytes, "application/octet-stream")}
        async with httpx.AsyncClient() as client:
            if type == "cad":
                response = await client.post(
                    self.DLL_URI + "/convert/cad/", files=files
                )
            else:
                response = await client.post(
                    self.DLL_URI + "/convert/gdt/", files=files
                )
            response.raise_for_status()
            return response.content  # 변환 결과 bytes (json)

    async def get_file_text(self, file_id: str, encoding: str = "utf-8") -> str:
        bio = await self.repository.get_file_byteio(file_id)  # BytesIO 반환
        bio.seek(0)
        return bio.read().decode(encoding, errors="ignore")

    async def get_file_bytes(self, file_id: str) -> bytes:
        """GridFS에서 파일을 읽어 bytes로 반환."""
        bio = await self.repository.get_file_byteio(file_id)
        bio.seek(0)
        return bio.read()
