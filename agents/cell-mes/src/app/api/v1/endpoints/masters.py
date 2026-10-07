"""Master data endpoints: Products and Standard Processes."""

import shutil
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, status, UploadFile, File
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ....core.config import settings
from ....models.master import (
    DtFileRef,
    DtProjectRef,
    DtProjectWorkplan,
    ProcessRouting,
    ProcessRoutingFile,
    Product,
    ProductDtProjectLink,
    StdProcess,
)
from ....schemas.master import (
    DtFileRefRead,
    DtProjectLinkRead,
    DtProjectSelect,
    DtProjectSummary,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    StdProcessCreate,
    StdProcessRead,
    StdProcessUpdate,
)
from ....services.dtp_client import DtpClient, DtpClientError, DtpConfigurationError
from ....services.dtp_xml_parser import parse_project_workplans
from ...deps import DBSession, CurrentUser

router = APIRouter()


def _upload_root() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    if upload_dir.is_absolute():
        return upload_dir
    return Path.cwd() / upload_dir


def _resolve_routing_file_path(routing_file: ProcessRoutingFile) -> Path | None:
    """Resolve only the file path recorded in DB against the configured upload root."""
    cwd = Path.cwd()
    raw_path = routing_file.file_path or ""
    candidates = []

    if raw_path.startswith("/uploads/"):
        candidates.append(_upload_root() / raw_path.removeprefix("/uploads/"))
    elif raw_path:
        candidate = Path(raw_path)
        candidates.append(candidate if candidate.is_absolute() else cwd / candidate)

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.is_file():
            return resolved
    return None


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


def _short_ref(value: str | None) -> str | None:
    if not value:
        return None
    return value.rstrip("/").rsplit("/", 1)[-1]


def _extract_references(raw: object) -> dict[str, str]:
    references: dict[str, str] = {}
    if isinstance(raw, dict):
        items = raw.items()
    elif isinstance(raw, list):
        items = []
        for item in raw:
            if isinstance(item, dict):
                key = item.get("key") or item.get("name") or item.get("type")
                value = item.get("value") or item.get("id") or item.get("ref")
                if key and value:
                    references[str(key)] = str(value)
        return references
    else:
        return references

    for key, value in items:
        if value is None:
            continue
        if isinstance(value, dict):
            value = value.get("value") or value.get("id") or value.get("ref")
        if isinstance(value, list):
            value = value[0] if value else None
        if value is not None:
            references[str(key)] = str(value)
    return references


def _extract_dtp_file_references(item: dict) -> dict[str, str]:
    references = _extract_references(item.get("references") or item.get("reference") or {})
    for ref_item in item.get("reflist") or []:
        if not isinstance(ref_item, dict):
            continue
        for pair in ref_item.get("keys") or []:
            if not isinstance(pair, dict):
                continue
            key = pair.get("key")
            value = pair.get("value")
            if key and value is not None:
                references[str(key)] = str(value)
    return references


def _reference_value(references: dict[str, str], *names: str) -> str | None:
    normalized = {
        key.lower().replace("_", "").replace("-", "").replace(" ", ""): value
        for key, value in references.items()
    }
    for name in names:
        value = normalized.get(name.lower().replace("_", "").replace("-", "").replace(" ", ""))
        if value:
            return value
    return None


def _project_summary(dt_project: DtProjectRef | None) -> DtProjectSummary | None:
    if not dt_project:
        return None
    workplans = sorted(dt_project.workplans, key=lambda item: (item.level, item.sequence, item.id))
    return DtProjectSummary(
        id=dt_project.id,
        platform=dt_project.platform,
        external_project_id=dt_project.external_project_id,
        asset_global_id=dt_project.asset_global_id,
        asset_id=dt_project.asset_id,
        element_id=dt_project.element_id,
        element_full_id=dt_project.element_full_id,
        element_category=dt_project.element_category,
        display_name=dt_project.display_name,
        uuid=dt_project.uuid,
        workplans=workplans,
    )


async def _current_dt_project(db: DBSession, product_id: int) -> DtProjectRef | None:
    result = await db.execute(
        select(ProductDtProjectLink)
        .where(
            ProductDtProjectLink.product_id == product_id,
            ProductDtProjectLink.relation_type == "PRIMARY",
            ProductDtProjectLink.is_current.is_(True),
        )
        .options(
            selectinload(ProductDtProjectLink.dt_project).selectinload(DtProjectRef.workplans)
        )
    )
    link = result.scalar_one_or_none()
    return link.dt_project if link else None


