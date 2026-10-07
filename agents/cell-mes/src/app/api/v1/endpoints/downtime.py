"""Downtime endpoints."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ....models.downtime import DowntimeReason, Downtime
from ....schemas.downtime import (
    DowntimeReasonCreate,
    DowntimeReasonRead,
    DowntimeCreate,
    DowntimeUpdate,
    DowntimeRead,
    DowntimeEnd,
)
from ...deps import DBSession, CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Downtime Reasons
# ============================================================================


@router.get("/reasons", response_model=List[DowntimeReasonRead])
async def list_downtime_reasons(
    db: DBSession,
    current_user: CurrentUser,
    category: Optional[str] = Query(None, description="카테고리 필터 (PLANNED, UNPLANNED, SETUP)"),
    active_only: bool = Query(True, description="활성 항목만"),
) -> List[DowntimeReason]:
    """정지 사유 코드 목록 조회."""
    query = select(DowntimeReason)

    if category:
        query = query.where(DowntimeReason.category == category)
    if active_only:
        query = query.where(DowntimeReason.is_active == True)

    query = query.order_by(DowntimeReason.category, DowntimeReason.code)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/reasons", response_model=DowntimeReasonRead, status_code=status.HTTP_201_CREATED)
async def create_downtime_reason(
    db: DBSession,
    current_user: CurrentUser,
    reason_in: DowntimeReasonCreate,
) -> DowntimeReason:
    """정지 사유 코드 생성."""
    # Check duplicate
    result = await db.execute(select(DowntimeReason).where(DowntimeReason.code == reason_in.code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Downtime reason code '{reason_in.code}' already exists",
        )

    reason = DowntimeReason(**reason_in.model_dump())
    db.add(reason)
    await db.commit()
    await db.refresh(reason)
    return reason


# ============================================================================
# Downtimes
# ============================================================================


@router.get("", response_model=List[DowntimeRead])
async def list_downtimes(
    db: DBSession,
    current_user: CurrentUser,
    equipment_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None, description="정지 사유 카테고리"),
    status_filter: Optional[str] = Query(None, alias="status", description="ACTIVE or COMPLETED"),
    ongoing_only: bool = Query(
        False, description="진행중인 다운타임만 (deprecated, use status=ACTIVE)"
    ),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> List[Downtime]:
    """다운타임 목록 조회."""
    query = select(Downtime).options(selectinload(Downtime.reason))

    if equipment_id:
        query = query.where(Downtime.equipment_id == equipment_id)
    # status filter: ACTIVE means ongoing (end_time is null)
    if status_filter == "ACTIVE":
        query = query.where(Downtime.end_time.is_(None))
    elif status_filter == "COMPLETED":
        query = query.where(Downtime.end_time.is_not(None))
    elif ongoing_only:
        query = query.where(Downtime.end_time.is_(None))
    if date_from:
        query = query.where(Downtime.start_time >= date_from)
    if date_to:
        query = query.where(Downtime.start_time <= date_to)
    if category:
        query = query.join(DowntimeReason).where(DowntimeReason.category == category)

    query = query.order_by(Downtime.start_time.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=DowntimeRead, status_code=status.HTTP_201_CREATED)
async def create_downtime(
    db: DBSession,
    current_user: CurrentUser,
    downtime_in: DowntimeCreate,
) -> Downtime:
    """다운타임 기록 생성."""
    downtime = Downtime(**downtime_in.model_dump())
    db.add(downtime)
    await db.commit()
    await db.refresh(downtime)

    # Load reason relationship
    result = await db.execute(
        select(Downtime).where(Downtime.id == downtime.id).options(selectinload(Downtime.reason))
    )
    return result.scalar_one()


@router.patch("/{downtime_id}", response_model=DowntimeRead)
async def update_downtime(
    db: DBSession,
    current_user: CurrentUser,
    downtime_id: int,
    downtime_update: DowntimeUpdate,
) -> Downtime:
    """다운타임 업데이트 (종료 처리 등)."""
    result = await db.execute(
        select(Downtime).where(Downtime.id == downtime_id).options(selectinload(Downtime.reason))
    )
    downtime = result.scalar_one_or_none()
    if not downtime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Downtime not found",
        )

    update_data = downtime_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(downtime, field, value)

    await db.commit()
    await db.refresh(downtime)
    return downtime


@router.post("/{downtime_id}/end", response_model=DowntimeRead)
async def end_downtime(
    db: DBSession,
    current_user: CurrentUser,
    downtime_id: int,
    end_data: Optional[DowntimeEnd] = None,
) -> Downtime:
    """다운타임 종료 처리."""
    result = await db.execute(
        select(Downtime).where(Downtime.id == downtime_id).options(selectinload(Downtime.reason))
    )
    downtime = result.scalar_one_or_none()
    if not downtime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Downtime not found",
        )

    if downtime.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Downtime already ended",
        )

    # Use provided end_time or current time
    if end_data and end_data.end_time:
        if end_data.end_time < downtime.start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time cannot be before start time",
            )
        downtime.end_time = end_data.end_time
    else:
        downtime.end_time = datetime.now(timezone.utc)

    # Add resolution notes to remarks if provided
    if end_data and end_data.resolution_notes:
        if downtime.remarks:
            downtime.remarks += f"\n[해제] {end_data.resolution_notes}"
        else:
            downtime.remarks = f"[해제] {end_data.resolution_notes}"

    await db.commit()
    await db.refresh(downtime)
    return downtime


@router.get("/summary")
async def get_downtime_summary(
    db: DBSession,
    current_user: CurrentUser,
    equipment_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    """다운타임 요약 통계."""
    query = (
        select(
            DowntimeReason.category,
            func.count(Downtime.id).label("count"),
            func.sum(Downtime.duration_minutes).label("total_minutes"),
        )
        .join(DowntimeReason, isouter=True)
        .group_by(DowntimeReason.category)
    )

    if equipment_id:
        query = query.where(Downtime.equipment_id == equipment_id)
    if date_from:
        query = query.where(Downtime.start_time >= date_from)
    if date_to:
        query = query.where(Downtime.start_time <= date_to)

    result = await db.execute(query)
    rows = result.all()

    return {
        "by_category": {
            row.category or "UNKNOWN": {
                "count": row.count,
                "total_minutes": row.total_minutes or 0,
            }
            for row in rows
        },
        "total_count": sum(row.count for row in rows),
        "total_minutes": sum(row.total_minutes or 0 for row in rows),
    }
