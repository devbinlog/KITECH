"""Production schemas: WorkOrder, ProdResult, WorkInfo."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    pass


# Embedded Product schema for WorkOrder response
class ProductEmbedded(BaseModel):
    """Embedded product info in work order response."""

    id: int
    code: str
    name: str
    unit: str

    model_config = ConfigDict(from_attributes=True)


# Work Order
class WorkOrderBase(BaseModel):
    """Base work order schema."""

    lot_no: str = Field(..., min_length=1, max_length=50)
    product_id: int
    scenario_id: Optional[int] = None
    target_qty: int = Field(..., gt=0)
    qty: int = Field(default=1, gt=0)
    priority: int = Field(default=5, ge=1, le=10)
    due_date: Optional[datetime] = None
    remarks: Optional[str] = Field(None, max_length=500)


class WorkOrderCreate(WorkOrderBase):
    """Schema for creating a work order."""

    pass


class WorkOrderRead(WorkOrderBase):
    """Schema for reading a work order."""

    id: int
    status: str
    completed_qty: int = 0
    current_process: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime
    product: Optional[ProductEmbedded] = None

    # Scheduled equipment info (from ProdResult.target_equipment_id)
    scheduled_equipment_name: Optional[str] = None

    # Aliases for frontend compatibility (plan_start/plan_end = start_time/end_time)
    plan_start: Optional[datetime] = None
    plan_end: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def copy_times_to_plan(self):
        """Copy start_time/end_time to plan_start/plan_end for frontend compatibility."""
        if self.plan_start is None and self.start_time is not None:
            self.plan_start = self.start_time
        if self.plan_end is None and self.end_time is not None:
            self.plan_end = self.end_time
        return self


class WorkOrderStatusUpdate(BaseModel):
    """Schema for updating work order status."""

    status: str = Field(..., pattern="^(RUNNING|PAUSE|DONE|ERROR|CANCEL)$")


# Unit Models
class UnitBase(BaseModel):
    """Base unit schema."""

    unit_no: int
    scenario_id: Optional[int] = None
    status: str = Field(default="READY")


class UnitCreate(UnitBase):
    """Schema for creating a unit."""

    work_order_id: int


class UnitRead(UnitBase):
    """Schema for reading a unit."""

    id: int
    work_order_id: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scenario_hold_started_at: Optional[datetime] = None
    scenario_hold_by: Optional[str] = None
    scenario: Optional["ScenarioReadMinimal"] = None

    model_config = ConfigDict(from_attributes=True)


class ScenarioReadMinimal(BaseModel):
    """Minimal scenario info embedded in UnitRead for UI display."""

    id: int
    name: str
    file_path: str

    model_config = ConfigDict(from_attributes=True)


# Update forward reference
UnitRead.model_rebuild()


class UnitListResponse(BaseModel):
    """List of units for UI monitoring."""
    
    items: List[UnitRead]
    total: int


class MiddlewareResumeRequest(BaseModel):
    """Request for resuming a middleware unit."""

    mode: Literal["CURRENT_STEP", "SKIP_CURRENT_STEP", "SPECIFIC_STEP"] = "CURRENT_STEP"
    resume_step_id: Optional[str] = None
    clear_retry: bool = True


class MiddlewareUnitState(BaseModel):
    """Merged MES + middleware runtime state for one unit."""

    unit_no: str
    mes_unit_id: Optional[int] = None
    mes_status: Optional[str] = None
    middleware_status: Optional[str] = None
    current_step_id: Optional[str] = None
    alarm_step_id: Optional[str] = None
    alarm_message: Optional[str] = None
    pending_stop: bool = False
    acq_map: Dict[str, Any] = Field(default_factory=dict)
    activity: Optional[Dict[str, Any]] = None
    recipe_name: Optional[str] = None
    recipe_steps: List[Dict[str, Any]] = Field(default_factory=list)
    nc_files: List[Dict[str, Any]] = Field(default_factory=list)
    unit_var: Optional[Any] = None
    unit_res: Optional[Any] = None
    unit_loc: Optional[Any] = None
    unit_pos: Optional[Any] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class OrderMiddlewareState(BaseModel):
    """Read-through middleware state for a work order."""

    status: str = "success"
    order_id: int
    lot_no: str
    mes_status: str
    middleware_lot_status: Optional[str] = None
    sync_status: Literal["SYNCED", "MISMATCHED", "MIDDLEWARE_NOT_FOUND", "ERROR"]
    last_synced_at: datetime
    units: List[MiddlewareUnitState] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class MiddlewareCommandResponse(BaseModel):
    """Normalized response for middleware unit control commands."""

    status: Literal["success"] = "success"
    message: str
    order_id: int
    lot_no: str
    unit_no: str
    middleware_response: Dict[str, Any] = Field(default_factory=dict)

# Production Result
class ProdResultBase(BaseModel):
    """Base production result schema."""

    unit_id: Optional[int] = None
    process_routing_id: Optional[int] = None
    target_equipment_id: Optional[int] = None  # Scheduler-assigned equipment
    equipment_id: Optional[int] = None  # Actual execution equipment
    ok_qty: int = Field(default=0, ge=0)
    ng_qty: int = Field(default=0, ge=0)


class ProdResultCreate(ProdResultBase):
    """Schema for creating a production result."""

    work_order_id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ProdResultRead(ProdResultBase):
    """Schema for reading a production result."""

    id: int
    work_order_id: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    total_qty: int = 0
    yield_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# Work Info Payload (for middleware)
class ProcessingStep(BaseModel):
    """Processing step in work info payload."""

    sequence: int
    process_code: str
    process_name: str
    files: List[Dict[str, Any]] = Field(default_factory=list)


class LogisticsInfo(BaseModel):
    """Logistics/scenario info in work info payload."""

    scenario_name: str
    control_file: str


class WorkInfoPayload(BaseModel):
    """Unified work info payload for middleware."""

    job_id: str  # lot_no
    product_code: str
    product_name: str
    target_qty: int
    logistics: Optional[LogisticsInfo] = None
    processing_steps: List[ProcessingStep] = Field(default_factory=list)


# Unit Queue Responses
class UnitQueueResponse(BaseModel):
    """Response schema for getting a ready unit (Global Queue)."""

    unit_id: int
    unit_no: str
    scenario_id: Optional[int] = None
    scenario_filename: str
    recipe: Optional[Dict[str, Any]] = None
    required_resources: Dict[str, List[str]] = Field(default_factory=dict)
    nc_files: List[Dict[str, Any]] = Field(default_factory=list)

    # Context injected for middleware execution
    work_order_id: int
    lot_no: str
    product_id: int
    priority: int
    target_qty: int


class ScenarioUpdateRequest(BaseModel):
    """Request schema for updating a work order's scenario."""
    
    scenario_id: int
