"""Equipment management endpoints with AAS synchronization."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status, Query

from datetime import datetime
from typing import Optional
from fastapi import Query

from ....models.equipment import Equipment, EquipmentStatusHistory
from ....schemas.equipment import (
    EquipmentCreate,
    EquipmentCellUpdate,
    EquipmentRead,
    EquipmentStatus,
    EquipmentSync,
    EquipmentVirtualCopyCreate,
    EquipmentVirtualCopyResult,
    EquipmentStatusHistoryCreate,
    EquipmentStatusHistoryRead,
)
from ....services.equipment_virtual_service import (
    VirtualEquipmentError,
    create_virtual_copies,
)
from ....services.sync_service import sync_equipments_from_middleware
from ....services.cell_service import CellError, assign_equipment_cell
from ....services.polling_service import poll_equipment_status
from ...deps import DBSession, CurrentUser, AdminUser
from sqlalchemy import select
from .....clients.middleware_client import middleware_client

router = APIRouter()


@router.patch("/{equipment_id}/cell", response_model=EquipmentRead)
async def set_equipment_cell(
    equipment_id: int,
    payload: EquipmentCellUpdate,
    db: DBSession,
    current_user: AdminUser,
) -> Equipment:
    try:
        return await assign_equipment_cell(
            db, equipment_id, payload.cell_id, payload.expected_cell_id
        )
    except CellError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("", response_model=List[EquipmentRead])
async def list_equipments(
    db: DBSession,
    current_user: CurrentUser,
    include_deleted: bool = False,
) -> List[Equipment]:
    """설비 목록 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        include_deleted: 삭제된 설비 포함 여부

    Returns:
        설비 목록 (이름순 정렬)

    """
    query = select(Equipment).order_by(Equipment.eq_name)
    if not include_deleted:
        query = query.where(Equipment.is_deleted.is_(False))
    result = await db.execute(query)
    return list(result.scalars().all())


# NOTE: Static paths MUST come before dynamic paths like /{equipment_id}
@router.post("/sync", response_model=EquipmentSync)
async def sync_equipments(
    db: DBSession,
    current_user: AdminUser,
    delete_orphans: bool = Query(
        False,
        description="True이면 미들웨어에 없는 기존 설비를 소프트 삭제"
    ),
) -> EquipmentSync:
    """미들웨어에서 설비 동기화 (AAS Asset Discovery).

    미들웨어 서버에서 등록된 설비 정보를 조회하여
    MES 데이터베이스와 동기화합니다.

    Args:
        db: 데이터베이스 세션
        current_user: 관리자 권한 사용자
        delete_orphans: True면 미들웨어에 없는 기존 설비 소프트 삭제

    Returns:
        동기화 결과 (created, updated, deleted, errors 수)

    """
    result = await sync_equipments_from_middleware(db, delete_orphans=delete_orphans)
    return result


@router.get("/middleware-health")
async def check_middleware_health(
    current_user: CurrentUser,
) -> Dict[str, Any]:
    """미들웨어 연결 상태 확인.

    Args:
        current_user: 현재 인증된 사용자

    Returns:
        연결 상태 (status, url, message)

    """
    try:
        healthy = await middleware_client.health_check()
        return {
            "status": "connected" if healthy else "disconnected",
            "url": middleware_client.base_url,
            "message": "미들웨어 서버에 연결되었습니다."
            if healthy
            else "미들웨어 서버에 연결할 수 없습니다.",
        }
    except ConnectionError:
        return {
            "status": "error",
            "url": middleware_client.base_url,
            "message": "미들웨어 서버에 연결할 수 없습니다.",
        }
    except TimeoutError:
        return {
            "status": "error",
            "url": middleware_client.base_url,
            "message": "미들웨어 서버 연결 시간 초과",
        }
    except Exception:
        return {
            "status": "error",
            "url": middleware_client.base_url,
            "message": "미들웨어 연결 중 오류가 발생했습니다.",
        }


@router.post("", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    db: DBSession,
    current_user: AdminUser,
    equipment_in: EquipmentCreate,
) -> Equipment:
    """설비 수동 등록.

    Args:
        db: 데이터베이스 세션
        current_user: 관리자 권한 사용자
        equipment_in: 설비 생성 데이터 (eq_name, equipment_type, aas_id 등)

    Returns:
        생성된 설비 정보

    Raises:
        HTTPException: AAS ID 중복 시 400 에러

    """
    # Check for duplicate aas_id if provided
    if equipment_in.aas_id:
        result = await db.execute(select(Equipment).where(Equipment.aas_id == equipment_in.aas_id))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Equipment with AAS ID '{equipment_in.aas_id}' already exists",
            )

    equipment = Equipment(**equipment_in.model_dump())
    db.add(equipment)
    await db.commit()
    await db.refresh(equipment)
    return equipment


@router.post(
    "/{equipment_id}/virtual-copies",
    response_model=EquipmentVirtualCopyResult,
    status_code=status.HTTP_201_CREATED,
)
async def create_equipment_virtual_copies(
    db: DBSession,
    current_user: AdminUser,
    equipment_id: int,
    payload: EquipmentVirtualCopyCreate,
) -> EquipmentVirtualCopyResult:
    """Create MES-managed virtual equipment copies from a physical source equipment."""
    try:
        created = await create_virtual_copies(db, equipment_id, payload)
    except VirtualEquipmentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return EquipmentVirtualCopyResult(created_count=len(created), created=created)


@router.get("/{equipment_id}", response_model=EquipmentRead)
async def get_equipment(
    db: DBSession,
    current_user: CurrentUser,
    equipment_id: int,
) -> Equipment:
    """설비 단건 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        equipment_id: 설비 ID

    Returns:
        설비 정보

    Raises:
        HTTPException: 설비 미존재 시 404 에러

    """
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )
    return equipment


@router.get("/{equipment_id}/status", response_model=EquipmentStatus)
async def get_equipment_status(
    db: DBSession,
    current_user: CurrentUser,
    equipment_id: int,
    refresh: bool = False,
) -> EquipmentStatus:
    """설비 상태 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        equipment_id: 설비 ID
        refresh: True면 미들웨어에서 최신 상태 갱신

    Returns:
        설비 상태 정보 (current_status, last_data, last_connected_at 등)

    Raises:
        HTTPException: 설비 미존재 시 404 에러

    """
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Optionally poll for fresh data
    if refresh:
        equipment = await poll_equipment_status(db, equipment)

    return EquipmentStatus(
        id=equipment.id,
        eq_code=equipment.eq_code,
        aas_id=equipment.aas_id,
        eq_name=equipment.eq_name,
        equipment_type=equipment.equipment_type,
        location=equipment.location,
        cell_id=equipment.cell_id,
        current_status=equipment.current_status,
        last_data=equipment.last_data,
        last_connected_at=equipment.last_connected_at,
    )


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(
    db: DBSession,
    current_user: AdminUser,
    equipment_id: int,
) -> None:
    """설비 삭제 (소프트 삭제).

    실제 삭제가 아닌 is_deleted 플래그 설정.

    Args:
        db: 데이터베이스 세션
        current_user: 관리자 권한 사용자
        equipment_id: 설비 ID

    Raises:
        HTTPException: 설비 미존재 시 404 에러

    """
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    equipment.is_deleted = True
    await db.commit()


# ============================================================================
# Equipment Status History
# ============================================================================


@router.get("/{equipment_id}/status-history", response_model=List[EquipmentStatusHistoryRead])
async def get_equipment_status_history(
    db: DBSession,
    current_user: CurrentUser,
    equipment_id: int,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> List[EquipmentStatusHistory]:
    """설비 상태 변경 이력 조회."""
    query = select(EquipmentStatusHistory).where(
        EquipmentStatusHistory.equipment_id == equipment_id
    )

    if date_from:
        query = query.where(EquipmentStatusHistory.changed_at >= date_from)
    if date_to:
        query = query.where(EquipmentStatusHistory.changed_at <= date_to)

    query = query.order_by(EquipmentStatusHistory.changed_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post(
    "/{equipment_id}/status-history",
    response_model=EquipmentStatusHistoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def record_status_change(
    db: DBSession,
    current_user: CurrentUser,
    equipment_id: int,
    status_in: EquipmentStatusHistoryCreate,
) -> EquipmentStatusHistory:
    """설비 상태 변경 기록 (수동 또는 시스템)."""
    # Verify equipment exists
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Calculate previous duration if we have previous record
    prev_query = (
        select(EquipmentStatusHistory)
        .where(EquipmentStatusHistory.equipment_id == equipment_id)
        .order_by(EquipmentStatusHistory.changed_at.desc())
        .limit(1)
    )
    prev_result = await db.execute(prev_query)
    prev_record = prev_result.scalar_one_or_none()

    previous_duration = None
    if prev_record:
        # Handle timezone-naive vs timezone-aware comparison
        prev_changed_at = prev_record.changed_at
        new_changed_at = status_in.changed_at
        if prev_changed_at.tzinfo is None and new_changed_at.tzinfo is not None:
            from datetime import timezone

            prev_changed_at = prev_changed_at.replace(tzinfo=timezone.utc)
        elif prev_changed_at.tzinfo is not None and new_changed_at.tzinfo is None:
            new_changed_at = new_changed_at.replace(tzinfo=prev_changed_at.tzinfo)
        delta = new_changed_at - prev_changed_at
        if delta.total_seconds() < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="changed_at cannot be before the previous status change time",
            )
        previous_duration = int(delta.total_seconds() / 60)

    # Create history record
    history = EquipmentStatusHistory(
        equipment_id=equipment_id,
        previous_status=equipment.current_status,
        new_status=status_in.new_status,
        changed_at=status_in.changed_at,
        previous_duration_minutes=previous_duration,
        reason=status_in.reason,
        work_order_id=status_in.work_order_id,
        changed_by=status_in.changed_by or "system",
    )
    db.add(history)

    # Update equipment current status
    equipment.current_status = status_in.new_status

    await db.commit()
    await db.refresh(history)
    return history


@router.get("/{equipment_id}/status-summary")
async def get_status_summary(
    db: DBSession,
    current_user: CurrentUser,
    equipment_id: int,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    """설비 상태별 시간 요약 (OEE 가동률 계산용)."""
    from sqlalchemy import func

    query = (
        select(
            EquipmentStatusHistory.new_status,
            func.sum(EquipmentStatusHistory.previous_duration_minutes).label("total_minutes"),
            func.count(EquipmentStatusHistory.id).label("count"),
        )
        .where(EquipmentStatusHistory.equipment_id == equipment_id)
        .group_by(EquipmentStatusHistory.new_status)
    )

    if date_from:
        query = query.where(EquipmentStatusHistory.changed_at >= date_from)
    if date_to:
        query = query.where(EquipmentStatusHistory.changed_at <= date_to)

    result = await db.execute(query)
    rows = result.all()

    summary = {
        row.new_status: {
            "total_minutes": row.total_minutes or 0,
            "count": row.count,
        }
        for row in rows
    }

    # Calculate availability
    total_time = sum(v["total_minutes"] for v in summary.values())
    run_time = summary.get("RUN", {}).get("total_minutes", 0)
    availability = (run_time / total_time * 100) if total_time > 0 else 0

    return {
        "equipment_id": equipment_id,
        "by_status": summary,
        "total_minutes": total_time,
        "run_minutes": run_time,
        "availability_percent": round(availability, 2),
    }
