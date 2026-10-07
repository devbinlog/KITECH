"""Add product routing cycle time fields.

Revision ID: 011
Revises: 010
Create Date: 2026-09-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("process_routings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("cycle_time_sec", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("cycle_time_breakdown", sa.JSON(), nullable=True))

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE process_routings
            SET cycle_time_sec = (
                SELECT std_processes.cycle_time_sec
                FROM std_processes
                WHERE std_processes.id = process_routings.std_process_id
            )
            WHERE cycle_time_sec IS NULL
            """
        )
    )


def downgrade() -> None:
    with op.batch_alter_table("process_routings", schema=None) as batch_op:
        batch_op.drop_column("cycle_time_breakdown")
        batch_op.drop_column("cycle_time_sec")
