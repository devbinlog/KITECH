"""Process routing endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from ....models.master import (
    DtFileRef,
    DtProjectRef,
    DtProjectWorkplan,
    ProcessCategory,
    ProcessRouting,
    ProcessRoutingFile,
    Product,
    ProductDtProjectLink,
    StdProcess,
)
from ....schemas.master import ProcessRoutingCreate, ProcessRoutingRead
from ....schemas.product_cell import ProductCellsRead, ProductCellsUpdate
from ....services import product_cell_service
from ....services.cell_service import CellError
from ...deps import DBSession, CurrentUser

router = APIRouter()


@router.get("/{product_id}/cells", response_model=ProductCellsRead)
async def get_product_cells(db: DBSession, current_user: CurrentUser, product_id: int):
    try:
        cell_ids = await product_cell_service.get_product_cells(db, product_id)
    except CellError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    return ProductCellsRead(product_id=product_id, cell_ids=cell_ids)


@router.put("/{product_id}/cells", response_model=ProductCellsRead)
async def save_product_cells(
    db: DBSession, current_user: CurrentUser, product_id: int, cells_in: ProductCellsUpdate
):
    try:
        cell_ids = await product_cell_service.save_product_cells(db, product_id, cells_in.cell_ids)
    except CellError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    return ProductCellsRead(product_id=product_id, cell_ids=cell_ids)

@router.get("/{product_id}/routings", response_model=List[ProcessRoutingRead])
async def get_product_routings(
    db: DBSession,
    current_user: CurrentUser,
    product_id: int,
) -> List[ProcessRouting]:
    """제품별 공정 라우팅 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        product_id: 제품 ID

    Returns:
        공정 라우팅 목록 (순서대로, 파일 및 표준공정 포함)

    Raises:
        HTTPException: 제품 미존재 시 404 에러

    """
    # Check product exists
    result = await db.execute(select(Product).where(Product.id == product_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Get routings with files and std_process
    result = await db.execute(
        select(ProcessRouting)
        .where(ProcessRouting.product_id == product_id)
        .options(
            selectinload(ProcessRouting.files).selectinload(ProcessRoutingFile.dt_file),
            selectinload(ProcessRouting.std_process).selectinload(StdProcess.category),
            selectinload(ProcessRouting.dt_workplan),
        )
        .order_by(ProcessRouting.sequence)
    )
    return list(result.scalars().all())


@router.put("/{product_id}/routings", response_model=List[ProcessRoutingRead])
async def save_product_routings(
    db: DBSession,
    current_user: CurrentUser,
    product_id: int,
    routings_in: List[ProcessRoutingCreate],
) -> List[ProcessRouting]:
    """제품별 공정 라우팅 저장 (전체 교체).

    기존 라우팅을 모두 삭제하고 새 라우팅으로 교체합니다.
    단일 트랜잭션으로 수행됩니다.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        product_id: 제품 ID
        routings_in: 새 라우팅 목록

    Returns:
        저장된 공정 라우팅 목록

    Raises:
        HTTPException: 제품 미존재 시 404, 표준공정 미존재/순서 중복 시 400 에러

    """
    # Check product exists
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Validate all std_process_ids exist and keep defaults available for routing timing.
    std_process_ids = {r.std_process_id for r in routings_in}
    std_process_by_id: dict[int, StdProcess] = {}
    if std_process_ids:
        result = await db.execute(select(StdProcess).where(StdProcess.id.in_(std_process_ids)))
        std_process_by_id = {process.id: process for process in result.scalars().all()}
    existing_ids = set(std_process_by_id)
    missing_ids = std_process_ids - existing_ids
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Standard processes not found: {missing_ids}",
        )

    dt_workplan_ids = {r.dt_workplan_id for r in routings_in if r.dt_workplan_id}
    dt_file_ref_ids = {
        file.dt_file_ref_id
        for routing in routings_in
        for file in routing.files
        if file.dt_file_ref_id
    }
    current_dt_project_id: int | None = None
    if dt_workplan_ids or dt_file_ref_ids:
        link_result = await db.execute(
            select(ProductDtProjectLink)
            .where(
                ProductDtProjectLink.product_id == product_id,
                ProductDtProjectLink.relation_type == "PRIMARY",
                ProductDtProjectLink.is_current.is_(True),
            )
            .options(selectinload(ProductDtProjectLink.dt_project))
        )
        link = link_result.scalar_one_or_none()
        if not link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="DT Project is required for DTP routing references",
            )
        current_dt_project_id = link.dt_project_ref_id

    if dt_workplan_ids:
        result = await db.execute(
            select(DtProjectWorkplan.id).where(
                DtProjectWorkplan.id.in_(dt_workplan_ids),
                DtProjectWorkplan.dt_project_ref_id == current_dt_project_id,
            )
        )
        existing_dt_workplans = set(result.scalars().all())
        missing_dt_workplans = dt_workplan_ids - existing_dt_workplans
        if missing_dt_workplans:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"DT workplans not found for product: {missing_dt_workplans}",
            )

    if dt_file_ref_ids:
        result = await db.execute(select(DtFileRef.id).where(DtFileRef.id.in_(dt_file_ref_ids)))
        existing_dt_files = set(result.scalars().all())
        missing_dt_files = dt_file_ref_ids - existing_dt_files
        if missing_dt_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"DTP files not found: {missing_dt_files}",
            )

    for routing_in in routings_in:
        for file_in in routing_in.files:
            if file_in.source_type == "DTP" and not file_in.dt_file_ref_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="dt_file_ref_id is required for DTP routing files",
                )
            if file_in.source_type == "LOCAL_UPLOAD" and file_in.dt_file_ref_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="LOCAL_UPLOAD files cannot reference dt_file_ref_id",
                )

    # Validate unique sequences
    sequences = [r.sequence for r in routings_in]
    if len(sequences) != len(set(sequences)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate sequences in routing",
        )

    # Delete existing routing files explicitly before replacing routings.
    # SQLAlchemy bulk deletes do not trigger ORM delete-orphan cascades, and
    # SQLite may not enforce FK cascades unless PRAGMA foreign_keys is enabled.
    existing_routings_result = await db.execute(
        select(ProcessRouting).where(ProcessRouting.product_id == product_id)
    )
    existing_routings = list(existing_routings_result.scalars().all())
    existing_timing_by_key = {
        (routing.sequence, routing.revision, routing.std_process_id): (
            routing.cycle_time_sec,
            routing.cycle_time_breakdown,
        )
        for routing in existing_routings
    }
    routing_ids = [routing.id for routing in existing_routings]
    if routing_ids:
        await db.execute(
            delete(ProcessRoutingFile).where(
                ProcessRoutingFile.process_routing_id.in_(routing_ids)
            )
        )
    await db.execute(delete(ProcessRouting).where(ProcessRouting.product_id == product_id))

    # Create new routings with files
    created_routings = []
    for routing_in in routings_in:
        timing_key = (routing_in.sequence, routing_in.revision, routing_in.std_process_id)
        previous_cycle_time, previous_breakdown = existing_timing_by_key.get(
            timing_key, (None, None)
        )
        cycle_time_sec = (
            routing_in.cycle_time_sec
            if "cycle_time_sec" in routing_in.model_fields_set
            else previous_cycle_time
        )
        cycle_time_breakdown = (
            routing_in.cycle_time_breakdown
            if "cycle_time_breakdown" in routing_in.model_fields_set
            else previous_breakdown
        )
        # Explicit null restores live standard timing; manual edits invalidate old provenance.
        if cycle_time_sec is None or (
            cycle_time_sec != previous_cycle_time
            and "cycle_time_breakdown" not in routing_in.model_fields_set
        ):
            cycle_time_breakdown = None
        routing = ProcessRouting(
            product_id=product_id,
            std_process_id=routing_in.std_process_id,
            sequence=routing_in.sequence,
            revision=routing_in.revision,
            setup_id=routing_in.setup_id,
            dt_workplan_id=routing_in.dt_workplan_id,
            required_machines=routing_in.required_machines,
            cycle_time_sec=cycle_time_sec,
            cycle_time_breakdown=cycle_time_breakdown,
            remarks=routing_in.remarks,
        )
        db.add(routing)
        await db.flush()  # Get routing.id

        # Add files
        for file_in in routing_in.files:
            file = ProcessRoutingFile(
                process_routing_id=routing.id,
                file_type=file_in.file_type,
                file_path=file_in.file_path,
                original_filename=file_in.original_filename,
                source_type=file_in.source_type,
                dt_file_ref_id=file_in.dt_file_ref_id,
                compatible_machines=file_in.compatible_machines,
                sort_order=file_in.sort_order,
            )
            db.add(file)

        created_routings.append(routing)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(ProcessRouting)
        .where(ProcessRouting.product_id == product_id)
        .options(
            selectinload(ProcessRouting.files).selectinload(ProcessRoutingFile.dt_file),
            selectinload(ProcessRouting.std_process).selectinload(StdProcess.category),
            selectinload(ProcessRouting.dt_workplan),
        )
        .order_by(ProcessRouting.sequence)
    )
    return list(result.scalars().all())
