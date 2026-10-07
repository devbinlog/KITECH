"""add_users_table

Revision ID: dcb434f47f7d
Revises: 004
Create Date: 2026-03-04 16:52:00.907028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'dcb434f47f7d'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table is already created in 001_initial_schema.py
    pass


def downgrade() -> None:
    # No-op as upgrade was no-op
    pass
