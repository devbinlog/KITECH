from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any


SOURCE_SCHEMA = "mes_src"
INTERFACE_SCHEMA = "mes_if"
ADMIN_SCHEMA = "if_admin"

META_COLUMNS = (
    ("_if_batch_id", "text"),
    ("_if_synced_at", "timestamptz"),
    ("_if_source_table", "text"),
    ("_if_source_pk", "text"),
)

SENSITIVE_TABLE_KEYWORDS = (
    "auth",
    "credential",
    "login",
    "password",
    "secret",
    "session",
    "token",
    "user",
)

SENSITIVE_COLUMNS_BY_TABLE = {
    "equipments": {"connection_config"},
    "measurement_devices": {"connection_config"},
    "process_routing_files": {"file_path"},
    "dt_file_refs": {"path", "raw_metadata"},
    "dt_project_refs": {"raw_metadata"},
}


@dataclass(frozen=True)
class SourceColumn:
    name: str
    declared_type: str
    not_null: bool
    pk_position: int

    @property
    def postgres_type(self) -> str:
        return map_sqlite_type(self.declared_type)


def quote_ident(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def interface_view_name(source_table: str) -> str:
    return f"if_{source_table}"


def is_excluded_table(table_name: str, explicit_excludes: set[str] | frozenset[str]) -> bool:
    normalized = table_name.lower()
    if normalized in explicit_excludes:
        return True
    return any(keyword in normalized for keyword in SENSITIVE_TABLE_KEYWORDS)


def map_sqlite_type(declared_type: str) -> str:
    normalized = declared_type.upper()
    if "INT" in normalized:
        return "bigint"
    if any(token in normalized for token in ("REAL", "FLOA", "DOUB")):
        return "double precision"
    if any(token in normalized for token in ("NUMERIC", "DECIMAL")):
        return "numeric"
    if "BOOL" in normalized:
        return "boolean"
    if "BLOB" in normalized:
        return "bytea"
    if "JSON" in normalized:
        return "jsonb"
    return "text"


def normalize_schema_snapshot(
    tables: dict[str, list[SourceColumn]],
) -> list[dict[str, Any]]:
    return [
        {
            "table": table_name,
            "columns": [
                {
                    "name": column.name,
                    "declared_type": column.declared_type,
                    "postgres_type": column.postgres_type,
                    "not_null": column.not_null,
                    "pk_position": column.pk_position,
                }
                for column in columns
            ],
        }
        for table_name, columns in sorted(tables.items())
    ]


def schema_hash(tables: dict[str, list[SourceColumn]]) -> str:
    payload = json.dumps(normalize_schema_snapshot(tables), sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_table_sql(table_name: str, columns: list[SourceColumn]) -> str:
    column_defs = [
        f"{quote_ident(column.name)} {column.postgres_type}" for column in columns
    ]
    column_defs.extend(f"{quote_ident(name)} {pg_type}" for name, pg_type in META_COLUMNS)
    columns_sql = ",\n    ".join(column_defs)
    return (
        f"CREATE TABLE IF NOT EXISTS {quote_ident(SOURCE_SCHEMA)}.{quote_ident(table_name)} (\n"
        f"    {columns_sql}\n"
        ");"
    )


def add_column_sql(table_name: str, column: SourceColumn) -> str:
    return (
        f"ALTER TABLE {quote_ident(SOURCE_SCHEMA)}.{quote_ident(table_name)} "
        f"ADD COLUMN IF NOT EXISTS {quote_ident(column.name)} {column.postgres_type};"
    )


def add_meta_column_sql(table_name: str, column_name: str, postgres_type: str) -> str:
    return (
        f"ALTER TABLE {quote_ident(SOURCE_SCHEMA)}.{quote_ident(table_name)} "
        f"ADD COLUMN IF NOT EXISTS {quote_ident(column_name)} {postgres_type};"
    )


def create_index_sql(table_name: str, column_name: str) -> str:
    index_name = f"idx_mes_src_{table_name}_{column_name}".lower()
    index_name = re.sub(r"[^a-z0-9_]+", "_", index_name)[:63]
    return (
        f"CREATE INDEX IF NOT EXISTS {quote_ident(index_name)} "
        f"ON {quote_ident(SOURCE_SCHEMA)}.{quote_ident(table_name)} ({quote_ident(column_name)});"
    )


def create_interface_view_sql(table_name: str, columns: list[SourceColumn]) -> str:
    hidden_columns = SENSITIVE_COLUMNS_BY_TABLE.get(table_name.lower(), set())
    visible_columns = [column.name for column in columns if column.name.lower() not in hidden_columns]
    visible_columns.extend(name for name, _ in META_COLUMNS)
    select_list = ", ".join(quote_ident(column_name) for column_name in visible_columns)
    view_name = interface_view_name(table_name)
    return (
        f"CREATE OR REPLACE VIEW {quote_ident(INTERFACE_SCHEMA)}.{quote_ident(view_name)} AS\n"
        f"SELECT {select_list}\n"
        f"FROM {quote_ident(SOURCE_SCHEMA)}.{quote_ident(table_name)};"
    )


def convert_value(value: Any, postgres_type: str) -> Any:
    if value is None:
        return None
    if postgres_type == "text":
        return str(value)
    if postgres_type == "bigint":
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    if postgres_type in {"double precision", "numeric"}:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if postgres_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "t", "yes", "y"}:
                return True
            if normalized in {"0", "false", "f", "no", "n"}:
                return False
        return None
    if postgres_type == "bytea":
        return value if isinstance(value, bytes) else bytes(str(value), "utf-8")
    if postgres_type == "jsonb":
        if isinstance(value, str):
            try:
                json.loads(value)
                return value
            except json.JSONDecodeError:
                return json.dumps(value, ensure_ascii=True)
        return json.dumps(value, ensure_ascii=True)
    return value
