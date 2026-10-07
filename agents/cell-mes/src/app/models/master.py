"""Master data models: ProcessCategory, Cell, StdProcess, Product, ProcessRouting, Scenario."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, String, Integer, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..db.base import Base

if TYPE_CHECKING:
    from .equipment import Equipment


class ProcessCategory(Base):
    """공정 카테고리 마스터 - 공정 유형 분류."""

    __tablename__ = "process_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    std_processes: Mapped[List["StdProcess"]] = relationship(
        "StdProcess", back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<ProcessCategory(id={self.id}, code='{self.code}', name='{self.name}')>"


class Cell(Base):
    """제조 셀 마스터 - 설비 그룹핑 단위."""

    __tablename__ = "cells"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    equipments: Mapped[List["Equipment"]] = relationship("Equipment", back_populates="cell")

    def __repr__(self) -> str:
        return f"<Cell(id={self.id}, code='{self.code}', name='{self.name}')>"


class StdProcess(Base):
    """Standard process library - defines reusable process templates."""

    __tablename__ = "std_processes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # FK to process_categories
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("process_categories.id"), nullable=True, index=True
    )
    # Scheduler integration fields
    equipment_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )  # Must match Equipment.equipment_type (e.g., "CNC", "LATHE", "ROBOT")
    required_machines: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True
    )  # Default machine candidates for this process; falls back from equipment_type.
    cycle_time_sec: Mapped[int] = mapped_column(
        Integer, default=60
    )  # Standard cycle time per unit in seconds
    setup_time_sec: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Setup/changeover time in seconds
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    category: Mapped[Optional["ProcessCategory"]] = relationship(
        "ProcessCategory", back_populates="std_processes"
    )
    routings: Mapped[List["ProcessRouting"]] = relationship(
        "ProcessRouting", back_populates="std_process"
    )

    def __repr__(self) -> str:
        return f"<StdProcess(id={self.id}, code='{self.code}', name='{self.name}')>"


class Product(Base):
    """Product/Item master data."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), default="EA")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    routings: Mapped[List["ProcessRouting"]] = relationship(
        "ProcessRouting", back_populates="product", cascade="all, delete-orphan"
    )
    scenarios: Mapped[List["Scenario"]] = relationship("Scenario", back_populates="product")
    dt_project_links: Mapped[List["ProductDtProjectLink"]] = relationship(
        "ProductDtProjectLink", back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, code='{self.code}', name='{self.name}')>"


