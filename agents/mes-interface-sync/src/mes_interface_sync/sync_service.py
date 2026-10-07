from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import asyncpg

from .config import Settings
from .schema import (
    META_COLUMNS,
    SOURCE_SCHEMA,
    SourceColumn,
    add_column_sql,
    add_meta_column_sql,
    convert_value,
    create_index_sql,
    create_table_sql,
    is_excluded_table,
    normalize_schema_snapshot,
    quote_ident,
    schema_hash,
)
from .view_config import InterfaceViewConfigSet

logger = logging.getLogger(__name__)


class MesInterfaceSyncService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.view_config = InterfaceViewConfigSet.load(settings.interface_view_config_path)

    async def run_once(self) -> str:
        batch_id = str(uuid4())
        snapshot_path: Path | None = None
        started_at = time.monotonic()

        conn = await self._connect()
        try:
            await self._insert_batch_started(conn, batch_id)
            locked = await conn.fetchval("SELECT pg_try_advisory_lock(hashtext('mes_interface_sync'))")
            if not locked:
                raise RuntimeError("Another MES interface sync batch is already running")

            try:
                snapshot_path = self._create_sqlite_snapshot(batch_id)
                tables = self._read_sqlite_schema(snapshot_path)
                current_hash = schema_hash(tables)
                await self._record_schema_change_if_needed(conn, batch_id, current_hash, tables)

                total_rows = 0
                async with conn.transaction():
                    await conn.execute(
                        """
                        INSERT INTO if_admin.schema_snapshots (
                            batch_id, schema_hash, snapshot
                        )
                        VALUES ($1, $2, $3::jsonb)
                        ON CONFLICT (batch_id) DO UPDATE
                        SET schema_hash = EXCLUDED.schema_hash,
                            snapshot = EXCLUDED.snapshot,
                            captured_at = now()
                        """,
                        batch_id,
                        current_hash,
                        json.dumps(normalize_schema_snapshot(tables), ensure_ascii=True),
                    )

                    for table_name, columns in tables.items():
                        table_started_at = time.monotonic()
                        row_count = await self._sync_table(conn, snapshot_path, batch_id, table_name, columns)
                        total_rows += row_count
                        await conn.execute(
                            """
                            INSERT INTO if_admin.sync_table_stats (
                                batch_id,
                                source_table,
                                target_table,
                                row_count,
                                duration_ms,
                                status
                            )
                            VALUES ($1, $2, $3, $4, $5, 'SUCCESS')
                            """,
                            batch_id,
                            table_name,
                            f"{SOURCE_SCHEMA}.{table_name}",
                            row_count,
                            int((time.monotonic() - table_started_at) * 1000),
                        )

                    await conn.execute(
                        """
                        UPDATE if_admin.sync_batches
                        SET status = 'SUCCESS',
                            schema_hash = $2,
                            table_count = $3,
                            row_count = $4,
                            completed_at = now(),
                            error_message = NULL
                        WHERE batch_id = $1
                        """,
                        batch_id,
                        current_hash,
                        len(tables),
                        total_rows,
                    )

                logger.info(
                    "MES interface sync completed batch_id=%s tables=%s rows=%s duration_ms=%s",
                    batch_id,
                    len(tables),
                    total_rows,
                    int((time.monotonic() - started_at) * 1000),
                )
                return batch_id
            finally:
                await conn.execute("SELECT pg_advisory_unlock(hashtext('mes_interface_sync'))")
        except Exception as exc:
            logger.exception("MES interface sync failed batch_id=%s", batch_id)
            await self._record_batch_failed(conn, batch_id, exc)
            raise
        finally:
            await conn.close()
            if snapshot_path is not None:
                self._cleanup_snapshot(snapshot_path)

    async def _connect(self) -> asyncpg.Connection:
        if self.settings.target_database_url:
            return await asyncpg.connect(self.settings.target_database_url)
        return await asyncpg.connect(
            host=self.settings.target_db_host,
            port=self.settings.target_db_port,
            database=self.settings.target_db_name,
            user=self.settings.target_db_user,
            password=self.settings.target_db_password,
        )

    def _create_sqlite_snapshot(self, batch_id: str) -> Path:
        source_path = self.settings.source_sqlite_path
        if not source_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {source_path}")

        self.settings.snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = self.settings.snapshot_dir / f"mes-{batch_id}.db"

        source_uri = f"file:{source_path}?mode=ro"
        with sqlite3.connect(source_uri, uri=True, timeout=30) as source:
            with sqlite3.connect(snapshot_path) as target:
                source.backup(target)

        return snapshot_path

    def _cleanup_snapshot(self, snapshot_path: Path) -> None:
        try:
            snapshot_path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to remove SQLite snapshot: %s", snapshot_path)

    def _read_sqlite_schema(self, snapshot_path: Path) -> dict[str, list[SourceColumn]]:
        with sqlite3.connect(snapshot_path) as conn:
            rows = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()

            tables: dict[str, list[SourceColumn]] = {}
            for (table_name,) in rows:
                excluded_tables = self.view_config.excluded_tables_with(self.settings.excluded_tables)
                if is_excluded_table(table_name, excluded_tables):
                    continue

                columns = [
                    SourceColumn(
                        name=row[1],
                        declared_type=row[2] or "",
                        not_null=bool(row[3]),
                        pk_position=int(row[5] or 0),
                    )
                    for row in conn.execute(f"PRAGMA table_info({quote_ident(table_name)})").fetchall()
                ]
                if columns:
                    tables[table_name] = columns

        return tables

    async def _sync_table(
        self,
        pg: asyncpg.Connection,
        snapshot_path: Path,
        batch_id: str,
        table_name: str,
        columns: list[SourceColumn],
    ) -> int:
        await self._ensure_target_table(pg, table_name, columns)
        await pg.execute(f"TRUNCATE TABLE {quote_ident(SOURCE_SCHEMA)}.{quote_ident(table_name)}")

        row_count = await self._copy_rows(pg, snapshot_path, batch_id, table_name, columns)
        view_sql = self.view_config.create_view_sql(table_name, columns)
        if view_sql:
            await pg.execute(view_sql)
            view_name = self.view_config.view_name_for_table(table_name)
            await pg.execute(
                f"GRANT SELECT ON {quote_ident('mes_if')}.{quote_ident(view_name)} "
                f"TO {quote_ident(self.settings.aps_reader_user)}"
            )
        return row_count

    async def _ensure_target_table(
        self,
        pg: asyncpg.Connection,
        table_name: str,
        columns: list[SourceColumn],
    ) -> None:
        await pg.execute(create_table_sql(table_name, columns))

        existing_columns = {
            row["column_name"]
            for row in await pg.fetch(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = $1
                  AND table_name = $2
                """,
                SOURCE_SCHEMA,
                table_name,
            )
        }

        for column in columns:
            if column.name not in existing_columns:
                await pg.execute(add_column_sql(table_name, column))
        for column_name, postgres_type in META_COLUMNS:
            if column_name not in existing_columns:
                await pg.execute(add_meta_column_sql(table_name, column_name, postgres_type))

        pk_columns = [column.name for column in columns if column.pk_position > 0]
        for column_name in pk_columns:
            await pg.execute(create_index_sql(table_name, column_name))
        await pg.execute(create_index_sql(table_name, "_if_batch_id"))

    async def _copy_rows(
        self,
        pg: asyncpg.Connection,
        snapshot_path: Path,
        batch_id: str,
        table_name: str,
        columns: list[SourceColumn],
    ) -> int:
        source_column_names = [column.name for column in columns]
        target_column_names = source_column_names + [name for name, _ in META_COLUMNS]
        placeholders = ", ".join(f"${index}" for index in range(1, len(target_column_names) + 1))
        insert_sql = (
            f"INSERT INTO {quote_ident(SOURCE_SCHEMA)}.{quote_ident(table_name)} "
            f"({', '.join(quote_ident(name) for name in target_column_names)}) "
            f"VALUES ({placeholders})"
        )

        total = 0
        pk_columns = [column.name for column in columns if column.pk_position > 0]
        with sqlite3.connect(snapshot_path) as sqlite_conn:
            sqlite_conn.row_factory = sqlite3.Row
            cursor = sqlite_conn.execute(
                f"SELECT {', '.join(quote_ident(name) for name in source_column_names)} "
                f"FROM {quote_ident(table_name)}"
            )

            batch: list[tuple[Any, ...]] = []
            while True:
                source_rows = cursor.fetchmany(self.settings.batch_size)
                if not source_rows:
                    break

                for row in source_rows:
                    row_values = [
                        convert_value(row[column.name], column.postgres_type) for column in columns
                    ]
                    source_pk = self._source_pk(row, pk_columns)
                    row_values.extend([batch_id, None, table_name, source_pk])
                    batch.append(tuple(row_values))

                if batch:
                    await pg.executemany(insert_sql, batch)
                    total += len(batch)
                    batch = []

        await pg.execute(
            f"UPDATE {quote_ident(SOURCE_SCHEMA)}.{quote_ident(table_name)} "
            "SET _if_synced_at = now() "
            "WHERE _if_batch_id = $1",
            batch_id,
        )
        return total

    def _source_pk(self, row: sqlite3.Row, pk_columns: list[str]) -> str | None:
        if not pk_columns:
            return None
        payload = {column: row[column] for column in pk_columns}
        return json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)

    async def _insert_batch_started(self, pg: asyncpg.Connection, batch_id: str) -> None:
        await pg.execute(
            """
            INSERT INTO if_admin.sync_batches (batch_id, status, source_path)
            VALUES ($1, 'STARTED', $2)
            """,
            batch_id,
            str(self.settings.source_sqlite_path),
        )

    async def _record_schema_change_if_needed(
        self,
        pg: asyncpg.Connection,
        batch_id: str,
        current_hash: str,
        tables: dict[str, list[SourceColumn]],
    ) -> None:
        previous_hash = await pg.fetchval(
            """
            SELECT schema_hash
            FROM if_admin.sync_batches
            WHERE status = 'SUCCESS'
              AND schema_hash IS NOT NULL
            ORDER BY completed_at DESC
            LIMIT 1
            """
        )
        if previous_hash and previous_hash != current_hash:
            await pg.execute(
                """
                INSERT INTO if_admin.schema_changes (
                    batch_id,
                    object_type,
                    change_type,
                    detail
                )
                VALUES ($1, 'schema', 'SCHEMA_HASH_CHANGED', $2::jsonb)
                """,
                batch_id,
                json.dumps(
                    {
                        "previous_hash": previous_hash,
                        "current_hash": current_hash,
                        "tables": sorted(tables),
                    },
                    ensure_ascii=True,
                ),
            )

    async def _record_batch_failed(
        self,
        pg: asyncpg.Connection,
        batch_id: str,
        exc: Exception,
    ) -> None:
        message = str(exc) or exc.__class__.__name__
        await pg.execute(
            """
            UPDATE if_admin.sync_batches
            SET status = 'FAILED',
                completed_at = now(),
                error_message = $2
            WHERE batch_id = $1
            """,
            batch_id,
            message,
        )
        await pg.execute(
            """
            INSERT INTO if_admin.sync_errors (batch_id, error_message, error_detail)
            VALUES ($1, $2, $3)
            """,
            batch_id,
            message,
            repr(exc),
        )
