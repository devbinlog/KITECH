"""Quality models: InspectionPlan, InspectionResult, SPCChart, NonConformance."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..db.base import Base


class InspectionType(str, Enum):
    """Inspection type enumeration."""

    INCOMING = "INCOMING"  # 입고 검사
    IN_PROCESS = "IN_PROCESS"  # 공정 검사
    FINAL = "FINAL"  # 최종 검사
    PERIODIC = "PERIODIC"  # 정기 검사


class SPCControlType(str, Enum):
    """SPC control chart type."""

    X_BAR_R = "X_BAR_R"  # X-bar R 관리도
    X_BAR_S = "X_BAR_S"  # X-bar S 관리도
    P_CHART = "P_CHART"  # P 관리도
    C_CHART = "C_CHART"  # C 관리도


class NCRStatus(str, Enum):
    """NCR (Non-Conformance Report) status."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"
    VERIFIED = "VERIFIED"
    CANCELLED = "CANCELLED"


class InspectionPlan(Base):
    """Inspection plan linked with PMI (Product Manufacturing Information).

    Defines what characteristics to inspect for each product/operation.
    Based on DIGITAL_THREAD_SPC_QMS.md design specification.
    """

    __tablename__ = "inspection_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    operation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("process_routings.id"), nullable=True
    )

    # Digital Thread 연계 (PMI Integration)
    pmi_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # STEP file path
    feature_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # PMI Feature ID

    # Inspection details (following existing design)
    characteristic: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # "외경", "깊이", "위치도"
    nominal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 기준값
    usl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Upper Spec Limit
    lsl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Lower Spec Limit
    unit: Mapped[str] = mapped_column(String(20), default="mm")

    # 검사 방법 (from design spec)
    inspection_type: Mapped[InspectionType] = mapped_column(
        String(20), default=InspectionType.IN_PROCESS
    )
    sampling_plan: Mapped[str] = mapped_column(
        String(50), default="PERIODIC"
    )  # FIRST_ARTICLE, PERIODIC, 100%
    frequency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # n개당 1회

    # SPC settings
    enable_spc: Mapped[bool] = mapped_column(Boolean, default=True)
    spc_control_type: Mapped[SPCControlType] = mapped_column(
        String(20), default=SPCControlType.X_BAR_R
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product")
    operation: Mapped[Optional["ProcessRouting"]] = relationship("ProcessRouting")
    inspection_results: Mapped[List["InspectionResult"]] = relationship(
        "InspectionResult", back_populates="inspection_plan", cascade="all, delete-orphan"
    )
    spc_charts: Mapped[List["SPCChart"]] = relationship(
        "SPCChart", back_populates="inspection_plan", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<InspectionPlan(id={self.id}, characteristic='{self.characteristic}')>"


class InspectionResult(Base):
    """Inspection measurement results from equipment/operators.

    Stores actual measurement data for quality analysis.
    Based on DIGITAL_THREAD_SPC_QMS.md design specification.
    """

    __tablename__ = "inspection_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    inspection_plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inspection_plans.id"), nullable=False, index=True
    )
    work_order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("work_orders.id"), nullable=False, index=True
    )
    equipment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("equipments.id"), nullable=True
    )

    # Digital Thread 연계 (Full Traceability)
    lot_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    serial_no: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )  # 개별 추적
    nc_program_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 측정 소스 (OMM/EQUATOR/CMM/MANUAL)
    source: Mapped[str] = mapped_column(String(20), default="MANUAL")  # OMM, EQUATOR, CMM, MANUAL
    device_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("measurement_devices.id"), nullable=True
    )

    # Measurement data
    measured_value: Mapped[float] = mapped_column(Float, nullable=False)
    deviation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 기준값 대비 편차

    # Result classification
    is_conforming: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Metadata (JSON pattern from equipment.py)
    measurement_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=dict
    )  # inspector, method, conditions

    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    inspection_plan: Mapped["InspectionPlan"] = relationship(
        "InspectionPlan", back_populates="inspection_results"
    )
    work_order: Mapped["WorkOrder"] = relationship("WorkOrder")
    equipment: Mapped[Optional["Equipment"]] = relationship("Equipment")

    def __repr__(self) -> str:
        return f"<InspectionResult(id={self.id}, value={self.measured_value}, conforming={self.is_conforming})>"


