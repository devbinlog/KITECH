import json

from mes_interface_sync.config import (
    DEFAULT_EXCLUDED_TABLES,
    Settings,
    _parse_bool,
    _parse_sync_schedule,
    _parse_table_list,
)
from mes_interface_sync.schema import (
    SourceColumn,
    convert_value,
    create_interface_view_sql,
    interface_view_name,
    is_excluded_table,
    map_sqlite_type,
    schema_hash,
)
from mes_interface_sync.sync_service import MesInterfaceSyncService


def test_parse_table_list_keeps_default_exclusions() -> None:
    assert _parse_table_list("custom_table") == DEFAULT_EXCLUDED_TABLES | {"custom_table"}


def test_parse_sync_schedule_reads_fixed_times() -> None:
    schedule = _parse_sync_schedule("02:00,14:30")

    assert [item.strftime("%H:%M") for item in schedule] == ["02:00", "14:30"]


def test_parse_sync_schedule_rejects_invalid_time() -> None:
    try:
        _parse_sync_schedule("25:00")
    except ValueError as exc:
        assert "Invalid sync schedule time" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_parse_bool_uses_default_and_common_true_values() -> None:
    assert _parse_bool(None, True) is True
    assert _parse_bool("yes", False) is True
    assert _parse_bool("false", True) is False


def test_sensitive_table_names_are_excluded() -> None:
    assert is_excluded_table("users", DEFAULT_EXCLUDED_TABLES)
    assert is_excluded_table("api_tokens", DEFAULT_EXCLUDED_TABLES)
    assert is_excluded_table("operator_sessions", DEFAULT_EXCLUDED_TABLES)
    assert not is_excluded_table("work_orders", DEFAULT_EXCLUDED_TABLES)


def test_interface_view_name_uses_if_prefix() -> None:
    assert interface_view_name("work_orders") == "if_work_orders"


def test_sqlite_type_mapping_uses_broad_postgres_types() -> None:
    assert map_sqlite_type("INTEGER") == "bigint"
    assert map_sqlite_type("BIGINT") == "bigint"
    assert map_sqlite_type("FLOAT") == "double precision"
    assert map_sqlite_type("JSON") == "jsonb"
    assert map_sqlite_type("VARCHAR(50)") == "text"


def test_interface_view_hides_sensitive_columns() -> None:
    sql = create_interface_view_sql(
        "equipments",
        [
            SourceColumn("id", "INTEGER", False, 1),
            SourceColumn("eq_name", "VARCHAR(100)", False, 0),
            SourceColumn("connection_config", "JSON", False, 0),
        ],
    )

    assert '"connection_config"' not in sql
    assert 'CREATE OR REPLACE VIEW "mes_if"."if_equipments"' in sql
    assert 'FROM "mes_src"."equipments"' in sql


def test_schema_hash_is_stable_for_same_schema() -> None:
    tables = {"work_orders": [SourceColumn("id", "BIGINT", False, 1)]}
    assert schema_hash(tables) == schema_hash(tables)


def test_jsonb_conversion_preserves_valid_json_and_wraps_invalid_text() -> None:
    valid = '{"a": 1}'
    invalid = "not-json"

    assert convert_value(valid, "jsonb") == valid
    assert json.loads(convert_value(invalid, "jsonb")) == invalid


def test_sync_service_imports() -> None:
    assert MesInterfaceSyncService.__name__ == "MesInterfaceSyncService"


def test_settings_reads_aps_reader_user_from_env(monkeypatch) -> None:
    monkeypatch.setenv("SOURCE_SQLITE_PATH", "/tmp/mes.db")
    monkeypatch.setenv("MES_INTERFACE_SYNC_PASSWORD", "secret!@34")
    monkeypatch.setenv("MES_INTERFACE_APS_READER_USER", "external_aps_reader")
    monkeypatch.setenv("MES_INTERFACE_SYNC_USER", "sync_user")
    monkeypatch.setenv("MES_INTERFACE_DB_NAME", "mes_interface")
    monkeypatch.setenv("MES_INTERFACE_SYNC_SCHEDULE", "03:00,15:00")
    monkeypatch.setenv("MES_INTERFACE_SYNC_TIMEZONE", "Asia/Seoul")
    monkeypatch.setenv("MES_INTERFACE_SYNC_RUN_ON_START", "false")

    settings = Settings.from_env()

    assert settings.aps_reader_user == "external_aps_reader"
    assert settings.target_db_user == "sync_user"
    assert settings.target_db_password == "secret!@34"
    assert settings.target_db_name == "mes_interface"
    assert [item.strftime("%H:%M") for item in settings.sync_schedule] == ["03:00", "15:00"]
    assert settings.sync_timezone == "Asia/Seoul"
    assert settings.sync_run_on_start is False
