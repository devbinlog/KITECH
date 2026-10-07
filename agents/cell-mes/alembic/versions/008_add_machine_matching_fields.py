"""Add machine matching fields to master routing tables.

Revision ID: 008
Revises: 007
Create Date: 2026-06-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("std_processes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("required_machines", sa.JSON(), nullable=True))

    with op.batch_alter_table("process_routings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("setup_id", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("required_machines", sa.JSON(), nullable=True))

    with op.batch_alter_table("process_routing_files", schema=None) as batch_op:
        batch_op.add_column(sa.Column("compatible_machines", sa.JSON(), nullable=True))

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE std_processes
            SET required_machines = json_array(equipment_type)
            WHERE required_machines IS NULL
              AND equipment_type IS NOT NULL
              AND equipment_type != ''
            """
        )
    )


def downgrade() -> None:
    with op.batch_alter_table("process_routing_files", schema=None) as batch_op:
        batch_op.drop_column("compatible_machines")

    with op.batch_alter_table("process_routings", schema=None) as batch_op:
        batch_op.drop_column("required_machines")
        batch_op.drop_column("setup_id")

    with op.batch_alter_table("std_processes", schema=None) as batch_op:
        batch_op.drop_column("required_machines")
