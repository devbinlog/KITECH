from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class AssetCreateRequest(BaseModel):
    xml: str = Field(..., description="dt_asset 전체 XML 원문")


class AssetCreateResponse(BaseModel):
    asset_mongo_id: str


class GlobalAssetListResponse(BaseModel):
    global_asset_ids: List[str]


class AssetIdListResponse(BaseModel):
    asset_ids: List[str]


class GroupedAssetIdsItem(BaseModel):
    global_asset_id: str
    asset_ids: List[str]


class GroupedAssetIdsResponse(BaseModel):
    items: List[GroupedAssetIdsItem]


class AssetDocument(BaseModel):
    id: str = Field(alias="_id")
    global_asset_id: str
    asset_id: str
    type: str
    category: Optional[str] = None
    element_id: str
    data: str


class AssetDocumentNoData(BaseModel):
    id: str = Field(alias="_id")
    global_asset_id: str
    asset_id: str
    type: str
    category: Optional[str] = None
    element_id: str

    # Pydantic v2
    @field_validator("id", mode="before")
    @classmethod
    def _coerce_objectid(cls, v):
        return str(v) if isinstance(v, ObjectId) else v


class AssetSearchQuery(BaseModel):
    global_asset_id: Optional[str] = None
    asset_id: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    element_id: Optional[str] = None
    # XML 본문 정규식 검색 (비권장: 비용 큼)
    data_regex: Optional[str] = None
    # 부분 일치(대소문자 무시)로 element_id 검색하고 싶을 때
    element_id_regex: Optional[str] = None


class AssetListResponse(BaseModel):
    assets: List[AssetDocumentNoData]


class AttachRefResponse(BaseModel):
    updated: bool
    project_mongo_id: str
