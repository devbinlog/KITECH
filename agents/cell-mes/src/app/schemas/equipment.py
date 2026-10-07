"""Equipment schemas with JSONB support."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EquipmentBase(BaseModel):
    """Base equipment schema."""

    eq_code: str = Field(..., min_length=1, max_length=30, description="설비 코드 (EQ-CNC-001)")
    eq_name: str = Field(..., min_length=1, max_length=100)
    model_name: Optional[str] = Field(None, max_length=100)
    # Allow any equipment type (CNC, ROBOT, AMR, PLC, MILL, TURN, DRILL, GRIND, WASH, INSP, ASSEM, LOAD, UNLOAD, etc.)
    equipment_type: str = Field(default="CNC", max_length=20)
    location: Optional[str] = Field(
        None, max_length=50, description="물리적 위치 (Building A, Line 1)"
    )
    cell_id: Optional[int] = Field(None, description="제조 셀 ID (FK to cells)")


class EquipmentCreate(EquipmentBase):
    """Schema for creating equipment."""

    aas_id: Optional[str] = Field(None, max_length=100)
    connection_config: Dict[str, Any] = Field(default_factory=dict)
    spec_data: Dict[str, Any] = Field(default_factory=dict)


class EquipmentCellUpdate(BaseModel):
    """Both nullable fields are required to detect stale assignments."""

    cell_id: Optional[int] = Field(..., gt=0)
    expected_cell_id: Optional[int] = Field(..., gt=0)


class EquipmentRead(EquipmentBase):
    """Schema for reading equipment."""

    id: int
    eq_code: str
    aas_id: Optional[str]
    location: Optional[str] = None
    cell_id: Optional[int] = None
    connection_config: Dict[str, Any]
    spec_data: Dict[str, Any]
    last_data: Dict[str, Any]
    current_status: str
    updated_at: datetime
    last_connected_at: Optional[datetime]
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class EquipmentStatus(BaseModel):
    """Equipment status response."""

    id: int
    eq_code: str
    aas_id: Optional[str]
    eq_name: str
    equipment_type: str
    location: Optional[str] = None
    cell_id: Optional[int] = None
    current_status: str
    last_data: Dict[str, Any]
    last_connected_at: Optional[datetime]


class EquipmentSync(BaseModel):
    """Equipment sync request/response from middleware."""

    synced_count: int
    created: List[str] = Field(default_factory=list)
    updated: List[str] = Field(default_factory=list)
    deleted: List[str] = Field(default_factory=list)  # 삭제된 고암 설비 목록
    errors: List[str] = Field(default_factory=list)


class EquipmentVirtualCopyCreate(BaseModel):
    """Request schema for creating MES-managed virtual equipment copies."""

    count: int = Field(default=1, ge=1, le=20)
    name_prefix: Optional[str] = Field(default=None, max_length=60)
    machineType: Optional[str] = Field(default=None, max_length=50)
    overrides: Dict[str, Any] = Field(default_factory=dict)


class EquipmentVirtualCopyResult(BaseModel):
    """Response schema for virtual equipment copy creation."""

    created_count: int
    created: List[EquipmentRead]


class AASAsset(BaseModel):
    """AAS Asset data from middleware."""

    id: str  # aas_id
    name: str
    type: str  # CNC, ROBOT, etc.
    connection: Dict[str, Any] = Field(default_factory=dict)
    spec: Dict[str, Any] = Field(default_factory=dict)


# Equipment Status History
class EquipmentStatusHistoryBase(BaseModel):
    """Base equipment status history schema."""

    previous_status: Optional[str] = None
    new_status: str = Field(..., pattern="^(RUN|IDLE|STOP|SETUP|ERROR|MAINTENANCE)$")
    changed_at: datetime
    previous_duration_minutes: Optional[int] = Field(None, ge=0)
    reason: Optional[str] = Field(None, max_length=100)
    work_order_id: Optional[int] = None
    changed_by: Optional[str] = Field(None, max_length=50)


class EquipmentStatusHistoryCreate(EquipmentStatusHistoryBase):
    """Schema for creating status history (equipment_id from URL path)."""

    pass


class EquipmentStatusHistoryRead(EquipmentStatusHistoryBase):
    """Schema for reading status history."""

    id: int
    equipment_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# OEE Summary
class OEESummary(BaseModel):
    """OEE (Overall Equipment Effectiveness) summary."""

    equipment_id: int
    equipment_name: str
    period_start: datetime
    period_end: datetime

    # Time breakdown (minutes)
    planned_time: int
    run_time: int
    idle_time: int
    downtime: int
    setup_time: int

    # OEE components (%)
    availability: float  # (계획시간 - 다운타임) / 계획시간
    performance: float  # 실제 사이클타임 / 표준 사이클타임
    quality: float  # 양품 / 총 생산량
    oee: float  # Availability * Performance * Quality