class ProductCell(Base):
    """Allowed manufacturing cells for the product's current routings."""

    __tablename__ = "product_cells"
    __table_args__ = (UniqueConstraint("product_id", "cell_id", name="uq_product_cell"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cell_id: Mapped[int] = mapped_column(
        ForeignKey("cells.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessRouting(Base):
    """Process routing - defines the sequence of processes for a product."""

    __tablename__ = "process_routings"
    __table_args__ = (
        UniqueConstraint(
            "product_id", "sequence", "revision", name="uq_routing_product_sequence_rev"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    std_process_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("std_processes.id"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)  # 10, 20, 30...
    revision: Mapped[str] = mapped_column(
        String(10), default="A", nullable=False
    )  # A, B, C or 1, 2, 3
    setup_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    dt_workplan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("dt_project_workplans.id"), nullable=True, index=True
    )
    required_machines: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True
    )  # Product-specific machine candidates; falls back to std_process.required_machines.
    cycle_time_sec: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Product/routing-specific cycle time; falls back to std_process.cycle_time_sec.
    cycle_time_breakdown: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Optional trace of NC/action timing components used to calculate cycle_time_sec.
    remarks: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="routings")
    std_process: Mapped["StdProcess"] = relationship("StdProcess", back_populates="routings")
    dt_workplan: Mapped[Optional["DtProjectWorkplan"]] = relationship(
        "DtProjectWorkplan", back_populates="routings"
    )
    files: Mapped[List["ProcessRoutingFile"]] = relationship(
        "ProcessRoutingFile", back_populates="routing", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ProcessRouting(id={self.id}, product_id={self.product_id}, seq={self.sequence})>"


class ProcessRoutingFile(Base):
    """Files associated with a process routing step (NC, Image, Doc)."""

    __tablename__ = "process_routing_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    process_routing_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("process_routings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_type: Mapped[str] = mapped_column(String(20), default="NC")  # NC, IMAGE, DOC
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), default="LOCAL_UPLOAD", nullable=False)
    dt_file_ref_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("dt_file_refs.id"), nullable=True, index=True
    )
    compatible_machines: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    routing: Mapped["ProcessRouting"] = relationship("ProcessRouting", back_populates="files")
    dt_file: Mapped[Optional["DtFileRef"]] = relationship(
        "DtFileRef", back_populates="routing_files"
    )

    def __repr__(self) -> str:
        return (
            f"<ProcessRoutingFile(id={self.id}, type='{self.file_type}', path='{self.file_path}')>"
        )


class DtProjectRef(Base):
    """Digital Thread platform project snapshot linked to MES products."""

    __tablename__ = "dt_project_refs"
    __table_args__ = (
        UniqueConstraint(
            "platform", "asset_global_id", "asset_id", "element_id",
            name="uq_dt_project_platform_element",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(50), default="DTP", nullable=False)
    external_project_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    asset_global_id: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_id: Mapped[str] = mapped_column(String(255), nullable=False)
    element_id: Mapped[str] = mapped_column(String(100), nullable=False)
    element_full_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    element_category: Mapped[str] = mapped_column(String(50), default="Project", nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    uuid: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    xml_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product_links: Mapped[List["ProductDtProjectLink"]] = relationship(
        "ProductDtProjectLink", back_populates="dt_project"
    )
    workplans: Mapped[List["DtProjectWorkplan"]] = relationship(
        "DtProjectWorkplan", back_populates="dt_project", cascade="all, delete-orphan"
    )


class ProductDtProjectLink(Base):
    """Product to DT Project relation. A product can remain unlinked."""

    __tablename__ = "product_dt_project_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dt_project_ref_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dt_project_refs.id"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(String(30), default="PRIMARY", nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    unlinked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="dt_project_links")
    dt_project: Mapped["DtProjectRef"] = relationship(
        "DtProjectRef", back_populates="product_links"
    )


class DtProjectWorkplan(Base):
    """Workplan parsed from a DT Project XML tree."""

    __tablename__ = "dt_project_workplans"
    __table_args__ = (
        UniqueConstraint(
            "dt_project_ref_id", "workplan_id", "source_path",
            name="uq_dt_project_workplan_path",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dt_project_ref_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dt_project_refs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workplan_id: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_workplan_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_path: Mapped[str] = mapped_column(String(500), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    has_direct_steps: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_fragment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dt_project: Mapped["DtProjectRef"] = relationship(
        "DtProjectRef", back_populates="workplans"
    )
    routings: Mapped[List["ProcessRouting"]] = relationship(
        "ProcessRouting", back_populates="dt_workplan"
    )


class DtFileRef(Base):
    """Digital Thread platform file snapshot, usually NC files referenced by workplan."""

    __tablename__ = "dt_file_refs"
    __table_args__ = (
        UniqueConstraint("platform", "external_file_id", name="uq_dt_file_platform_external"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(50), default="DTP", nullable=False)
    external_file_id: Mapped[str] = mapped_column(String(100), nullable=False)
    asset_global_id: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    element_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    element_full_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    element_category: Mapped[str] = mapped_column(String(50), default="NC", nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    references: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    workplan_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    routing_files: Mapped[List["ProcessRoutingFile"]] = relationship(
        "ProcessRoutingFile", back_populates="dt_file"
    )


class Scenario(Base):
    """Logistics/Robot scenarios for production control."""

    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )  # SCN-001
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="scenarios")

    def __repr__(self) -> str:
        return f"<Scenario(id={self.id}, name='{self.name}', active={self.is_active})>"
