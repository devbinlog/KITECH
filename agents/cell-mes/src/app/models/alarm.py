"""Alarm models: AlarmDefinition, Alarm for equipment monitoring."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..db.base import Base


class AlarmDefinition(Base):
    """알람 정의 마스터.

    Severity levels:
    - INFO: 정보성 알람
    - WARNING: 경고 (주의 필요)
    - CRITICAL: 긴급 (즉시 조치 필요)
    - EMERGENCY: 비상 (설비 정지)
    """

    __tablename__ = "alarm_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="WARNING", index=True
    )  # INFO, WARNING, CRITICAL, EMERGENCY
    category: Mapped[str] = mapped_column(
        String(30), nullable=False, default="EQUIPMENT", index=True
    )  # EQUIPMENT, PROCESS, QUALITY, SAFETY
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    auto_stop: Mapped[bool] = mapped_column(Boolean, default=False)  # 자동 설비 정지 여부
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    alarms: Mapped[list["Alarm"]] = relationship("Alarm", back_populates="definition")

    def __repr__(self) -> str:
        return f"<AlarmDefinition(code='{self.code}', severity='{self.severity}')>"


class Alarm(Base):
    """알람 발생/해제 기록.

    Status:
    - ACTIVE: 발생 중
    - ACKNOWLEDGED: 확인됨 (조치 중)
    - RESOLVED: 해제됨
    """

    __tablename__ = "alarms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    definition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("alarm_definitions.id"), nullable=False, index=True
    )
    equipment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("equipments.id"), nullable=True, index=True
    )
    work_order_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("work_orders.id"), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE", index=True
    )  # ACTIVE, ACKNOWLEDGED, RESOLVED

    # 시간 정보
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # 상세 정보
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 동적 메시지
    value: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # 발생 시 값 (예: 온도 85°C)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    definition: Mapped["AlarmDefinition"] = relationship("AlarmDefinition", back_populates="alarms")

    def __repr__(self) -> str:
        return f"<Alarm(definition_id={self.definition_id}, status='{self.status}')>"

    @property
    def duration_minutes(self) -> Optional[int]:
        """알람 지속 시간(분)."""
        end = self.resolved_at or datetime.now(self.occurred_at.tzinfo)
        delta = end - self.occurred_at
        return int(delta.total_seconds() / 60)

    @property
    def is_active(self) -> bool:
        """활성 알람 여부."""
        return self.status == "ACTIVE"
