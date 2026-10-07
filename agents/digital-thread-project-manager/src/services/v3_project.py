from typing import Optional, List, Tuple, Dict, Any
import xmltodict
import re
import httpx
import logging

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError

from src.models.entities.asset import AssetRepository
from src.utils.v3_xml_parser import (
    extract_dtasset_meta,
    validate_xml_against_schema,
    get_inner_data,
    pick_dt_project,
    find_workplan_in_project,
    find_workpiece_in_project,
    find_operation_in_workplan,
    _as_list,
)
from src.utils.exceptions import CustomException, ExceptionEnum
from src.utils.env import get_env_or_default
from src.models.schemas.asset import (
    AssetCreateRequest,
    AssetListResponse,
    AssetSearchQuery,
    AssetDocument,
    AssetDocumentNoData,
)
from src.config import settings
from src.services.file import FileService

logger = logging.getLogger(__name__)

# 타입/카테고리 규칙
REF_RULES: Dict[Tuple[str, Optional[str]], Dict[str, Any]] = {
    ("dt_machine_tool", None): {
        "anchor": "workplan",
        "tag": "ref_dt_machine_tool",
        "key": "DT_MACHINE_TOOL",
        "requires": ["workplan_id"],
        "multi": False,
    },
    ("dt_material", None): {
        "anchor": "workpiece",
        "tag": "ref_dt_material",
        "key": "DT_MATERIAL",
        "requires": ["workpiece_id"],
        "multi": False,
    },
    ("dt_cutting_tool_13399", None): {
        "anchor": "operation",
        "tag": "ref_dt_cutting_tool",
        "key": "DT_CUTTING_TOOL_13399",
        "requires": ["workplan_id", "workingstep_id"],
        "multi": False,
    },
}