async def _attach_dt_project_summary(db: DBSession, product: Product) -> Product:
    product.current_dt_project = _project_summary(await _current_dt_project(db, product.id))
    return product


async def _upsert_dt_project_ref(
    db: DBSession,
    selected: DtProjectSelect,
    tree: dict,
) -> DtProjectRef:
    xml_str = tree.get("xmlStr") or tree.get("xml") or tree.get("projectXml") or ""
    workplans = parse_project_workplans(xml_str)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(DtProjectRef)
        .where(
            DtProjectRef.platform == "DTP",
            DtProjectRef.asset_global_id == selected.asset_global_id,
            DtProjectRef.asset_id == selected.asset_id,
            DtProjectRef.element_id == selected.element_id,
        )
        .options(selectinload(DtProjectRef.workplans))
    )
    dt_project = result.scalar_one_or_none()
    project_data = {
        "platform": "DTP",
        "external_project_id": selected.external_project_id or str(tree.get("id") or ""),
        "asset_global_id": selected.asset_global_id,
        "asset_id": selected.asset_id,
        "element_id": selected.element_id,
        "element_full_id": selected.element_full_id,
        "element_category": selected.element_category,
        "display_name": selected.display_name or tree.get("name") or selected.element_id,
        "uuid": selected.uuid or str(tree.get("uuid") or "") or None,
        "xml_path": tree.get("path") or tree.get("xmlPath"),
        "raw_metadata": tree,
        "synced_at": now,
    }
    is_new_project = dt_project is None
    if dt_project:
        for field, value in project_data.items():
            setattr(dt_project, field, value)
    else:
        dt_project = DtProjectRef(**project_data)
        db.add(dt_project)
        await db.flush()

    existing = {}
    if not is_new_project:
        existing = {
            (workplan.workplan_id, workplan.source_path): workplan
            for workplan in dt_project.workplans
        }
    for parsed in workplans:
        key = (parsed.workplan_id, parsed.source_path)
        row = existing.get(key)
        data = {
            "dt_project_ref_id": dt_project.id,
            "workplan_id": parsed.workplan_id,
            "parent_workplan_id": parsed.parent_workplan_id,
            "display_name": parsed.display_name,
            "source_path": parsed.source_path,
            "level": parsed.level,
            "sequence": parsed.sequence,
            "has_direct_steps": parsed.has_direct_steps,
            "raw_fragment": parsed.raw_fragment,
        }
        if row:
            for field, value in data.items():
                setattr(row, field, value)
        else:
            db.add(DtProjectWorkplan(**data))
    await db.flush()
    await db.refresh(dt_project, attribute_names=["workplans"])
    return dt_project


async def _link_product_to_dt_project(
    db: DBSession,
    product: Product,
    selected: DtProjectSelect,
) -> DtProjectRef:
    client = DtpClient()
    try:
        tree = await client.get_project_tree(selected.asset_global_id, selected.asset_id)
    except (DtpConfigurationError, DtpClientError) as exc:
        raise _dtp_http_error(exc) from exc

    dt_project = await _upsert_dt_project_ref(db, selected, tree)
    result = await db.execute(
        select(ProductDtProjectLink).where(
            ProductDtProjectLink.product_id == product.id,
            ProductDtProjectLink.relation_type == "PRIMARY",
            ProductDtProjectLink.is_current.is_(True),
        )
    )
    for link in result.scalars().all():
        link.is_current = False
        link.unlinked_at = datetime.now(timezone.utc)
    await db.flush()
    db.add(
        ProductDtProjectLink(
            product_id=product.id,
            dt_project_ref_id=dt_project.id,
            relation_type="PRIMARY",
            is_current=True,
        )
    )
    await db.flush()
    await db.refresh(dt_project, attribute_names=["workplans"])
    return dt_project


@router.post("/files/upload")
async def upload_master_file(
    db: DBSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    """마스터 기준 (NC 등) 물리 파일 업로드 API."""
    upload_dir = _upload_root() / "nc"
    upload_dir.mkdir(parents=True, exist_ok=True)

    _, ext = os.path.splitext(file.filename)
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = upload_dir / safe_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "success",
        "file_path": f"/uploads/nc/{safe_filename}",
        "original_filename": file.filename,
    }


