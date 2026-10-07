"""Downtime schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# Downtime Reason
class DowntimeReasonBase(BaseModel):
    """Base downtime reason schema."""

    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(default="UNPLANNED", pattern="^(PLANNED|UNPLANNED|SETUP)$")
    description: Optional[str] = None


class DowntimeReasonCreate(DowntimeReasonBase):
    """Schema for creating a downtime reason."""

    pass


class DowntimeReasonRead(DowntimeReasonBase):
    """Schema for reading a downtime reason."""

    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Downtime
class DowntimeBase(BaseModel):
    """Base downtime schema."""

    equipment_id: int
    reason_id: Optional[int] = None
    work_order_id: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    remarks: Optional[str] = None
    reported_by: Optional[str] = Field(None, max_length=50)


class DowntimeCreate(DowntimeBase):
    """Schema for creating a downtime record."""

    pass


class DowntimeUpdate(BaseModel):
    """Schema for updating a downtime record."""

    reason_id: Optional[int] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    remarks: Optional[str] = None


class DowntimeEnd(BaseModel):
    """Schema for ending a downtime record."""

    end_time: Optional[datetime] = None  # If not provided, uses current time
    resolution_notes: Optional[str] = Field(None, max_length=500)


class DowntimeRead(DowntimeBase):
    """Schema for reading a downtime record."""

    id: int
    created_at: datetime
    reason: Optional[DowntimeReasonRead] = None
    # Computed fields
    calculated_duration_minutes: Optional[int] = None
    is_ongoing: bool = False
    status: str = "COMPLETED"  # ACTIVE or COMPLETED (computed from end_time)

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def compute_status(self) -> "DowntimeRead":
        """Compute status from end_time."""
        if self.end_time is None:
            self.status = "ACTIVE"
        else:
            self.status = "COMPLETED"
        return self