class V3ProjectService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.repo = AssetRepository(collection)
        self.base_uri_prefix = get_env_or_default(
            "DT_BASE_URI_PREFIX", "https://digital-thread.re"
        )
        self.user_prefix = get_env_or_default("DT_USER_PREFIX", "kitech")

        # DP 설정 (config.py -> Settings에서 로드)
        self._dp_base = settings.dp_base_url.rstrip("/")
        self._dp_api_key = settings.dp_api_key
        self._dp_endpoint_xml = f"{self._dp_base}/openapi/v2/asset/xml"
        self._dp_endpoint_xml_with_file = (
            f"{self._dp_base}/openapi/v2/asset/xml-with-file"
        )
        self._dp_headers = {"Authorization": self._dp_api_key}

    # ---------------- 기본 조회/생성 ----------------

    async def exists_by_keys(self, xml_string: str):
        meta = extract_dtasset_meta(xml_string=xml_string)
        res = await self.repo.exists_by_keys(
            global_asset_id=meta["global_asset_id"],
            asset_id=meta["asset_id"],
            type=meta["type"],
            element_id=meta["element_id"],
        )
        if res is None:
            return False
        raise CustomException(ExceptionEnum.ASSET_ID_DUPLICATION)

    async def create_from_xml(self, xml: str):
        if not validate_xml_against_schema(xml):
            raise CustomException(ExceptionEnum.INVALID_XML_FORMAT)

        meta = extract_dtasset_meta(xml, strict=True)

        # global_asset_id 정규화
        normalized_global_id = self.normalize_global_asset_id(meta["global_asset_id"])
        if normalized_global_id != meta["global_asset_id"]:
            doc = xmltodict.parse(xml)
            if "dt_asset" in doc and "asset_global_id" in doc["dt_asset"]:
                doc["dt_asset"]["asset_global_id"] = normalized_global_id
            xml = xmltodict.unparse(doc)

        if meta["type"] != "dt_project":
            raise CustomException(ExceptionEnum.INVALID_ATTRIBUTE)

        return await self.repo.insert_asset(req=AssetCreateRequest(xml=xml))

    async def list_projects(
        self, *, global_asset_id: str, asset_id: Optional[str] = None
    ) -> AssetListResponse:
        query = AssetSearchQuery(
            global_asset_id=global_asset_id, asset_id=asset_id, type="dt_project"
        )
        rows = await self.repo.search_assets(query)
        if hasattr(AssetDocumentNoData, "model_validate"):  # pydantic v2
            parsed = [AssetDocumentNoData.model_validate(r) for r in rows]
        else:
            parsed = [AssetDocumentNoData.parse_obj(r) for r in rows]
        return AssetListResponse(assets=parsed)

    async def get_by_keys(
        self, *, global_asset_id: str, asset_id: str, type: str, element_id: str
    ) -> Optional[dict]:
        return await self.repo.get_asset_by_keys(
            global_asset_id=global_asset_id,
            asset_id=asset_id,
            type=type,
            element_id=element_id,
        )

    async def extract_attribute_path(self, xml_string: str, path: str) -> str:
        return get_inner_data(project=xml_string, path=path)

    # ---------------- 참조 추가/삭제 ----------------

    async def attach_ref(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        project_element_id: str,
        ref_global_asset_id: str,
        ref_asset_id: str,
        ref_element_id: str,
        ref_type: str,
        ref_category: Optional[str] = None,
        workplan_id: Optional[str] = None,
        workpiece_id: Optional[str] = None,
        workingstep_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        # 프로젝트 존재 확인
        project_doc = await self.repo.get_asset_by_keys(
            global_asset_id=global_asset_id,
            asset_id=asset_id,
            type="dt_project",
            element_id=project_element_id,
        )
        if not project_doc:
            raise CustomException(
                ExceptionEnum.NO_DATA_FOUND, detail="project not found by keys"
            )

        # dt_file → 파일이 프로젝트를 참조
        if (ref_type or "").strip() == "dt_file":
            if not workplan_id:
                raise CustomException(
                    ExceptionEnum.INVALID_ATTRIBUTE,
                    detail="workplan_id required for dt_file reference",
                )
            file_doc = await self.repo.get_asset_by_keys(
                global_asset_id=ref_global_asset_id,
                asset_id=ref_asset_id,
                type="dt_file",
                element_id=ref_element_id,
            )
            if not file_doc:
                raise CustomException(
                    ExceptionEnum.NO_DATA_FOUND, detail="dt_file not found by keys"
                )
            doc = xmltodict.parse(file_doc["data"])
            node = self._pick_dt_file_node(doc, ref_element_id)
            changed = self._ensure_file_references_project(
                node,
                project_global_asset_id=self.normalize_global_asset_id(global_asset_id),
                project_asset_id=asset_id,
                project_element_id=project_element_id,
                workplan_id=workplan_id,
                workingstep_id=workingstep_id,
            )
            if not changed:
                raise CustomException(ExceptionEnum.REF_ALREADY_EXISTS)
            new_xml = xmltodict.unparse(doc)
            await self.repo.update_asset_xml_by_mongo_id(str(file_doc["_id"]), new_xml)
            return {"updated": True, "file_mongo_id": str(file_doc["_id"])}

        # 비-파일 타입
        rule = REF_RULES.get((ref_type, ref_category))
        if not rule:
            raise CustomException(ExceptionEnum.INVALID_ATTRIBUTE)

        provided = {
            "workplan_id": workplan_id,
            "workpiece_id": workpiece_id,
            "workingstep_id": workingstep_id,
        }
        required = list(rule.get("requires", []))
        if ref_type == "dt_material" and "workpiece_id" in required:
            required.remove("workpiece_id")
        missing = [k for k in required if not provided.get(k)]
        if missing:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                detail=f"missing required params for {ref_type}{'/' + ref_category if ref_category else ''}: {missing}",
            )

        doc = xmltodict.parse(project_doc["data"])
        dt_proj = pick_dt_project(doc, project_element_id)
 
        if rule["anchor"] == "workplan":
            target = find_workplan_in_project(dt_proj, workplan_id)
        elif rule["anchor"] == "workpiece":
            target = (
                self._ensure_workpiece_and_get(dt_proj, workpiece_id)
                if ref_type == "dt_material"
                else find_workpiece_in_project(dt_proj, workpiece_id)
            )
        elif rule["anchor"] == "operation":
            wp = find_workplan_in_project(dt_proj, workplan_id)
            target = find_operation_in_workplan(wp, workingstep_id)
        else:
            raise CustomException(ExceptionEnum.INVALID_ATTRIBUTE)

        full_uri = self._build_element_fullpath(
            ref_global_asset_id, ref_asset_id, ref_element_id
        )
        tag = rule["tag"]

        if self._has_fullpath(target, tag, full_uri):
            raise CustomException(ExceptionEnum.REF_ALREADY_EXISTS)

        prefix_map = {
            "ref_dt_machine_tool": "machine-tool",
            "ref_dt_material": "material",
            "ref_dt_cutting_tool": "cutting-tool",
        }
        display_map = {
            "dt_machine_tool": "Machine Tool Ref",
            "dt_material": "Material Ref",
            "dt_cutting_tool_13399": "Cutting Tool Ref",
        }
        prefix = prefix_map.get(tag, "reference")
        display = display_map.get(ref_type, "Reference")

        element_id_auto = self._next_ref_element_id(target, tag, prefix)
        ref_obj = self._make_element_ref(
            element_id=element_id_auto,
            display_name=display,
            type_name=ref_type,
            full_uri=full_uri,
        )

        target[tag] = ref_obj

        # workplan의 machine tool ref는 맨 아래로
        if rule["anchor"] == "workplan" and tag == "ref_dt_machine_tool":
            self._move_child_to_end(target, tag)

        new_xml = xmltodict.unparse(doc)
        await self.repo.update_asset_xml_by_mongo_id(str(project_doc["_id"]), new_xml)
        return {"updated": True, "project_mongo_id": str(project_doc["_id"])}

    async def remove_ref(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        project_element_id: str,
        ref_global_asset_id: str,
        ref_asset_id: str,
        ref_element_id: str,
        ref_type: str,
        ref_category: Optional[str] = None,
        workplan_id: Optional[str] = None,
        workpiece_id: Optional[str] = None,
        workingstep_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if (ref_type or "").strip() == "dt_file":
            if not workplan_id:
                raise CustomException(
                    ExceptionEnum.INVALID_ATTRIBUTE,
                    detail="workplan_id required for dt_file removal",
                )
            file_doc = await self.repo.get_asset_by_keys(
                global_asset_id=ref_global_asset_id,
                asset_id=ref_asset_id,
                type="dt_file",
                element_id=ref_element_id,
            )
            if not file_doc:
                raise CustomException(
                    ExceptionEnum.NO_DATA_FOUND, detail="dt_file not found by keys"
                )
            doc = xmltodict.parse(file_doc["data"])
            node = self._pick_dt_file_node(doc, ref_element_id)
            removed = self._remove_project_reference_from_file(
                node,
                project_global_asset_id=self.normalize_global_asset_id(global_asset_id),
                project_asset_id=asset_id,
                project_element_id=project_element_id,
                workplan_id=workplan_id,
                workingstep_id=workingstep_id,
            )
            if not removed:
                raise CustomException(
                    ExceptionEnum.REF_NOT_FOUND, detail="reference not found in dt_file"
                )
            new_xml = xmltodict.unparse(doc)
            await self.repo.update_asset_xml_by_mongo_id(str(file_doc["_id"]), new_xml)
            return {"removed": True, "file_mongo_id": str(file_doc["_id"])}

        project_doc = await self.repo.get_asset_by_keys(
            global_asset_id=global_asset_id,
            asset_id=asset_id,
            type="dt_project",
            element_id=project_element_id,
        )
        if not project_doc:
            raise CustomException(
                ExceptionEnum.NO_DATA_FOUND, detail="project not found by keys"
            )

        rule = REF_RULES.get((ref_type, ref_category))
        if not rule:
            raise CustomException(ExceptionEnum.INVALID_ATTRIBUTE)

        provided = {
            "workplan_id": workplan_id,
            "workpiece_id": workpiece_id,
            "workingstep_id": workingstep_id,
        }
        missing = [k for k in rule.get("requires", []) if not provided.get(k)]
        if missing:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                detail=f"missing required params for {ref_type}{'/' + ref_category if ref_category else ''}: {missing}",
            )

        doc = xmltodict.parse(project_doc["data"])
        dt_proj = pick_dt_project(doc, project_element_id)
        if rule["anchor"] == "workplan":
            target = find_workplan_in_project(dt_proj, workplan_id)
        elif rule["anchor"] == "workpiece":
            target = find_workpiece_in_project(dt_proj, workpiece_id)
        elif rule["anchor"] == "operation":
            wp = find_workplan_in_project(dt_proj, workplan_id)
            target = find_operation_in_workplan(wp, workingstep_id)
        else:
            raise CustomException(ExceptionEnum.INVALID_ATTRIBUTE)

        tag = rule["tag"]
        full_uri = self._build_element_fullpath(
            ref_global_asset_id, ref_asset_id, ref_element_id
        )

        removed = False
        cur = target.get(tag)
        if isinstance(cur, dict):
            k = cur.get("keys")
            vals = [k] if isinstance(k, dict) else (k if isinstance(k, list) else [])
            hit = any(
                isinstance(kv, dict)
                and kv.get("key") == "DT_ELEMENT_FULLPATH"
                and kv.get("value") == full_uri
                for kv in vals
            )
            if hit:
                target.pop(tag, None)
                removed = True
        elif isinstance(cur, list):
            kept = []
            for ref in cur:
                k = ref.get("keys") if isinstance(ref, dict) else None
                kvs = [k] if isinstance(k, dict) else (k if isinstance(k, list) else [])
                hit = any(
                    isinstance(kv, dict)
                    and kv.get("key") == "DT_ELEMENT_FULLPATH"
                    and kv.get("value") == full_uri
                    for kv in kvs
                )
                if not hit:
                    kept.append(ref)
            if len(kept) != len(cur):
                removed = True
                target[tag] = kept if kept else target.pop(tag, None)

        if not removed:
            raise CustomException(
                ExceptionEnum.REF_NOT_FOUND,
                detail=f"reference not found for FULLPATH={full_uri}",
            )

        new_xml = xmltodict.unparse(doc)
        await self.repo.update_asset_xml_by_mongo_id(str(project_doc["_id"]), new_xml)
        return {"removed": True, "project_mongo_id": str(project_doc["_id"])}

    # ---------------- DP 업로드 ----------------
    def _decode_body(self, resp: httpx.Response) -> str | dict:
        # 응답 본문을 최대한 읽어 사람이 볼 수 있게 디코드
        ct = (resp.headers.get("content-type") or "").lower()
        try:
            if "application/json" in ct or "+json" in ct:
                return resp.json()
        except Exception:
            pass
        try:
            return resp.text  # httpx가 charset 추정해서 디코드해줌
        except Exception:
            return resp.content.decode("utf-8", "ignore")

    async def _try_xml(
        self, client: httpx.AsyncClient, content_type: str, xml_text: str
    ) -> dict:
        headers = {**self._dp_headers, "Content-Type": content_type}
        resp = await client.post(
            self._dp_endpoint_xml,
            headers=headers,
            # ✅ UTF-8로 명시 인코딩
            content=xml_text.encode("utf-8"),
        )
        body = self._decode_body(resp)

        # ❗서버 메시지를 로그에 남겨 원인 확인 가능하게
        import logging

        logging.info(
            "[DP XML upload] try ct=%s -> %s, body-preview=%s",
            content_type,
            resp.status_code,
            (body if isinstance(body, str) else str(body))[:800],  # 800자만 미리보기
        )

        return {
            "ok": resp.status_code in (200, 201),
            "status": resp.status_code,
            "body": body,
        }

    async def _dp_upload_xml(self, xml_text: str) -> dict:
        """
        XML-only 업로드: raw XML 본문 전송.
        1) application/xml; charset=utf-8
        2) text/xml; charset=utf-8 (폴백 한 번만)
        응답 본문을 항상 캡처해 리턴.
        """
        async with httpx.AsyncClient(timeout=60) as client:
            # 1차: application/xml
            r1 = await self._try_xml(client, "application/xml; charset=utf-8", xml_text)
            if r1["ok"]:
                return r1

            # 2차(폴백): text/xml
            r2 = await self._try_xml(client, "text/xml; charset=utf-8", xml_text)

            # 둘 다 실패면 더 자세한 진단을 위해 1차/2차 결과를 묶어서 반환
            return {
                "ok": False,
                "status": r2["status"],
                "body": {
                    "attempts": [
                        {"content_type": "application/xml; charset=utf-8", **r1},
                        {"content_type": "text/xml; charset=utf-8", **r2},
                    ]
                },
            }

    # async def _dp_upload_xml(self, xml_text: str) -> dict:
    #     """
    #     XML-only 업로드: raw XML 본문 + Content-Type: application/xml
    #     (일부 배포 호환용으로 text/xml 1회 폴백만 유지)
    #     """
    #     headers = {**self._dp_headers, "Content-Type": "application/xml"}

    #     async with httpx.AsyncClient(timeout=60) as client:
    #         # 1) application/xml
    #         resp = await client.post(
    #             self._dp_endpoint_xml,
    #             headers=headers,
    #             content=xml_text,  # ✅ raw XML 본문
    #         )
    #         if resp.status_code in (200, 201):
    #             return {
    #                 "ok": True,
    #                 "status": resp.status_code,
    #                 "body": self._safe_body(resp),
    #             }

    #         # 2) (옵션) 일부 구환경 text/xml
    #         resp = await client.post(
    #             self._dp_endpoint_xml,
    #             headers={**self._dp_headers, "Content-Type": "text/xml"},
    #             content=xml_text,
    #         )
    #         return {
    #             "ok": resp.status_code in (200, 201),
    #             "status": resp.status_code,
    #             "body": self._safe_body(resp),
    #         }

    async def _dp_upload_xml_with_file(
        self, xml_text: str, files: list[tuple[str, bytes]]
    ) -> dict:
        multipart = []
        for fname, content in files:
            multipart.append(("files", (fname, content, "application/octet-stream")))
        # XML은 파일 파트로, 타입을 application/xml로 명시
        multipart.append(("xmlData", ("payload.xml", xml_text, "application/xml")))

        async with httpx.AsyncClient(timeout=60) as client:
            # ⚠️ 여기서는 Content-Type을 수동 지정하지 말 것 (경계값 깨짐)
            resp = await client.post(
                self._dp_endpoint_xml_with_file,
                headers=self._dp_headers,
                files=multipart,
            )

        return {
            "ok": resp.status_code in (200, 201),
            "status": resp.status_code,
            "body": self._safe_body(resp),
        }

    def _safe_body(self, resp: httpx.Response):
        ctype = resp.headers.get("content-type", "")
        if "application/json" in ctype:
            try:
                return resp.json()
            except Exception:
                return resp.text
        return resp.text

    async def upload_project_and_related(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        project_element_id: str,
        file_service: FileService,
        include_ref_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        프로젝트 + 모든 관련 참조 자산 업로드 (필터 미사용 시 전체).
        - dt_file은 파일 OID가 있으면 xml-with-file, 없으면 xml만
        - 파일 OID가 있는데 실제 파일이 없으면 실패로 집계
        - 업로드 성공 시 각 문서 is_upload = True
        """
        include_ref_types = include_ref_types or [
            "dt_file",
            "dt_material",
            "dt_machine_tool",
            "dt_cutting_tool_13399",
        ]

        # 프로젝트 조회
        project_doc = await self.repo.get_asset_by_keys(
            global_asset_id=global_asset_id,
            asset_id=asset_id,
            type="dt_project",
            element_id=project_element_id,
        )
        if not project_doc:
            return {"ok": False, "error": "project_not_found"}

        results: Dict[str, Any] = {"project": None, "related": []}

        # 프로젝트 XML 업로드
        proj_xml: str = project_doc.get("data", "")
        proj_up = await self._dp_upload_xml(proj_xml)
        if proj_up["ok"]:
            await self.repo.set_is_upload_true_by_mongo_id(str(project_doc["_id"]))
        results["project"] = proj_up

        # 관련 자산 수집
        related_assets = await self._collect_related_assets_by_project_xml(
            proj_xml, global_asset_id, asset_id, project_element_id, include_ref_types
        )

        # 중복 제거 (type, global, asset, element 기준)
        unique = set()
        deduped = []
        for it in related_assets:
            key = (it["type"], it["global_asset_id"], it["asset_id"], it["element_id"])
            if key in unique:
                continue
            unique.add(key)
            deduped.append(it)
        related_assets = deduped

        # 업로드 실행
        for item in related_assets:
            doc = await self.repo.get_asset_by_keys(
                global_asset_id=item["global_asset_id"],
                asset_id=item["asset_id"],
                type=item["type"],
                element_id=item["element_id"],
            )
            if not doc:
                results["related"].append(
                    {
                        **item,
                        "ok": False,
                        "status": 404,
                        "error": "related_asset_not_found",
                    }
                )
                continue

            xml_text = doc.get("data", "")

            if item["type"] == "dt_file":
                try:
                    node = self._pick_dt_file_node(
                        xmltodict.parse(xml_text), item["element_id"]
                    )
                    file_oid = self._extract_file_oid_from_dt_file_node(node)

                    # ✅ 파일명은 display_name 기반
                    display_name = node.get("display_name") or node.get("element_id")

                    if file_oid:
                        # FileService 통해 GridFS에서 바이너리 읽기
                        bio = await file_service.repository.get_file_byteio(file_oid)
                        bin_bytes = bio.getvalue()

                        # display_name을 파일 이름으로 사용
                        up = await self._dp_upload_xml_with_file(
                            xml_text, [(display_name, bin_bytes)]
                        )
                    else:
                        up = await self._dp_upload_xml(xml_text)
                except Exception as e:
                    results["related"].append(
                        {
                            **item,
                            "ok": False,
                            "status": 500,
                            "error": f"upload_exception: {e}",
                        }
                    )
                    continue
            else:
                up = await self._dp_upload_xml(xml_text)

            if up["ok"]:
                await self.repo.set_is_upload_true_by_mongo_id(str(doc["_id"]))
            results["related"].append({**item, **up})

        return results

    async def upload_single_asset(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        type: str,
        element_id: str,
        file_service: FileService,
    ) -> dict:
        # 1) 자산 조회
        doc = await self.repo.get_asset_by_keys(
            global_asset_id=global_asset_id,
            asset_id=asset_id,
            type=type,
            element_id=element_id,
        )
        if not doc:
            return {
                "ok": False,
                "status": 404,
                "error": "asset_not_found",
                "meta": {
                    "type": type,
                    "global_asset_id": global_asset_id,
                    "asset_id": asset_id,
                    "element_id": element_id,
                },
            }

        xml_text: str = doc.get("data", "")

        # 2) 타입별 업로드 분기
        if (type or "").strip() == "dt_file":
            try:
                node = self._pick_dt_file_node(xmltodict.parse(xml_text), element_id)
                file_oid = self._extract_file_oid_from_dt_file_node(node)
                display_name = (
                    node.get("display_name") or node.get("element_id") or "file.bin"
                )

                if file_oid:
                    bio = await file_service.repository.get_file_byteio(file_oid)
                    bin_bytes = bio.getvalue()
                    up = await self._dp_upload_xml_with_file(
                        xml_text, [(display_name, bin_bytes)]
                    )
                else:
                    up = await self._dp_upload_xml(xml_text)
            except Exception as e:
                return {
                    "ok": False,
                    "status": 500,
                    "error": f"upload_exception: {e}",
                    "meta": {
                        "type": type,
                        "global_asset_id": global_asset_id,
                        "asset_id": asset_id,
                        "element_id": element_id,
                    },
                }
        else:
            up = await self._dp_upload_xml(xml_text)

        # 3) 성공 시 업로드 플래그
        if up.get("ok"):
            await self.repo.set_is_upload_true_by_mongo_id(str(doc["_id"]))

        # 4) 표준 응답
        return {
            "ok": up.get("ok", False),
            "status": up.get("status"),
            "body": up.get("body"),
            "meta": {
                "type": type,
                "global_asset_id": doc.get("global_asset_id"),
                "asset_id": doc.get("asset_id"),
                "element_id": element_id,
            },
        }

    # ---------------- 수집/파싱 유틸 ----------------

    async def _collect_related_assets_by_project_xml(
        self,
        project_xml: str,
        global_asset_id: str,
        asset_id: str,
        project_element_id: str,
        include_ref_types: List[str],
    ) -> List[Dict[str, str]]:
        related: List[Dict[str, str]] = []
        doc = xmltodict.parse(project_xml)
        proj = (doc.get("dt_asset") or {}).get("dt_elements")
        if not isinstance(proj, dict) or (proj.get("@xsi:type") != "dt_project"):
            return related

        # dt_material
        if "dt_material" in include_ref_types:
            related.extend(self._collect_refs_in_workpieces(proj))

        # dt_machine_tool
        if "dt_machine_tool" in include_ref_types:
            related.extend(self._collect_ref_in_workplan_machine_tool(proj))

        # dt_cutting_tool_13399
        if "dt_cutting_tool_13399" in include_ref_types:
            related.extend(self._collect_refs_in_workingsteps_tools(proj))

        # dt_file (NC) — 프로젝트를 참조하는 파일들을 리포지토리에서 찾아서 추가
        if "dt_file" in include_ref_types:
            wp_ids = self._extract_workplan_ids_from_project_xml(project_xml)
            for wp_id in wp_ids:
                try:
                    # ✅ category 필터 없이 모든 dt_file 검색
                    rows = await self.repo.find_files_by_ref(
                        global_asset_id=global_asset_id,
                        asset_id=asset_id,
                        project_element_id=project_element_id,
                        workplan_id=wp_id,
                        workingstep_id=None,
                        categories=None,  # None이면 NC/VM/기타 다 포함
                    )
                    for r in rows:
                        related.append(
                            {
                                "type": r.get("type") or "dt_file",
                                "global_asset_id": r["global_asset_id"],
                                "asset_id": r["asset_id"],
                                "element_id": r["element_id"],
                            }
                        )
                except Exception:
                    logging.exception(
                        "find_files_by_ref failed for workplan_id=%s", wp_id
                    )

        # dt_file (프로젝트 레벨) — WORKPLAN 없이 프로젝트를 참조하는 파일들도 포함
        if "dt_file" in include_ref_types:
            try:
                rows = await self.repo.find_files_by_project_ref(
                    global_asset_id=global_asset_id,
                    asset_id=asset_id,
                    project_element_id=project_element_id,
                    categories=None,  # None이면 STEP/TITLE_IMAGE 포함 전부
                )
                for r in rows:
                    related.append(
                        {
                            "type": r.get("type") or "dt_file",
                            "global_asset_id": r["global_asset_id"],
                            "asset_id": r["asset_id"],
                            "element_id": r["element_id"],
                        }
                    )
            except Exception:
                logging.exception("find_files_by_project_ref failed")

        # 최종 중복 제거
        dedup = []
        seen = set()
        for it in related:
            key = (it["type"], it["global_asset_id"], it["asset_id"], it["element_id"])
            if key in seen:
                continue
            seen.add(key)
            dedup.append(it)
        return dedup

    def _collect_workplan_ids_from_project(self, proj_node: dict) -> List[str]:
        ids: List[str] = []
        mw = proj_node.get("main_workplan")
        if isinstance(mw, dict):
            wid = mw.get("its_id")
            if isinstance(wid, str) and wid.strip():
                ids.append(wid.strip())
        # (추가 워크플랜이 있다면 여기에 파싱 로직 보강)
        return ids

    def _safe_get(self, d: dict, path: List[str]):
        cur = d
        for k in path:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(k)
        return cur

    def _collect_refs_in_workpieces(self, proj: dict) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        wps = proj.get("its_workpieces")
        if not isinstance(wps, dict):
            return out
        ref = wps.get("ref_dt_material")
        if not ref:
            return out
        uri = self._extract_full_uri_from_ref(ref)
        if uri:
            out.append(self._split_full_uri_to_keys("dt_material", uri))
        return out

    def _collect_ref_in_workplan_machine_tool(self, proj: dict) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        # ✅ 프로젝트 내 모든 workplan 후보를 돌면서 ref_dt_machine_tool 탐색
        for wp in self._iter_workplan_nodes_in_project(proj):
            if not isinstance(wp, dict):
                continue

            ref = wp.get("ref_dt_machine_tool")
            if not ref:
                continue

            uri = self._extract_full_uri_from_ref(ref)
            if uri:
                out.append(self._split_full_uri_to_keys("dt_machine_tool", uri))

        return out

    def _collect_refs_in_workingsteps_tools(self, proj: dict) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []

        # ✅ 프로젝트 내 workplan들을 모두 훑는다
        for wp in self._iter_workplan_nodes_in_project(proj):
            if not isinstance(wp, dict):
                continue

            elems = wp.get("its_elements")
            # its_elements는 workingstep(list/dict)일 수도 있고, workplan 컨테이너(dict)일 수도 있음
            ws_list = []
            if isinstance(elems, list):
                ws_list = elems
            elif isinstance(elems, dict):
                # dict 하나면 workingstep일 수도 있고(workplan 컨테이너일 수도 있음)
                # - workingstep이면 its_operation이 있다
                # - workplan 컨테이너면 @xsi:type=="workplan" 이다
                if "its_operation" in elems:
                    ws_list = [elems]
                else:
                    # workplan 컨테이너 형태면 여기서 workingstep이 안 나오므로 skip
                    ws_list = []

            for ws in ws_list:
                if not isinstance(ws, dict):
                    continue

                op = ws.get("its_operation")
                if not isinstance(op, dict):
                    continue

                ref = op.get("ref_dt_cutting_tool")
                if not ref:
                    continue

                uri = self._extract_full_uri_from_ref(ref)
                if uri:
                    out.append(
                        self._split_full_uri_to_keys("dt_cutting_tool_13399", uri)
                    )

        return out

    def _extract_full_uri_from_ref(self, ref_node: dict) -> Optional[str]:
        ks = ref_node.get("keys")
        if not ks:
            return None
        items = ks if isinstance(ks, list) else [ks]
        for it in items:
            val = it.get("value")
            if isinstance(val, str) and val.strip():
                return val.strip()
        return None

    def _split_full_uri_to_keys(
        self, guessed_type: str, full_uri: str
    ) -> Dict[str, str]:
        parts = full_uri.strip("/").split("/")
        if len(parts) < 3:
            return {
                "type": guessed_type,
                "global_asset_id": "",
                "asset_id": "",
                "element_id": "",
            }
        return {
            "type": guessed_type,
            "global_asset_id": "/".join(parts[:-2]),
            "asset_id": parts[-2],
            "element_id": parts[-1],
        }

    def _iter_workplan_nodes_in_project(self, proj: dict) -> List[dict]:
        """
        프로젝트(dt_project) 노드에서 '실제 workplan 노드'들을 모두 수집한다.

        지원하는 구조:
        A) (구버전/단순) main_workplan 바로 아래에 workingstep/ref가 있는 경우
        - main_workplan 자체를 workplan처럼 취급
        B) (현재 v31 형태) main_workplan/its_elements 가 workplan(xsi:type="workplan") 인 경우
        - 그 하위 workplan들을 모두 수집
        C) its_workplans 같은 추가 컨테이너가 생기는 경우에도 최대한 유연하게 대응
        """
        out: List[dict] = []

        mw = proj.get("main_workplan")
        if isinstance(mw, dict):
            # main_workplan 자체가 "workplan처럼" 생긴 케이스(구버전 호환)
            # - ref_dt_machine_tool 이 있거나
            # - its_elements가 machining_workingstep들을 담고 있거나
            out.append(mw)

            # main_workplan 아래에 workplan 컨테이너가 있는 케이스(v31)
            mw_elems = mw.get("its_elements")
            out.extend(self._extract_workplans_from_container(mw_elems))

        # (확장) its_workplans 같은 컨테이너가 별도로 있을 경우도 대응
        wps = proj.get("its_workplans")
        if isinstance(wps, dict):
            # 스키마/작성 방식에 따라 workplan 키가 다를 수 있어 안전하게 탐색
            out.extend(self._extract_workplans_from_container(wps.get("workplan")))
            out.extend(self._extract_workplans_from_container(wps.get("its_elements")))

        # 중복 제거 (객체 동일성 기준)
        uniq: List[dict] = []
        seen_ids = set()
        for node in out:
            if not isinstance(node, dict):
                continue
            # dict는 hash 불가라 id() 사용
            ptr = id(node)
            if ptr in seen_ids:
                continue
            seen_ids.add(ptr)
            uniq.append(node)
        return uniq

    def _extract_workplans_from_container(self, container: Any) -> List[dict]:
        """
        container에서 workplan 노드(또는 workplan 리스트)를 최대한 안전하게 뽑아낸다.
        - dict/list/None 모두 대응
        - @xsi:type == "workplan" 인 dict를 우선적으로 workplan으로 취급
        - 이미 workplan dict 형태(its_id + its_elements)를 가진 경우도 허용
        """
        if container is None:
            return []

        items = container if isinstance(container, list) else [container]
        out: List[dict] = []

        for it in items:
            if not isinstance(it, dict):
                continue

            t = it.get("@xsi:type") or it.get("xsi:type")

            # 명시적으로 workplan
            if t == "workplan":
                out.append(it)
                continue

            # 경우에 따라 workplan wrapper가 없이 workplan 비슷한 dict가 들어올 수도 있음
            # (its_id/its_elements 존재하면 workplan로 취급)
            if "its_id" in it and "its_elements" in it:
                out.append(it)
                continue

        return out

    # ---------------- dt_file 유틸 ----------------

    def _as_list(self, v):
        if v is None:
            return []
        return v if isinstance(v, list) else [v]

    def _pick_dt_file_node(self, doc: dict, target_element_id: str) -> dict:
        dt_asset = doc.get("dt_asset") or doc
        elems = self._as_list(dt_asset.get("dt_elements"))
        for e in elems:
            if not isinstance(e, dict):
                continue
            t = e.get("@xsi:type") or e.get("xsi:type")
            if t == "dt_file" and e.get("element_id") == target_element_id:
                return e
        raise CustomException(
            ExceptionEnum.NO_DATA_FOUND,
            detail=f"dt_file(element_id='{target_element_id}') not found",
        )

    def _extract_file_oid_from_dt_file_node(self, file_node: dict) -> Optional[str]:
        if not isinstance(file_node, dict):
            return None
        v = file_node.get("value")
        if isinstance(v, str) and v.strip():
            return v.strip()
        return None

    def _ensure_file_references_project(
        self,
        file_node: dict,
        *,
        project_global_asset_id: str,
        project_asset_id: str,
        project_element_id: str,
        workplan_id: str,
        workingstep_id: Optional[str] = None,
    ) -> bool:
        if not isinstance(file_node, dict):
            return False

        refs = file_node.get("reference")
        refs_list = (
            refs
            if isinstance(refs, list)
            else ([refs] if isinstance(refs, dict) else [])
        )

        # 프로젝트 reference 선택(없으면 새로 하나 만든다)
        def _is_project_ref(ref_dict: dict) -> bool:
            keys = _as_list(ref_dict.get("keys"))
            names = set()
            for kv in keys:
                if isinstance(kv, dict) and isinstance(kv.get("key"), str):
                    names.add(kv["key"].strip().upper())
            return "DT_GLOBAL_ASSET" in names and "DT_ASSET" in names

        target_ref = None
        for r in refs_list:
            if isinstance(r, dict) and _is_project_ref(r):
                target_ref = r
                break

        if target_ref is None:
            target_ref = {}
            # 기존이 없었다면 단일 → 리스트로 승격
            if not refs_list:
                file_node["reference"] = [target_ref]
            elif isinstance(refs, dict):
                file_node["reference"] = [refs, target_ref]
            else:
                refs_list.append(target_ref)

        keys_list = _as_list(target_ref.get("keys"))

        def has_kv(k, v):
            for kv in keys_list:
                if isinstance(kv, dict) and kv.get("key") == k and kv.get("value") == v:
                    return True
            return False

        desired = [
            ("DT_GLOBAL_ASSET", project_global_asset_id),
            ("DT_ASSET", project_asset_id),
            ("DT_PROJECT", project_element_id),
            ("WORKPLAN", workplan_id),
        ]
        if workingstep_id:
            desired.append(("WORKINGSTEP", workingstep_id))

        changed = False
        for k, v in desired:
            if not has_kv(k, v):
                keys_list.append({"key": k, "value": v})
                changed = True

        target_ref["keys"] = keys_list[0] if len(keys_list) == 1 else keys_list
        return changed

    def _remove_project_reference_from_file(
        self,
        file_node: dict,
        *,
        project_global_asset_id: str,
        project_asset_id: str,
        project_element_id: str,
        workplan_id: str,
        workingstep_id: Optional[str] = None,
    ) -> bool:
        ref = file_node.get("reference")
        if not isinstance(ref, dict):
            return False
        keys_list = self._as_list(ref.get("keys"))
        if not keys_list:
            return False

        targets = {
            ("DT_GLOBAL_ASSET", project_global_asset_id),
            ("DT_ASSET", project_asset_id),
            ("DT_PROJECT", project_element_id),
            ("WORKPLAN", workplan_id),
        }
        if workingstep_id:
            targets.add(("WORKINGSTEP", workingstep_id))

        def is_target(kv):
            if not isinstance(kv, dict):
                return False
            return (kv.get("key"), kv.get("value")) in targets

        kept = [kv for kv in keys_list if not is_target(kv)]
        removed = len(kept) != len(keys_list)
        if not removed:
            return False
        if kept:
            ref["keys"] = kept[0] if len(kept) == 1 else kept
        else:
            file_node.pop("reference", None)
        return True

    # ---------------- 공통 유틸 ----------------

    def normalize_global_asset_id(self, global_asset_id: str) -> str:
        if global_asset_id.startswith("http://") or global_asset_id.startswith(
            "https://"
        ):
            return global_asset_id
        return f"{self.base_uri_prefix}/{self.user_prefix}/{global_asset_id}"

    def _build_element_fullpath(
        self, ref_global_asset_id: str, ref_asset_id: str, ref_element_id: str
    ) -> str:
        base = ref_global_asset_id.strip()
        if not (base.startswith("http://") or base.startswith("https://")):
            base = f"{self.base_uri_prefix}/{self.user_prefix}/{base}"
        return f"{base.rstrip('/')}/{ref_asset_id}/{ref_element_id}"

    def _next_ref_element_id(self, container: dict, tag: str, prefix: str) -> str:
        items = container.get(tag)
        if items is None:
            return f"{prefix}-001"
        if isinstance(items, dict):
            items = [items]
        mx = 0
        for it in items:
            if not isinstance(it, dict):
                continue
            eid = (it.get("element_id") or "").strip()
            m = re.fullmatch(rf"{re.escape(prefix)}-(\d+)", eid)
            if m:
                mx = max(mx, int(m.group(1)))
        return f"{prefix}-{mx+1:03d}"

    def _make_element_ref(
        self, *, element_id: str, display_name: str, type_name: str, full_uri: str
    ) -> dict:
        return {
            "element_id": element_id,
            "category": "reference",
            "display_name": display_name,
            "element_description": f"Reference to {type_name}",
            "keys": {"key": "DT_ELEMENT_FULLPATH", "value": full_uri},
        }

    def _ref_list(self, node: dict, tag: str):
        cur = node.get(tag)
        if cur is None:
            return []
        return cur if isinstance(cur, list) else [cur]

    def _has_fullpath(self, node: dict, tag: str, fullpath: str) -> bool:
        for ref in self._ref_list(node, tag):
            if not isinstance(ref, dict):
                continue
            k = ref.get("keys")
            if isinstance(k, dict):
                if k.get("key") == "DT_ELEMENT_FULLPATH" and k.get("value") == fullpath:
                    return True
            elif isinstance(k, list):
                for kv in k:
                    if (
                        isinstance(kv, dict)
                        and kv.get("key") == "DT_ELEMENT_FULLPATH"
                        and kv.get("value") == fullpath
                    ):
                        return True
        return False

    def _next_workpiece_id(self, project_node: dict, prefix: str = "workpiece") -> str:
        items = project_node.get("its_workpieces")
        if items is None:
            return f"{prefix}-001"
        items = items if isinstance(items, list) else [items]
        mx = 0
        for it in items:
            if not isinstance(it, dict):
                continue
            wp = it.get("workpiece") if isinstance(it.get("workpiece"), dict) else it
            wid = (wp.get("its_id") or "").strip()
            m = re.fullmatch(rf"{re.escape(prefix)}-(\d+)", wid)
            if m:
                mx = max(mx, int(m.group(1)))
        return f"{prefix}-{mx+1:03d}"

    def _ensure_workpiece_and_get(
        self, project_node: dict, workpiece_id: Optional[str]
    ) -> dict:
        if workpiece_id:
            try:
                return find_workpiece_in_project(project_node, workpiece_id)
            except Exception:
                new_wp = {"its_id": workpiece_id}
                cur = project_node.get("its_workpieces")
                if cur is None:
                    project_node["its_workpieces"] = [new_wp]
                elif isinstance(cur, list):
                    cur.append(new_wp)
                else:
                    project_node["its_workpieces"] = [cur, new_wp]
                return new_wp

        auto_id = self._next_workpiece_id(project_node)
        new_wp = {"its_id": auto_id}
        cur = project_node.get("its_workpieces")
        if cur is None:
            project_node["its_workpieces"] = [new_wp]
        elif isinstance(cur, list):
            cur.append(new_wp)
        else:
            project_node["its_workpieces"] = [cur, new_wp]
        return new_wp

    def _move_child_to_end(self, parent: dict, key: str) -> None:
        if isinstance(parent, dict) and key in parent:
            val = parent.pop(key)
            parent[key] = val

    def _extract_workplan_ids(self, project_xml: str) -> list[str]:
        try:
            doc = xmltodict.parse(project_xml)
            proj = doc.get("dt_asset", {}).get("dt_elements", {})
            wp = proj.get("main_workplan") or {}
            its_id = wp.get("its_id")
            ids = set()
            if isinstance(its_id, str) and its_id.strip():
                ids.add(its_id.strip())
            # 필요하면 보조 workplan도 여기서 더 모을 수 있음
            return list(ids)
        except Exception:
            return []

    def _extract_all_workplan_ids_from_project_xml(self, proj_xml: str) -> list[str]:
        """
        프로젝트 XML에서 main_workplan 및 기타 워크플랜들의 its_id를 전부 수집.
        (현재 스키마에선 main_workplan만 있어도 동작)
        """
        try:
            doc = xmltodict.parse(proj_xml)
        except Exception:
            return []
        proj = doc.get("dt_asset", {}).get("dt_elements", {})
        if not isinstance(proj, dict) or (proj.get("@xsi:type") != "dt_project"):
            return []

        wp_ids: list[str] = []
        main_wp = proj.get("main_workplan")
        if isinstance(main_wp, dict):
            mid = main_wp.get("its_id")
            if isinstance(mid, str) and mid.strip():
                wp_ids.append(mid.strip())

        # (확장 시) 추가 워크플랜 컬렉션이 있다면 여기서 더 수집

        # 중복 제거
        return list(dict.fromkeys(wp_ids))

    async def _collect_dt_files_referencing_project(
        self,
        *,
        project_xml: str,
        project_global_asset_id: str,
        project_asset_id: str,
        project_element_id: str,
    ) -> list[dict]:
        """
        프로젝트/워크플랜을 참조하는 dt_file들을 전부 수집.
        - repo.find_nc_files_by_ref()가 workplan_id를 요구하므로, 프로젝트 XML에서 WP ID를 전부 뽑아 반복 호출
        - DT_GLOBAL_ASSET은 정규화/비정규화 둘 다 시도 (이력 데이터 대비)
        """
        out: list[dict] = []

        # 워크플랜 ID 뽑기
        wp_ids = self._extract_all_workplan_ids_from_project_xml(project_xml)
        if not wp_ids:
            return out

        # 정규화/비정규화 모두 시도
        norm_global = self.normalize_global_asset_id(project_global_asset_id)
        raw_global = project_global_asset_id  # 사용자가 쿼리로 넘긴 원문

        seen = set()
        for wp_id in wp_ids:
            for g in (norm_global, raw_global):
                try:
                    rows = await self.repo.find_nc_files_by_ref(
                        global_asset_id=g,
                        asset_id=project_asset_id,
                        project_element_id=project_element_id,
                        workplan_id=wp_id,  # ✅ 반드시 WP ID 지정
                    )
                except Exception:
                    rows = []
                for r in rows or []:
                    key = (
                        r.get("global_asset_id"),
                        r.get("asset_id"),
                        r.get("element_id"),
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(
                        {
                            "type": "dt_file",
                            "global_asset_id": r.get("global_asset_id"),
                            "asset_id": r.get("asset_id"),
                            "element_id": r.get("element_id"),
                        }
                    )
        return out

    def _extract_workplan_ids_from_project_xml(self, project_xml: str) -> list[str]:
        """
        프로젝트 XML에서 워크플랜 its_id 목록을 모두 수집.
        - main_workplan/its_id
        - main_workplan/its_elements(workplan)/its_id  ✅ 추가
        - (선택) its_workplans 컨테이너가 있다면 거기서도
        """
        ids: List[str] = []
        try:
            doc = xmltodict.parse(project_xml)
            proj = (doc.get("dt_asset") or {}).get("dt_elements") or {}
            if not isinstance(proj, dict):
                return []

            # main_workplan
            mw = proj.get("main_workplan")
            if isinstance(mw, dict):
                mid = (mw.get("its_id") or "").strip()
                if mid:
                    ids.append(mid)

                # ✅ main_workplan 아래 workplan들
                mw_elems = mw.get("its_elements")
                wps = self._extract_workplans_from_container(mw_elems)
                for wp in wps:
                    wid = (wp.get("its_id") or "").strip()
                    if wid:
                        ids.append(wid)

            # (확장) its_workplans
            wps_container = proj.get("its_workplans")
            if isinstance(wps_container, dict):
                wps = []
                wps.extend(
                    self._extract_workplans_from_container(
                        wps_container.get("workplan")
                    )
                )
                wps.extend(
                    self._extract_workplans_from_container(
                        wps_container.get("its_elements")
                    )
                )
                for wp in wps:
                    wid = (wp.get("its_id") or "").strip()
                    if wid:
                        ids.append(wid)

        except Exception:
            pass

        return list(dict.fromkeys(ids))
