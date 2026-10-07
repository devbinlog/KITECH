"""Add unit scenario hold metadata fields.

Revision ID: 009
Revises: 008
Create Date: 2026-06-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.add_column(sa.Column("scenario_hold_started_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("scenario_hold_by", sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.drop_column("scenario_hold_by")
        batch_op.drop_column("scenario_hold_started_at")