class SPCChart(Base):
    """SPC (Statistical Process Control) chart configuration.

    Stores control limits and chart settings for process monitoring.
    """

    __tablename__ = "spc_charts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inspection_plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inspection_plans.id"), nullable=False, index=True
    )

    # Control limits
    center_line: Mapped[float] = mapped_column(Float, nullable=False)  # X-bar or P
    upper_control_limit: Mapped[float] = mapped_column(Float, nullable=False)  # UCL
    lower_control_limit: Mapped[float] = mapped_column(Float, nullable=False)  # LCL
    upper_warning_limit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lower_warning_limit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Range chart (for X-bar R charts)
    range_center_line: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # R-bar
    range_upper_control_limit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    range_lower_control_limit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Chart statistics
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    last_calculation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Chart metadata
    chart_type: Mapped[SPCControlType] = mapped_column(String(20), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    inspection_plan: Mapped["InspectionPlan"] = relationship(
        "InspectionPlan", back_populates="spc_charts"
    )
    data_points: Mapped[List["SPCDataPoint"]] = relationship(
        "SPCDataPoint", back_populates="spc_chart", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SPCChart(id={self.id}, type='{self.chart_type}', UCL={self.upper_control_limit})>"


class SPCDataPoint(Base):
    """SPC chart data points for control chart visualization.

    Each point represents a subgroup of measurements.
    """

    __tablename__ = "spc_data_points"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    spc_chart_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("spc_charts.id"), nullable=False, index=True
    )

    # Data point values
    subgroup_number: Mapped[int] = mapped_column(Integer, nullable=False)
    mean_value: Mapped[float] = mapped_column(Float, nullable=False)  # X-bar
    range_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # R
    standard_deviation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # S

    # Subgroup data
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_values: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)

    # Violation flags (Western Electric Rules)
    is_out_of_control: Mapped[bool] = mapped_column(Boolean, default=False)
    violation_rules: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Metadata
    work_order_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("work_orders.id"), nullable=True
    )
    lot_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    spc_chart: Mapped["SPCChart"] = relationship("SPCChart", back_populates="data_points")
    work_order: Mapped[Optional["WorkOrder"]] = relationship("WorkOrder")

    def __repr__(self) -> str:
        return (
            f"<SPCDataPoint(id={self.id}, subgroup={self.subgroup_number}, mean={self.mean_value})>"
        )


class NonConformance(Base):
    """Non-Conformance Report (NCR) for quality issues.

    Generated automatically when SPC rules are violated or manually reported.
    Based on DIGITAL_THREAD_SPC_QMS.md design specification.
    """

    __tablename__ = "non_conformances"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ncr_no: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )  # "NCR-2026-0001"

    # Digital Thread 연계 (추적성)
    work_order_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("work_orders.id"), nullable=True
    )
    lot_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    serial_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    machine_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("equipments.id"), nullable=True
    )
    inspection_result_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("inspection_results.id"), nullable=True
    )
    inspection_plan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("inspection_plans.id"), nullable=True
    )

    # 부적합 내용 (from design spec)
    defect_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # DIMENSION, SURFACE, MATERIAL
    characteristic: Mapped[str] = mapped_column(String(100), nullable=False)  # 어떤 항목
    specified_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 처리 (Disposition)
    disposition: Mapped[str] = mapped_column(
        String(20), default="PENDING"
    )  # REWORK, SCRAP, USE_AS_IS, RETURN
    status: Mapped[NCRStatus] = mapped_column(String(20), default=NCRStatus.OPEN)

    # Description
    description: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 5 Why
    corrective_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Personnel
    reported_by: Mapped[str] = mapped_column(String(50), nullable=False)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Dates
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Auto-generation flag (SPC alerts)
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    trigger_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=dict
    )  # SPC violation data

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    work_order: Mapped[Optional["WorkOrder"]] = relationship("WorkOrder")
    equipment: Mapped[Optional["Equipment"]] = relationship("Equipment")
    inspection_plan: Mapped[Optional["InspectionPlan"]] = relationship("InspectionPlan")

    def __repr__(self) -> str:
        return f"<NonConformance(id={self.id}, ncr_no='{self.ncr_no}', status='{self.status}')>"


# Forward references for circular import resolution
from .master import Product, ProcessRouting  # noqa: E402
from .production import WorkOrder  # noqa: E402
from .equipment import Equipment  # noqa: E402


class MeasurementDevice(Base):
    """측정 장비 마스터 (from DIGITAL_THREAD_SPC_QMS.md)"""

    __tablename__ = "measurement_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "EQUATOR-01", "CNC01-PROBE"
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # OMM, EQUATOR, CMM, MANUAL

    # 장비별 설정
    machine_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("equipments.id"), nullable=True
    )
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    calibration_due: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 연동 설정 (JSON pattern from equipment.py)
    connection_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # {"connection_type": "FILE", "path": "/data/equator/", "format": "csv"}

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    machine: Mapped[Optional["Equipment"]] = relationship("Equipment")
    inspection_results: Mapped[List["InspectionResult"]] = relationship("InspectionResult")

    def __repr__(self) -> str:
        return f"<MeasurementDevice(id={self.id}, name='{self.name}', type='{self.source_type}')>"
