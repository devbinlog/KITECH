"""Equipment models with JSON support for flexible data structures."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..db.base import Base

if TYPE_CHECKING:
    from .master import Cell


class Equipment(Base):
    """Equipment/Machine with AAS integration and JSON data storage."""

    __tablename__ = "equipments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    eq_code: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )  # Standard code: EQ-CNC-001, EQ-ROBOT-001
    aas_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )  # AAS unique identifier from middleware
    eq_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    equipment_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="CNC", index=True
    )  # CNC, ROBOT, AMR, PLC
    location: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Physical location: Building A, Line 1
    cell_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("cells.id"), nullable=True, index=True
    )  # FK to cells table

    # JSON columns for flexible data (compatible with SQLite and PostgreSQL)
    connection_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )  # {"ip": "192.168.1.1", "port": 502, "protocol": "modbus"}
    spec_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict
    )  # Static specs: {"manufacturer": "Doosan", "max_rpm": 20000}
    last_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict
    )  # Real-time data: {"spindle_rpm": 15000, "load_percent": 45.5}

    current_status: Mapped[str] = mapped_column(String(20), default="STOP")  # RUN, STOP, ERROR
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    cell: Mapped[Optional["Cell"]] = relationship("Cell", back_populates="equipments")
    logs: Mapped[List["EqLog"]] = relationship("EqLog", back_populates="equipment")
    status_history: Mapped[List["EquipmentStatusHistory"]] = relationship(
        "EquipmentStatusHistory", back_populates="equipment"
    )

    def __repr__(self) -> str:
        return f"<Equipment(id={self.id}, aas_id='{self.aas_id}', name='{self.eq_name}', type='{self.equipment_type}')>"

    @property
    def is_connected(self) -> bool:
        """Check if equipment was connected within the last 30 seconds."""
        if self.last_connected_at is None:
            return False
        delta = datetime.now(self.last_connected_at.tzinfo) - self.last_connected_at
        return delta.total_seconds() < 30


class EqLog(Base):
    """Equipment event logs."""

    __tablename__ = "eq_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("equipments.id"), nullable=False, index=True
    )
    level: Mapped[str] = mapped_column(String(10), default="INFO")  # INFO, WARN, ERROR
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    equipment: Mapped["Equipment"] = relationship("Equipment", back_populates="logs")

    def __repr__(self) -> str:
        return f"<EqLog(id={self.id}, equipment_id={self.equipment_id}, level='{self.level}')>"


class EquipmentStatusHistory(Base):
    """설비 상태 변경 이력.

    상태 변경 시마다 기록하여 가동률/OEE 분석에 활용.

    Status values:
    - RUN: 가동 중
    - IDLE: 대기 (가동 가능하지만 작업 없음)
    - STOP: 정지
    - SETUP: 셋업/준비 중
    - ERROR: 에러/고장
    - MAINTENANCE: 보전 중
    """

    __tablename__ = "equipment_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("equipments.id"), nullable=False, index=True
    )

    previous_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # 상태 변경 시점
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # 이전 상태 지속 시간 (분)
    previous_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 변경 원인/관련 정보
    reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    work_order_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("work_orders.id"), nullable=True
    )
    changed_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 시스템 or 사용자

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    equipment: Mapped["Equipment"] = relationship("Equipment", back_populates="status_history")

    def __repr__(self) -> str:
        return f"<EquipmentStatusHistory(equipment_id={self.equipment_id}, {self.previous_status} -> {self.new_status})>"
