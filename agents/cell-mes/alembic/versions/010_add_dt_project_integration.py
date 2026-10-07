"""Add DT Project integration tables.

Revision ID: 010
Revises: 009
Create Date: 2026-06-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dt_project_refs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("external_project_id", sa.String(length=100), nullable=True),
        sa.Column("asset_global_id", sa.String(length=255), nullable=False),
        sa.Column("asset_id", sa.String(length=255), nullable=False),
        sa.Column("element_id", sa.String(length=100), nullable=False),
        sa.Column("element_full_id", sa.String(length=255), nullable=True),
        sa.Column("element_category", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("uuid", sa.String(length=100), nullable=True),
        sa.Column("xml_path", sa.String(length=255), nullable=True),
        sa.Column("raw_metadata", sa.JSON(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "platform", "asset_global_id", "asset_id", "element_id",
            name="uq_dt_project_platform_element",
        ),
    )
    op.create_index("ix_dt_project_refs_external_project_id", "dt_project_refs", ["external_project_id"])

    op.create_table(
        "product_dt_project_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("dt_project_ref_id", sa.Integer(), nullable=False),
        sa.Column("relation_type", sa.String(length=30), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("unlinked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["dt_project_ref_id"], ["dt_project_refs.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_dt_project_links_product_id", "product_dt_project_links", ["product_id"])
    op.create_index(
        "ix_product_dt_project_links_dt_project_ref_id",
        "product_dt_project_links",
        ["dt_project_ref_id"],
    )
    op.create_index(
        "ix_product_dt_project_one_current_primary",
        "product_dt_project_links",
        ["product_id", "relation_type"],
        unique=True,
        sqlite_where=sa.text("is_current = 1"),
        postgresql_where=sa.text("is_current = true"),
    )

    op.create_table(
        "dt_project_workplans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("dt_project_ref_id", sa.Integer(), nullable=False),
        sa.Column("workplan_id", sa.String(length=100), nullable=False),
        sa.Column("parent_workplan_id", sa.String(length=100), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("source_path", sa.String(length=500), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("has_direct_steps", sa.Boolean(), nullable=False),
        sa.Column("raw_fragment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["dt_project_ref_id"], ["dt_project_refs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "dt_project_ref_id", "workplan_id", "source_path",
            name="uq_dt_project_workplan_path",
        ),
    )
    op.create_index(
        "ix_dt_project_workplans_dt_project_ref_id",
        "dt_project_workplans",
        ["dt_project_ref_id"],
    )

    op.create_table(
        "dt_file_refs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("external_file_id", sa.String(length=100), nullable=False),
        sa.Column("asset_global_id", sa.String(length=255), nullable=False),
        sa.Column("asset_id", sa.String(length=255), nullable=True),
        sa.Column("element_id", sa.String(length=100), nullable=True),
        sa.Column("element_full_id", sa.String(length=255), nullable=True),
        sa.Column("element_category", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column("references", sa.JSON(), nullable=True),
        sa.Column("workplan_id", sa.String(length=100), nullable=True),
        sa.Column("raw_metadata", sa.JSON(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("platform", "external_file_id", name="uq_dt_file_platform_external"),
    )
    op.create_index("ix_dt_file_refs_workplan_id", "dt_file_refs", ["workplan_id"])

    with op.batch_alter_table("process_routings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("dt_workplan_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_process_routings_dt_workplan_id",
            "dt_project_workplans",
            ["dt_workplan_id"],
            ["id"],
        )
        batch_op.create_index("ix_process_routings_dt_workplan_id", ["dt_workplan_id"])

    with op.batch_alter_table("process_routing_files", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("source_type", sa.String(length=20), server_default="LOCAL_UPLOAD", nullable=False)
        )
        batch_op.add_column(sa.Column("dt_file_ref_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_process_routing_files_dt_file_ref_id",
            "dt_file_refs",
            ["dt_file_ref_id"],
            ["id"],
        )
        batch_op.create_index("ix_process_routing_files_dt_file_ref_id", ["dt_file_ref_id"])


def downgrade() -> None:
    with op.batch_alter_table("process_routing_files", schema=None) as batch_op:
        batch_op.drop_index("ix_process_routing_files_dt_file_ref_id")
        batch_op.drop_constraint("fk_process_routing_files_dt_file_ref_id", type_="foreignkey")
        batch_op.drop_column("dt_file_ref_id")
        batch_op.drop_column("source_type")

    with op.batch_alter_table("process_routings", schema=None) as batch_op:
        batch_op.drop_index("ix_process_routings_dt_workplan_id")
        batch_op.drop_constraint("fk_process_routings_dt_workplan_id", type_="foreignkey")
        batch_op.drop_column("dt_workplan_id")

    op.drop_index("ix_dt_file_refs_workplan_id", table_name="dt_file_refs")
    op.drop_table("dt_file_refs")
    op.drop_index("ix_dt_project_workplans_dt_project_ref_id", table_name="dt_project_workplans")
    op.drop_table("dt_project_workplans")
    op.drop_index("ix_product_dt_project_one_current_primary", table_name="product_dt_project_links")
    op.drop_index("ix_product_dt_project_links_dt_project_ref_id", table_name="product_dt_project_links")
    op.drop_index("ix_product_dt_project_links_product_id", table_name="product_dt_project_links")
    op.drop_table("product_dt_project_links")
    op.drop_index("ix_dt_project_refs_external_project_id", table_name="dt_project_refs")
    op.drop_table("dt_project_refs")