@router.get("/files/{file_id}/download")
async def download_routing_file(
    file_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """ProcessRoutingFile의 NC 파일 본문 조회.

    미들웨어가 공정별 NC 파일 내용을 응답 본문으로 직접 읽을 때 사용.
    GET /api/v1/masters/products/{product_id}/routings 로 file_id를 먼저 조회할 것.
    """
    result = await db.execute(
        select(ProcessRoutingFile)
        .where(ProcessRoutingFile.id == file_id)
        .options(selectinload(ProcessRoutingFile.dt_file))
    )
    routing_file = result.scalar_one_or_none()
    if not routing_file:
        raise HTTPException(status_code=404, detail="File record not found")

    if routing_file.source_type == "DTP":
        if not routing_file.dt_file:
            raise HTTPException(status_code=404, detail="DTP file reference not found")
        client = DtpClient()
        try:
            content = await client.download_userdata_file(routing_file.dt_file.path)
        except (DtpConfigurationError, DtpClientError) as exc:
            raise _dtp_http_error(exc) from exc
        return PlainTextResponse(
            content=content.decode("utf-8", errors="replace"),
            media_type="text/plain",
        )

    actual_path = _resolve_routing_file_path(routing_file)
    if not actual_path:
        raise HTTPException(status_code=404, detail="File not found on disk")

    with open(actual_path, "r", encoding="utf-8", errors="replace") as file:
        content = file.read()

    return PlainTextResponse(content=content, media_type="text/plain")


# ============================================================================
# Standard Processes
# ============================================================================


@router.get("/std-processes", response_model=List[StdProcessRead])
async def list_std_processes(
    db: DBSession,
    current_user: CurrentUser,
) -> List[StdProcess]:
    """표준공정 목록 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        표준공정 목록 (코드순 정렬)

    """
    result = await db.execute(
        select(StdProcess).options(selectinload(StdProcess.category)).order_by(StdProcess.code)
    )
    return list(result.scalars().all())


@router.post("/std-processes", response_model=StdProcessRead, status_code=status.HTTP_201_CREATED)
async def create_std_process(
    db: DBSession,
    current_user: CurrentUser,
    process_in: StdProcessCreate,
) -> StdProcess:
    """표준공정 생성.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        process_in: 표준공정 데이터 (code, name, equipment_type 등)

    Returns:
        생성된 표준공정 정보

    Raises:
        HTTPException: 코드 중복 시 400 에러

    """
    # Check for duplicate code
    result = await db.execute(select(StdProcess).where(StdProcess.code == process_in.code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Standard process with code '{process_in.code}' already exists",
        )

    process_data = process_in.model_dump()
    if process_data.get("required_machines") is None and process_data.get("equipment_type"):
        process_data["required_machines"] = [process_data["equipment_type"]]

    process = StdProcess(**process_data)
    db.add(process)
    await db.commit()
    await db.refresh(process)
    return process


@router.get("/std-processes/{process_id}", response_model=StdProcessRead)
async def get_std_process(
    db: DBSession,
    current_user: CurrentUser,
    process_id: int,
) -> StdProcess:
    """표준공정 단건 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        process_id: 표준공정 ID

    Returns:
        표준공정 정보

    Raises:
        HTTPException: 표준공정 미존재 시 404 에러

    """
    result = await db.execute(
        select(StdProcess)
        .options(selectinload(StdProcess.category))
        .where(StdProcess.id == process_id)
    )
    process = result.scalar_one_or_none()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Standard process not found",
        )
    return process


@router.delete("/std-processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_std_process(
    db: DBSession,
    current_user: CurrentUser,
    process_id: int,
) -> None:
    """표준공정 삭제.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        process_id: 표준공정 ID

    Raises:
        HTTPException: 표준공정 미존재 시 404 에러

    """
    result = await db.execute(select(StdProcess).where(StdProcess.id == process_id))
    process = result.scalar_one_or_none()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Standard process not found",
        )

    await db.delete(process)
    await db.commit()


