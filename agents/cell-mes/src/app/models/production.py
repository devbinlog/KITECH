"""Production models: WorkOrder and ProdResult."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..db.base import Base

if TYPE_CHECKING:
    from .master import ProcessRouting


class WorkOrder(Base):
    """Work order for production execution.

    Schema:
    - start_time/end_time: Actual execution time for entire WO
    - completed_qty/current_process: Progress tracking
    - Per-operation scheduling is stored in ProdResult
    """

    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lot_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=True
    )
    scenario_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("scenarios.id"), nullable=True
    )
    target_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    qty: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # Order quantity for scheduler
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1=highest, 10=lowest
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Progress tracking
    completed_qty: Mapped[int] = mapped_column(Integer, default=0)  # Completed quantity
    current_process: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Current process code

    # Actual execution time (updated when WO starts/ends)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    remarks: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="READY"
    )  # READY, RUNNING, PAUSE, DONE, ERROR
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product: Mapped[Optional["Product"]] = relationship("Product")
    scenario: Mapped[Optional["Scenario"]] = relationship("Scenario")
    units: Mapped[List["Unit"]] = relationship(
        "Unit", back_populates="work_order", cascade="all, delete-orphan"
    )
    results: Mapped[List["ProdResult"]] = relationship(
        "ProdResult", back_populates="work_order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<WorkOrder(id={self.id}, lot_no='{self.lot_no}', status='{self.status}')>"

    # State machine transitions
    VALID_TRANSITIONS = {
        "READY": ["SCHEDULED", "RUNNING", "CANCEL"],
        "SCHEDULED": ["RUNNING", "CANCEL"],
        "RUNNING": ["PAUSE", "DONE", "ERROR", "CANCEL"],
        "PAUSE": ["RUNNING", "DONE", "CANCEL"],
        "ERROR": ["RUNNING", "DONE"],
        "DONE": [],
        "CANCEL": [],
    }

    def can_transition_to(self, new_status: str) -> bool:
        """Check if transition to new status is valid."""
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])


# Forward reference for Product and Equipment (circular import resolution)
from .master import Product, Scenario  # noqa: E402


class Unit(Base):
    """Queue token / physical unit representing Lot-Size 1 dispatching.
    
    status: READY (in MES queue), RUNNING (with Middleware), DONE, ERROR
    """
    
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("work_orders.id"), nullable=False, index=True
    )
    unit_no: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Snapshot of the scenario_id at the time this unit was queued.
    # Allows dynamic scenario overrides mid-flight for waiting units.
    scenario_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("scenarios.id"), nullable=True
    )
    
    status: Mapped[str] = mapped_column(String(20), default="READY")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scenario_hold_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scenario_hold_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    work_order: Mapped["WorkOrder"] = relationship("WorkOrder", back_populates="units")
    results: Mapped[List["ProdResult"]] = relationship(
        "ProdResult", back_populates="unit", cascade="all, delete-orphan"
    )
    scenario: Mapped[Optional["Scenario"]] = relationship("Scenario")

    def __repr__(self) -> str:
        return f"<Unit(id={self.id}, wo={self.work_order_id}, no={self.unit_no}, status='{self.status}')>"


class ProdResult(Base):
    """Production result/traceability record.

    Each record represents one operation's execution:
    - target_equipment_id: Scheduler-assigned equipment
    - equipment_id: Actual execution equipment
    """

    __tablename__ = "prod_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("work_orders.id"), nullable=False, index=True
    )
    unit_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("units.id"), nullable=True, index=True
    )
    process_routing_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("process_routings.id"), nullable=True
    )
    equipment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("equipments.id"), nullable=True
    )
    # Scheduler-assigned equipment (may differ from actual equipment_id after execution)
    target_equipment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("equipments.id"), nullable=True
    )
    ok_qty: Mapped[int] = mapped_column(Integer, default=0)
    ng_qty: Mapped[int] = mapped_column(Integer, default=0)

    # Scheduled/actual time for this operation
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    work_order: Mapped["WorkOrder"] = relationship("WorkOrder", back_populates="results")
    unit: Mapped[Optional["Unit"]] = relationship("Unit", back_populates="results")
    process_routing: Mapped[Optional["ProcessRouting"]] = relationship("ProcessRouting")

    def __repr__(self) -> str:
        return f"<ProdResult(id={self.id}, wo_id={self.work_order_id}, ok={self.ok_qty}, ng={self.ng_qty})>"

    @property
    def total_qty(self) -> int:
        """Total quantity processed."""
        return self.ok_qty + self.ng_qty

    @property
    def yield_rate(self) -> float:
        """Calculate yield rate (OK / Total)."""
        if self.total_qty == 0:
            return 0.0
        return self.ok_qty / self.total_qty * 100
