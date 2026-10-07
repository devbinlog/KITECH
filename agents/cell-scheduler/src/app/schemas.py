"""
Pydantic Schemas for Cell-Scheduler API

Defines request and response models for the scheduling API.
MES v5 Schema: Job layer removed, WorkOrder contains operations directly.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class SolverTypeEnum(str, Enum):
    """Available solver types"""

    OR_TOOLS = "OR_TOOLS"
    GA = "GA"
    SA = "SA"
    TABU = "TABU"
    ALNS = "ALNS"
    AUTO = "AUTO"  # Auto-select based on problem size


# ============================================================================
# Request Models
# ============================================================================


class BreakSchema(BaseModel):
    """Shift break interval"""
    start: str  # "HH:MM"
    end: str    # "HH:MM"


class CalendarSchema(BaseModel):
    """Equipment shift calendar"""
    shift_start: str  # "HH:MM"
    shift_end: str    # "HH:MM"
    breaks: List[BreakSchema] = []


class AMRSchema(BaseModel):
    """Autonomous Mobile Robot"""
    amr_id: str
    model: str = ""
    status: str = "available"
    current_location: str = ""
    accessible_machines: List[str] = []
    speed_m_per_sec: float = 1.0


class SchedulerConfigSchema(BaseModel):
    """Global scheduler configuration"""
    lot_size: int = 1
    amr_transfer_time_sec: int = 60


class NcCodeSchema(BaseModel):
    """NC program information"""

    program_id: str
    file_path: str
    cycle_time_sec: int
    cycle_time_confidence: float = 1.0
    tool_list: List[str] = []
    tool_change_count: int = 0
    compatible_machines: List[str] = []


class OperationSchema(BaseModel):
    """Work operation - directly under WorkOrder (no Job layer)"""

    op_id: str
    op_name: str
    sequence: int
    predecessors: List[str] = []
    required_machines: List[str] = []   # list of machine IDs, machine types, or "AMR"
    setup_id: str = ""
    nc_code: Optional[NcCodeSchema] = None
    cycle_time_sec: Optional[int] = None  # promoted from nc_code for simpler access

    def get_cycle_time(self) -> int:
        """Get cycle time, preferring direct value over nc_code"""
        if self.cycle_time_sec is not None:
            return self.cycle_time_sec
        if self.nc_code:
            return self.nc_code.cycle_time_sec
        return 0


class WorkOrderSchema(BaseModel):
    """Work order definition - MES v5 (operations directly, no jobs layer)"""

    wo_id: str
    product_id: str
    product_name: str
    order_quantity: int
    due_date: datetime
    priority: int = 5
    release_date: datetime
    customer: str
    # MES work_orders.lot_no — 작업지시의 고유 별칭 (분할 순번 sublot_no와 무관)
    lot_no: str = ""
    # MES v5: operations directly under work order
    operations: List[OperationSchema]


class OccupiedSlotSchema(BaseModel):
    """Time slot already occupied on a machine (existing schedule)"""

    start: int  # seconds from horizon start
    end: int  # seconds from horizon start
    wo_id: Optional[str] = None  # optional: which WO occupies this slot


class MachineSchema(BaseModel):
    """Machine/Equipment definition"""

    machine_id: str
    machine_name: str
    machine_type: str
    status: str
    available_from: datetime
    current_setup_id: Optional[str] = None
    setup_change_time_min: int = 5
    occupied_slots: List[OccupiedSlotSchema] = []
    calendar: Optional[CalendarSchema] = None


class MachineTypeParamsSchema(BaseModel):
    """Machine type parameters"""

    loading_type: str
    amr_transport_qty: int = 1
    exchange_time_sec: int = 0
    load_unload_time_sec: int = 0


class SchedulingHorizonSchema(BaseModel):
    """Scheduling time horizon"""

    start: datetime
    end: datetime


class SolverOptionsSchema(BaseModel):
    """Solver configuration options"""

    solver_type: SolverTypeEnum = SolverTypeEnum.OR_TOOLS
    time_limit_sec: int = 60

    # OR-Tools specific
    num_workers: Optional[int] = 8

    # GA specific
    population_size: Optional[int] = 100
    generations: Optional[int] = 500
    crossover_rate: Optional[float] = 0.8
    mutation_rate: Optional[float] = 0.2

    # SA specific
    initial_temp: Optional[float] = 100.0
    cooling_rate: Optional[float] = 0.95

    # Tabu specific
    tabu_tenure: Optional[int] = 10
    tabu_iterations: Optional[int] = 5000

    # ALNS specific
    alns_destroy_rate: Optional[float] = None
    alns_iterations: Optional[int] = None
    alns_segment_size: Optional[int] = None


class ScheduleRequest(BaseModel):
    """Complete scheduling request.

    machines / machine_type_params / amrs / scheduler_config 는 선택 필드입니다.
    서버에 AAS_PATH가 설정된 경우 AAS에서 자동으로 로드되므로 보내지 않아도 됩니다.
    AAS_PATH가 없는 경우 machines는 필수입니다.
    """

    work_orders: List[WorkOrderSchema]
    machines: List[MachineSchema] = []
    machine_type_params: Dict[str, MachineTypeParamsSchema] = {}
    scheduling_horizon: SchedulingHorizonSchema
    constraints: Dict[str, Any] = {}
    options: SolverOptionsSchema = Field(default_factory=SolverOptionsSchema)
    amrs: List[AMRSchema] = []
    scheduler_config: SchedulerConfigSchema = Field(default_factory=SchedulerConfigSchema)


# ============================================================================
# Response Models
# ============================================================================


class SetupIntervalSchema(BaseModel):
    """Setup time interval"""
    machine_id: str
    wo_id: str
    start_time: int
    end_time: int
    duration_sec: int


class ScheduledTaskSchema(BaseModel):
    """Scheduled task result - MES v5 (no job_id)"""

    wo_id: str
    op_id: str
    machine_id: str
    start_time: int  # seconds from horizon start
    end_time: int
    quantity: int
    setup_time: int = 0
    sublot_no: int = 1   # 작업지시 qty를 lot_size로 분할한 조각의 순번 (1,2,3,…)
    lot_no: str = ""     # MES work_orders.lot_no — 이 task가 속한 작업지시의 별칭
    op_name: str = ""
    assigned_machines: Dict[str, str] = {}
    amr_transfer_sec: int = 0


class ScheduleStatisticsSchema(BaseModel):
    """Scheduling statistics"""

    total_tasks: int
    makespan_seconds: int
    makespan_hours: float
    machine_utilization: Dict[str, float]
    bottleneck_machines: List[str]
    solve_time_sec: float
    objective_value: float
    # Lexicographic 목적함수 컴포넌트 (tardiness → completion → makespan → setup)
    weighted_tardiness_sec: int = 0
    weighted_completion_sec: int = 0
    total_setup_sec: int = 0


class QualityMetricsSchema(BaseModel):
    """Schedule quality metrics"""

    status: str
    makespan_hours: float
    total_lateness_hours: float
    avg_machine_utilization: float
    machine_utilization: Dict[str, float] = {}
    bottleneck_machines: List[str] = []
    schedule_efficiency: float
    per_wo_lateness: Dict[str, float] = {}
    total_scheduled_tasks: int
    total_work_orders: int
    total_machines: int
    # Lexicographic 목적함수 컴포넌트
    weighted_tardiness_hours: float = 0.0
    weighted_completion_minutes: float = 0.0
    total_setup_minutes: float = 0.0


class GanttTaskSchema(BaseModel):
    """Single Gantt chart task"""

    name: str
    start: str
    end: str
    resource: str
    priority: int
    color: str
    quantity: int
    duration_minutes: float


class GanttDataSchema(BaseModel):
    """Gantt chart data"""

    tasks: List[GanttTaskSchema]
    resources: List[str]
    start: str
    end: str


class SolverInfoSchema(BaseModel):
    """Solver information"""

    type: str
    name: str
    version: str = ""
    description: str = ""
    best_for: str = ""
    characteristics: Dict[str, Any] = {}
    default_params: Dict[str, Any] = {}
    error: Optional[str] = None


class ScheduleResponse(BaseModel):
    """Complete scheduling response"""

    status: str
    scheduled_tasks: List[ScheduledTaskSchema]
    statistics: ScheduleStatisticsSchema
    quality_metrics: QualityMetricsSchema
    gantt_data: GanttDataSchema
    solver_info: SolverInfoSchema
    request_id: Optional[str] = None
    setup_intervals: List[SetupIntervalSchema] = []
    infeasible_wos: List[str] = []
    machine_name_map: Dict[str, str] = {}  # machine_id → machine_name (e.g. "EQ-12" → "NX5500")


class SolverListResponse(BaseModel):
    """List of available solvers"""

    solvers: List[SolverInfoSchema]


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    service: str


class ErrorResponse(BaseModel):
    """Error response"""

    status: str = "error"
    error: str
    detail: Optional[str] = None
