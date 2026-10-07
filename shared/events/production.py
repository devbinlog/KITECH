"""
Production domain events.

Events related to work orders and production recording.
"""

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import ConfigDict, Field

from .base import Event


class WorkOrderCreatedEvent(Event):
    """
    Published when a new work order is created.

    Consumers:
    - Scheduler: May trigger re-scheduling
    - Dashboard: Update work order count
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "work_order.created"

    # Work order data
    work_order_id: int
    lot_no: str
    product_id: int
    product_code: str
    order_qty: int
    priority: int = 50
    due_date: Optional[datetime] = None
    release_date: Optional[datetime] = None


class WorkOrderStatusChangedEvent(Event):
    """
    Published when a work order's status changes.

    Status transitions:
    - PLANNED -> RELEASED -> RUNNING -> COMPLETED
    - Any -> CANCELLED
    - Any -> ON_HOLD

    Consumers:
    - Dashboard: Update status displays
    - Analytics: Track cycle times
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "work_order.status_changed"

    work_order_id: int
    lot_no: str
    previous_status: str
    new_status: str
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    changed_by: Optional[str] = None
    reason: Optional[str] = None


class ProductionRecordedEvent(Event):
    """
    Published when production results are recorded.

    Consumers:
    - Analytics: Update KPIs (yield, throughput)
    - Quality: Trigger inspection if needed
    - Inventory: Update stock levels
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "production.recorded"

    work_order_id: int
    lot_no: str
    operation_id: int
    equipment_id: int
    equipment_name: str

    # Production quantities
    ok_qty: int
    ng_qty: int
    scrap_qty: int = 0

    # Time data
    start_time: datetime
    end_time: datetime
    cycle_time_sec: Optional[float] = None

    # Quality data
    defect_codes: List[str] = Field(default_factory=list)
    inspection_result: Optional[str] = None


class ProductionStartedEvent(Event):
    """
    Published when production starts on an operation.

    Consumers:
    - Dashboard: Real-time status update
    - Scheduler: Track actual vs planned start
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "production.started"

    work_order_id: int
    lot_no: str
    operation_id: int
    equipment_id: int
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    operator_id: Optional[str] = None


class ProductionCompletedEvent(Event):
    """
    Published when production completes on an operation.

    Consumers:
    - Scheduler: Release equipment for next job
    - Analytics: Calculate actual cycle times
    """

    model_config = ConfigDict(frozen=True)
    event_type: str = "production.completed"

    work_order_id: int
    lot_no: str
    operation_id: int
    equipment_id: int
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_ok_qty: int
    total_ng_qty: int
