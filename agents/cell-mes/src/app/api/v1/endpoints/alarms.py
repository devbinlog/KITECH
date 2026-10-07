"""Alarm endpoints."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ....models.alarm import AlarmDefinition, Alarm
from ....schemas.alarm import (
    AlarmDefinitionCreate,
    AlarmDefinitionRead,
    AlarmCreate,
    AlarmAcknowledge,
    AlarmResolve,
    AlarmRead,
    ActiveAlarmsSummary,
)
from ...deps import DBSession, CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Alarm Definitions
# ============================================================================


@router.get("/definitions", response_model=List[AlarmDefinitionRead])
async def list_alarm_definitions(
    db: DBSession,
    current_user: CurrentUser,
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    active_only: bool = Query(True),
) -> List[AlarmDefinition]:
    """알람 정의 목록 조회."""
    query = select(AlarmDefinition)

    if severity:
        query = query.where(AlarmDefinition.severity == severity)
    if category:
        query = query.where(AlarmDefinition.category == category)
    if active_only:
        query = query.where(AlarmDefinition.is_active == True)

    query = query.order_by(AlarmDefinition.severity, AlarmDefinition.code)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post(
    "/definitions", response_model=AlarmDefinitionRead, status_code=status.HTTP_201_CREATED
)
async def create_alarm_definition(
    db: DBSession,
    current_user: CurrentUser,
    definition_in: AlarmDefinitionCreate,
) -> AlarmDefinition:
    """알람 정의 생성."""
    # Check duplicate
    result = await db.execute(
        select(AlarmDefinition).where(AlarmDefinition.code == definition_in.code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Alarm definition code '{definition_in.code}' already exists",
        )

    definition = AlarmDefinition(**definition_in.model_dump())
    db.add(definition)
    await db.commit()
    await db.refresh(definition)
    return definition


# ============================================================================
# Alarms
# ============================================================================


@router.get("", response_model=List[AlarmRead])
async def list_alarms(
    db: DBSession,
    current_user: CurrentUser,
    equipment_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> List[Alarm]:
    """알람 목록 조회."""
    query = select(Alarm).options(selectinload(Alarm.definition))

    if equipment_id:
        query = query.where(Alarm.equipment_id == equipment_id)
    if status_filter:
        query = query.where(Alarm.status == status_filter)
    if severity:
        query = query.join(AlarmDefinition).where(AlarmDefinition.severity == severity)
    if date_from:
        query = query.where(Alarm.occurred_at >= date_from)
    if date_to:
        query = query.where(Alarm.occurred_at <= date_to)

    query = query.order_by(Alarm.occurred_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/active", response_model=List[AlarmRead])
async def list_active_alarms(
    db: DBSession,
    current_user: CurrentUser,
    equipment_id: Optional[int] = Query(None),
) -> List[Alarm]:
    """활성 알람 목록 (ACTIVE, ACKNOWLEDGED)."""
    query = (
        select(Alarm)
        .options(selectinload(Alarm.definition))
        .where(Alarm.status.in_(["ACTIVE", "ACKNOWLEDGED"]))
    )

    if equipment_id:
        query = query.where(Alarm.equipment_id == equipment_id)

    query = query.order_by(Alarm.occurred_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/active/summary", response_model=ActiveAlarmsSummary)
async def get_active_alarms_summary(
    db: DBSession,
    current_user: CurrentUser,
) -> ActiveAlarmsSummary:
    """활성 알람 요약."""
    # Total count
    total_query = select(func.count(Alarm.id)).where(Alarm.status.in_(["ACTIVE", "ACKNOWLEDGED"]))
    total = (await db.execute(total_query)).scalar() or 0

    # By severity
    severity_query = (
        select(AlarmDefinition.severity, func.count(Alarm.id))
        .join(AlarmDefinition)
        .where(Alarm.status.in_(["ACTIVE", "ACKNOWLEDGED"]))
        .group_by(AlarmDefinition.severity)
    )
    severity_result = await db.execute(severity_query)
    by_severity = {row[0]: row[1] for row in severity_result.all()}

    # By equipment
    from ....models.equipment import Equipment

    eq_query = (
        select(Equipment.eq_name, func.count(Alarm.id))
        .join(Equipment, Alarm.equipment_id == Equipment.id)
        .where(Alarm.status.in_(["ACTIVE", "ACKNOWLEDGED"]))
        .group_by(Equipment.eq_name)
    )
    eq_result = await db.execute(eq_query)
    by_equipment = {row[0]: row[1] for row in eq_result.all()}

    return ActiveAlarmsSummary(
        total=total,
        by_severity=by_severity,
        by_equipment=by_equipment,
    )


@router.post("", response_model=AlarmRead, status_code=status.HTTP_201_CREATED)
async def create_alarm(
    db: DBSession,
    current_user: CurrentUser,
    alarm_in: AlarmCreate,
) -> Alarm:
    """알람 발생 기록."""
    alarm = Alarm(**alarm_in.model_dump(), status="ACTIVE")
    db.add(alarm)
    await db.commit()
    await db.refresh(alarm)

    result = await db.execute(
        select(Alarm).where(Alarm.id == alarm.id).options(selectinload(Alarm.definition))
    )
    return result.scalar_one()


@router.post("/{alarm_id}/acknowledge", response_model=AlarmRead)
async def acknowledge_alarm(
    db: DBSession,
    current_user: CurrentUser,
    alarm_id: int,
    ack_data: AlarmAcknowledge,
) -> Alarm:
    """알람 확인 처리."""
    result = await db.execute(
        select(Alarm).where(Alarm.id == alarm_id).options(selectinload(Alarm.definition))
    )
    alarm = result.scalar_one_or_none()
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm not found",
        )

    if alarm.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot acknowledge alarm in status '{alarm.status}'",
        )

    alarm.status = "ACKNOWLEDGED"
    alarm.acknowledged_at = datetime.now(timezone.utc)
    alarm.acknowledged_by = ack_data.acknowledged_by

    await db.commit()
    await db.refresh(alarm)
    return alarm


@router.post("/{alarm_id}/resolve", response_model=AlarmRead)
async def resolve_alarm(
    db: DBSession,
    current_user: CurrentUser,
    alarm_id: int,
    resolve_data: AlarmResolve,
) -> Alarm:
    """알람 해제 처리."""
    result = await db.execute(
        select(Alarm).where(Alarm.id == alarm_id).options(selectinload(Alarm.definition))
    )
    alarm = result.scalar_one_or_none()
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm not found",
        )

    if alarm.status == "RESOLVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alarm already resolved",
        )

    alarm.status = "RESOLVED"
    alarm.resolved_at = datetime.now(timezone.utc)
    alarm.resolved_by = resolve_data.resolved_by
    alarm.resolution_note = resolve_data.resolution_note

    await db.commit()
    await db.refresh(alarm)
    return alarm
