"""Digital Thread Platform lookup endpoints for MES screens."""

from typing import Any, List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ....schemas.digital_twin import P4RPayloadPreview
from ....schemas.master import DtProjectLookupRead
from ....services.dtp_client import DtpClient, DtpClientError, DtpConfigurationError
from ....services.digital_twin.p4r_adapter import P4RPayloadAdapter
from ...deps import CurrentUser, DBSession

router = APIRouter()


def _dtp_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, DtpConfigurationError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DTP API key is not configured",
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(exc) or "DTP request failed",
    )


def _string(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if value is not None and value != "":
            return str(value)
    return None


def _normalize_project(item: dict[str, Any]) -> DtProjectLookupRead | None:
    asset_global_id = _string(item, "assetGlobalId", "asset_global_id", "gid", "globalAssetId")
    asset_id = _string(item, "assetId", "asset_id", "aid")
    element_id = _string(item, "elementId", "element_id", "id")
    if not asset_global_id or not asset_id or not element_id:
        return None
    return DtProjectLookupRead(
        asset_global_id=asset_global_id,
        asset_id=asset_id,
        element_id=element_id,
        element_full_id=_string(item, "elementFullId", "element_full_id", "fullId"),
        element_category=_string(item, "elementCategory", "category") or "Project",
        external_project_id=_string(item, "uuid", "projectId", "project_id", "id"),
        display_name=_string(item, "name", "displayName", "elementName") or element_id,
        uuid=_string(item, "uuid"),
        raw_metadata=item,
    )


@router.get("/projects", response_model=List[DtProjectLookupRead])
async def list_dtp_projects(
    current_user: CurrentUser,
    keyword: str | None = None,
) -> List[DtProjectLookupRead]:
    """DTP Project 목록 검색."""
    client = DtpClient()
    try:
        raw_projects = await client.list_projects(keyword=keyword)
    except (DtpConfigurationError, DtpClientError) as exc:
        raise _dtp_http_error(exc) from exc
    return [project for item in raw_projects if (project := _normalize_project(item))]


@router.get("/projects/tree")
async def get_dtp_project_tree(
    current_user: CurrentUser,
    asset_global_id: str,
    asset_id: str,
) -> dict[str, Any]:
    """DTP Project tree 원문 조회. 화면 미리보기와 디버깅용."""
    client = DtpClient()
    try:
        return await client.get_project_tree(asset_global_id, asset_id)
    except (DtpConfigurationError, DtpClientError) as exc:
        raise _dtp_http_error(exc) from exc


@router.get("/p4r-payload/preview", response_model=P4RPayloadPreview)
async def preview_p4r_payload(
    db: DBSession,
    current_user: CurrentUser,
    lot_no: str,
    raw: bool = False,
) -> P4RPayloadPreview | JSONResponse:
    """LOT 기준 P4R JSON preview 생성.

    `raw=true`이면 wrapper 없이 실제 P4R payload만 반환한다.
    """
    adapter = P4RPayloadAdapter()
    try:
        preview = await adapter.build_preview(db, lot_no)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if raw:
        return JSONResponse(content=preview["payload"])
    return P4RPayloadPreview(**preview)
