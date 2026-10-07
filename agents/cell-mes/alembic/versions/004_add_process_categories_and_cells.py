"""Add process_categories and cells tables.

Revision ID: 004
Revises: 003
Create Date: 2025-02-09

Also adds missing columns:
- equipments.eq_code
- equipments.location
- equipments.cell_id
- std_processes.category_id
- std_processes.equipment_type
- std_processes.cycle_time_sec
- std_processes.setup_time_sec
- scenarios.code
- process_routings.revision
- work_orders.qty
- work_orders.completed_qty
- work_orders.current_process
- work_orders.due_date
- work_orders.start_time
- work_orders.end_time
- work_orders.remarks
- prod_results.target_equipment_id
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create process_categories table
    op.create_table(
        "process_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_process_categories_code", "process_categories", ["code"])

    # 2. Create cells table
    op.create_table(
        "cells",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_cells_code", "cells", ["code"])

    # 3. Add columns to equipments
    with op.batch_alter_table("equipments") as batch_op:
        batch_op.add_column(sa.Column("eq_code", sa.String(30), nullable=True))
        batch_op.add_column(sa.Column("location", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("cell_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_equipments_eq_code", ["eq_code"])
        batch_op.create_index("ix_equipments_cell_id", ["cell_id"])

    # 4. Add columns to std_processes
    with op.batch_alter_table("std_processes") as batch_op:
        batch_op.add_column(sa.Column("category_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("setup_time_sec", sa.Integer(), server_default="0", nullable=True)
        )
        batch_op.create_index("ix_std_processes_category_id", ["category_id"])

    # 5. Add columns to scenarios
    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.add_column(sa.Column("code", sa.String(20), nullable=True))
        batch_op.create_unique_constraint("uq_scenarios_code", ["code"])
        batch_op.create_index("ix_scenarios_code", ["code"])

    # 6. Add columns to process_routings
    with op.batch_alter_table("process_routings") as batch_op:
        batch_op.add_column(sa.Column("revision", sa.String(10), server_default="A", nullable=True))
        # Drop old unique constraint and create new one with revision
        batch_op.drop_constraint("uq_routing_product_sequence", type_="unique")
        batch_op.create_unique_constraint(
            "uq_routing_product_sequence_rev", ["product_id", "sequence", "revision"]
        )

    # 7. Add columns to work_orders
    with op.batch_alter_table("work_orders") as batch_op:
        batch_op.add_column(sa.Column("qty", sa.Integer(), server_default="1", nullable=True))
        batch_op.add_column(sa.Column("priority", sa.Integer(), server_default="5", nullable=True))
        batch_op.add_column(
            sa.Column("completed_qty", sa.Integer(), server_default="0", nullable=True)
        )
        batch_op.add_column(sa.Column("current_process", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("due_date", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("start_time", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("end_time", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("remarks", sa.String(500), nullable=True))

    # 8. Add columns to prod_results
    with op.batch_alter_table("prod_results") as batch_op:
        batch_op.add_column(sa.Column("target_equipment_id", sa.Integer(), nullable=True))

    # 9. Create equipment_status_history table
    op.create_table(
        "equipment_status_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("previous_status", sa.String(20), nullable=True),
        sa.Column("new_status", sa.String(20), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("previous_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(100), nullable=True),
        sa.Column("work_order_id", sa.Integer(), nullable=True),
        sa.Column("changed_by", sa.String(50), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_equipment_status_history_equipment_id", "equipment_status_history", ["equipment_id"]
    )
    op.create_index(
        "ix_equipment_status_history_changed_at", "equipment_status_history", ["changed_at"]
    )
    op.create_index(
        "ix_equipment_status_history_new_status", "equipment_status_history", ["new_status"]
    )


def downgrade() -> None:
    # Drop equipment_status_history table
    op.drop_table("equipment_status_history")

    # Remove columns from prod_results
    with op.batch_alter_table("prod_results") as batch_op:
        batch_op.drop_column("target_equipment_id")

    # Remove columns from work_orders
    with op.batch_alter_table("work_orders") as batch_op:
        batch_op.drop_column("remarks")
        batch_op.drop_column("end_time")
        batch_op.drop_column("start_time")
        batch_op.drop_column("due_date")
        batch_op.drop_column("current_process")
        batch_op.drop_column("completed_qty")
        batch_op.drop_column("priority")
        batch_op.drop_column("qty")

    # Remove columns from process_routings
    with op.batch_alter_table("process_routings") as batch_op:
        batch_op.drop_constraint("uq_routing_product_sequence_rev", type_="unique")
        batch_op.create_unique_constraint("uq_routing_product_sequence", ["product_id", "sequence"])
        batch_op.drop_column("revision")

    # Remove columns from scenarios
    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.drop_index("ix_scenarios_code")
        batch_op.drop_constraint("uq_scenarios_code", type_="unique")
        batch_op.drop_column("code")

    # Remove columns from std_processes
    with op.batch_alter_table("std_processes") as batch_op:
        batch_op.drop_index("ix_std_processes_equipment_type")
        batch_op.drop_index("ix_std_processes_category_id")
        batch_op.drop_column("setup_time_sec")
        batch_op.drop_column("cycle_time_sec")
        batch_op.drop_column("equipment_type")
        batch_op.drop_column("category_id")

    # Remove columns from equipments
    with op.batch_alter_table("equipments") as batch_op:
        batch_op.drop_index("ix_equipments_cell_id")
        batch_op.drop_index("ix_equipments_eq_code")
        batch_op.drop_column("cell_id")
        batch_op.drop_column("location")
        batch_op.drop_column("eq_code")

    # Drop cells table
    op.drop_table("cells")

    # Drop process_categories table
    op.drop_table("process_categories")
