"""Alarm schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# Alarm Definition
class AlarmDefinitionBase(BaseModel):
    """Base alarm definition schema."""

    code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=100)
    severity: str = Field(default="WARNING", pattern="^(INFO|WARNING|CRITICAL|EMERGENCY)$")
    category: str = Field(default="EQUIPMENT", pattern="^(EQUIPMENT|PROCESS|QUALITY|SAFETY)$")
    description: Optional[str] = None
    recommended_action: Optional[str] = None
    auto_stop: bool = False


class AlarmDefinitionCreate(AlarmDefinitionBase):
    """Schema for creating an alarm definition."""

    pass


class AlarmDefinitionRead(AlarmDefinitionBase):
    """Schema for reading an alarm definition."""

    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Alarm
class AlarmBase(BaseModel):
    """Base alarm schema."""

    definition_id: int
    equipment_id: Optional[int] = None
    work_order_id: Optional[int] = None
    occurred_at: datetime
    message: Optional[str] = None
    value: Optional[str] = Field(None, max_length=100)


class AlarmCreate(AlarmBase):
    """Schema for creating an alarm."""

    pass


class AlarmAcknowledge(BaseModel):
    """Schema for acknowledging an alarm."""

    acknowledged_by: str = Field(..., max_length=50)


class AlarmResolve(BaseModel):
    """Schema for resolving an alarm."""

    resolved_by: str = Field(..., max_length=50)
    resolution_note: Optional[str] = None


class AlarmRead(AlarmBase):
    """Schema for reading an alarm."""

    id: int
    status: str
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_note: Optional[str] = None
    created_at: datetime
    definition: Optional[AlarmDefinitionRead] = None
    # Computed
    duration_minutes: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Active alarms summary
class ActiveAlarmsSummary(BaseModel):
    """Summary of active alarms."""

    total: int
    by_severity: dict[str, int]  # {"CRITICAL": 2, "WARNING": 5}
    by_equipment: dict[str, int]  # {"CNC-001": 3, "ROBOT-001": 1}
