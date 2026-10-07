import re, os
from typing import Optional, Dict, Any, List, Tuple
import xmltodict

from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorCollection

from fastapi import UploadFile  # API 쪽에서 사용, 여기서 타입힌트만

from src.models.schemas.asset import (
    AssetCreateRequest,
    AssetCreateResponse,
    AssetSearchQuery,
    AssetListResponse,
    AssetDocument,
    GlobalAssetListResponse,
    AssetIdListResponse,
    GroupedAssetIdsResponse,
    GroupedAssetIdsItem,
    AssetDocumentNoData,
)
from src.models.entities.asset import AssetRepository
from src.services.file import FileService
from src.utils.v3_xml_parser import (
    extract_dtasset_meta,
    validate_xml_against_schema,
    ensure_dtasset_namespaces,
    select_dt_file_node,
    infer_type_and_category,
    split_dt_asset_xml,
    get_file_display_name,
    inject_file_id_into_xml,
    workplan_exists_in_project_xml,
    extract_file_reference_tuple,
    workingstep_exists_in_project_xml,
    build_nc_dt_file_xml,
)
from src.utils.env import get_env_or_default
from src.utils.exceptions import CustomException, ExceptionEnum


class AssetService:
    """
    - 입력이 XML이면 그대로 저장(or upsert)
    - 입력이 파일(dt_file)이면 dt_asset XML을 서비스에서 생성한 뒤 저장
    - 메타 추출/보정은 여기서 처리
    """

    # 파일 object_id 타입을 검사히기 위한 정규식
    _OID_RE = re.compile(r"^[0-9a-f]{24}$", re.IGNORECASE)
    _GRIDFS_URI_RE = re.compile(r"^gridfs://([0-9a-f]{24})$", re.IGNORECASE)

    DEFAULT_SCHEMA_VERSION = "v31"

    def __init__(self, collection: AsyncIOMotorCollection):
        self.repo = AssetRepository(collection)
        self.base_uri_prefix = get_env_or_default(
            "DT_BASE_URI_PREFIX", "https://digital-thread.re"
        )
        self.user_prefix = get_env_or_default("DT_USER_PREFIX", "kitech")

    # --------------- 공용 유틸 ---------------

    def _map_util_error(e: Exception) -> CustomException:
        msg = str(e).lower()
        if "no dt_file" in msg or "not found" in msg:
            return CustomException(ExceptionEnum.NO_DATA_FOUND)
        if "schema" in msg or "xml" in msg:
            return CustomException(ExceptionEnum.INVALID_XML_FORMAT)
        return CustomException(ExceptionEnum.INVALID_ATTRIBUTE)

    def _prettify_xml(self, d: Dict[str, Any]) -> str:
        """dict → XML 문자열 (pretty는 호출부에서 선택)."""
        return xmltodict.unparse(d)

    def _extract_dt_file_value(
        self, xml: str, target_element_id: str | None = None
    ) -> str | None:
        """기존 XML에서 dt_file의 value(=파일 OID) 추출."""
        d = xmltodict.parse(xml)
        try:
            dt_file = select_dt_file_node(d, target_element_id)
        except Exception as e:
            raise self._map_util_error(e)
        return dt_file.get("value")

    # --- 내부: dt_file XML에서 파일 OID들 추출 ---
    def _extract_file_ids_from_dt_file_xml(self, xml: str) -> List[str]:
        """
        단일 dt_elements(@xsi:type='dt_file') 기준으로 value 또는 path(gridfs://OID)에서 OID 추출
        (여러개가 들어있을 상황도 대비해서 리스트로 반환)
        """
        try:
            doc = xmltodict.parse(xml)
        except Exception:
            return []

        root = doc.get("dt_asset") or doc
        elems = root.get("dt_elements")
        if elems is None:
            return []

        if not isinstance(elems, list):
            elems = [elems]

        oids: List[str] = []
        for e in elems:
            if not isinstance(e, dict):
                continue
            if e.get("@xsi:type") != "dt_file":
                continue

            val = e.get("value") or ""
            if isinstance(val, dict):
                # 값이 dict로 들어온 특수 케이스 방지
                val = ""
            if val and self._OID_RE.match(val):
                oids.append(val)

            path = e.get("path") or ""
            if isinstance(path, dict):
                path = ""
            if path:
                m = self._GRIDFS_URI_RE.match(path)
                if m:
                    oids.append(m.group(1))

        # 중복 제거
        return sorted(set([x for x in oids if self._OID_RE.match(x)]))

    # --------------- XML 직접 등록 ---------------

    async def create_from_xml_multi(
        self,
        *,
        xml: str,
        upload_files: List[UploadFile] | None,
        file_service: FileService,
        validate_schema: bool = True,
    ) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        created = 0
        failed = 0

        try:
            parts = split_dt_asset_xml(xml)
        except Exception as e:
            return {
                "results": [
                    {
                        "element_id": None,
                        "status": "failed",
                        "reason": f"xml-parse-failed: {e}",
                    }
                ],
                "summary": {"total": 1, "created": 0, "failed": 1},
            }

        if not parts:
            return {"results": [], "summary": {"total": 0, "created": 0, "failed": 0}}

        file_map = {f.filename: f for f in (upload_files or [])}
        has_uploads = bool(file_map)  # 업로드 파일 동봉 여부

        for part_xml in parts:
            try:
                # A) 메타 파싱
                try:
                    meta = extract_dtasset_meta(part_xml, strict=True)
                    el_type = meta["type"]
                    category = meta.get("category")
                    element_id = meta["element_id"]

                    # global_asset_id 정규화 보정
                    if meta.get("global_asset_id"):
                        fixed_gid = self._normalize_global_asset_id(
                            meta["global_asset_id"]
                        )
                        if fixed_gid != meta["global_asset_id"]:
                            d = xmltodict.parse(part_xml)
                            if "dt_asset" in d and "asset_global_id" in d["dt_asset"]:
                                d["dt_asset"]["asset_global_id"] = fixed_gid
                                part_xml = xmltodict.unparse(d)

                except Exception as e:
                    failed += 1
                    results.append(
                        {
                            "element_id": None,
                            "status": "failed",
                            "reason": f"meta-parse-failed: {e}",
                        }
                    )
                    continue

                # B) 스키마 검증
                if validate_schema and not validate_xml_against_schema(part_xml):
                    failed += 1
                    results.append(
                        {
                            "element_id": element_id,
                            "type": el_type,
                            "category": category,
                            "status": "failed",
                            "reason": "invalid-xml-schema",
                        }
                    )
                    continue

                patched_xml = part_xml

                # C) 파일 요소 처리 (CHANGED)
                if el_type == "dt_file":
                    # 1) 요소 파싱 & display_name 추출
                    try:
                        d = xmltodict.parse(part_xml)
                        elem = (d.get("dt_asset") or d).get("dt_elements")
                    except Exception:
                        elem = None

                    # 1-1) reference가 여러 개인 경우, DT_PROJECT 키가 있는 reference 노드 하나를 우선 선택 (없으면 첫 번째)
                    try:
                        if (
                            isinstance(elem, dict)
                            and "reference" in elem
                            and isinstance(elem["reference"], list)
                        ):

                            def _ref_has_key(ref_node, key_name: str) -> bool:
                                ks = ref_node.get("keys")
                                items = (
                                    ks
                                    if isinstance(ks, list)
                                    else ([ks] if isinstance(ks, dict) else [])
                                )
                                for kv in items:
                                    if (
                                        isinstance(kv, dict)
                                        and (kv.get("key") or "").strip().upper()
                                        == key_name
                                    ):
                                        return True
                                return False

                            proj_refs = [
                                r
                                for r in elem["reference"]
                                if _ref_has_key(r, "DT_PROJECT")
                            ]
                            picked = proj_refs[0] if proj_refs else elem["reference"][0]
                            # 선택한 reference만 남기고 extract_file_reference_tuple 이 안전히 동작하도록 정규화
                            elem = {**elem, "reference": picked}
                    except Exception:
                        # reference 구조가 이상해도 여기서 죽지 않게
                        pass

                    # 1-2) display_name
                    try:
                        display_name = get_file_display_name(elem)
                    except Exception:
                        display_name = None

                    # 2) 참조 검증 (DT_GLOBAL_ASSET/DT_ASSET/DT_PROJECT 필수, WP/WS 선택)
                    try:
                        dt_global_url, dt_asset_url, proj_id, wp_id, ws_id = (
                            extract_file_reference_tuple(elem)
                        )

                        if not (dt_global_url and dt_asset_url and proj_id):
                            failed += 1
                            results.append(
                                {
                                    "element_id": element_id,
                                    "type": el_type,
                                    "category": category,
                                    "status": "failed",
                                    "reason": "file-reference-missing (require DT_GLOBAL_ASSET, DT_ASSET, DT_PROJECT)",
                                }
                            )
                            continue

                        # 프로젝트 XML 로드
                        proj_xml = await self.repo.get_project_xml_by_keys(
                            global_asset_id=dt_global_url,
                            asset_id=dt_asset_url,
                            project_element_id=proj_id,
                        )
                        if not proj_xml:
                            failed += 1
                            results.append(
                                {
                                    "element_id": element_id,
                                    "type": el_type,
                                    "category": category,
                                    "status": "failed",
                                    "reason": f"project-not-found: (GLOBAL={dt_global_url}, ASSET={dt_asset_url}, PROJ={proj_id})",
                                }
                            )
                            continue

                        # WORKPLAN 존재 확인(있으면)
                        if wp_id and not workplan_exists_in_project_xml(
                            proj_xml, proj_id, wp_id
                        ):
                            failed += 1
                            results.append(
                                {
                                    "element_id": element_id,
                                    "type": el_type,
                                    "category": category,
                                    "status": "failed",
                                    "reason": f"workplan-not-found: (GLOBAL={dt_global_url}, ASSET={dt_asset_url}, PROJ={proj_id}, WP={wp_id})",
                                }
                            )
                            continue

                        # WORKINGSTEP 존재 확인(있으면)
                        if ws_id:
                            if not wp_id:
                                failed += 1
                                results.append(
                                    {
                                        "element_id": element_id,
                                        "type": el_type,
                                        "category": category,
                                        "status": "failed",
                                        "reason": "reference-invalid: WORKINGSTEP requires WORKPLAN",
                                    }
                                )
                                continue
                            if not workingstep_exists_in_project_xml(
                                proj_xml, proj_id, wp_id, ws_id
                            ):
                                failed += 1
                                results.append(
                                    {
                                        "element_id": element_id,
                                        "type": el_type,
                                        "category": category,
                                        "status": "failed",
                                        "reason": f"workingstep-not-found: (GLOBAL={dt_global_url}, ASSET={dt_asset_url}, PROJ={proj_id}, WP={wp_id}, WS={ws_id})",
                                    }
                                )
                                continue

                        # NC 전용 중복 체크
                        if (category or "").upper() == "NC":
                            dup = await self.repo.exists_nc_reference_refset(
                                dt_global_asset_url=dt_global_url,
                                dt_asset_url=dt_asset_url,
                                project_element_id=proj_id,
                                workplan_id=wp_id or "",
                            )
                            if dup:
                                failed += 1
                                results.append(
                                    {
                                        "element_id": element_id,
                                        "type": el_type,
                                        "category": category,
                                        "status": "failed",
                                        "reason": (
                                            "nc-reference-duplicate: "
                                            f"(GLOBAL={dt_global_url}, ASSET={dt_asset_url}, PROJ={proj_id}, WP={wp_id})"
                                        ),
                                    }
                                )
                                continue
                    except Exception as e:
                        failed += 1
                        results.append(
                            {
                                "element_id": element_id,
                                "type": el_type,
                                "category": category,
                                "status": "failed",
                                "reason": f"file-reference-parse-failed: {e}",
                            }
                        )
                        continue

                    # 3) 파일 첨부/주입 판단 (CHANGED)
                    # 이미 연결되어 있으면 스킵
                    already_linked = False
                    try:
                        if isinstance(elem, dict):
                            val = elem.get("value")
                            path = elem.get("path")
                            if isinstance(val, str) and self._OID_RE.match(val):
                                already_linked = True
                            elif isinstance(path, str):
                                m = self._GRIDFS_URI_RE.match(path)
                                if m:
                                    already_linked = True
                    except Exception:
                        pass

                    if already_linked:
                        patched_xml = part_xml  # 그대로 저장
                    else:
                        # 업로드 파일이 동봉된 경우에만 매칭/업로드 시도
                        fobj = None
                        if has_uploads and display_name:
                            fobj = file_map.get(display_name)

                        if fobj:
                            try:
                                file_oid = await file_service.process_upload(file=fobj)
                                patched_xml = inject_file_id_into_xml(
                                    xml=part_xml,
                                    file_id=file_oid,
                                    target_element_id=element_id,
                                    fill="both",
                                    overwrite=True,
                                    default_content_type=fobj.content_type
                                    or "application/octet-stream",
                                    path_template="",
                                )
                            except Exception as e:
                                failed += 1
                                results.append(
                                    {
                                        "element_id": element_id,
                                        "type": el_type,
                                        "category": category,
                                        "status": "failed",
                                        "reason": f"file-upload-failed: {e}",
                                    }
                                )
                                continue
                        else:
                            # 업로드 파일이 없거나(display_name 없음/미매칭 포함) → 베스트에포트: 그대로 저장
                            patched_xml = part_xml

                # D) DB 저장
                try:
                    resp = await self.repo.insert_asset(
                        AssetCreateRequest(xml=patched_xml)
                    )
                    created += 1
                    results.append(
                        {
                            "element_id": element_id,
                            "type": el_type,
                            "category": category,
                            "status": "created",
                            "asset_mongo_id": resp.asset_mongo_id,
                            "is_upload": False,
                        }
                    )
                except Exception as e:
                    failed += 1
                    results.append(
                        {
                            "element_id": element_id,
                            "type": el_type,
                            "category": category,
                            "status": "failed",
                            "reason": f"db-insert-failed: {e}",
                        }
                    )
                    continue

            except Exception as e:
                failed += 1
                results.append(
                    {
                        "element_id": None,
                        "status": "failed",
                        "reason": f"unexpected-error: {type(e).__name__}: {e}",
                    }
                )

        return {
            "results": results,
            "summary": {"total": len(parts), "created": created, "failed": failed},
        }

    async def create_from_xml(
        self, xml: str, *, upsert: bool = False
    ) -> AssetCreateResponse:
        """
        사용자가 올린 dt_asset 전체 XML을 그대로 저장.
        - (선택) 스키마 검사를 하고 싶으면 validate 호출
        - 네임스페이스 누락 보정
        - 메타 추출 후 repo로 위임
        """
        # (선택) 스키마 검사
        if not validate_xml_against_schema(xml):
            raise ValueError("Invalid XML schema")

        # 네임스페이스 보정(파서가 관대한 경우 생략 가능하지만 안전하게)
        d = xmltodict.parse(xml)
        if "dt_asset" in d:
            ensure_dtasset_namespaces(d["dt_asset"])
            # global_asset_id 보정 (내부 헬퍼 활용)
            raw_gid = d["dt_asset"].get("asset_global_id")
            if isinstance(raw_gid, str) and raw_gid.strip():
                d["dt_asset"]["asset_global_id"] = self._normalize_global_asset_id(
                    raw_gid
                )

            xml = self._prettify_xml(d)

        req = AssetCreateRequest(xml=xml)
        if upsert:
            return await self.repo.upsert_asset(req)
        return await self.repo.insert_asset(req)

    async def create_from_xml_with_file_id(
        self,
        *,
        xml: str,
        file_id: str,
        target_element_id: Optional[str] = None,
        fill: str = "value",  # "value" | "path" | "both"
        overwrite: bool = True,
        path_template: str = "gridfs://{oid}",
        default_content_type: str = "application/octet-stream",
        validate_schema: bool = True,
        upsert: bool = False,
    ) -> AssetCreateResponse:
        """
        file_id(이미 GridFS에 저장된 OID)를 dt_file 요소에 주입한 뒤 assets에 저장.
        - fill: 어떤 필드를 채울지 선택 ("value", "path", "both")
        - overwrite=False 이면 기존 값이 있을 때 덮어쓰지 않음
        - content_type이 XML에 없으면 default_content_type 채움
        - target_element_id로 주입 대상 dt_file을 특정 가능 (여러 개 있을 때 필수)
        """
        if fill not in ("value", "path", "both"):
            raise ValueError("fill은 'value' | 'path' | 'both' 중 하나여야 합니다.")

        d = xmltodict.parse(xml)  # 네임스페이스는 유지(단순 주입 목적)
        try:
            dt_file = select_dt_file_node(d, target_element_id)
        except Exception as e:
            raise self._map_util_error(e)

        # content_type 보정(없으면 기본값 채움)
        if dt_file.get("content_type") in (None, ""):
            dt_file["content_type"] = default_content_type

        # value/path 주입
        if fill in ("value", "both"):
            if overwrite or not dt_file.get("value"):
                dt_file["value"] = file_id

        if fill in ("path", "both"):
            if overwrite or not dt_file.get("path"):
                dt_file["path"] = path_template.format(oid=file_id)

        # 최종 XML 직렬화
        patched_xml = xmltodict.unparse(d)

        # (선택) 스키마 검증
        if validate_schema and not validate_xml_against_schema(patched_xml):
            raise ValueError("XML schema validation failed after injection")

        # 저장 (외부에서 중복 검사를 했더라도 레이스 대비)
        try:
            req = AssetCreateRequest(xml=patched_xml)
            if upsert:
                return await self.repo.upsert_asset(req)
            return await self.repo.insert_asset(req)
        except DuplicateKeyError as e:
            # 라우터에서 잡아 409로 변환하기 좋게 재전달
            raise CustomException(ExceptionEnum.ASSET_ID_DUPLICATION)

    # --------------- 조회/검색/삭제 (Repository 위임) ---------------

    async def list_global_asset_ids(self) -> GlobalAssetListResponse:
        ids = await self.repo.list_distinct_global_asset_ids()
        return GlobalAssetListResponse(global_asset_ids=sorted(ids))

    async def list_asset_ids_by_global(
        self, global_asset_id: str
    ) -> AssetIdListResponse:
        ids = await self.repo.list_distinct_asset_ids(global_asset_id)
        return AssetIdListResponse(asset_ids=ids)

    async def list_grouped_asset_ids(self) -> GroupedAssetIdsResponse:
        rows = await self.repo.list_grouped_asset_ids()
        items = [GroupedAssetIdsItem(**r) for r in rows]
        return GroupedAssetIdsResponse(items=items)

    async def list_assets(
        self,
        *,
        global_asset_id: str,
        asset_id: Optional[str] = None,
        type: Optional[str] = None,
    ) -> AssetListResponse:
        """
        - global_asset_id: 필수
        - asset_id, type: 선택 필터
        """
        norm_type, inferred_category = infer_type_and_category(type)
        query = AssetSearchQuery(
            global_asset_id=global_asset_id,
            asset_id=asset_id,
            type=norm_type,
            category=inferred_category,
        )
        rows = await self.repo.search_assets(query)

        # Pydantic v1/v2 호환
        parsed: List[AssetDocumentNoData]
        if hasattr(AssetDocumentNoData, "model_validate"):  # pydantic v2
            parsed = [AssetDocumentNoData.model_validate(r) for r in rows]
        else:  # pydantic v1
            parsed = [AssetDocumentNoData.parse_obj(r) for r in rows]

        return AssetListResponse(assets=parsed)

    async def get_by_mongo_id(self, mongo_id: str) -> Optional[dict]:
        return await self.repo.get_asset_by_mongo_id(mongo_id)

    async def get_by_keys(
        self, *, global_asset_id: str, asset_id: str, type: str, element_id: str
    ) -> Optional[dict]:
        return await self.repo.get_asset_by_keys(
            global_asset_id=global_asset_id,
            asset_id=asset_id,
            type=type,
            element_id=element_id,
        )

    async def get_by_keys_any(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        type: str,
        element_id: str,
    ) -> Optional[dict]:
        # type 별칭(normalize) → (정식 type, 암시적 category)
        resolved_type, inferred_category = infer_type_and_category(type)

        # global_asset_id 정규화/원문 둘 다 시도
        norm_gid = self._normalize_global_asset_id(global_asset_id)
        for gid in (norm_gid, global_asset_id):
            doc = await self.repo.get_asset_by_keys(
                global_asset_id=gid,
                asset_id=asset_id,
                type=resolved_type or type,
                element_id=element_id,
            )
            if not doc:
                continue
            # 별칭이 category를 내포했다면(예: nc → "NC"), 실제 문서와 불일치 시 무시
            if inferred_category is not None:
                if (doc.get("category") or "").lower() != inferred_category.lower():
                    continue
            return doc
        return None

    async def search(self, query: AssetSearchQuery) -> List[dict]:
        return await self.repo.search_assets(query)

    async def delete_by_mongo_id(self, mongo_id: str) -> bool:
        return await self.repo.delete_by_mongo_id(mongo_id)

    async def delete_by_keys(
        self, *, global_asset_id: str, asset_id: str, type: str, element_id: str
    ) -> bool:
        return await self.repo.delete_by_keys(
            global_asset_id=global_asset_id,
            asset_id=asset_id,
            type=type,
            element_id=element_id,
        )

    async def exists_by_keys(self, xml_string: str):
        """
        xml string에 있는 키 조합이 이미 존재하는지 확인한다.
        """

        meta = extract_dtasset_meta(xml_string=xml_string)
        res = await self.repo.exists_by_keys(
            global_asset_id=meta["global_asset_id"],
            asset_id=meta["asset_id"],
            type=meta["type"],
            element_id=meta["element_id"],
        )

        # 중복이 없을 경우
        if res is None:
            return False
        else:
            # 중복이 있으면 바로 에러로 발생
            raise CustomException(ExceptionEnum.ASSET_ID_DUPLICATION)

    # ------------update---------------------
    async def update_from_xml(
        self,
        *,
        mongo_id: str,
        xml: str,
        validate_schema: bool = True,
        forbid_type_change: bool = True,
        precheck_dup_conflict: bool = True,
    ) -> bool:
        """XML만 교체하는 업데이트."""
        old = await self.repo.get_asset_by_mongo_id(mongo_id)
        if not old:
            raise CustomException(ExceptionEnum.NO_DATA_FOUND)

        if validate_schema and not validate_xml_against_schema(xml):
            raise CustomException(ExceptionEnum.INVALID_ATTRIBUTE, "Invalid XML schema")

        new_meta = extract_dtasset_meta(xml, strict=True)

        # 타입 변경 금지
        if forbid_type_change and old.get("type") != new_meta["type"]:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE, "type change is not allowed"
            )

        # 키 변경 시 충돌 선검사(가독성 좋은 에러)
        if precheck_dup_conflict:
            keys_changed = any(
                old.get(k) != new_meta[k]
                for k in ("global_asset_id", "asset_id", "type", "element_id")
            )
            if keys_changed:
                other = await self.repo.get_asset_by_keys(
                    global_asset_id=new_meta["global_asset_id"],
                    asset_id=new_meta["asset_id"],
                    type=new_meta["type"],
                    element_id=new_meta["element_id"],
                )
                if other and str(other["_id"]) != str(old["_id"]):
                    raise CustomException(ExceptionEnum.ASSET_ID_DUPLICATION)

        # 실제 업데이트(유니크 인덱스 충돌은 여기서도 catch 가능)
        ok = await self.repo.update_asset_xml_by_mongo_id(mongo_id, xml)
        return ok

    async def update_from_xml_with_file_id(
        self,
        *,
        mongo_id: str,
        xml: str,
        new_file_id: str,
        target_element_id: str | None = None,
        fill: str = "value",  # "value" | "path" | "both"
        overwrite: bool = True,
        path_template: str = "gridfs://{oid}",
        default_content_type: str = "application/octet-stream",
        validate_schema: bool = True,
        forbid_type_change: bool = True,
        precheck_dup_conflict: bool = True,
    ) -> str | None:
        """
        새 file_id를 XML(dt_file)에 주입해 업데이트.
        반환: 기존 파일 OID(있으면) -> 라우터에서 정리용.
        """
        old = await self.repo.get_asset_by_mongo_id(mongo_id)
        if not old:
            raise CustomException(ExceptionEnum.NO_DATA_FOUND)

        # 기존 파일 OID 추출(있을 수도/없을 수도)
        old_file_id = self._extract_dt_file_value(old["data"], target_element_id)

        # 새 file_id를 주입해 패치된 XML 생성(POST 로직 재사용)
        patched_xml = xml
        d = xmltodict.parse(xml)
        try:
            dt_file = select_dt_file_node(d, target_element_id)
        except Exception as e:
            raise self._map_util_error(e)

        if dt_file.get("content_type") in (None, ""):
            dt_file["content_type"] = default_content_type

        if fill in ("value", "both"):
            if overwrite or not dt_file.get("value"):
                dt_file["value"] = new_file_id

        if fill in ("path", "both"):
            if overwrite or not dt_file.get("path"):
                dt_file["path"] = path_template.format(oid=new_file_id)

        patched_xml = xmltodict.unparse(d)

        # 나머지 검증/중복체크/업데이트는 공용 함수 사용
        await self.update_from_xml(
            mongo_id=mongo_id,
            xml=patched_xml,
            validate_schema=validate_schema,
            forbid_type_change=forbid_type_change,
            precheck_dup_conflict=precheck_dup_conflict,
        )
        return old_file_id

    async def extract(
        self,
        *,
        global_asset_id: str,
        asset_id: str | None = None,
        type: str | None = None,
        element_id: str | None = None,
        pretty: bool = True,
    ) -> str:
        """
        1) global만 -> 해당 조건에 맞는 모든 asset들의 dt_elements를 합쳐서 하나의 dt_asset으로 반환
        2) element_id 까지 오면 -> 해당 단일 asset 그대로 반환(= 원문 XML)
        3) type 이 오면 -> 동일 타입만 합쳐서 반환 (별칭: nc/tdms/vm/tool/machine 등 지원)
        """
        # element_id가 오면 단건 그대로 반환(원문)
        if element_id:
            # type/category 필터도 적용하고 싶으면 함께 넘겨도 OK
            norm_type, inferred_category = infer_type_and_category(type)
            q = AssetSearchQuery(
                global_asset_id=global_asset_id,
                asset_id=asset_id,
                type=norm_type,
                category=inferred_category,
                element_id=element_id,
            )
            rows = await self.repo.search_assets(q)
            if not rows:
                raise CustomException(ExceptionEnum.NO_DATA_FOUND)
            # 보통 1건이어야 함
            return rows[0]["data"]

        # 여러 개를 합쳐서 하나의 dt_asset으로 만들어 주는 경로
        norm_type, inferred_category = infer_type_and_category(type)
        q = AssetSearchQuery(
            global_asset_id=global_asset_id,
            asset_id=asset_id,
            type=norm_type,
            category=inferred_category,
        )
        rows = await self.repo.search_assets(q)
        if not rows:
            raise CustomException(ExceptionEnum.NO_DATA_FOUND)

        # dt_elements 모으기
        merged_elems: list[dict] = []
        for r in rows:
            try:
                d = xmltodict.parse(r["data"])
            except Exception:
                # 깨진 XML은 스킵(원하면 여기서 예외로 바꿔도 됨)
                continue
            root = d.get("dt_asset") or d  # 안전
            elems = root.get("dt_elements")
            if elems is None:
                continue
            if not isinstance(elems, list):
                elems = [elems]

            # type 파라미터가 들어왔을 때 방어적 필터(문서당 1개지만 안전하게)
            if norm_type:
                elems = [e for e in elems if e.get("@xsi:type") == norm_type]

            merged_elems.extend(elems)

        if not merged_elems:
            raise CustomException(ExceptionEnum.NO_DATA_FOUND)

        # (선택) element_id + @xsi:type 기준 중복 제거
        deduped: list[dict] = []
        seen: set[tuple[str | None, str | None]] = set()
        for e in merged_elems:
            k = (e.get("element_id"), e.get("@xsi:type"))
            if k in seen:
                continue
            seen.add(k)
            deduped.append(e)

        # 합쳐진 루트 구성
        root = {
            "dt_asset": {
                "@xmlns": "http://digital-thread.re/dt_asset",
                "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "@schemaVersion": self.DEFAULT_SCHEMA_VERSION,
                "asset_global_id": global_asset_id,
                # asset_id가 지정됐으면 그걸 root id로, 아니면 AGGREGATED로
                "id": asset_id or "AGGREGATED",
                "asset_kind": "instance",
                "dt_elements": deduped,
            }
        }
        return xmltodict.unparse(root, pretty=pretty)

    # --- 삭제: mongo_id 또는 키 조합으로 삭제 ---
    async def delete_asset(
        self,
        *,
        mongo_id: Optional[str] = None,
        global_asset_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        type: Optional[str] = None,
        element_id: Optional[str] = None,
        file_service: Optional[FileService] = None,
        delete_file: bool = True,
    ) -> Dict[str, Any]:
        """
        1) 대상 문서 조회
        2) dt_file이면 XML에서 OID 추출 → (옵션) 파일 삭제
        3) asset 문서 삭제
        """
        # 1) 조회
        if mongo_id:
            doc = await self.repo.get_asset_by_mongo_id(mongo_id)
        else:
            if not (global_asset_id and asset_id and type and element_id):
                raise CustomException(ExceptionEnum.INVALID_ATTRIBUTE)

            # type 별칭(normalize) → (정식 type, 암시적 category)
            resolved_type, inferred_category = infer_type_and_category(type)

            if not resolved_type:
                # 알 수 없는 타입 별칭
                raise CustomException(ExceptionEnum.INVALID_ATTRIBUTE)

            # 카테고리를 키로 쓰지는 않지만, 조회 후 검증은 해준다.
            doc = await self.repo.get_asset_by_keys(
                global_asset_id=global_asset_id,
                asset_id=asset_id,
                type=resolved_type,
                element_id=element_id,
            )

            if not doc:
                # 해당 키 조합 자체가 없음
                raise CustomException(ExceptionEnum.NO_DATA_FOUND)

            # 별칭이 category를 내포(nc→"NC", tdms→"TDMS", vm→"VM")하는 경우
            # 실제 문서 category와 불일치하면 '없다'로 간주
            if inferred_category is not None:
                if (doc.get("category") or "").lower() != inferred_category.lower():
                    raise CustomException(ExceptionEnum.NO_DATA_FOUND)

        if not doc:
            raise CustomException(ExceptionEnum.NO_DATA_FOUND)

        # 2) 파일 삭제 (dt_file인 경우만)
        deleted_file_ids: List[str] = []
        if delete_file and (doc.get("type") == "dt_file"):
            if not file_service:
                # 파일도 지워야 하는데 파일 서비스가 없으면 서버 설정 문제로 간주
                raise CustomException(ExceptionEnum.NO_FILE_UPLOADED)
            file_ids = self._extract_file_ids_from_dt_file_xml(doc.get("data", ""))
            for fid in file_ids:
                try:
                    await file_service.delete_file_by_id(fid)
                    deleted_file_ids.append(fid)
                except Exception:
                    # 파일이 이미 없거나 삭제 실패 → 에러로 올릴지 무시할지 정책에 따라 결정
                    # 여기선 '존재하지 않아도' 계속 진행하게 처리 (원하면 커스텀 예외로 변경)
                    pass

        # 3) asset 문서 삭제
        if mongo_id:
            ok = await self.repo.delete_by_mongo_id(mongo_id)
        else:
            ok = await self.repo.delete_by_keys(
                global_asset_id=global_asset_id,
                asset_id=asset_id,
                type=resolved_type,
                element_id=element_id,
            )
        if not ok:
            # 문서 삭제 실패
            raise CustomException(ExceptionEnum.ASSET_DELETE_FAILED)

        return {
            "deleted": True,
            "asset_mongo_id": str(doc.get("_id")),
            "deleted_file_ids": deleted_file_ids,
            "type": doc.get("type"),
            "global_asset_id": doc.get("global_asset_id"),
            "asset_id": doc.get("asset_id"),
            "element_id": doc.get("element_id"),
        }

    async def get_file_oid_by_asset_keys(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        element_id: str,
        type: str = "dt_file",
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """
        에셋 키로 dt_file 문서를 찾고, XML의 <value>(OID), display_name, content_type 반환.
        (스트림은 반환하지 않음)
        """
        doc = await self.repo.get_asset_by_keys(
            global_asset_id=global_asset_id,
            asset_id=asset_id,
            type=type,
            element_id=element_id,
        )
        if not doc:
            raise CustomException(
                ExceptionEnum.NO_DATA_FOUND, "dt_file not found by keys"
            )

        xml = doc.get("data") or ""
        oid = self._extract_dt_file_value(xml, target_element_id=element_id)
        if not oid or not self._OID_RE.match(oid):
            raise CustomException(
                ExceptionEnum.NO_DATA_FOUND, "file ObjectId(value) not found in xml"
            )

        # 메타(파일명/콘텐츠 타입) 추출은 헤더용 보조값
        display_name, content_type = self._extract_display_and_content_type(
            xml, target_element_id=element_id
        )
        return oid, display_name, content_type

    def _extract_display_and_content_type(
        self, xml: str, target_element_id: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        dt_file 노드에서 display_name, content_type 추출
        """
        try:
            d = xmltodict.parse(xml)
            dt_asset = d.get("dt_asset") or d
            elems = dt_asset.get("dt_elements")
            if not elems:
                return None, None
            elems = elems if isinstance(elems, list) else [elems]
            for e in elems:
                if not isinstance(e, dict):
                    continue
                if e.get("@xsi:type") != "dt_file":
                    continue
                if target_element_id and e.get("element_id") != target_element_id:
                    continue
                return e.get("display_name"), e.get("content_type")
        except Exception:
            pass
        return None, None

    def _normalize_global_asset_id(self, global_asset_id: str) -> str:
        """
        global_asset_id가 URI 형태인지 검사 후,
        아니라면 base_uri_prefix + user_prefix를 붙여서 URI로 변환한다.
        """
        if global_asset_id.startswith("http://") or global_asset_id.startswith(
            "https://"
        ):
            return global_asset_id
        # 기본 prefix 붙여서 URI로 만듦
        return f"{self.base_uri_prefix}/{self.user_prefix}/{global_asset_id}"

    def _norm_global_url(self, url_or_id: str) -> str:
        if url_or_id.startswith(("http://", "https://")):
            return url_or_id
        return f"{self.base_uri_prefix}/{self.user_prefix}/{url_or_id}"

    def _norm_asset_id(self, dt_asset_url_or_id: str) -> str:
        if dt_asset_url_or_id.startswith(("http://", "https://")):
            from urllib.parse import urlparse

            parts = [p for p in urlparse(dt_asset_url_or_id).path.split("/") if p]
            return parts[-1] if parts else ""
        return dt_asset_url_or_id

    def _rx_kv(self, key: str, val: str) -> Dict[str, Any]:
        """<key>KEY</key><value>VAL</value> 정규식 쿼리 보조"""
        import re

        def _esc(s: str) -> str:
            return re.escape(s)

        return {
            "data": {
                "$regex": rf"<key>\s*{_esc(key)}\s*</key>\s*<value>\s*{_esc(val)}\s*</value>",
                "$options": "is",
            }
        }

    async def find_nc_files_by_project_ref(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        project_element_id: str,
        workplan_id: str,
        validate_project_exists: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        지정 프로젝트/워크플랜을 참조하는 NC dt_file들을 검색하여 반환.
        - global_asset_id가 URI가 아니면 prefix 붙여 정규화
        - DT_GLOBAL_ASSET/DT_ASSET/DT_PROJECT/WORKPLAN 4키 모두 AND 매칭
        - (옵션) 먼저 프로젝트/워크플랜 존재 확인
        """
        g_url = self._normalize_global_asset_id(global_asset_id)
        a_url = asset_id

        if validate_project_exists:
            ok = await self.repo.project_workplan_exists(
                global_asset_id=g_url,
                asset_id=a_url,  # 저장은 URL 그대로 비교하도록 맞춘 상태
                project_element_id=project_element_id,
                workplan_id=workplan_id,
            )
            if not ok:
                # 프로젝트 자체가 없거나 해당 워크플랜이 없음
                raise CustomException(
                    ExceptionEnum.NO_DATA_FOUND,
                    detail=f"project/workplan not found (project={project_element_id}, wp={workplan_id})",
                )

        # dt_file/NC + 4개 key/value 매칭
        q = {
            "$and": [
                {"type": "dt_file"},
                {"category": "NC"},
                self._rx_kv("DT_GLOBAL_ASSET", g_url),
                self._rx_kv("DT_ASSET", a_url),
                self._rx_kv("DT_PROJECT", project_element_id),
                self._rx_kv("WORKPLAN", workplan_id),
            ]
        }
        cursor = self.repo.collection.find(
            q,
            projection={
                "_id": 1,
                "global_asset_id": 1,
                "asset_id": 1,
                "type": 1,
                "category": 1,
                "element_id": 1,
            },
        )
        return await cursor.to_list(length=None)

    def ensure_uploaded_filename_matches_xml(
        self,
        *,
        xml: str,
        element_id: str | None,
        uploaded_filename: str,
        case_sensitive: bool = True,
        compare_basename_only: bool = True,
    ) -> None:
        """
        XML(dt_file)의 <display_name>과 업로드 파일 이름이 일치하는지 검증.
        - 일치하지 않으면 CustomException(INVALID_ATTRIBUTE) 발생
        - case_sensitive=False 로 주면 대소문자 무시
        - compare_basename_only=True 면 경로/확장자 포함 이름에서 basename 만 비교
        """
        display_name, _ = self._extract_display_and_content_type(xml, element_id)
        if not display_name:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                "XML missing <display_name> for dt_file element",
            )

        left = (
            os.path.basename(uploaded_filename)
            if compare_basename_only
            else uploaded_filename
        )
        right = (
            os.path.basename(display_name) if compare_basename_only else display_name
        )

        if not case_sensitive:
            left, right = left.lower(), right.lower()

        if left != right:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                f"display_name mismatch: XML='{display_name}', uploaded='{uploaded_filename}'",
            )

    async def create_nc_dt_file_from_upload(
        self,
        *,
        global_asset_id: str,  # 프로젝트 dt_asset_global_id (URL or ID)
        project_asset_id: str,  # 프로젝트 asset_id (예: prj_011)
        project_element_id: str,  # dt_project element_id (예: milling_prj)
        workplan_id: str,  # workplan its_id (예: wp_001)
        file: UploadFile,
        file_service: FileService,
    ) -> AssetCreateResponse:
        """
        NC 파일 업로드 → 해당 프로젝트/워크플랜을 참조하는 NC dt_file dt_asset를 자동 생성해 저장.

        1) 프로젝트 + 워크플랜 존재 여부 확인 (find_nc_files_by_project_ref 내부에서 수행)
        2) 이미 동일 워크플랜을 참조하는 NC dt_file 이 있으면 400 (INVALID_ATTRIBUTE)
        3) 파일을 GridFS(FileService) 에 저장 → OID
        4) NC dt_file 전용 dt_asset XML 생성 (build_nc_dt_file_xml)
        5) AssetRepository 에 insert
        """

        # 1 + 2. 프로젝트/워크플랜 존재 확인 + NC 중복 체크
        #    - find_nc_files_by_project_ref: 존재 안 하면 NO_DATA_FOUND 던짐
        #    - NC dt_file 있으면 리스트 길이 > 0
        nc_files = await self.find_nc_files_by_project_ref(
            global_asset_id=global_asset_id,
            asset_id=project_asset_id,
            project_element_id=project_element_id,
            workplan_id=workplan_id,
            validate_project_exists=True,
        )

        if nc_files:
            # 이미 같은 프로젝트/워크플랜을 참조하는 NC dt_file 존재
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                detail="해당 워크플랜을 참조하는 NC dt_file 이 이미 존재합니다.",
            )

        # 3. 파일을 GridFS 에 저장 → OID
        file_oid = await file_service.process_upload(file=file)

        # 4. NC dt_file 전용 dt_asset XML 생성
        #    - global_asset_id는 내부 규칙에 따라 URI로 정규화해서 쓰는 게 안전
        norm_gid = self._normalize_global_asset_id(global_asset_id)

        nc_xml = build_nc_dt_file_xml(
            nc_global_asset_id=norm_gid,
            project_asset_id=project_asset_id,
            project_element_id=project_element_id,
            workplan_id=workplan_id,
            file_oid=str(file_oid),
            file_name=file.filename or "nc_program.tap",
        )

        # 5. AssetRepository 를 통해 MongoDB 에 저장
        req = AssetCreateRequest(xml=nc_xml)
        resp = await self.repo.insert_asset(req)
        return resp

    async def find_latest_step_file_by_project_ref(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        project_element_id: str,
        validate_project_exists: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        지정 '프로젝트'를 참조하는 STEP dt_file 중 최신 1개를 반환.
        - category in (STEP, STP)
        - 여러 개면 _id desc로 최신 1개 선택
        - 없으면 None
        """
        g_url = self._normalize_global_asset_id(global_asset_id)
        a_url = asset_id

        # ✅ project_exists()는 레포에 없음
        # ✅ 대신 get_project_xml_by_keys로 프로젝트 존재 여부 확인
        if validate_project_exists:
            project_xml = await self.repo.get_project_xml_by_keys(
                global_asset_id=g_url,
                asset_id=a_url,
                project_element_id=project_element_id,
            )
            if not project_xml:
                raise CustomException(
                    ExceptionEnum.NO_DATA_FOUND,
                    detail=f"project not found (project={project_element_id})",
                )

        q = {
            "$and": [
                {"type": "dt_file"},
                {"category": {"$in": ["STEP", "STP"]}},
                self._rx_kv("DT_GLOBAL_ASSET", g_url),
                self._rx_kv("DT_ASSET", a_url),
                self._rx_kv("DT_PROJECT", project_element_id),
                # ✅ WORKPLAN 조건 제거
            ]
        }

        cursor = self.repo.collection.find(
            q,
            projection={"_id": 1, "data": 1, "element_id": 1, "category": 1, "type": 1},
        ).sort([("_id", -1)])

        docs = await cursor.to_list(length=1)
        return docs[0] if docs else None
