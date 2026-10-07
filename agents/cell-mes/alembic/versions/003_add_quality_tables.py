"""Add quality management tables

Revision ID: 003
Revises: 002
Create Date: 2026-02-07 07:35:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create inspection_plans table
    op.create_table(
        "inspection_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("operation_id", sa.Integer(), nullable=True),
        sa.Column("pmi_source", sa.String(length=255), nullable=True),
        sa.Column("feature_id", sa.String(length=100), nullable=True),
        sa.Column("characteristic", sa.String(length=100), nullable=False),
        sa.Column("nominal", sa.Float(), nullable=True),
        sa.Column("usl", sa.Float(), nullable=True),
        sa.Column("lsl", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=False, default="mm"),
        sa.Column("inspection_type", sa.String(length=20), nullable=False, default="IN_PROCESS"),
        sa.Column("sampling_plan", sa.String(length=50), nullable=False, default="PERIODIC"),
        sa.Column("frequency", sa.Integer(), nullable=True),
        sa.Column("enable_spc", sa.Boolean(), nullable=False, default=True),
        sa.Column("spc_control_type", sa.String(length=20), nullable=False, default="X_BAR_R"),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["operation_id"],
            ["process_routings.id"],
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_inspection_plans_product_id"), "inspection_plans", ["product_id"], unique=False
    )

    # Create inspection_results table
    op.create_table(
        "inspection_results",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("inspection_plan_id", sa.Integer(), nullable=False),
        sa.Column("work_order_id", sa.BigInteger(), nullable=False),
        sa.Column("equipment_id", sa.Integer(), nullable=True),
        sa.Column("lot_no", sa.String(length=50), nullable=True),
        sa.Column("serial_no", sa.String(length=50), nullable=True),
        sa.Column("nc_program_id", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False, default="MANUAL"),
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("measured_value", sa.Float(), nullable=False),
        sa.Column("deviation", sa.Float(), nullable=True),
        sa.Column("is_conforming", sa.Boolean(), nullable=False),
        sa.Column("measurement_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "measured_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["measurement_devices.id"],
        ),
        sa.ForeignKeyConstraint(
            ["equipment_id"],
            ["equipments.id"],
        ),
        sa.ForeignKeyConstraint(
            ["inspection_plan_id"],
            ["inspection_plans.id"],
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["work_orders.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_inspection_results_inspection_plan_id"),
        "inspection_results",
        ["inspection_plan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_inspection_results_serial_no"),
        "inspection_results",
        ["serial_no"],
        unique=False,
    )
    op.create_index(
        op.f("ix_inspection_results_work_order_id"),
        "inspection_results",
        ["work_order_id"],
        unique=False,
    )

    # Create spc_charts table
    op.create_table(
        "spc_charts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("inspection_plan_id", sa.Integer(), nullable=False),
        sa.Column("center_line", sa.Float(), nullable=False),
        sa.Column("upper_control_limit", sa.Float(), nullable=False),
        sa.Column("lower_control_limit", sa.Float(), nullable=False),
        sa.Column("upper_warning_limit", sa.Float(), nullable=True),
        sa.Column("lower_warning_limit", sa.Float(), nullable=True),
        sa.Column("range_center_line", sa.Float(), nullable=True),
        sa.Column("range_upper_control_limit", sa.Float(), nullable=True),
        sa.Column("range_lower_control_limit", sa.Float(), nullable=True),
        sa.Column("sample_count", sa.Integer(), nullable=False, default=0),
        sa.Column("last_calculation_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chart_type", sa.String(length=20), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, default=1),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["inspection_plan_id"],
            ["inspection_plans.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_spc_charts_inspection_plan_id"), "spc_charts", ["inspection_plan_id"], unique=False
    )

    # Create spc_data_points table
    op.create_table(
        "spc_data_points",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("spc_chart_id", sa.Integer(), nullable=False),
        sa.Column("subgroup_number", sa.Integer(), nullable=False),
        sa.Column("mean_value", sa.Float(), nullable=False),
        sa.Column("range_value", sa.Float(), nullable=True),
        sa.Column("standard_deviation", sa.Float(), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("raw_values", sa.JSON(), nullable=True),
        sa.Column("is_out_of_control", sa.Boolean(), nullable=False, default=False),
        sa.Column("violation_rules", sa.JSON(), nullable=True),
        sa.Column("work_order_id", sa.BigInteger(), nullable=True),
        sa.Column("lot_number", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["spc_chart_id"],
            ["spc_charts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["work_orders.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_spc_data_points_spc_chart_id"), "spc_data_points", ["spc_chart_id"], unique=False
    )

    # Create non_conformances table
    op.create_table(
        "non_conformances",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("ncr_no", sa.String(length=50), nullable=False),
        sa.Column("work_order_id", sa.BigInteger(), nullable=True),
        sa.Column("lot_no", sa.String(length=50), nullable=True),
        sa.Column("serial_no", sa.String(length=50), nullable=True),
        sa.Column("machine_id", sa.Integer(), nullable=True),
        sa.Column("inspection_result_id", sa.BigInteger(), nullable=True),
        sa.Column("inspection_plan_id", sa.Integer(), nullable=True),
        sa.Column("defect_type", sa.String(length=50), nullable=False),
        sa.Column("characteristic", sa.String(length=100), nullable=False),
        sa.Column("specified_value", sa.Float(), nullable=True),
        sa.Column("actual_value", sa.Float(), nullable=True),
        sa.Column("disposition", sa.String(length=20), nullable=False, default="PENDING"),
        sa.Column("status", sa.String(length=20), nullable=False, default="OPEN"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("corrective_action", sa.Text(), nullable=True),
        sa.Column("reported_by", sa.String(length=50), nullable=False),
        sa.Column("assigned_to", sa.String(length=50), nullable=True),
        sa.Column(
            "reported_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_auto_generated", sa.Boolean(), nullable=False, default=False),
        sa.Column("trigger_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["inspection_plan_id"],
            ["inspection_plans.id"],
        ),
        sa.ForeignKeyConstraint(
            ["inspection_result_id"],
            ["inspection_results.id"],
        ),
        sa.ForeignKeyConstraint(
            ["machine_id"],
            ["equipments.id"],
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"],
            ["work_orders.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_non_conformances_ncr_no"), "non_conformances", ["ncr_no"], unique=True
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f("ix_non_conformances_ncr_no"), table_name="non_conformances")
    op.drop_table("non_conformances")
    op.drop_index(op.f("ix_spc_data_points_spc_chart_id"), table_name="spc_data_points")
    op.drop_table("spc_data_points")
    op.drop_index(op.f("ix_spc_charts_inspection_plan_id"), table_name="spc_charts")
    op.drop_table("spc_charts")
    op.drop_index(op.f("ix_inspection_results_work_order_id"), table_name="inspection_results")
    op.drop_index(op.f("ix_inspection_results_serial_number"), table_name="inspection_results")
    op.drop_index(op.f("ix_inspection_results_inspection_plan_id"), table_name="inspection_results")
    op.drop_table("inspection_results")
    op.drop_index(op.f("ix_inspection_plans_product_id"), table_name="inspection_plans")
    op.drop_table("inspection_plans")
