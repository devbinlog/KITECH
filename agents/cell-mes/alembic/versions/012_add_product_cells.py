"""Add product allowed cells without changing routing revisions or existing data."""

from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_cells",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cell_id", sa.Integer(), sa.ForeignKey("cells.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("product_id", "cell_id", name="uq_product_cell"),
    )
    op.create_index("ix_product_cells_product_id", "product_cells", ["product_id"])
    op.create_index("ix_product_cells_cell_id", "product_cells", ["cell_id"])


def downgrade() -> None:
    op.drop_table("product_cells")
