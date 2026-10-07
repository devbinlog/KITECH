from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .schema import (
    INTERFACE_SCHEMA,
    META_COLUMNS,
    SOURCE_SCHEMA,
    SENSITIVE_COLUMNS_BY_TABLE,
    SourceColumn,
    interface_view_name,
    quote_ident,
)


@dataclass(frozen=True)
class InterfaceColumnConfig:
    name: str
    source: str | None = None
    source_candidates: tuple[str, ...] = ()
    required: bool = False
    default: Any = None
    has_default: bool = False

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InterfaceColumnConfig":
        name = payload.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("View column config requires a non-empty 'name'")

        source = payload.get("source")
        if source is not None and not isinstance(source, str):
            raise ValueError(f"Column {name} has invalid 'source'")

        candidates = payload.get("source_candidates", ())
        if candidates is None:
            candidates = ()
        if not isinstance(candidates, list | tuple) or not all(
            isinstance(item, str) and item for item in candidates
        ):
            raise ValueError(f"Column {name} has invalid 'source_candidates'")

        return cls(
            name=name,
            source=source,
            source_candidates=tuple(candidates),
            required=bool(payload.get("required", False)),
            default=payload.get("default"),
            has_default="default" in payload,
        )

    @property
    def candidates(self) -> tuple[str, ...]:
        values: list[str] = []
        if self.source:
            values.append(self.source)
        values.extend(self.source_candidates)
        return tuple(dict.fromkeys(values))


