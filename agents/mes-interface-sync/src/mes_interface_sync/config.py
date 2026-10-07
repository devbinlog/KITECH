from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time
from pathlib import Path


DEFAULT_EXCLUDED_TABLES = frozenset({"users", "middleware_config", "alembic_version"})
DEFAULT_SYNC_SCHEDULE = (time(hour=2), time(hour=14))


def _parse_table_list(value: str | None) -> frozenset[str]:
    if not value:
        return DEFAULT_EXCLUDED_TABLES
    tables = {item.strip().lower() for item in value.split(",") if item.strip()}
    return frozenset(tables | DEFAULT_EXCLUDED_TABLES)


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_sync_schedule(value: str | None) -> tuple[time, ...]:
    if not value or not value.strip():
        return DEFAULT_SYNC_SCHEDULE

    schedule: list[time] = []
    for item in value.split(","):
        token = item.strip()
        if not token:
            continue

        parts = token.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid sync schedule time '{token}'. Expected HH:MM")

        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except ValueError as exc:
            raise ValueError(f"Invalid sync schedule time '{token}'. Expected HH:MM") from exc

        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError(f"Invalid sync schedule time '{token}'. Expected HH:MM")

        schedule.append(time(hour=hour, minute=minute))

    if not schedule:
        raise ValueError("MES_INTERFACE_SYNC_SCHEDULE must include at least one HH:MM time")
    return tuple(sorted(set(schedule)))


@dataclass(frozen=True)
class Settings:
    source_sqlite_path: Path
    target_database_url: str | None = None
    target_db_host: str = "mes-interface-db"
    target_db_port: int = 5432
    target_db_name: str = "mes_interface"
    target_db_user: str = "if_sync_writer"
    target_db_password: str = ""
    sync_schedule: tuple[time, ...] = DEFAULT_SYNC_SCHEDULE
    sync_timezone: str = "Asia/Seoul"
    sync_run_on_start: bool = True
    excluded_tables: frozenset[str] = DEFAULT_EXCLUDED_TABLES
    snapshot_dir: Path = Path("/tmp/mes-interface-sync")
    batch_size: int = 1_000
    log_level: str = "INFO"
    aps_reader_user: str = "aps_user"
    interface_view_config_path: Path | None = Path("config/interface_views.yaml")

    @classmethod
    def from_env(cls) -> "Settings":
        source_path = os.getenv("SOURCE_SQLITE_PATH", "/source/mes/mes.db")
        target_url = os.getenv("TARGET_DATABASE_URL")
        target_password = os.getenv("MES_INTERFACE_SYNC_PASSWORD", "")
        if not target_url and not target_password:
            raise RuntimeError("MES_INTERFACE_SYNC_PASSWORD is required")

        return cls(
            source_sqlite_path=Path(source_path),
            target_database_url=target_url,
            target_db_host=os.getenv("TARGET_DB_HOST", "mes-interface-db"),
            target_db_port=int(os.getenv("TARGET_DB_PORT", "5432")),
            target_db_name=os.getenv("TARGET_DB_NAME", os.getenv("MES_INTERFACE_DB_NAME", "mes_interface")),
            target_db_user=os.getenv("MES_INTERFACE_SYNC_USER", "if_sync_writer"),
            target_db_password=target_password,
            sync_schedule=_parse_sync_schedule(os.getenv("MES_INTERFACE_SYNC_SCHEDULE")),
            sync_timezone=os.getenv("MES_INTERFACE_SYNC_TIMEZONE", "Asia/Seoul"),
            sync_run_on_start=_parse_bool(os.getenv("MES_INTERFACE_SYNC_RUN_ON_START"), True),
            excluded_tables=_parse_table_list(os.getenv("EXCLUDED_TABLES")),
            snapshot_dir=Path(os.getenv("SNAPSHOT_DIR", "/tmp/mes-interface-sync")),
            batch_size=int(os.getenv("SYNC_BATCH_SIZE", "1000")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            aps_reader_user=os.getenv("MES_INTERFACE_APS_READER_USER", "aps_user"),
            interface_view_config_path=Path(
                os.getenv("INTERFACE_VIEW_CONFIG_PATH", "config/interface_views.yaml")
            ),
        )
