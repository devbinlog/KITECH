"""
Cell-MES <-> Cell-Scheduler Communication Protocol

This module defines the data structures for inter-agent communication
between Cell-MES and Cell-Scheduler agents.

WorkOrder contains operations directly (no Job layer).

Message Flow:
1. Cell-MES creates SchedulingRequest with equipment and work orders
2. Cell-Scheduler processes and returns SchedulingResult
3. Cell-MES applies scheduled times to work orders
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional
from enum import Enum


class EquipmentStatus(str, Enum):
    """Equipment status values compatible with cell-scheduler"""

    AVAILABLE = "AVAILABLE"
    RUNNING = "RUNNING"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"


class Priority(str, Enum):
    """Work order priority levels"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EquipmentAvailability:
    """
    Equipment availability data for cell-scheduler.

    This is the format cell-scheduler expects for machine data.
    """

    machine_id: str  # Format: "EQ-{id}"
    machine_name: str
    machine_type: str  # Maps to required_machine_type in operations
    status: str  # EquipmentStatus value
    available_from: str  # ISO format datetime
    current_setup_id: Optional[str] = None
    setup_change_time_min: int = 5

    # MES-specific metadata
    mes_equipment_id: Optional[int] = None
    aas_id: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EquipmentAvailability":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class NcCodeInfo:
    """NC program information for an operation"""

    program_id: str
    file_path: str
    cycle_time_sec: int = 60
    cycle_time_confidence: float = 0.9
    tool_list: List[str] = field(default_factory=list)
    tool_change_count: int = 0
    compatible_machines: List[str] = field(default_factory=list)


@dataclass
class OperationInfo:
    """Operation (공정) information for scheduling"""

    op_id: str  # Format: "OP-{routing_id}"
    op_name: str
    sequence: int
    predecessors: List[str] = field(default_factory=list)
    required_machine_type: str = "GENERAL"
    setup_id: str = ""
    nc_code: Optional[NcCodeInfo] = None
    # cycle_time_sec promoted for simpler access
    cycle_time_sec: Optional[int] = None
    # MES-specific: routing_id for result tracking
    process_routing_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.nc_code:
            data["nc_code"] = asdict(self.nc_code)
        return data

    def get_cycle_time(self) -> int:
        """Get cycle time, preferring direct value over nc_code"""
        if self.cycle_time_sec is not None:
            return self.cycle_time_sec
        if self.nc_code:
            return self.nc_code.cycle_time_sec
        return 60  # default


@dataclass
class WorkOrderForScheduling:
    """
    Work order data for cell-scheduler.

    Operations are directly under work order (no Job layer).
    This is the format cell-scheduler expects for work order data.
    """

    wo_id: str  # Format: "WO-{id}"
    product_id: str  # Format: "PROD-{id}"
    product_name: str
    order_quantity: int
    due_date: str  # ISO format datetime
    priority: int  # Priority value (1-10, higher = more urgent)
    release_date: str  # ISO format datetime
    customer: str = "Internal"
    # Operations directly under work order
    operations: List[OperationInfo] = field(default_factory=list)

    # MES-specific metadata
    mes_work_order_id: Optional[int] = None
    lot_no: Optional[str] = None
    scenario_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["operations"] = [op.to_dict() for op in self.operations]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkOrderForScheduling":
        """Create from dict (operations directly)"""
        operations = [
            OperationInfo(
                op_id=op["op_id"],
                op_name=op["op_name"],
                sequence=op["sequence"],
                predecessors=op.get("predecessors", []),
                required_machine_type=op.get("required_machine_type", "GENERAL"),
                setup_id=op.get("setup_id", ""),
                nc_code=NcCodeInfo(**op["nc_code"]) if op.get("nc_code") else None,
                cycle_time_sec=op.get("cycle_time_sec"),
                process_routing_id=op.get("process_routing_id"),
            )
            for op in data.get("operations", [])
        ]

        return cls(
            wo_id=data["wo_id"],
            product_id=data["product_id"],
            product_name=data["product_name"],
            order_quantity=data["order_quantity"],
            due_date=data["due_date"],
            priority=data.get("priority", 5),
            release_date=data["release_date"],
            customer=data.get("customer", "Internal"),
            operations=operations,
            mes_work_order_id=data.get("mes_work_order_id"),
            lot_no=data.get("lot_no"),
            scenario_id=data.get("scenario_id"),
        )


@dataclass
class SchedulingRequest:
    """
    Complete scheduling request for cell-scheduler.

    Contains all data needed to run the scheduling algorithm.
    """

    request_id: str
    request_time: str  # ISO format datetime
    horizon_start: str  # ISO format datetime
    horizon_end: str  # ISO format datetime

    machines: List[EquipmentAvailability]
    work_orders: List[WorkOrderForScheduling]
    machine_type_params: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Solver options
    solver_time_limit_sec: int = 60
    optimization_goal: str = "minimize_makespan"

    def to_scheduler_format(self) -> Dict[str, Any]:
        """Convert to cell-scheduler input format"""
        return {
            "request": {
                "scheduling_request": {
                    "request_id": self.request_id,
                    "request_time": self.request_time,
                    "scheduling_horizon": {
                        "start": self.horizon_start,
                        "end": self.horizon_end,
                    },
                    "options": {
                        "solver_time_limit_sec": self.solver_time_limit_sec,
                        "optimization_goal": self.optimization_goal,
                    },
                },
            },
            "work_orders": [wo.to_dict() for wo in self.work_orders],
            "machines": [m.to_dict() for m in self.machines],
            "machine_type_params": self.machine_type_params,
            "cell_layout": {},
            "constraints": {},
        }


@dataclass
class ScheduledTask:
    """
    A single scheduled task from cell-scheduler.

    Represents one operation assigned to a machine with timing.
    """

    wo_id: str
    op_id: str
    machine_id: str
    start_time: int  # Seconds from horizon start
    end_time: int  # Seconds from horizon start
    quantity: int
    setup_time: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledTask":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SchedulingResult:
    """
    Scheduling result from cell-scheduler.

    Contains scheduled tasks and statistics.
    """

    status: str  # "success", "no_solution", "error"
    scheduled_tasks: List[ScheduledTask]
    objective_value: float = 0.0
    solve_time_sec: float = 0.0
    total_makespan: int = 0
    machine_utilization: Dict[str, float] = field(default_factory=dict)
    bottleneck_machines: List[str] = field(default_factory=list)

    # Gantt data for visualization
    gantt_data: Optional[Dict[str, Any]] = None

    @classmethod
    def from_scheduler_output(cls, output: Dict[str, Any]) -> "SchedulingResult":
        """Create from cell-scheduler process() output"""
        tasks = [ScheduledTask.from_dict(t) for t in output.get("scheduled_tasks", [])]

        stats = output.get("statistics", {})

        return cls(
            status=output.get("status", "error"),
            scheduled_tasks=tasks,
            objective_value=stats.get("objective_value", 0),
            solve_time_sec=stats.get("solve_time_sec", 0),
            total_makespan=stats.get("makespan_seconds", 0),
            machine_utilization=stats.get("machine_utilization", {}),
            bottleneck_machines=stats.get("bottleneck_machines", []),
            gantt_data=output.get("gantt_data"),
        )

    def get_tasks_for_work_order(self, wo_id: str) -> List[ScheduledTask]:
        """Get all tasks for a specific work order"""
        return [t for t in self.scheduled_tasks if t.wo_id == wo_id]

    def get_tasks_for_machine(self, machine_id: str) -> List[ScheduledTask]:
        """Get all tasks for a specific machine"""
        return [t for t in self.scheduled_tasks if t.machine_id == machine_id]
