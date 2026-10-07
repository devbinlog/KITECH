"""Quality schemas for API serialization."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, ConfigDict, model_validator

from ..models.quality import InspectionType, SPCControlType, NCRStatus


# Lightweight embedded schemas for relationship serialization
class _ProductEmbedded(BaseModel):
    """Minimal product info for nested relationships."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str


class _WorkOrderEmbedded(BaseModel):
    """Minimal work order info for inspection result context."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    lot_no: Optional[str] = None
    status: Optional[str] = None
    product: Optional[_ProductEmbedded] = None


class _InspectionPlanEmbedded(BaseModel):
    """Minimal inspection plan info for inspection result context."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    characteristic: str
    nominal: Optional[float] = None
    usl: Optional[float] = None
    lsl: Optional[float] = None
    unit: str = "mm"
    inspection_type: Optional[str] = None
    product: Optional[_ProductEmbedded] = None


# InspectionPlan schemas (based on DIGITAL_THREAD_SPC_QMS.md)
class InspectionPlanBase(BaseModel):
    """Base inspection plan schema with Digital Thread integration."""

    product_id: int
    operation_id: Optional[int] = None

    # Digital Thread 연계 (PMI Integration)
    pmi_source: Optional[str] = Field(None, max_length=255, description="STEP file path")
    feature_id: Optional[str] = Field(None, max_length=100, description="PMI Feature ID")

    # Inspection details (following design spec naming)
    characteristic: str = Field(
        ..., min_length=1, max_length=100, description="외경, 깊이, 위치도 등"
    )
    nominal: Optional[float] = Field(None, description="기준값")
    usl: Optional[float] = Field(None, description="Upper Spec Limit")
    lsl: Optional[float] = Field(None, description="Lower Spec Limit")
    unit: str = Field(default="mm", max_length=20)

    # 검사 방법 (from design spec)
    inspection_type: InspectionType = InspectionType.IN_PROCESS
    sampling_plan: str = Field(default="PERIODIC", description="FIRST_ARTICLE, PERIODIC, 100%")
    frequency: Optional[int] = Field(None, ge=1, description="n개당 1회")

    # SPC settings
    enable_spc: bool = True
    spc_control_type: SPCControlType = SPCControlType.X_BAR_R
    is_active: bool = True


class InspectionPlanCreate(InspectionPlanBase):
    """Create inspection plan schema."""

    pass


class InspectionPlanUpdate(BaseModel):
    """Update inspection plan schema."""

    operation_id: Optional[int] = None
    characteristic: Optional[str] = Field(None, min_length=1, max_length=100)
    lsl: Optional[float] = Field(None, description="Lower Spec Limit")
    usl: Optional[float] = Field(None, description="Upper Spec Limit")
    nominal: Optional[float] = Field(None, description="Target value")
    unit: Optional[str] = Field(None, max_length=20)
    inspection_type: Optional[InspectionType] = None
    sampling_plan: Optional[str] = Field(None, max_length=50)
    frequency: Optional[int] = Field(None, ge=1)
    enable_spc: Optional[bool] = None
    spc_control_type: Optional[SPCControlType] = None
    is_active: Optional[bool] = None


