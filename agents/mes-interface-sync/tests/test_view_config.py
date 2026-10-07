from pathlib import Path

from mes_interface_sync.schema import SourceColumn
from mes_interface_sync.view_config import InterfaceViewConfigSet, sql_literal


def test_configured_view_uses_first_existing_source_candidate(tmp_path: Path) -> None:
    config_path = tmp_path / "interface_views.yaml"
    config_path.write_text(
        """
version: 1
views:
  - name: if_work_orders
    source_table: work_orders
    columns:
      - name: due_date
        source_candidates:
          - due_date
          - delivery_date
        required: true
""",
        encoding="utf-8",
    )

    config = InterfaceViewConfigSet.load(config_path)
    sql = config.create_view_sql(
        "work_orders",
        [SourceColumn("delivery_date", "DATETIME", False, 0)],
    )

    assert '"delivery_date" AS "due_date"' in sql
    assert 'FROM "mes_src"."work_orders"' in sql
    assert 'DROP VIEW IF EXISTS "mes_if"."if_work_orders"' in sql


def test_configured_view_uses_default_for_missing_optional_column(tmp_path: Path) -> None:
    config_path = tmp_path / "interface_views.yaml"
    config_path.write_text(
        """
version: 1
views:
  - name: if_work_orders
    source_table: work_orders
    columns:
      - name: priority
        source: priority
        required: false
        default: 0
""",
        encoding="utf-8",
    )

    config = InterfaceViewConfigSet.load(config_path)
    sql = config.create_view_sql("work_orders", [SourceColumn("id", "INTEGER", False, 1)])

    assert '0 AS "priority"' in sql


def test_configured_view_fails_when_required_column_is_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "interface_views.yaml"
    config_path.write_text(
        """
version: 1
views:
  - name: if_work_orders
    source_table: work_orders
    columns:
      - name: lot_no
        source: lot_no
        required: true
""",
        encoding="utf-8",
    )

    config = InterfaceViewConfigSet.load(config_path)

    try:
        config.create_view_sql("work_orders", [SourceColumn("id", "INTEGER", False, 1)])
    except ValueError as exc:
        assert "Required column lot_no" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_auto_view_uses_yaml_sensitive_columns(tmp_path: Path) -> None:
    config_path = tmp_path / "interface_views.yaml"
    config_path.write_text(
        """
version: 1
sensitive_columns:
  custom_table:
    - secret_note
""",
        encoding="utf-8",
    )

    config = InterfaceViewConfigSet.load(config_path)
    sql = config.create_view_sql(
        "custom_table",
        [
            SourceColumn("id", "INTEGER", False, 1),
            SourceColumn("secret_note", "TEXT", False, 0),
        ],
    )

    assert '"secret_note"' not in sql
    assert 'CREATE VIEW "mes_if"."if_custom_table"' in sql


def test_sql_literal_escapes_text_defaults() -> None:
    assert sql_literal("planner's hold") == "'planner''s hold'"


def test_product_cells_auto_view_with_shipped_config() -> None:
    config = InterfaceViewConfigSet.load(Path(__file__).parents[1] / "config/interface_views.yaml")
    sql = config.create_view_sql("product_cells", [
        SourceColumn("id", "INTEGER", False, 1),
        SourceColumn("product_id", "INTEGER", False, 0),
        SourceColumn("cell_id", "INTEGER", False, 0),
        SourceColumn("created_at", "DATETIME", False, 0),
    ])
    assert 'CREATE VIEW "mes_if"."if_product_cells"' in sql
    assert '"product_id"' in sql
    assert '"cell_id"' in sql
    assert '"_if_batch_id"' in sql
