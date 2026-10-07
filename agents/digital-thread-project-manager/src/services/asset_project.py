import json
import os
import re
import uuid
from typing import Optional, Dict, Any, Tuple
from fastapi import UploadFile
import xmltodict
import xml.dom.minidom
from motor.motor_asyncio import AsyncIOMotorCollection
from src.models.schemas.project import ProjectListResponse
from src.models.entities.model_v27 import *
from src.utils.exceptions import CustomException, ExceptionEnum
from src.utils.asset_xml_parser import (
    create_feature_xml,
    validate_xml_against_schema,
    serializer,
)
import logging
from src.models.entities.project import ProjectRepository

from src.utils.stock import get_stock_code_by_name
from src.utils.nc_spliter import process_nc_file, extract_tool_numbers_from_paths
from src.utils.file_modifier import (
    zip_folder,
    create_prj_file,
    create_vm_project_name,
)


logger = logging.getLogger(__name__)
if not logger.handlers:  # 중복 핸들러 방지
    logging.basicConfig(
        level=logging.INFO,  # 필요시 DEBUG
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


class AssetProjectService:
    """
    프로젝트 생성, 조회, 삭제, 파일/캠 데이터 등록, XML 핸들링 등
    프로젝트 업무 전반을 담당하는 서비스 클래스.
    """

    _BRACKET_RE = re.compile(r"^(?P<tag>[^[]+)(?:\[(?P<idx>\d+)\])?$")
    _FILTER_RE = re.compile(
        r"^(?P<tag>[^[]+)\[@(?P<attr>[^=]+)=(?:'|\")(?P<val>[^'\"]+)(?:'|\")\]$"
    )
    _COMBO_RE = re.compile(
        r"^(?P<tag>[^\[]+)\[@(?P<attr>[^=]+)=(?:'|\")(?P<val>[^'\"]+)(?:'|\")\](?:\[(?P<idx>\d+)\])?$"
    )

    def __init__(self, collection: AsyncIOMotorCollection):
        # MongoDB collection 주입, 실제 작업은 ProjectRepository에 위임
        self.repository = ProjectRepository(collection)

    async def create_project_from_info(self, project_info: Dict[str, Any]) -> dict:
        """
        프로젝트 정보(dict)를 받아 완전한 dt_asset XML 구조를 생성하고 저장합니다.
        """
        project_id = project_info.get("its_id", f"project_{uuid.uuid4().hex[:8]}")

        dt_project_instance = DtProject(
            element_id=f"proj-{uuid.uuid4()}",
            category="Project",
            display_name=project_info.get("display_name", "New Project"),
            element_description=project_info.get(
                "element_description", "A dt_project instance."
            ),
            its_id=project_id,
            main_workplan=Workplan(
                its_id=f"WP_{project_id}",
                ref_dt_machine_tool=DtReference(
                    element_id="REF_MACHINE_DEFAULT",
                    category="Reference",
                    display_name="Default Machine Reference",
                    element_description="Reference to a default machine tool asset.",
                ),
            ),
            its_workpieces=[],
        )

        asset = DtAsset(
            asset_global_id=f"urn:uuid:{uuid.uuid4()}",
            id=f"ASSET_{project_id}",
            asset_kind=DtAssetKind.INSTANCE,
            dt_elements=[dt_project_instance],
        )

        xml_string = serializer.render(asset)

        project_data = await self.repository.insert_project(xml_string, project_id)
        if not project_data:
            raise CustomException(ExceptionEnum.PROJECT_CREATION_FAILED)
        return project_data

    async def create_project_from_xml(self, xml_string: str) -> dict:
        """
        입력받은 XML 문자열을 검증하고 신규 프로젝트로 생성합니다.
        """
        if not validate_xml_against_schema(xml_content=xml_string):
            raise CustomException(
                ExceptionEnum.INVALID_XML_FORMAT,
            )

        try:
            xml_dict = xmltodict.parse(xml_string)
            project_sub_dict = self._get_project_sub_dict(xml_dict)
            if not project_sub_dict or "its_id" not in project_sub_dict:
                raise KeyError("its_id not found in dt_project.")
            project_id = project_sub_dict["its_id"]
        except Exception as e:
            raise CustomException(ExceptionEnum.INVALID_XML_FORMAT)

        pretty_xml_string = self.save_xml_data(xml_dict)

        project_data = await self.repository.insert_project(
            pretty_xml_string, project_id
        )
        if not project_data:
            raise CustomException(ExceptionEnum.PROJECT_CREATION_FAILED)
        return project_data

    def _get_by_local(self, d: dict, local: str):
        """
        복사 없이 로컬명으로 dict 키 접근:
        - 'dt_asset' 또는 '{ns}dt_asset' 또는 'prefix:dt_asset' 모두 잡음.
        - 못 찾으면 None.
        """
        if not isinstance(d, dict):
            return None
        if local in d:
            return d[local]
        for k in d.keys():
            if isinstance(k, str) and (
                k.endswith("}" + local) or k.split(":")[-1] == local
            ):
                return d[k]
        return None

    def _set_by_local(self, d: dict, local: str, value):
        """
        복사 없이 로컬명으로 dict 키 설정:
        - 같은 로컬명의 기존 키가 있으면 그 키에 덮어씀(원본 키 보존).
        - 없으면 로컬명 키로 새로 추가.
        """
        if not isinstance(d, dict):
            raise TypeError("set_by_local target is not a dict")
        # 기존 키 중 로컬명이 같은 게 있으면 그 키로 덮어쓰기
        for k in list(d.keys()):
            if isinstance(k, str) and (
                k == local or k.endswith("}" + local) or k.split(":")[-1] == local
            ):
                d[k] = value
                return
        # 없으면 로컬명으로 새로 추가
        d[local] = value

    def _get_attr(self, d: dict, name: str):
        """속성 키도 '@xsi:type' / 'xsi:type' 둘 다 잡음."""
        if not isinstance(d, dict):
            return None
        return d.get("@" + name) or d.get(name)

    def _strip_ns_keys(self, obj):
        # dict 키에 붙은 {ns} 접두 제거 (dict 입력 대비)
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                nk = (
                    k.split("}", 1)[-1]
                    if isinstance(k, str) and k.startswith("{")
                    else k
                )
                out[nk] = self._strip_ns_keys(v)
            return out
        if isinstance(obj, list):
            return [self._strip_ns_keys(x) for x in obj]
        return obj

    def _get_project_sub_dict(self, xml_dict: dict) -> dict | None:
        """
        전체 dict에서 dt_project(내용물)를 '원본 참조'로 반환.
        - 새 구조: dt_asset/dt_elements[@xsi:type='dt_project']
        - (레거시가 있으면) project
        """
        # dt_asset
        dt_asset = self._get_by_local(xml_dict, "dt_asset")
        if isinstance(dt_asset, dict):
            elems = self._get_by_local(dt_asset, "dt_elements")
            if elems is None:
                return None
            items = elems if isinstance(elems, list) else [elems]

            # 표준: xsi:type 매칭
            for item in items:
                if (
                    isinstance(item, dict)
                    and self._get_attr(item, "xsi:type") == "dt_project"
                ):
                    return item  # ← 원본 참조

            # 예외: 'dt_project' 키로 중첩된 구조(있다면)
            for item in items:
                if isinstance(item, dict) and "dt_project" in item:
                    return item["dt_project"]

            return None

        # (레거시) project
        project = self._get_by_local(xml_dict, "project")
        return project if isinstance(project, dict) else None

    def _looks_like_workplan(self, node: dict) -> bool:
        # 스키마상 workplan의 특징(둘 중 하나라도)
        return isinstance(node, dict) and (
            "ref_dt_machine_tool" in node or "its_elements" in node
        )

    def _locate_workplan(self, project_node: dict, workplan_id: str):
        """
        프로젝트 트리에서 해당 workplan의 (parent_container, key_or_index)를 반환.
        - parent_container[key_or_index] 가 workplan dict (원본 참조).
        - 없으면 (None, None)
        """
        # 1) main_workplan 먼저
        main_wp = self._get_by_local(project_node, "main_workplan")
        if isinstance(main_wp, dict):
            its_id = self._get_by_local(main_wp, "its_id") or main_wp.get("its_id")
            if its_id == workplan_id:
                return (
                    project_node,
                    next(
                        k
                        for k in project_node.keys()
                        if k == "main_workplan"
                        or str(k).endswith("}main_workplan")
                        or str(k).split(":")[-1] == "main_workplan"
                    ),
                )
        if isinstance(main_wp, list):
            for i, wp in enumerate(main_wp):
                if isinstance(wp, dict) and (
                    wp.get("its_id") == workplan_id
                    or self._get_by_local(wp, "its_id") == workplan_id
                ):
                    return (main_wp, i)

        # 2) 다른 컨테이너 후보(있다면)
        for key in ("workplan", "workplans", "its_workplans"):
            cont = self._get_by_local(project_node, key)
            if isinstance(cont, dict) and (cont.get("its_id") == workplan_id):
                return (
                    project_node,
                    next(
                        k
                        for k in project_node.keys()
                        if k == key
                        or str(k).endswith("}" + key)
                        or str(k).split(":")[-1] == key
                    ),
                )
            if isinstance(cont, list):
                for i, wp in enumerate(cont):
                    if isinstance(wp, dict) and wp.get("its_id") == workplan_id:
                        return (cont, i)

        # 3) DFS: its_id 매칭 + workplan 형태
        stack = [(None, None, project_node)]
        while stack:
            parent, pkey, cur = stack.pop()
            if isinstance(cur, dict):
                its_id = cur.get("its_id") or self._get_by_local(cur, "its_id")
                if its_id == workplan_id and self._looks_like_workplan(cur):
                    return (
                        (parent, pkey)
                        if parent is not None
                        else ({"__root__": cur}, "__root__")
                    )
                for k, v in cur.items():
                    if isinstance(v, (dict, list)):
                        stack.append((cur, k, v))
            elif isinstance(cur, list):
                for i, it in enumerate(cur):
                    if isinstance(it, (dict, list)):
                        stack.append((cur, i, it))
        return (None, None)

    def save_xml_data(self, data: dict) -> str:
        """수정된 전체 딕셔너리(dt_asset 루트)를 예쁘게 포맷된 XML 문자열로 변환합니다."""
        if "dt_asset" in data and "@xmlns" not in data["dt_asset"]:
            data["dt_asset"]["@xmlns"] = "http://digital-thread.re/dt_asset"
            data["dt_asset"]["@xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"

        xml_string = xmltodict.unparse(data)
        try:
            dom = xml.dom.minidom.parseString(xml_string)
            pretty_xml = dom.toprettyxml(indent="  ")
            return "\n".join([line for line in pretty_xml.split("\n") if line.strip()])
        except Exception as e:
            logging.error(f"XML pretty printing failed: {e}")
            return xml_string

    def _find_operation_in_project(
        self, project_sub_dict: dict, workplan_id: str, operation_id: str
    ) -> Optional[dict]:
        try:
            main_workplan = project_sub_dict.get("main_workplan")
            if not main_workplan or main_workplan.get("its_id") != workplan_id:
                return None

            its_elements = main_workplan.get("its_elements", [])
            elements = (
                [its_elements] if isinstance(its_elements, dict) else its_elements
            )

            for element in elements:
                if element.get("@xsi:type") == "machining_workingstep":
                    operation = element.get("its_operation", {})
                    for op_type, op_details in operation.items():
                        if (
                            isinstance(op_details, dict)
                            and op_details.get("its_id") == operation_id
                        ):
                            return op_details
            return None
        except (AttributeError, TypeError, KeyError):
            return None

    def _find_workplan_in_project(
        self, project_sub_dict: dict, workplan_id: str
    ) -> Optional[dict]:
        # (이전 답변의 코드와 동일)
        try:
            main_workplan = project_sub_dict.get("main_workplan")
            if not main_workplan:
                return None

            if main_workplan.get("its_id") == workplan_id:
                return main_workplan

            its_elements = main_workplan.get("its_elements", [])
            elements = (
                [its_elements] if isinstance(its_elements, dict) else its_elements
            )

            for element in elements:
                if (
                    element.get("@xsi:type") == "workplan"
                    and element.get("its_id") == workplan_id
                ):
                    return element

            return None
        except (AttributeError, TypeError, KeyError):
            return None

    def _add_file_asset(
        self,
        xml_dict: Dict[str, Any],
        file_id: str,  # ← dt_file.value 로 들어갈 ID
        file_info: Dict[
            str, Any
        ],  # category, display_name, description, content_type, keys(옵션)
    ) -> Tuple[Dict[str, Any], str]:
        file_element_id = f"file-{file_info['category'].lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
        content_type = file_info.get("content_type") or "application/octet-stream"

        new_file_asset = {
            "@xsi:type": "dt_file",
            "element_id": file_element_id,
            "category": file_info["category"],
            "display_name": file_info["display_name"],
            "element_description": file_info["description"],
            "content_type": content_type,
            "value": file_id,  # ← TDMS 로그의 Mongo ObjectId
        }

        extra_keys = file_info.get("keys")
        if extra_keys:
            new_file_asset["keys"] = (
                extra_keys  # 예: [{"key":"raw","value":"file:///..."}]
            )

        dt_asset = xml_dict.setdefault("dt_asset", {})
        dt_elems = dt_asset.setdefault("dt_elements", [])
        if not isinstance(dt_elems, list):
            dt_asset["dt_elements"] = [dt_elems]
            dt_elems = dt_asset["dt_elements"]

        dt_elems.append(new_file_asset)
        return xml_dict, file_element_id

    async def nc_upload(
        self,
        project: dict,
        workplan_id: str,
        file_id: str,
        filename: str,
    ) -> dict:
        """
        1) dt_file 자산으로 NC 파일을 추가.
        2) 해당 파일을 Workplan.ref_dt_nc_file (DtReference 리스트)로 연결.
        3) DB 업데이트 후 최신 프로젝트 반환.
        """
        # 0) XML 로드
        raw = project["data"]
        xml_dict = xmltodict.parse(raw) if isinstance(raw, (bytes, str)) else raw

        # 1) dt_file 자산 추가
        file_info = {
            "category": "NC Code",
            "display_name": filename,
            "description": "NC program file (uploaded).",
            "content_type": "text/x-gcode",
        }
        xml_dict, dt_file_element_id = self._add_file_asset(
            xml_dict, file_id, file_info
        )

        # 2) 프로젝트/워크플랜 찾기
        project_sub = self._get_project_sub_dict(xml_dict)
        if not project_sub:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                detail="dt_project not found for referencing.",
            )
        parent, key = self._locate_workplan(project_sub, workplan_id)
        if parent is None:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                detail=f"Workplan '{workplan_id}' not found.",
            )
        wp = parent[key]

        # 3) ref_dt_nc_file 다중 append
        ref_value = {
            "element_id": dt_file_element_id,
            "category": "file",
            "display_name": filename,
            "element_description": "Reference to uploaded NC dt_file asset.",
            "keys": [
                {"key": "dt_file_id", "value": file_id},
            ],
        }
        self._append_multi_ref(wp, "ref_dt_nc_file", ref_value)

        # 4) 저장/반환
        updated_xml = self.save_xml_data(xml_dict)
        ok = await self.repository.update_project_data(project["_id"], updated_xml)
        if not ok:
            raise CustomException(ExceptionEnum.PROJECT_UPLOAD_FAILED)
        return await self.repository.get_project_by_id(str(project["_id"]))

    async def tdms_upload(
        self,
        project: dict,
        workplan_id: str,
        log_file_oid: str,  # ← TDMS 로그의 Mongo ObjectId (dt_file.value로 사용)
        filename: str,
        *,
        raw_path: str,  # ← 원본 경로/URI (dt_file.keys.raw로 사용)
    ) -> dict:
        # 0) XML 로드
        raw = project["data"]
        xml_dict = xmltodict.parse(raw) if isinstance(raw, (bytes, str)) else raw

        # 1) dt_file 자산 추가: value=log_file_oid, keys.raw=raw_path
        file_info = {
            "category": "TDMS",
            "display_name": filename,
            "description": "TDMS measurement file (uploaded).",
            "content_type": "application/x-tdms",
            "keys": [{"key": "raw", "value": raw_path}],
        }
        xml_dict, dt_file_element_id = self._add_file_asset(
            xml_dict, log_file_oid, file_info
        )

        # 2) 프로젝트/워크플랜 찾기
        project_sub = self._get_project_sub_dict(xml_dict)
        if not project_sub:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE, detail="dt_project not found."
            )
        parent, key = self._locate_workplan(project_sub, workplan_id)
        if parent is None:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                detail=f"Workplan '{workplan_id}' not found.",
            )
        wp = parent[key]

        # 3) ref_dt_tdms_file 다중 append (dt_file_id + raw 둘 다 보존)
        ref_value = {
            "element_id": dt_file_element_id,
            "category": "file",
            "display_name": filename,
            "element_description": "Reference to uploaded TDMS dt_file asset.",
            "keys": [
                {"key": "dt_file_id", "value": log_file_oid},
                {"key": "raw", "value": raw_path},
            ],
        }
        self._append_multi_ref(wp, "ref_dt_tdms_file", ref_value)

        # 4) 저장/반환
        updated_xml = self.save_xml_data(xml_dict)
        ok = await self.repository.update_project_data(project["_id"], updated_xml)
        if not ok:
            raise CustomException(ExceptionEnum.PROJECT_UPLOAD_FAILED)
        return await self.repository.get_project_by_id(str(project["_id"]))

    async def get_project_list(self) -> ProjectListResponse:
        """
        전체 프로젝트 목록 조회 (project_id만 반환).
        """
        projects = await self.repository.get_dtasset_project_list()
        project_ids = [str(project["_id"]) for project in projects]
        return ProjectListResponse(project_id=project_ids)

    async def get_project_by_id(self, xml_string: str):
        """
        프로젝트 ID로 프로젝트 조회.
        """
        project = await self.repository.get_project_by_id(xml_string)
        if not project:
            raise CustomException(ExceptionEnum.PROJECT_NOT_FOUND)
        return project

    async def delete_project_by_id(self, project_id: str) -> None:
        """
        프로젝트 삭제. 실패 시 예외 발생.
        """
        deleted = await self.repository.delete_project_by_id(project_id)
        if not deleted:
            raise CustomException(ExceptionEnum.PROJECT_DELETE_FAILED)
        return

    async def file_upload(self, project_id: str, file_id: str, file_type: str):
        """
        프로젝트에 파일(ObjectId) 연결. file_type에 따라 필드 결정.
        """
        status = await self.repository.add_file_to_project(
            project_id, file_id, file_type
        )
        if not status:
            raise CustomException(ExceptionEnum.STP_UPLOAD_FAILED)
        return

    async def _insert_to_workplan_element(
        self, data: dict, workplan_id: str, payload: dict
    ) -> bool:
        """
        data: xmltodict.parse(...) 결과 또는 그에 준하는 dict
        workplan_id: WP의 its_id
        payload: workplan에 삽입할 요소(예: ref_dt_nc_file)
        """
        project_node = self._get_project_sub_dict(data)
        if not project_node:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                detail="dt_project (or legacy project) not found.",
            )

        main_workplan = project_node.get("main_workplan")
        if not main_workplan:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE, detail="main_workplan not found."
            )

        # its_id가 workplan_id인지 확인(여러 workplan을 지원한다면 검색 로직 필요)
        if main_workplan.get("its_id") != workplan_id:
            # 다중 워크플랜을 지원한다면 여기서 리스트 탐색으로 확장
            pass

        # 여기서 payload 반영 (예: ref_dt_nc_file)
        # payload = {"ref_dt_nc_file": {...}} 같은 dict라고 가정
        for k, v in payload.items():
            main_workplan[k] = v

        return True

    async def vm_upload(
        self,
        project: dict,
        workplan_id: str,
        file_id: str,
        filename: str,
    ) -> dict:
        """
        1) dt_file 자산으로 VM 파일을 추가.
        2) 해당 파일을 Workplan.ref_dt_vm_file (DtReference, 다중 허용)로 연결.
        3) DB 업데이트 후 최신 프로젝트 반환.
        """
        # 0) XML 로드 (원본 유지)
        raw = project["data"]
        xml_dict = xmltodict.parse(raw) if isinstance(raw, (bytes, str)) else raw

        # 1) dt_file 자산 추가: value=file_id
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext in ("zip",):
            content_type = "application/zip"
        elif ext in ("prj",):
            content_type = "application/octet-stream"  # 별도 표준 MIME 없음
        else:
            content_type = "application/octet-stream"

        file_info = {
            "category": "VM",
            "display_name": filename,
            "description": "VM project file (uploaded).",
            "content_type": content_type,
            # keys 필요시 여기에 추가 가능(예: 원본 경로나 부가정보)
        }
        xml_dict, dt_file_element_id = self._add_file_asset(
            xml_dict, file_id, file_info
        )

        # 2) 프로젝트/워크플랜 찾기 (원본 참조 유지)
        project_sub = self._get_project_sub_dict(xml_dict)
        if not project_sub:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE, detail="dt_project not found."
            )

        parent, key = self._locate_workplan(project_sub, workplan_id)
        if parent is None:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                detail=f"Workplan '{workplan_id}' not found.",
            )

        wp = parent[key]

        # 3) 워크플랜 참조(ref_dt_vm_file) 다중 append
        ref_value = {
            "element_id": dt_file_element_id,
            "category": "file",
            "display_name": filename,
            "element_description": "Reference to uploaded VM dt_file asset.",
            "keys": [
                {"key": "dt_file_id", "value": file_id},
            ],
        }
        self._append_multi_ref(wp, "ref_dt_vm_file", ref_value)

        # 4) 저장/반환
        updated_xml = self.save_xml_data(xml_dict)
        ok = await self.repository.update_project_data(project["_id"], updated_xml)
        if not ok:
            raise CustomException(ExceptionEnum.PROJECT_UPLOAD_FAILED)
        return await self.repository.get_project_by_id(str(project["_id"]))

    def _append_multi_ref(self, node: dict, tag: str, ref_value: dict):
        """
        같은 태그(tag)를 여러 번 나열할 수 있게 해준다.
        - 태그가 없으면 [ref_value]로 생성
        - dict(단일)이면 [기존, ref_value]로 리스트 승격
        - list면 append
        네임스페이스 섞임을 고려해 _get_child/_set_by_local 사용.
        """
        current = self._get_child(node, tag) if isinstance(node, dict) else None
        if current is None:
            self._set_by_local(node, tag, [ref_value])
            return
        if isinstance(current, list):
            current.append(ref_value)
            return
        # dict → list 승격
        self._set_by_local(node, tag, [current, ref_value])

    async def add_cam_to_project(
        self,
        project: dict,
        cam_type: str,
        cam_json_file: UploadFile,
        mapping_json_file: UploadFile,
    ):
        try:
            json_text = (await cam_json_file.read()).decode("utf-8-sig")
            mapping_text = (await mapping_json_file.read()).decode("utf-8-sig")
            parsed_data = json.loads(json_text)
            mapping_data = json.loads(mapping_text)
        except Exception as e:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE, detail=f"CAM/MAPPING 파싱 실패: {e}"
            )

        # 전체 XML 딕셔너리 로드
        xml_dict = xmltodict.parse(project["data"])

        # project 부분만 추출
        project_sub_dict = self._get_project_sub_dict(xml_dict)
        if not project_sub_dict:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE, detail="dt_project not found in XML."
            )

        # main_workplan 및 its_elements 초기화 보장
        main_workplan = project_sub_dict.setdefault("main_workplan", {})
        its_elements = main_workplan.setdefault("its_elements", [])
        if not isinstance(its_elements, list):
            main_workplan["its_elements"] = [its_elements]

        cam_data_list = (
            parsed_data.get("values", [])
            if cam_type.lower() == "nx"
            else ([parsed_data] if isinstance(parsed_data, dict) else parsed_data)
        )

        if not cam_data_list:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,  # 또는 새로운 Enum: EMPTY_CAM_DATA
                detail=f"CAM 데이터(values)가 비어 있습니다. cam_type={cam_type}",
            )

        # 변환된 CAM 데이터를 its_elements에 추가
        for data_item in cam_data_list:
            feature_xml = create_feature_xml(data_item, mapping_data)
            feature_dict = xmltodict.parse(feature_xml)
            if "its_elements" in feature_dict:
                main_workplan["its_elements"].append(feature_dict["its_elements"])

        # 수정된 전체 딕셔너리를 XML로 변환
        update_data = self.save_xml_data(xml_dict)

        success = await self.repository.update_project_data(project["_id"], update_data)
        if not success:
            raise CustomException(ExceptionEnum.PROJECT_UPLOAD_FAILED)
        return

    def xml_to_dict(self, project_xml: str):
        """프로젝트 XML을 dict로 변환."""
        project_dict = xmltodict.parse(project_xml)
        return project_dict

    def get_inner_data(self, project: Any, path: str) -> str:
        """
        XML(문자열/바이트) 또는 이미 파싱된 dict에서 특정 경로를 추출해 XML 문자열로 반환.
        - 올바르지 않은 경로/노드 없음 등은 500 대신 <error> XML로 반환.
        - 새 구조(dt_asset)와 옛 구조(project) 모두 지원.
        """
        try:
            # 1) 입력 파싱
            if isinstance(project, (bytes, str)):
                doc = xmltodict.parse(
                    project,
                    process_namespaces=True,
                    namespaces={
                        "http://digital-thread.re/dt_asset": None,
                        "http://digital-thread.re/iso14649": None,
                        "http://www.w3.org/2001/XMLSchema-instance": "xsi",
                    },
                    attr_prefix="@",
                    cdata_key="#text",
                )
            elif isinstance(project, dict):
                doc = project
            else:
                return self._error_xml(
                    code="UNSUPPORTED_INPUT",
                    path=path,
                    detail=f"Unsupported project type: {type(project)}",
                )

            # 2) 토크나이즈
            try:
                tokens = self._tokenize(path)
                if not tokens:
                    return self._error_xml(
                        code="EMPTY_PATH",
                        path=path,
                        detail="경로가 비어 있습니다.",
                    )
            except re.error as e:
                return self._error_xml(
                    code="PATH_PARSE_ERROR",
                    path=path,
                    detail=f"경로 파싱 실패: {e}",
                )

            # 3) 루트 언랩 및 첫 토큰 스킵
            root_local = None
            if isinstance(doc, dict) and len(doc) == 1:
                only_key = next(iter(doc))
                local = (
                    only_key.split("}", 1)[-1] if only_key.startswith("{") else only_key
                )
                if local in ("dt_asset", "project"):
                    cur = doc[only_key]
                    root_local = local
                else:
                    cur = doc
            else:
                cur = doc

            if tokens and root_local and tokens[0]["tag"] == root_local:
                tokens = tokens[1:]

            # 4) 경로 적용
            try:
                for step in tokens:
                    cur = self._apply_step(cur, step)
            except IndexError as e:
                return self._error_xml(
                    code="INDEX_ERROR",
                    path=path,
                    detail=str(e),
                )
            except KeyError as e:
                # 내부에서 raise KeyError("태그 없음: ...") 등
                return self._error_xml(
                    code="NODE_NOT_FOUND",
                    path=path,
                    detail=str(e),
                )
            except TypeError as e:
                # 리스트/딕트 타입 미스 등
                return self._error_xml(
                    code="TYPE_ERROR",
                    path=path,
                    detail=str(e),
                )

            # 5) 직렬화 (리스트 안전 직렬화)
            wrapper_name = next(
                (t["tag"] for t in reversed(tokens) if t["tag"]), root_local or "result"
            )
            if isinstance(cur, list):
                return self._safe_unparse_list(wrapper_name, cur)
            else:
                return xmltodict.unparse(
                    {wrapper_name: cur}, pretty=True, attr_prefix="@"
                )

        except Exception as e:
            # 예기치 못한 모든 오류는 500 대신 에러 XML로 감싼다.
            return self._error_xml(
                code="INTERNAL_ERROR",
                path=path,
                detail=f"{type(e).__name__}: {e}",
            )

    # ------------- 내부 유틸 -------------

    def _tokenize(self, path: str):
        toks = []
        for raw in filter(None, path.split("/")):
            # 필터+인덱스 동시
            m = self._COMBO_RE.match(raw)
            if m:
                toks.append(
                    {
                        "tag": m.group("tag"),
                        "index": int(m.group("idx")) if m.group("idx") else None,
                        "filter": (f"@{m.group('attr')}", m.group("val")),
                    }
                )
                continue
            # 필터만
            m = self._FILTER_RE.match(raw)
            if m:
                toks.append(
                    {
                        "tag": m.group("tag"),
                        "index": None,
                        "filter": (f"@{m.group('attr')}", m.group("val")),
                    }
                )
                continue
            # 인덱스만
            m = self._BRACKET_RE.match(raw)
            if m:
                toks.append(
                    {
                        "tag": m.group("tag"),
                        "index": int(m.group("idx")) if m.group("idx") else None,
                        "filter": None,
                    }
                )
                continue
            # 순수 숫자 세그먼트 → 인덱스 접근 (※ XPath 표준은 아니지만 기존 커스텀 문법 지원 시)
            if raw.isdigit():
                toks.append({"tag": None, "index": int(raw), "filter": None})
            else:
                toks.append({"tag": raw, "index": None, "filter": None})
        return toks

    def _apply_step(self, cur, step):
        # 인덱스 전용 세그먼트
        if step["tag"] is None:
            if not isinstance(cur, list):
                raise KeyError("현재 노드는 리스트가 아닙니다. (인덱스로 접근 불가)")
            if step["index"] < 0 or step["index"] >= len(cur):
                raise IndexError(f"인덱스 범위를 벗어났습니다: {step['index']}")
            return cur[step["index"]]

        # 자식 찾기 (네임스페이스 안전)
        node = self._get_child(cur, step["tag"]) if isinstance(cur, dict) else None
        if node is None:
            raise KeyError(f"태그 없음: {step['tag']}")

        # 리스트 노드 처리
        if isinstance(node, list):
            # 속성 필터
            if step["filter"]:
                k, v = step["filter"]
                matches = [it for it in node if isinstance(it, dict) and it.get(k) == v]
                if not matches:
                    raise KeyError(f"필터 불일치: {step['tag']}[{k}={v}]")
                if step["index"] is not None:
                    if step["index"] < 0 or step["index"] >= len(matches):
                        raise IndexError(f"인덱스 범위를 벗어났습니다: {step['index']}")
                    return matches[step["index"]]
                # ✅ 인덱스가 없으면 리스트 전체 반환 (후속 '/0' 같은 세그먼트를 위해 축약 금지)
                return matches
            # 인덱스만
            if step["index"] is not None:
                if step["index"] < 0 or step["index"] >= len(node):
                    raise IndexError(f"인덱스 범위를 벗어났습니다: {step['index']}")
                return node[step["index"]]
            # 필터/인덱스 없음 → 리스트 그대로
            return node

        # 딕셔너리 노드 처리
        if step["index"] is not None:
            raise KeyError(
                f"리스트가 아닌 노드에 인덱스 접근: {step['tag']}[{step['index']}]"
            )
        if step["filter"]:
            k, v = step["filter"]
            if not (isinstance(node, dict) and node.get(k) == v):
                raise KeyError(f"필터 불일치: {step['tag']}[{k}={v}]")
        return node

    def _get_child(self, cur: dict, tag: str):
        # 1) 로컬명
        if tag in cur:
            return cur[tag]
        # 2) '{ns}tag'
        for k in cur.keys():
            if isinstance(k, str) and k.endswith("}" + tag):
                return cur[k]
        # 3) 'ns:tag'
        for k in cur.keys():
            if isinstance(k, str) and k.split(":")[-1] == tag:
                return cur[k]
        return None

    def _safe_unparse_list(self, item_tag: str, items: list) -> str:
        """
        <item_tag_list>
          <item_tag>...</item_tag>
          <item_tag>...</item_tag>
        </item_tag_list>
        형태로 안전 직렬화.
        """
        norm = []
        for it in items:
            if isinstance(it, dict):
                norm.append(it)
            else:
                norm.append({"#text": str(it)})
        payload = {f"{item_tag}_list": {item_tag: norm}}
        return xmltodict.unparse(payload, pretty=True, attr_prefix="@")

    def _error_xml(self, code: str, path: str, detail: str) -> str:
        """에러를 XML로 감싸 반환 (HTTP 200 본문으로 내려 500 방지)."""
        err = {
            "error": {
                "code": code,
                "path": path,
                "message": detail,
            }
        }
        return xmltodict.unparse(err, pretty=True, attr_prefix="@")

    def get_nested_attribute(self, data, attributes):
        """
        dict/list 구조에서 attribute 경로 따라 하위 요소 접근.
        """
        for attr in attributes:
            if isinstance(data, dict):
                data = data.get(attr, None)
            elif isinstance(data, list) and attr.isdigit():
                data = data[int(attr)] if len(data) > int(attr) else None
            else:
                return None
        return data

    def _as_list(self, x):
        if x is None:
            return []
        return x if isinstance(x, list) else [x]

    def _extract_keys_list(self, ref_node: dict) -> list[dict]:
        """
        <keys><key>..</key><value>..</value></keys> 가
        여러 번 나올 수 있음. (dict 또는 list로 파싱될 수 있으니 정규화)
        """
        keys = ref_node.get("keys")
        keys_list = self._as_list(keys)
        # xmltodict 특성상 <keys>가 텍스트만 담는 형태라면 dict에 'key','value'가 있음
        # (이미 dict면 그대로, list면 각 item이 dict)
        return [k for k in keys_list if isinstance(k, dict)]

    def _resolve_ref_tag(self, file_type: str) -> str:
        """
        'nc' | 'tdms' | 'vm' → ref tag 이름으로 변환
        """
        m = {
            "nc": "ref_dt_nc_file",
            "tdms": "ref_dt_tdms_file",
            "vm": "ref_dt_vm_file",
        }
        tag = m.get(file_type.lower())
        if not tag:
            # 필요시 확장
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                detail=f"Unsupported file_type: {file_type}",
            )
        return tag

    def valid_file_id(self, data: dict, workplan_id: str, file_id: str, file_type: str):
        """
        dt_asset 구조 기준:
        - dt_project/main_workplan (또는 대상 workplan) 아래의 ref_dt_*_file 들에서
        keys.key == 'dt_file_id' && keys.value == file_id 인 항목이 존재하는지 확인.
        - 없으면 예외 발생.
        """
        # 1) XML 파싱
        xml_dict = self.xml_to_dict(data["data"])

        # 2) dt_project 서브트리(원본 참조) 찾기
        project_sub = self._get_project_sub_dict(xml_dict)
        if not project_sub:
            logging.warning("[valid_file_id] dt_project not found")
            raise CustomException(ExceptionEnum.INVALID_ATTRIBUTE)

        # 3) 워크플랜 찾기
        parent, key = self._locate_workplan(project_sub, workplan_id)
        if parent is None:
            logging.warning(f"[valid_file_id] workplan not found: {workplan_id}")
            raise CustomException(ExceptionEnum.INVALID_ATTRIBUTE)
        wp = parent[key]

        # 4) 파일 타입 → ref 태그 결정
        ref_tag = self._resolve_ref_tag(file_type)

        # 5) ref 노드(단일/리스트) 정규화
        refs = self._as_list(wp.get(ref_tag))

        # 6) 매칭 검사 (keys.dt_file_id == file_id)
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            for kv in self._extract_keys_list(ref):
                if kv.get("key") == "dt_file_id" and kv.get("value") == file_id:
                    return  # 발견 → 정상 종료

        # 7) 여기까지 못 찾았으면 실패
        raise CustomException(ExceptionEnum.NO_DATA_FOUND)

    def get_tdms_list(self, data: str, workplan_id: str) -> list[str]:
        """
        dt_asset 기반 프로젝트에서, 지정한 workplan의 ref_dt_tdms_file 안에 있는
        keys/raw 값들을 리스트로 반환.
        - 우선 workplan의 ref_dt_tdms_file.keys에서 raw를 수집
        - 없으면 dt_file 자산(dt_asset/dt_elements[@xsi:type='dt_file'])을 뒤져서
        element_id 매칭 후 keys.raw를 수집 (fallback)
        """
        # 1) XML 파싱
        xml_dict = self.xml_to_dict(data["data"])

        # 2) dt_project 가져오기 (네임스페이스 안전)
        proj = self._get_project_sub_dict(xml_dict)
        if not proj:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE, detail="dt_project not found."
            )

        # 3) workplan 찾기 (원본 참조)
        parent, key = self._locate_workplan(proj, workplan_id)
        if parent is None:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                detail=f"Workplan '{workplan_id}' not found.",
            )
        wp = parent[key]

        # -------- 유틸: keys 구조에서 raw 추출 --------
        def _extract_raw_from_keys(keys_node) -> list[str]:
            if not keys_node:
                return []
            items = keys_node if isinstance(keys_node, list) else [keys_node]
            raws = []
            for it in items:
                # <keys><key>raw</key><value>...</value></keys>
                if isinstance(it, dict) and it.get("key") == "raw":
                    val = it.get("value")
                    if val:
                        raws.append(val)
            return raws

        raws: list[str] = []

        # 4) workplan 내 ref_dt_tdms_file에서 raw 수집
        ref_node = self._get_by_local(wp, "ref_dt_tdms_file")
        if ref_node:
            refs = ref_node if isinstance(ref_node, list) else [ref_node]
            # dt_file element_id도 모아 fallback에 활용
            ref_element_ids = []
            for ref in refs:
                # 수집 1) keys.raw
                raws.extend(_extract_raw_from_keys(self._get_by_local(ref, "keys")))
                # 수집 2) element_id (dt_file 자산 역참조용)
                eid = self._get_by_local(ref, "element_id") or ref.get("element_id")
                if eid:
                    ref_element_ids.append(eid)
        else:
            refs = []
            ref_element_ids = []

        # 5) raw가 아직 없으면, dt_file 자산에서 element_id 매칭해 keys.raw 추출 (fallback)
        if not raws and ref_element_ids:
            dt_asset = self._get_by_local(xml_dict, "dt_asset") or {}
            dt_elems = self._get_by_local(dt_asset, "dt_elements")
            elems = (
                dt_elems
                if isinstance(dt_elems, list)
                else ([dt_elems] if dt_elems else [])
            )
            for el in elems:
                if not isinstance(el, dict):
                    continue
                if (el.get("@xsi:type") or el.get("xsi:type")) == "dt_file":
                    eid = self._get_by_local(el, "element_id") or el.get("element_id")
                    if eid and eid in ref_element_ids:
                        raws.extend(
                            _extract_raw_from_keys(self._get_by_local(el, "keys"))
                        )

        # 6) 정리해서 반환 (중복 제거 원하면 set 사용)
        return [r for r in raws if r]

    def extract_material_identifier(self, project: dict) -> list[str]:
        """
        XML에서 소재 이름(material_identifier)을 추출합니다.
        여러 workpiece가 존재할 경우 리스트로 반환합니다.
        """
        data = project["data"]
        xml_dict = xmltodict.parse(data)
        try:
            workpieces = xml_dict["project"]["its_workpieces"]["workpiece"]

            # 단일 workpiece일 경우 dict, 여러 개일 경우 list
            if isinstance(workpieces, dict):
                workpieces = [workpieces]

            material_names = []
            for wp in workpieces:
                name = wp.get("its_material", {}).get("material_identifier")
                if name:
                    material_names.append(name)
            return material_names
        except Exception as e:
            raise ValueError(f"소재 이름 추출 실패: {e}")

    def extract_rawpiece_bounding_box(self, project: dict) -> list[float] | str:
        """
        rawpiece 영역의 좌표를 순서대로 [min_x, min_y, min_z, max_x, max_y, max_z]로 반환.
        값이 하나라도 없으면 오류 메시지를 반환.
        """
        data = project["data"]
        xml_dict = xmltodict.parse(data)

        try:
            workpiece = xml_dict["project"]["its_workpieces"]["workpiece"]
            if isinstance(workpiece, list):
                workpiece = workpiece[0]

            parameters = workpiece["its_rawpiece"]["its_geometry"][
                "advanced_brep_shape_representation"
            ]["workpiece_property"]["numeric_parameter"]
            if isinstance(parameters, dict):
                parameters = [parameters]

            coord_map = {
                p["parameter_name"]: float(p["its_parameter_value"]) for p in parameters
            }

            keys = ["min_x", "min_y", "min_z", "max_x", "max_y", "max_z"]
            if not all(k in coord_map for k in keys):
                return "소재 정보를 추출할 수 없습니다."

            return [coord_map[k] for k in keys]
        except Exception:
            return "소재 정보를 추출할 수 없습니다."

    def extract_material_code(self, project: dict) -> int | str:
        """
        XML에서 소재 이름을 추출하고, 대응되는 소재 코드(int)를 반환.
        해당 코드가 없으면 메시지를 반환.
        """
        data = project["data"]
        try:
            xml_dict = xmltodict.parse(data)
            workpiece = xml_dict["project"]["its_workpieces"]["workpiece"]

            # 단일 또는 리스트 구조 대응
            if isinstance(workpiece, list):
                workpiece = workpiece[0]

            material_name = workpiece.get("its_material", {}).get("material_identifier")
            if not material_name:
                return "소재 정보를 추출할 수 없습니다."

            code = get_stock_code_by_name(material_name)
            return code if code is not None else "해당 소재 코드가 존재하지 않습니다."
        except Exception:
            return "소재 정보를 추출할 수 없습니다."

    def extract_tool_summary_list(self, project: dict) -> list[list]:
        """
        프로젝트 XML에서 main_workplan 아래 its_elements에 있는 툴 정보를 추출하여 리스트 반환.
        [툴번호, dia, rad, edis, fdis, bangle, sangle, 툴길이, 툴날수]
        """
        try:
            xml_dict = xmltodict.parse(project["data"])
            elements = (
                xml_dict["project"].get("main_workplan", {}).get("its_elements", [])
            )
            if isinstance(elements, dict):
                elements = [elements]

            result = []

            for el in elements:
                op = el.get("its_operation", {})
                tool = op.get("its_tool", {})
                tool_id = tool.get("its_id", "UNKNOWN")
                dia = float(tool.get("effective_cutting_diameter", 0))
                rad = float(tool.get("edge_radius", 0))

                # 날 수 정보가 없으면 1로 처리
                flutes = (
                    int(tool.get("number_of_effective_teeth", 1))
                    if "number_of_effective_teeth" in tool
                    else 1
                )

                # cutting edge (툴 길이)
                cutting_edge = tool.get("its_cutting_edges", {}).get(
                    "tool_functional_length", 0
                )
                if isinstance(cutting_edge, list):
                    tool_len = float(cutting_edge[0])
                else:
                    tool_len = float(cutting_edge)

                # eDis, fDis 값 계산하여 추가
                e_dis = (dia / 2) - rad  # 직경 / 2 - 코너 반경
                f_dis = rad  # 코너 곡률 90' 이하로 가정

                result.append([tool_id, dia, rad, e_dis, f_dis, 0, 0, tool_len, flutes])

            return result
        except Exception:
            logger.exception("툴 정보 추출 실패")
            return []

    async def process_project_vm(self, project: dict, file_service) -> list[list]:
        """
        1. 프로젝트에서 main_workplan 안에 NC 파일 존재 확인
        2. 없으면 예외
        3. 있으면 get_file_stream으로 NC 가져오기
        4. tmp/프로젝트이름/ 에 저장
        5. nc_spliter로 tmp/프로젝트이름/ncdata 에 분할 저장
        6. 분할된 NC 파일에서 툴번호 순서대로 추출
        7. extract_tool_summary_list() 호출로 툴 정보 가져오기
        8. 개수 다르면 raise
        9. 툴 정보에 순서대로 툴 번호 입력
        """
        # 1~2. NC ID 확인
        xml_dict = self.xml_to_dict(project["data"])
        main_workplan = xml_dict.get("project", {}).get("main_workplan", {})
        nc_codes = main_workplan.get("nc_code")
        if not nc_codes:
            raise CustomException(ExceptionEnum.NO_DATA_FOUND)
        if isinstance(nc_codes, dict):
            nc_codes = [nc_codes]

        nc_id = nc_codes[0].get("its_id")
        if not nc_id:
            raise CustomException(ExceptionEnum.NO_DATA_FOUND)

        # 3. NC 파일 가져오기
        nc_stream = await file_service.get_file_stream(nc_id)
        nc_bytes = await nc_stream.read()

        # 3.5 프로젝트 폴더 이름 민들기
        project_folder_name = create_vm_project_name()

        # 4. NC 파일 저장
        project_id = xml_dict["project"].get("its_id", "unnamed_project")
        base_path = os.path.join("tmp", project_folder_name)
        os.makedirs(base_path, exist_ok=True)
        nc_path = os.path.join(base_path, f"{project_id}.nc")
        with open(nc_path, "wb") as f:
            f.write(nc_bytes)

        # 5. 툴별로 분할
        split_path = os.path.join(base_path, "ncdata")
        os.makedirs(split_path, exist_ok=True)
        split_files = process_nc_file(nc_path, split_path)

        # 6. nc 파일 압축
        nc_zip_path = os.path.join(base_path, "ncdata.zip")
        nc_zip_path = zip_folder(split_path, nc_zip_path)

        # 6. 툴 번호 추출 (숫자)
        tool_numbers = extract_tool_numbers_from_paths(split_files)

        # 7. 프로젝트 툴 정보 가져오기
        tool_infos = self.extract_tool_summary_list(project)

        # 8. 개수 확인
        if len(tool_numbers) != len(tool_infos):
            raise CustomException(ExceptionEnum.INVALID_ATTRIBUTE)

        # 9. 툴 정보에 툴 넘버 할당
        for idx, info in enumerate(tool_infos):
            tnum = tool_numbers[idx]
            info[0] = tnum

        # 10. 소재 타입 가져오기
        stock_type = self.extract_material_code(project)

        # 11. 소재 사이즈 가져오기
        stock_coords = self.extract_rawpiece_bounding_box(project)

        # 12. 프로젝트 파일 만들기
        prj_file_path = os.path.join(base_path, f"{project_id}.prj")
        project_file_path = create_prj_file(
            stock_type=stock_type,
            stock_coords=stock_coords,
            nc_file_paths=split_files,
            tool_infos=tool_infos,
            output_path=prj_file_path,
        )

        # # 13. s3에 프로젝트 파일, nc파일 업로드
        # project_s3_path = vm_file_s3_upload(
        #     file_path=project_file_path, parent_path=project_folder_name
        # )
        # project_s3_path = project_s3_path["file_url"]
        # nc_s3_path = vm_file_s3_upload(
        #     file_path=nc_zip_path, parent_path=project_folder_name
        # )
        # nc_s3_path = nc_s3_path["file_url"]

        # 임시코드
        project_s3_path = "https://kitech-file.s3.ap-northeast-2.amazonaws.com/2025-07-02_ap_4_34_05/Test_Project1.prj"
        nc_s3_path = "https://kitech-file.s3.ap-northeast-2.amazonaws.com/2025-07-02_ap_4_34_05/ncdata.zip"

        return (project_s3_path, nc_s3_path, project_id)

    def validate_project(self, project: dict) -> bool:
        """프로젝트의 xml 스키마 형식에 맞는지 체크합니다."""
        data = project["data"]
        return validate_xml_against_schema(xml_content=data)
