"""
Scheduling domain events.

Events related to production scheduling.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import ConfigDict, Field

from .base import Event


class ScheduleRequestedEvent(Event):
    """
    Published when a scheduling solve is requested.

    Consumers:
    - Scheduler: Execute solve (if not already handling)
    - Dashboard: Show "scheduling in progress"
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "schedule.requested"

    request_id: str
    horizon_hours: int = 24
    solver_type: str = "OR_TOOLS"
    time_limit_sec: int = 60
    include_running: bool = False
    requested_by: Optional[str] = None
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Optional filters
    equipment_ids: List[int] = Field(default_factory=list)
    work_order_ids: List[int] = Field(default_factory=list)


class ScheduleCompletedEvent(Event):
    """
    Published when a scheduling solve completes.

    Consumers:
    - MES: Apply schedule to work orders
    - Dashboard: Display new schedule
    - Visualizer: Generate Gantt chart
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "schedule.completed"

    request_id: str
    success: bool
    solver_type: str

    # Results summary
    makespan_hours: Optional[float] = None
    total_jobs_scheduled: int = 0
    total_machines_used: int = 0
    objective_value: Optional[float] = None
    gap: Optional[float] = None

    # Timing
    solve_time_sec: float = 0.0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Error info (if failed)
    error_message: Optional[str] = None

    # Schedule data (for consumers that need it)
    schedule_summary: Dict[str, Any] = Field(default_factory=dict)


class ScheduleAppliedEvent(Event):
    """
    Published when a schedule is applied to work orders.

    Consumers:
    - Dashboard: Refresh schedule view
    - Equipment: Update assigned jobs
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "schedule.applied"

    request_id: str
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    applied_by: Optional[str] = None

    # Applied changes
    work_orders_updated: int = 0
    operations_scheduled: int = 0


class EquipmentAvailabilityChangedEvent(Event):
    """
    Published when equipment availability changes.

    Triggers:
    - Equipment breakdown
    - Maintenance scheduled
    - Equipment returned to service

    Consumers:
    - Scheduler: May trigger re-scheduling
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "equipment.availability_changed"

    equipment_id: int
    equipment_name: str
    previous_status: str
    new_status: str
    reason: Optional[str] = None
    expected_return: Optional[datetime] = None
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
