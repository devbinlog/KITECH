"""Add original filename to routing files

Revision ID: 007
Revises: 006
Create Date: 2026-05-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("process_routing_files", schema=None) as batch_op:
        batch_op.add_column(sa.Column("original_filename", sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("process_routing_files", schema=None) as batch_op:
        batch_op.drop_column("original_filename")
