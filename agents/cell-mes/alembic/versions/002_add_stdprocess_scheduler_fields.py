"""Add scheduler integration fields to std_processes

Revision ID: 002
Revises: 001
Create Date: 2026-02-01

Adds equipment_type and cycle_time_sec fields to std_processes table
for scheduler integration.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add equipment_type column (matches Equipment.equipment_type for scheduler matching)
    op.add_column(
        "std_processes", sa.Column("equipment_type", sa.String(50), nullable=True, index=True)
    )
    # Add cycle_time_sec column (standard cycle time per unit in seconds)
    op.add_column(
        "std_processes",
        sa.Column("cycle_time_sec", sa.Integer(), nullable=False, server_default="60"),
    )


def downgrade() -> None:
    op.drop_index("ix_std_processes_equipment_type", table_name="std_processes")
    op.drop_column("std_processes", "cycle_time_sec")
    op.drop_column("std_processes", "equipment_type")
