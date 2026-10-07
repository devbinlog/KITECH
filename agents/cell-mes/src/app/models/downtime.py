"""Downtime models: DowntimeReason, Downtime for OEE calculation."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..db.base import Base


class DowntimeReason(Base):
    """정지 사유 코드 마스터.

    Categories:
    - PLANNED: 계획 정지 (정기 보전, 교대 휴식 등)
    - UNPLANNED: 비계획 정지 (고장, 품질 문제 등)
    - SETUP: 셋업/교체 (공구 교체, 품목 변경 등)
    """

    __tablename__ = "downtime_reasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(
        String(20), nullable=False, default="UNPLANNED", index=True
    )  # PLANNED, UNPLANNED, SETUP
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    downtimes: Mapped[list["Downtime"]] = relationship("Downtime", back_populates="reason")

    def __repr__(self) -> str:
        return f"<DowntimeReason(code='{self.code}', category='{self.category}')>"


class Downtime(Base):
    """설비 다운타임 기록.

    OEE 가동률 계산에 사용:
    - Availability = (계획 가동시간 - 다운타임) / 계획 가동시간
    """

    __tablename__ = "downtimes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("equipments.id"), nullable=False, index=True
    )
    reason_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("downtime_reasons.id"), nullable=True
    )
    work_order_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("work_orders.id"), nullable=True
    )  # 관련 작업지시 (있는 경우)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # 수동 입력 정보
    duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 자동 계산 or 수동 입력
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reported_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    reason: Mapped[Optional["DowntimeReason"]] = relationship(
        "DowntimeReason", back_populates="downtimes"
    )

    def __repr__(self) -> str:
        return f"<Downtime(equipment_id={self.equipment_id}, start='{self.start_time}')>"

    @property
    def calculated_duration_minutes(self) -> Optional[int]:
        """다운타임 시간(분) 계산."""
        if self.duration_minutes:
            return self.duration_minutes
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return None

    @property
    def is_ongoing(self) -> bool:
        """진행 중인 다운타임 여부."""
        return self.end_time is None