class InspectionPlanResponse(InspectionPlanBase):
    """Inspection plan response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class InspectionPlanWithResults(InspectionPlanResponse):
    """Inspection plan with related results."""

    inspection_results: List["InspectionResultResponse"] = []
    spc_charts: List["SPCChartResponse"] = []


# InspectionResult schemas (based on DIGITAL_THREAD_SPC_QMS.md)
class InspectionResultBase(BaseModel):
    """Base inspection result schema with Digital Thread integration."""

    inspection_plan_id: int
    work_order_id: int
    equipment_id: Optional[int] = None

    # Digital Thread 연계 (Full Traceability)
    lot_no: Optional[str] = Field(None, max_length=50)
    serial_no: Optional[str] = Field(None, max_length=50, description="개별 추적")
    nc_program_id: Optional[str] = Field(None, max_length=50)

    # 측정 소스 (from design spec)
    source: str = Field(default="MANUAL", description="OMM, EQUATOR, CMM, MANUAL")
    device_id: Optional[int] = Field(None, description="측정 장비 ID")

    # Measurement data
    measured_value: float
    deviation: Optional[float] = Field(None, description="기준값 대비 편차")

    # Metadata (JSON pattern)
    measurement_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="inspector, method, conditions 등"
    )


class InspectionResultCreate(InspectionResultBase):
    """Create inspection result schema."""

    pass


class InspectionResultUpdate(BaseModel):
    """Update inspection result schema."""

    measured_value: Optional[float] = None
    serial_number: Optional[str] = Field(None, max_length=50)
    lot_number: Optional[str] = Field(None, max_length=50)
    inspector_name: Optional[str] = Field(None, max_length=50)
    measurement_method: Optional[str] = Field(None, max_length=100)
    environmental_conditions: Optional[Dict[str, Any]] = None


class InspectionResultResponse(InspectionResultBase):
    """Inspection result response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_conforming: bool
    deviation: Optional[float] = None
    measured_at: datetime
    created_at: datetime

    # Computed fields for frontend compatibility
    judgment: Optional[str] = None
    inspector: Optional[str] = None
    inspection_date: Optional[str] = None

    # Eager-loaded relationships
    inspection_plan: Optional[_InspectionPlanEmbedded] = None
    work_order: Optional[_WorkOrderEmbedded] = None

    @model_validator(mode="after")
    def compute_frontend_fields(self) -> "InspectionResultResponse":
        """Derive judgment/inspector/inspection_date from model fields."""
        if self.judgment is None:
            self.judgment = "OK" if self.is_conforming else "NG"
        if self.inspector is None and self.measurement_metadata:
            self.inspector = self.measurement_metadata.get("inspector", "")
        if self.inspection_date is None and self.measured_at:
            self.inspection_date = self.measured_at.isoformat() if isinstance(self.measured_at, datetime) else str(self.measured_at)
        return self


# SPCChart schemas
class SPCChartBase(BaseModel):
    """Base SPC chart schema."""

    inspection_plan_id: int
    center_line: float
    upper_control_limit: float
    lower_control_limit: float
    upper_warning_limit: Optional[float] = None
    lower_warning_limit: Optional[float] = None
    range_center_line: Optional[float] = None
    range_upper_control_limit: Optional[float] = None
    range_lower_control_limit: Optional[float] = None
    chart_type: SPCControlType
    is_active: bool = True


class SPCChartCreate(SPCChartBase):
    """Create SPC chart schema."""

    pass


class SPCChartUpdate(BaseModel):
    """Update SPC chart schema."""

    center_line: Optional[float] = None
    upper_control_limit: Optional[float] = None
    lower_control_limit: Optional[float] = None
    upper_warning_limit: Optional[float] = None
    lower_warning_limit: Optional[float] = None
    range_center_line: Optional[float] = None
    range_upper_control_limit: Optional[float] = None
    range_lower_control_limit: Optional[float] = None
    is_active: Optional[bool] = None


class SPCChartResponse(SPCChartBase):
    """SPC chart response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sample_count: int
    last_calculation_date: Optional[datetime] = None
    revision: int
    created_at: datetime
    updated_at: datetime


class SPCChartWithDataPoints(SPCChartResponse):
    """SPC chart with data points."""

    data_points: List["SPCDataPointResponse"] = []


# SPCDataPoint schemas
class SPCDataPointBase(BaseModel):
    """Base SPC data point schema."""

    spc_chart_id: int
    subgroup_number: int
    mean_value: float
    range_value: Optional[float] = None
    standard_deviation: Optional[float] = None
    sample_size: int = Field(..., ge=1)
    raw_values: Optional[List[float]] = None
    work_order_id: Optional[int] = None
    lot_number: Optional[str] = Field(None, max_length=50)


class SPCDataPointCreate(SPCDataPointBase):
    """Create SPC data point schema."""

    pass


class SPCDataPointUpdate(BaseModel):
    """Update SPC data point schema."""

    mean_value: Optional[float] = None
    range_value: Optional[float] = None
    standard_deviation: Optional[float] = None
    sample_size: Optional[int] = Field(None, ge=1)
    raw_values: Optional[List[float]] = None
    lot_number: Optional[str] = Field(None, max_length=50)


class SPCDataPointResponse(SPCDataPointBase):
    """SPC data point response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_out_of_control: bool
    violation_rules: Optional[List[str]] = None
    created_at: datetime


# MeasurementDevice schemas (from DIGITAL_THREAD_SPC_QMS.md)
class MeasurementDeviceBase(BaseModel):
    """Base measurement device schema."""

    name: str = Field(..., min_length=1, max_length=100, description="EQUATOR-01, CNC01-PROBE 등")
    source_type: str = Field(..., description="OMM, EQUATOR, CMM, MANUAL")
    machine_id: Optional[int] = None
    serial_number: Optional[str] = Field(None, max_length=100)
    calibration_due: Optional[datetime] = None
    connection_config: Dict[str, Any] = Field(default_factory=dict, description="연동 설정 JSON")
    is_active: bool = True