@router.patch("/std-processes/{process_id}", response_model=StdProcessRead)
async def update_std_process(
    db: DBSession,
    current_user: CurrentUser,
    process_id: int,
    process_in: StdProcessUpdate,
) -> StdProcess:
    """표준공정 수정.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        process_id: 표준공정 ID
        process_in: 수정할 데이터

    Returns:
        수정된 표준공정 정보

    Raises:
        HTTPException: 표준공정 미존재 시 404 에러

    """
    result = await db.execute(
        select(StdProcess)
        .options(selectinload(StdProcess.category))
        .where(StdProcess.id == process_id)
    )
    process = result.scalar_one_or_none()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Standard process not found",
        )

    update_data = process_in.model_dump(exclude_unset=True)
    if (
        "required_machines" not in update_data
        and update_data.get("equipment_type")
        and not process.required_machines
    ):
        update_data["required_machines"] = [update_data["equipment_type"]]
    for field, value in update_data.items():
        setattr(process, field, value)

    await db.commit()
    await db.refresh(process)
    return process


# ============================================================================
# Products
# ============================================================================


@router.get("/products", response_model=List[ProductRead])
async def list_products(
    db: DBSession,
    current_user: CurrentUser,
    include_deleted: bool = False,
) -> List[Product]:
    """제품 목록 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        include_deleted: 삭제된 제품 포함 여부

    Returns:
        제품 목록 (코드순 정렬)

    """
    query = select(Product).order_by(Product.code)
    if not include_deleted:
        query = query.where(Product.is_deleted.is_(False))
    result = await db.execute(query)
    products = list(result.scalars().all())
    for product in products:
        await _attach_dt_project_summary(db, product)
    return products


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    db: DBSession,
    current_user: CurrentUser,
    product_in: ProductCreate,
) -> Product:
    """제품 생성.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        product_in: 제품 데이터 (code, name 등)

    Returns:
        생성된 제품 정보

    Raises:
        HTTPException: 코드 중복 시 400 에러

    """
    # Check for duplicate code
    result = await db.execute(select(Product).where(Product.code == product_in.code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with code '{product_in.code}' already exists",
        )

    product = Product(**product_in.model_dump(exclude={"dt_project"}))
    db.add(product)
    await db.flush()
    if product_in.dt_project:
        dt_project = await _link_product_to_dt_project(db, product, product_in.dt_project)
        product.current_dt_project = _project_summary(dt_project)
    await db.commit()
    await db.refresh(product)
    if not getattr(product, "current_dt_project", None):
        await _attach_dt_project_summary(db, product)
    return product


@router.get("/products/{product_id}", response_model=ProductRead)
async def get_product(
    db: DBSession,
    current_user: CurrentUser,
    product_id: int,
) -> Product:
    """제품 단건 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        product_id: 제품 ID

    Returns:
        제품 정보

    Raises:
        HTTPException: 제품 미존재 시 404 에러

    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return await _attach_dt_project_summary(db, product)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    db: DBSession,
    current_user: CurrentUser,
    product_id: int,
) -> None:
    """제품 삭제 (소프트 삭제).

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        product_id: 제품 ID

    Raises:
        HTTPException: 제품 미존재 시 404 에러

    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    product.is_deleted = True
    await db.commit()


@router.patch("/products/{product_id}", response_model=ProductRead)
async def update_product(
    db: DBSession,
    current_user: CurrentUser,
    product_id: int,
    product_in: ProductUpdate,
) -> Product:
    """제품 수정.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        product_id: 제품 ID
        product_in: 수정할 데이터

    Returns:
        수정된 제품 정보

    Raises:
        HTTPException: 제품 미존재 시 404 에러

    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    await _attach_dt_project_summary(db, product)
    return product


@router.get("/products/{product_id}/dt-project", response_model=DtProjectLinkRead)
async def get_product_dt_project(
    db: DBSession,
    current_user: CurrentUser,
    product_id: int,
) -> DtProjectLinkRead:
    """제품에 현재 연결된 DT Project 조회."""
    result = await db.execute(select(Product.id).where(Product.id == product_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    dt_project = await _current_dt_project(db, product_id)
    return DtProjectLinkRead(product_id=product_id, dt_project=_project_summary(dt_project))


@router.put("/products/{product_id}/dt-project", response_model=DtProjectLinkRead)
async def link_product_dt_project(
    db: DBSession,
    current_user: CurrentUser,
    product_id: int,
    dt_project_in: DtProjectSelect,
) -> DtProjectLinkRead:
    """제품에 DT Project를 연결하거나 현재 연결을 교체."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    dt_project = await _link_product_to_dt_project(db, product, dt_project_in)
    await db.commit()
    await db.refresh(dt_project, attribute_names=["workplans"])
    return DtProjectLinkRead(product_id=product_id, dt_project=_project_summary(dt_project))


@router.delete("/products/{product_id}/dt-project", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_product_dt_project(
    db: DBSession,
    current_user: CurrentUser,
    product_id: int,
) -> None:
    """제품 DT Project 연결 해제. DTP NC 파일을 쓰는 라우팅이 있으면 막는다."""
    result = await db.execute(select(Product.id).where(Product.id == product_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    in_use = await db.execute(
        select(ProcessRoutingFile.id)
        .join(ProcessRouting, ProcessRoutingFile.process_routing_id == ProcessRouting.id)
        .where(
            ProcessRouting.product_id == product_id,
            ProcessRoutingFile.source_type == "DTP",
        )
        .limit(1)
    )
    if in_use.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot unlink DT Project while DTP routing files are in use",
        )

    result = await db.execute(
        select(ProductDtProjectLink).where(
            ProductDtProjectLink.product_id == product_id,
            ProductDtProjectLink.relation_type == "PRIMARY",
            ProductDtProjectLink.is_current.is_(True),
        )
    )
    for link in result.scalars().all():
        link.is_current = False
        link.unlinked_at = datetime.now(timezone.utc)
    await db.commit()


@router.get("/products/{product_id}/dt-nc-files", response_model=List[DtFileRefRead])
async def list_product_dt_nc_files(
    db: DBSession,
    current_user: CurrentUser,
    product_id: int,
    workplan_id: str | None = None,
) -> List[DtFileRef]:
    """현재 제품의 DT Project와 선택 workplan에 맞는 NC 파일 목록 조회."""
    dt_project = await _current_dt_project(db, product_id)
    if not dt_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product is not linked to a DT Project",
        )

    client = DtpClient()
    try:
        raw_files = await client.find_nc_files(dt_project.asset_global_id)
    except (DtpConfigurationError, DtpClientError) as exc:
        raise _dtp_http_error(exc) from exc

    matched: list[DtFileRef] = []
    for item in raw_files:
        references = _extract_dtp_file_references(item)
        ref_global_asset = _reference_value(references, "DT_global_asset", "DTGLOBALASSET")
        ref_asset = _reference_value(references, "DT_asset", "DTASSET")
        ref_project = _reference_value(references, "DT_project", "DTPROJECT")
        ref_workplan = _reference_value(
            references,
            "DT_project_workplan",
            "DT_workplan",
            "workplan",
        )

        if ref_global_asset and ref_global_asset != dt_project.asset_global_id:
            continue
        if ref_asset and ref_asset != dt_project.asset_id and _short_ref(ref_asset) != _short_ref(dt_project.asset_id):
            continue
        if ref_project and ref_project != dt_project.element_id and _short_ref(ref_project) != dt_project.element_id:
            continue
        if workplan_id and ref_workplan and ref_workplan != workplan_id and _short_ref(ref_workplan) != workplan_id:
            continue
        if workplan_id and not ref_workplan:
            continue

        external_file_id = str(item.get("id") or item.get("uuid") or item.get("elementId") or "")
        path = item.get("path") or item.get("filePath")
        if not external_file_id or not path:
            continue

        result = await db.execute(
            select(DtFileRef).where(
                DtFileRef.platform == "DTP",
                DtFileRef.external_file_id == external_file_id,
            )
        )
        row = result.scalar_one_or_none()
        data = {
            "platform": "DTP",
            "external_file_id": external_file_id,
            "asset_global_id": item.get("assetGlobalId") or dt_project.asset_global_id,
            "asset_id": item.get("assetId") or ref_asset,
            "element_id": item.get("elementId"),
            "element_full_id": item.get("elementFullId") or item.get("fullId"),
            "element_category": item.get("elementCategory") or item.get("category") or "NC",
            "display_name": item.get("name") or item.get("displayName") or Path(path).name,
            "path": path,
            "references": references,
            "workplan_id": _short_ref(ref_workplan) if ref_workplan else None,
            "raw_metadata": item,
            "synced_at": datetime.now(timezone.utc),
        }
        if row:
            for field, value in data.items():
                setattr(row, field, value)
        else:
            row = DtFileRef(**data)
            db.add(row)
        matched.append(row)

    await db.commit()
    for row in matched:
        await db.refresh(row)
    return matched
