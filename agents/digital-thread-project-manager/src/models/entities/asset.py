from __future__ import annotations

import re
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError
from src.utils.exceptions import CustomException, ExceptionEnum

from src.models.schemas.asset import (
    AssetCreateRequest,
    AssetCreateResponse,
    AssetSearchQuery,
)
from src.utils.v3_xml_parser import extract_dtasset_meta, project_workplan_exists_in_xml


def _esc(s: str) -> str:
    return re.escape(s)


def _stringify_object_id(doc: dict | None) -> dict | None:
    if not doc:
        return doc
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc


# Asset 정보를 MongoDB에 저장, 조회, 수정, 삭제 등 프로젝트 관련 DB 작업을 담당하는 클래스입니다.
class AssetRepository:
    """
    v30 자산 저장소:
    - 컬렉션: assets
    - 문서 스키마:
        {
          _id: ObjectId,
          global_asset_id: str,
          asset_id: str,
          type: str,           # dt_elements의 @xsi:type (예: dt_cutting_tool_13399, dt_file, dt_project ...)
          category: str|None,  # dt_elements/category
          element_id: str,     # dt_elements/element_id
          data: str,           # 원본 dt_asset XML
        }
    - 유니크 인덱스: (global_asset_id, asset_id, type, element_id)
    """

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection: AsyncIOMotorCollection = collection

    # -----------------------------
    # Create
    # -----------------------------
    async def insert_asset(self, req: AssetCreateRequest) -> AssetCreateResponse:
        """
        XML에서 메타 추출 후 저장.
        필수 필드(global_asset_id, asset_id, type, element_id) 누락 시 예외.
        중복 키일 경우 DuplicateKeyError 발생.
        """
        meta = extract_dtasset_meta(req.xml, strict=True)  # 반드시 strip 포함(아래 3번)
        doc = {
            "global_asset_id": meta["global_asset_id"],
            "asset_id": meta["asset_id"],
            "type": meta["type"],
            "category": meta.get("category"),
            "element_id": meta["element_id"],
            "is_upload": False,  # <<< NEW: 외부 API 업로드 여부 기본 False
            "data": req.xml,
        }
        try:
            result = await self.collection.insert_one(doc)
            return AssetCreateResponse(asset_mongo_id=str(result.inserted_id))
        except DuplicateKeyError:
            # 같은 키 조합의 기존 문서 찾아서 함께 보고
            existing = await self.collection.find_one(
                {
                    "global_asset_id": doc["global_asset_id"],
                    "asset_id": doc["asset_id"],
                    "type": doc["type"],
                    "element_id": doc["element_id"],
                },
                {
                    "_id": 1,
                    "global_asset_id": 1,
                    "asset_id": 1,
                    "type": 1,
                    "element_id": 1,
                },
            )
            # 로그로 남기기
            import logging

            logging.warning(
                "DUP on %s keys=%r existing=%r",
                self.collection.full_name,
                {
                    k: doc[k]
                    for k in ("global_asset_id", "asset_id", "type", "element_id")
                },
                existing,
            )
            # 409로 올려보내기(키 정보 포함)
            from src.utils.exceptions import CustomException, ExceptionEnum

            ex = CustomException(ExceptionEnum.ASSET_ID_DUPLICATION)
            ex.detail = {
                "message": "Duplicate asset key",
                "conflict_keys": {
                    k: doc[k]
                    for k in ("global_asset_id", "asset_id", "type", "element_id")
                },
                "existing": existing,
            }
            raise ex

    async def upsert_asset(self, req: AssetCreateRequest) -> AssetCreateResponse:
        """
        존재하면 교체(update), 없으면 생성(insert).
        매칭 키: (global_asset_id, asset_id, type, element_id)
        """
        meta = extract_dtasset_meta(req.xml, strict=True)
        key = {
            "global_asset_id": meta["global_asset_id"],
            "asset_id": meta["asset_id"],
            "type": meta["type"],
            "element_id": meta["element_id"],
        }

        # 기존 문서가 있으면 is_upload 잠금 검사
        existing = await self.collection.find_one(
            key, projection={"_id": 1, "is_upload": 1}
        )
        if existing and existing.get("is_upload") is True:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                "이미 플랫폼에 업로드 완료된 asset/project는 수정할 수 없습니다.",
            )

        update = {
            "$set": {
                "category": meta.get("category"),
                "data": req.xml,
            },
            "$setOnInsert": {"is_upload": False},  # <<< NEW
        }
        result = await self.collection.update_one(key, update, upsert=True)
        if result.upserted_id:
            return AssetCreateResponse(asset_mongo_id=str(result.upserted_id))
        # upsert가 아닌 순수 업데이트였다면, 기존 문서 _id를 다시 조회
        existing = await self.collection.find_one(key, projection={"_id": 1})
        return AssetCreateResponse(asset_mongo_id=str(existing["_id"]))

    # -----------------------------
    # Read
    # -----------------------------
    async def get_asset_by_mongo_id(self, mongo_id: str) -> Optional[dict]:
        return await self.collection.find_one({"_id": ObjectId(mongo_id)})

    async def get_asset_by_keys(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        type: str,
        element_id: str,
    ) -> Optional[dict]:
        doc = await self.collection.find_one(
            {
                "global_asset_id": global_asset_id,
                "asset_id": asset_id,
                "type": type,
                "element_id": element_id,
            }
        )
        return _stringify_object_id(doc)

    async def search_assets(self, query: AssetSearchQuery) -> List[dict]:
        """
        키 기반 필터 + 선택적 정규식(주의: 비용 큼)
        """
        q: Dict[str, Any] = {}
        if query.global_asset_id:
            q["global_asset_id"] = query.global_asset_id
        if query.asset_id:
            q["asset_id"] = query.asset_id
        if query.type:
            q["type"] = query.type
        if query.category:
            q["category"] = query.category
        if query.element_id:
            q["element_id"] = query.element_id
        if query.element_id_regex:
            q["element_id"] = {"$regex": query.element_id_regex, "$options": "i"}
        if query.data_regex:
            q["data"] = {"$regex": query.data_regex, "$options": "i"}

        cursor = self.collection.find(q)
        return await cursor.to_list(length=None)

    async def list_by_asset_id(self, asset_id: str) -> List[dict]:
        cursor = self.collection.find({"asset_id": asset_id})
        return await cursor.to_list(length=None)

    async def list_by_type(self, type_name: str) -> List[dict]:
        cursor = self.collection.find({"type": type_name})
        return await cursor.to_list(length=None)

    async def list_by_category(self, category: str) -> List[dict]:
        cursor = self.collection.find({"category": category})
        return await cursor.to_list(length=None)

    async def list_distinct_global_asset_ids(self) -> list[str]:
        """
        assets 컬렉션에서 중복 제거된 global_asset_id 목록 반환
        """
        ids = await self.collection.distinct("global_asset_id")
        # Mongo가 None을 포함할 수 있으니 문자열만 필터링
        return [i for i in ids if isinstance(i, str)]

    async def list_distinct_asset_ids(self, global_asset_id: str) -> list[str]:
        """
        특정 global_asset_id 아래의 중복 없는 asset_id 목록
        """
        ids = await self.collection.distinct(
            "asset_id",
            {"global_asset_id": global_asset_id},
        )
        return sorted([i for i in ids if isinstance(i, str)])

    async def list_grouped_asset_ids(self) -> list[dict]:
        """
        글로벌별 asset_id 배열을 묶어서 반환
        결과 예: [{"global_asset_id":"GA-1","asset_ids":["A-1","A-2"]}, ...]
        """
        cursor = self.collection.aggregate(
            [
                {
                    "$group": {
                        "_id": "$global_asset_id",
                        "asset_ids": {"$addToSet": "$asset_id"},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "global_asset_id": "$_id",
                        "asset_ids": 1,
                    }
                },
                {"$sort": {"global_asset_id": 1}},
            ]
        )
        rows = await cursor.to_list(length=None)
        # 문자열만 필터링 및 정렬
        for r in rows:
            r["asset_ids"] = sorted(
                [a for a in r.get("asset_ids", []) if isinstance(a, str)]
            )
        # None 글로벌 제거
        rows = [r for r in rows if isinstance(r.get("global_asset_id"), str)]
        return rows

    # -----------------------------
    # Update
    # -----------------------------
    async def update_asset_xml_by_mongo_id(self, mongo_id: str, new_xml: str) -> bool:
        """
        XML 교체 시, 메타가 달라질 수 있으므로 안전하게:
        - 새 XML 메타 추출
        - 기존 문서의 키와 달라지면 유니크 충돌 가능 → 키도 함께 갱신
        """
        # 수정 전 잠금 검사 (is_upload=True 면 예외)
        await self.check_upload_locked(mongo_id)

        meta = extract_dtasset_meta(new_xml, strict=True)
        update = {
            "$set": {
                "global_asset_id": meta["global_asset_id"],
                "asset_id": meta["asset_id"],
                "type": meta["type"],
                "category": meta.get("category"),
                "element_id": meta["element_id"],
                "data": new_xml,
                # is_upload 는 여기서 건드리지 않음 (외부 업로드 프로세스가 변경)
            }
        }
        result = await self.collection.update_one({"_id": ObjectId(mongo_id)}, update)
        return result.modified_count > 0

    # -----------------------------
    # Delete
    # -----------------------------
    async def delete_by_mongo_id(self, mongo_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(mongo_id)})
        return result.deleted_count > 0

    async def delete_by_keys(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        type: str,
        element_id: str,
    ) -> bool:
        result = await self.collection.delete_one(
            {
                "global_asset_id": global_asset_id,
                "asset_id": asset_id,
                "type": type,
                "element_id": element_id,
            }
        )
        return result.deleted_count > 0

    # in AssetRepository
    async def exists_by_keys(
        self, *, global_asset_id: str, asset_id: str, type: str, element_id: str
    ) -> bool:
        doc = await self.collection.find_one(
            {
                "global_asset_id": global_asset_id,
                "asset_id": asset_id,
                "type": type,
                "element_id": element_id,
            },
            projection={"_id": 1},
        )

        return doc

    # NEW: NC 1:1 중복 참조 검사
    async def exists_nc_reference_refset(
        self,
        *,
        dt_global_asset_url: str,  # URL/문자 그대로 비교 (정확히 동일 문자열)
        dt_asset_url: str,  # URL 혹은 asset_id… 저장된 그대로 비교
        project_element_id: str,
        workplan_id: str,
    ) -> bool:
        """
        NC dt_file 문서에서 아래 4개의 키-값이 모두 들어있는지 AND 조건으로 검사.
        - type == "dt_file"
        - category == "NC"
        - data 안에 아래 4가지 <key>/<value> 쌍이 모두 존재
        """
        # 각 키-값 쌍을 독립 정규식으로 만들고 $and로 결합
        rx_proj = {
            "data": {
                "$regex": rf"<key>\s*DT_PROJECT\s*</key>\s*<value>\s*{_esc(project_element_id)}\s*</value>",
                "$options": "is",
            }
        }
        rx_wp = {
            "data": {
                "$regex": rf"<key>\s*WORKPLAN\s*</key>\s*<value>\s*{_esc(workplan_id)}\s*</value>",
                "$options": "is",
            }
        }
        rx_global = {
            "data": {
                "$regex": rf"<key>\s*DT_GLOBAL_ASSET\s*</key>\s*<value>\s*{_esc(dt_global_asset_url)}\s*</value>",
                "$options": "is",
            }
        }
        rx_asset = {
            "data": {
                "$regex": rf"<key>\s*DT_ASSET\s*</key>\s*<value>\s*{_esc(dt_asset_url)}\s*</value>",
                "$options": "is",
            }
        }

        q = {
            "$and": [
                {"type": "dt_file"},
                {"category": "NC"},
                rx_proj,
                rx_wp,
                rx_global,
                rx_asset,
            ]
        }
        doc = await self.collection.find_one(q, projection={"_id": 1})
        return bool(doc)

    async def check_upload_locked(self, mongo_id: str) -> None:
        """
        주어진 mongo_id 문서의 is_upload가 True이면 예외 발생.
        """
        doc = await self.collection.find_one(
            {"_id": ObjectId(mongo_id)}, {"is_upload": 1}
        )
        if doc and doc.get("is_upload") is True:
            raise CustomException(
                ExceptionEnum.INVALID_ATTRIBUTE,
                detail="이미 플랫폼에 업로드 완료된 asset/project는 수정할 수 없습니다.",
            )

    async def project_workplan_exists(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        project_element_id: str,
        workplan_id: str,
    ) -> bool:
        """
        지정된 프로젝트 문서를 DB에서 찾고, 해당 XML 안에 workplan_id(its_id)가 실제로 존재하는지 검사.
        - True  -> 프로젝트가 있고 해당 워크플랜도 존재
        - False -> 프로젝트가 없거나, 워크플랜이 없음
        """
        proj = await self.collection.find_one(
            {
                "global_asset_id": global_asset_id,
                "asset_id": asset_id,
                "type": "dt_project",
                "element_id": project_element_id,
            },
            projection={"_id": 1, "data": 1},
        )
        if not proj or not isinstance(proj.get("data"), str):
            return False

        return project_workplan_exists_in_xml(
            proj["data"],
            project_element_id=project_element_id,
            workplan_id=workplan_id,
        )

    async def get_project_xml_by_keys(
        self, *, global_asset_id: str, asset_id: str, project_element_id: str
    ) -> Optional[str]:
        doc = await self.collection.find_one(
            {
                "global_asset_id": global_asset_id,
                "asset_id": asset_id,
                "type": "dt_project",
                "element_id": project_element_id,
            },
            projection={"_id": 0, "data": 1},
        )
        return doc["data"] if doc and isinstance(doc.get("data"), str) else None

    ## CAM 실패시 롤백을 위한 추가 함수 ##
    async def rollback_restore_xml_by_mongo_id(
        self, mongo_id: str, xml_text: str
    ) -> bool:
        """
        롤백 전용:
        - 잠금 검사/메타 갱신 무시
        - data 필드만 강제 복원
        """
        result = await self.collection.update_one(
            {"_id": ObjectId(mongo_id)},
            {"$set": {"data": xml_text}},
        )
        return result.modified_count > 0

    async def rollback_delete_tool_by_keys(
        self, *, global_asset_id: str, asset_id: str, element_id: str
    ) -> bool:
        """
        롤백 전용:
        - 생성된 cutting_tool 같은 부속 asset을 강제로 삭제
        - category/type 조건 없이 element_id 기준으로 단순 삭제
        """
        result = await self.collection.delete_one(
            {
                "global_asset_id": global_asset_id,
                "asset_id": asset_id,
                "element_id": element_id,
            }
        )
        return result.deleted_count > 0

    async def rollback_delete_by_mongo_id(self, mongo_id: str) -> bool:
        """
        롤백 전용:
        - 잠금 검사 무시하고 바로 삭제
        """
        result = await self.collection.delete_one({"_id": ObjectId(mongo_id)})
        return result.deleted_count > 0

    async def set_is_upload_true_by_mongo_id(self, mongo_id: str) -> bool:
        """
        업로드 성공 시 문서의 is_upload 플래그를 True로 세팅.
        """
        res = await self.collection.update_one(
            {"_id": ObjectId(mongo_id)}, {"$set": {"is_upload": True}}
        )
        return res.modified_count > 0

    async def set_is_upload_true_by_keys(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        type: str,
        element_id: str,
    ) -> bool:
        """
        키 조합으로 찾아 is_upload=True.
        """
        res = await self.collection.update_one(
            {
                "global_asset_id": global_asset_id,
                "asset_id": asset_id,
                "type": type,
                "element_id": element_id,
            },
            {"$set": {"is_upload": True}},
        )
        return res.modified_count > 0

    async def find_nc_files_by_ref(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        project_element_id: str,
        workplan_id: str,
        workingstep_id: Optional[str] = None,
        limit: int = 500,
    ) -> list[dict]:
        """
        (기존 기능 유지)
        - category == 'NC' 인 dt_file만 찾는 버전
        """
        return await self.find_files_by_ref(
            global_asset_id=global_asset_id,
            asset_id=asset_id,
            project_element_id=project_element_id,
            workplan_id=workplan_id,
            workingstep_id=workingstep_id,
            categories=["NC"],  # ✅ 여기서만 NC로 제한
            limit=limit,
        )

    async def find_files_by_ref(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        project_element_id: str,
        workplan_id: str,
        workingstep_id: Optional[str] = None,
        categories: Optional[list[str]] = None,
        limit: int = 500,
    ) -> list[dict]:
        """
        dt_file 문서들 중에서 reference.keys 안에
        - DT_GLOBAL_ASSET == global_asset_id
        - DT_ASSET == asset_id
        - DT_PROJECT == project_element_id
        - WORKPLAN == workplan_id
        - (옵션) WORKINGSTEP == workingstep_id
        를 모두 포함하는 dt_file들을 찾는다.
        categories 가 주어지면 category 필터를 적용한다.
        """
        conditions: list[dict] = [
            {"type": "dt_file"},
            {
                "data": {
                    "$regex": (
                        f"<key>DT_GLOBAL_ASSET</key>"
                        f"\\s*<value>{re.escape(global_asset_id)}</value>"
                    )
                }
            },
            {
                "data": {
                    "$regex": (
                        f"<key>DT_ASSET</key>"
                        f"\\s*<value>{re.escape(asset_id)}</value>"
                    )
                }
            },
            {
                "data": {
                    "$regex": (
                        f"<key>DT_PROJECT</key>"
                        f"\\s*<value>{re.escape(project_element_id)}</value>"
                    )
                }
            },
            {
                "data": {
                    "$regex": (
                        f"<key>WORKPLAN</key>"
                        f"\\s*<value>{re.escape(workplan_id)}</value>"
                    )
                }
            },
        ]

        if workingstep_id:
            conditions.append(
                {
                    "data": {
                        "$regex": (
                            f"<key>WORKINGSTEP</key>"
                            f"\\s*<value>{re.escape(workingstep_id)}</value>"
                        )
                    }
                }
            )

        # ✅ category 필터는 옵션
        if categories:
            if len(categories) == 1:
                conditions.append({"category": categories[0]})
            else:
                conditions.append({"category": {"$in": categories}})

        query = {"$and": conditions}
        cursor = self.collection.find(
            query,
            projection={"_id": 1, "global_asset_id": 1, "asset_id": 1, "element_id": 1},
            limit=limit,
        )
        return await cursor.to_list(length=limit)

    async def find_files_by_project_ref(
        self,
        *,
        global_asset_id: str,
        asset_id: str,
        project_element_id: str,
        categories: Optional[list[str]] = None,
        limit: int = 500,
    ) -> list[dict]:
        """
        dt_file 문서들 중에서 reference.keys 안에
        - DT_GLOBAL_ASSET == global_asset_id
        - DT_ASSET == asset_id
        - DT_PROJECT == project_element_id
        를 포함하는 dt_file들을 찾는다.
        (WORKPLAN 조건 없음 = 프로젝트 레벨 파일: STEP, TITLE_IMAGE 등 포함)

        categories 가 주어지면 category 필터를 적용한다.
        """
        conditions: list[dict] = [
            {"type": "dt_file"},
            {
                "data": {
                    "$regex": (
                        f"<key>DT_GLOBAL_ASSET</key>"
                        f"\\s*<value>{re.escape(global_asset_id)}</value>"
                    )
                }
            },
            {
                "data": {
                    "$regex": (
                        f"<key>DT_ASSET</key>"
                        f"\\s*<value>{re.escape(asset_id)}</value>"
                    )
                }
            },
            {
                "data": {
                    "$regex": (
                        f"<key>DT_PROJECT</key>"
                        f"\\s*<value>{re.escape(project_element_id)}</value>"
                    )
                }
            },
        ]

        # ✅ category 필터는 find_files_by_ref와 동일 방식(=Mongo 필드 category)
        if categories:
            if len(categories) == 1:
                conditions.append({"category": categories[0]})
            else:
                conditions.append({"category": {"$in": categories}})

        query = {"$and": conditions}
        cursor = self.collection.find(
            query,
            projection={"_id": 1, "global_asset_id": 1, "asset_id": 1, "element_id": 1},
            limit=limit,
        )
        return await cursor.to_list(length=limit)