class MeasurementDeviceCreate(MeasurementDeviceBase):
    """Create measurement device schema."""

    pass


class MeasurementDeviceUpdate(BaseModel):
    """Update measurement device schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    source_type: Optional[str] = None
    machine_id: Optional[int] = None
    serial_number: Optional[str] = Field(None, max_length=100)
    calibration_due: Optional[datetime] = None
    connection_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class MeasurementDeviceResponse(MeasurementDeviceBase):
    """Measurement device response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# NonConformance schemas (based on DIGITAL_THREAD_SPC_QMS.md)
class NonConformanceBase(BaseModel):
    """Base non-conformance schema with Digital Thread integration."""

    # Digital Thread 연계 (추적성)
    work_order_id: Optional[int] = None
    lot_no: Optional[str] = Field(None, max_length=50)
    serial_no: Optional[str] = Field(None, max_length=50)
    machine_id: Optional[int] = None
    inspection_result_id: Optional[int] = None

    # 부적합 내용 (from design spec)
    defect_type: str = Field(..., description="DIMENSION, SURFACE, MATERIAL")
    characteristic: str = Field(..., min_length=1, max_length=100, description="어떤 항목")
    specified_value: Optional[float] = None
    actual_value: Optional[float] = None

    # 처리 (Disposition)
    disposition: str = Field(default="PENDING", description="REWORK, SCRAP, USE_AS_IS, RETURN")

    # Description
    description: str = Field(..., min_length=1)
    root_cause: Optional[str] = Field(None, description="5 Why 분석")
    corrective_action: Optional[str] = None

    # Personnel
    reported_by: str = Field(..., min_length=1, max_length=50)
    assigned_to: Optional[str] = Field(None, max_length=50)
    due_date: Optional[datetime] = None


class NonConformanceCreate(NonConformanceBase):
    """Create non-conformance schema."""

    pass


class NonConformanceUpdate(BaseModel):
    """Update non-conformance schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    severity: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    category: Optional[str] = Field(None, max_length=50)
    status: Optional[NCRStatus] = None
    assigned_to: Optional[str] = Field(None, max_length=50)
    due_date: Optional[datetime] = None


class NonConformanceResponse(NonConformanceBase):
    """Non-conformance response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ncr_no: str
    status: NCRStatus
    reported_at: datetime
    closed_at: Optional[datetime] = None
    is_auto_generated: bool
    trigger_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


# SPC Analysis schemas
class SPCCapabilityAnalysis(BaseModel):
    """SPC capability analysis result."""

    characteristic: str
    sample_count: int
    mean: float
    std_deviation: float
    cp: Optional[float] = None  # Process capability
    cpk: Optional[float] = None  # Process capability index
    pp: Optional[float] = None  # Process performance
    ppk: Optional[float] = None  # Process performance index
    specification_min: Optional[float] = None
    specification_max: Optional[float] = None
    target_value: Optional[float] = None
    analysis_date: datetime


class SPCViolationRule(BaseModel):
    """SPC violation rule result."""

    rule_number: int
    rule_description: str
    violated_points: List[int]  # Subgroup numbers
    severity: str  # WARNING, ALERT


class SPCAnalysisResult(BaseModel):
    """Comprehensive SPC analysis result."""

    chart_id: int
    characteristic: str
    total_points: int
    out_of_control_points: int
    capability_analysis: Optional[SPCCapabilityAnalysis] = None
    violated_rules: List[SPCViolationRule] = []
    trend_analysis: Dict[str, Any] = {}
    recommendations: List[str] = []
    analysis_date: datetime


# Traceability schemas
class QualityTraceabilityRecord(BaseModel):
    """Quality traceability record."""

    serial_no: str
    work_order_id: int
    lot_number: Optional[str] = None
    product_name: str
    inspection_results: List[InspectionResultResponse] = []
    ncr_records: List[NonConformanceResponse] = []
    overall_status: str  # PASS, FAIL, CONDITIONAL
    quality_score: Optional[float] = None  # 0-100
    traced_at: datetime


# Batch operations
class BatchInspectionResult(BaseModel):
    """Batch inspection result creation."""

    inspection_plan_id: int
    work_order_id: int
    equipment_id: Optional[int] = None
    results: List[Dict[str, Any]]  # List of measurement data
    inspector_name: Optional[str] = None
    measurement_method: Optional[str] = None


class BatchInspectionResponse(BaseModel):
    """Batch inspection result response."""

    created_count: int
    failed_count: int
    created_results: List[InspectionResultResponse] = []
    errors: List[str] = []
