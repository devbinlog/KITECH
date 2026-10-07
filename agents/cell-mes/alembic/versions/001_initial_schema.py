"""Initial schema for Cell-MES

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users & System Config
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), server_default="OPERATOR", nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "middleware_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. Master Data (Standards)
    op.create_table(
        "std_processes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_std_processes_code", "std_processes", ["code"])

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("unit", sa.String(10), server_default="EA", nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_products_code", "products", ["code"])

    # 3. Equipments (AAS Integrated)
    op.create_table(
        "equipments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("aas_id", sa.String(100), nullable=True),
        sa.Column("eq_name", sa.String(100), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=True),
        sa.Column("equipment_type", sa.String(20), server_default="CNC", nullable=False),
        sa.Column("connection_config", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("spec_data", sa.JSON(), server_default="{}", nullable=True),
        sa.Column("last_data", sa.JSON(), server_default="{}", nullable=True),
        sa.Column("current_status", sa.String(20), server_default="STOP", nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.Column("last_connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aas_id"),
    )
    op.create_index("idx_equipments_aas", "equipments", ["aas_id"])

    # 4. Routing & Scenarios
    op.create_table(
        "process_routings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("std_process_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("remarks", sa.String(255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["std_process_id"], ["std_processes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "sequence", name="uq_routing_product_sequence"),
    )
    op.create_index("idx_routing_product", "process_routings", ["product_id"])

    op.create_table(
        "process_routing_files",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("process_routing_id", sa.Integer(), nullable=False),
        sa.Column("file_type", sa.String(20), server_default="NC", nullable=True),
        sa.Column("file_path", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="1", nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["process_routing_id"], ["process_routings.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_routing_files", "process_routing_files", ["process_routing_id"])

    op.create_table(
        "scenarios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("file_path", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 5. Transaction Data
    op.create_table(
        "work_orders",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lot_no", sa.String(50), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("scenario_id", sa.Integer(), nullable=True),
        sa.Column("target_qty", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="READY", nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lot_no"),
    )
    op.create_index("ix_work_orders_lot_no", "work_orders", ["lot_no"])

    op.create_table(
        "prod_results",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("work_order_id", sa.BigInteger(), nullable=False),
        sa.Column("process_routing_id", sa.Integer(), nullable=True),
        sa.Column("equipment_id", sa.Integer(), nullable=True),
        sa.Column("ok_qty", sa.Integer(), server_default="0", nullable=True),
        sa.Column("ng_qty", sa.Integer(), server_default="0", nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.id"]),
        sa.ForeignKeyConstraint(["process_routing_id"], ["process_routings.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_results_wo", "prod_results", ["work_order_id"])

    op.create_table(
        "eq_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(10), server_default="INFO", nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eq_logs_equipment_id", "eq_logs", ["equipment_id"])


def downgrade() -> None:
    op.drop_table("eq_logs")
    op.drop_table("prod_results")
    op.drop_table("work_orders")
    op.drop_table("scenarios")
    op.drop_table("process_routing_files")
    op.drop_table("process_routings")
    op.drop_table("equipments")
    op.drop_table("products")
    op.drop_table("std_processes")
    op.drop_table("middleware_config")
    op.drop_table("users")