@dataclass(frozen=True)
class InterfaceViewConfig:
    name: str
    source_table: str
    description: str = ""
    exclude_columns: frozenset[str] = frozenset()
    columns: tuple[InterfaceColumnConfig, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InterfaceViewConfig":
        name = payload.get("name")
        source_table = payload.get("source_table")
        if not isinstance(name, str) or not name:
            raise ValueError("View config requires a non-empty 'name'")
        if not isinstance(source_table, str) or not source_table:
            raise ValueError(f"View {name} requires a non-empty 'source_table'")

        exclude_columns = payload.get("exclude_columns", ())
        if exclude_columns is None:
            exclude_columns = ()
        if not isinstance(exclude_columns, list | tuple) or not all(
            isinstance(item, str) and item for item in exclude_columns
        ):
            raise ValueError(f"View {name} has invalid 'exclude_columns'")

        columns = payload.get("columns", ())
        if not isinstance(columns, list | tuple):
            raise ValueError(f"View {name} has invalid 'columns'")

        return cls(
            name=name,
            source_table=source_table,
            description=str(payload.get("description", "")),
            exclude_columns=frozenset(item.lower() for item in exclude_columns),
            columns=tuple(InterfaceColumnConfig.from_dict(item) for item in columns),
        )


@dataclass(frozen=True)
class InterfaceViewDefaults:
    include_meta_columns: bool = True
    create_auto_views_for_unmapped_tables: bool = True
    on_missing_required_column: str = "fail"
    on_missing_optional_column: str = "null"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InterfaceViewDefaults":
        return cls(
            include_meta_columns=bool(payload.get("include_meta_columns", True)),
            create_auto_views_for_unmapped_tables=bool(
                payload.get("create_auto_views_for_unmapped_tables", True)
            ),
            on_missing_required_column=str(payload.get("on_missing_required_column", "fail")),
            on_missing_optional_column=str(payload.get("on_missing_optional_column", "null")),
        )


@dataclass(frozen=True)
class InterfaceViewConfigSet:
    defaults: InterfaceViewDefaults = field(default_factory=InterfaceViewDefaults)
    exclude_tables: frozenset[str] = frozenset()
    sensitive_columns: dict[str, frozenset[str]] = field(default_factory=dict)
    views_by_source_table: dict[str, InterfaceViewConfig] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None) -> "InterfaceViewConfigSet":
        if path is None or not path.exists():
            return cls(sensitive_columns=SENSITIVE_COLUMNS_BY_TABLE)

        with path.open("r", encoding="utf-8") as file:
            payload = yaml.safe_load(file) or {}

        if not isinstance(payload, dict):
            raise ValueError(f"Interface View config must be a mapping: {path}")

        defaults = InterfaceViewDefaults.from_dict(payload.get("defaults", {}))
        exclude_tables = frozenset(
            str(item).lower() for item in payload.get("exclude_tables", []) if str(item).strip()
        )

        sensitive_columns: dict[str, frozenset[str]] = {
            table: frozenset(columns) for table, columns in SENSITIVE_COLUMNS_BY_TABLE.items()
        }
        for table_name, columns in (payload.get("sensitive_columns", {}) or {}).items():
            if not isinstance(columns, list | tuple):
                raise ValueError(f"sensitive_columns.{table_name} must be a list")
            current = set(sensitive_columns.get(str(table_name).lower(), frozenset()))
            current.update(str(column).lower() for column in columns)
            sensitive_columns[str(table_name).lower()] = frozenset(current)

        views = tuple(
            InterfaceViewConfig.from_dict(item) for item in payload.get("views", [])
        )
        views_by_source_table = {view.source_table.lower(): view for view in views}

        return cls(
            defaults=defaults,
            exclude_tables=exclude_tables,
            sensitive_columns=sensitive_columns,
            views_by_source_table=views_by_source_table,
        )

    def excluded_tables_with(self, explicit_excludes: frozenset[str]) -> frozenset[str]:
        return frozenset(set(explicit_excludes) | set(self.exclude_tables))

    def create_view_sql(self, table_name: str, columns: list[SourceColumn]) -> str | None:
        configured_view = self.views_by_source_table.get(table_name.lower())
        if configured_view:
            return self._create_configured_view_sql(configured_view, columns)
        if not self.defaults.create_auto_views_for_unmapped_tables:
            return None
        return self._create_auto_view_sql(table_name, columns)

    def view_name_for_table(self, table_name: str) -> str:
        configured_view = self.views_by_source_table.get(table_name.lower())
        if configured_view:
            return configured_view.name
        return interface_view_name(table_name)

    def _create_auto_view_sql(self, table_name: str, columns: list[SourceColumn]) -> str:
        hidden_columns = self.sensitive_columns.get(table_name.lower(), frozenset())
        visible_columns = [
            column.name for column in columns if column.name.lower() not in hidden_columns
        ]
        if self.defaults.include_meta_columns:
            visible_columns.extend(name for name, _ in META_COLUMNS)
        select_list = ", ".join(quote_ident(column_name) for column_name in visible_columns)
        view_name = interface_view_name(table_name)
        return (
            f"DROP VIEW IF EXISTS {quote_ident(INTERFACE_SCHEMA)}.{quote_ident(view_name)};\n"
            f"CREATE VIEW {quote_ident(INTERFACE_SCHEMA)}.{quote_ident(view_name)} AS\n"
            f"SELECT {select_list}\n"
            f"FROM {quote_ident(SOURCE_SCHEMA)}.{quote_ident(table_name)};"
        )

    def _create_configured_view_sql(
        self,
        view: InterfaceViewConfig,
        columns: list[SourceColumn],
    ) -> str:
        source_columns = {column.name.lower(): column.name for column in columns}
        hidden_columns = set(self.sensitive_columns.get(view.source_table.lower(), frozenset()))
        hidden_columns.update(view.exclude_columns)

        select_parts: list[str] = []
        for column in view.columns:
            if column.name.lower() in hidden_columns:
                continue
            source_column = self._resolve_source_column(column, source_columns)
            if source_column is not None:
                select_parts.append(f"{quote_ident(source_column)} AS {quote_ident(column.name)}")
            elif column.has_default:
                select_parts.append(f"{sql_literal(column.default)} AS {quote_ident(column.name)}")
            elif column.required and self.defaults.on_missing_required_column == "fail":
                raise ValueError(
                    f"Required column {column.name} for view {view.name} is missing from "
                    f"source table {view.source_table}. Candidates: {', '.join(column.candidates)}"
                )
            else:
                select_parts.append(f"NULL AS {quote_ident(column.name)}")

        if self.defaults.include_meta_columns:
            select_parts.extend(
                f"{quote_ident(column_name)} AS {quote_ident(column_name)}"
                for column_name, _ in META_COLUMNS
            )

        select_list = ", ".join(select_parts)
        return (
            f"DROP VIEW IF EXISTS {quote_ident(INTERFACE_SCHEMA)}.{quote_ident(view.name)};\n"
            f"CREATE VIEW {quote_ident(INTERFACE_SCHEMA)}.{quote_ident(view.name)} AS\n"
            f"SELECT {select_list}\n"
            f"FROM {quote_ident(SOURCE_SCHEMA)}.{quote_ident(view.source_table)};"
        )

    def _resolve_source_column(
        self,
        column: InterfaceColumnConfig,
        source_columns: dict[str, str],
    ) -> str | None:
        for candidate in column.candidates:
            resolved = source_columns.get(candidate.lower())
            if resolved is not None:
                return resolved
        return None


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int | float):
        return str(value)
    return "'" + json.dumps(str(value), ensure_ascii=True)[1:-1].replace("'", "''") + "'"
