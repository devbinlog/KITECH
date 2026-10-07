CREATE SCHEMA IF NOT EXISTS mes_src;
CREATE SCHEMA IF NOT EXISTS mes_if;
CREATE SCHEMA IF NOT EXISTS aps_if;
CREATE SCHEMA IF NOT EXISTS if_admin;

REVOKE ALL ON SCHEMA public FROM PUBLIC;

CREATE TABLE IF NOT EXISTS if_admin.sync_batches (
    batch_id text PRIMARY KEY,
    status text NOT NULL,
    source_path text NOT NULL,
    schema_hash text,
    table_count integer NOT NULL DEFAULT 0,
    row_count bigint NOT NULL DEFAULT 0,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    error_message text,
    CONSTRAINT sync_batches_status_check CHECK (
        status IN ('STARTED', 'SUCCESS', 'FAILED')
    )
);

CREATE TABLE IF NOT EXISTS if_admin.sync_table_stats (
    id bigserial PRIMARY KEY,
    batch_id text NOT NULL REFERENCES if_admin.sync_batches(batch_id) ON DELETE CASCADE,
    source_table text NOT NULL,
    target_table text NOT NULL,
    row_count bigint NOT NULL DEFAULT 0,
    duration_ms integer NOT NULL DEFAULT 0,
    status text NOT NULL,
    error_message text,
    synced_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT sync_table_stats_status_check CHECK (
        status IN ('SUCCESS', 'FAILED', 'SKIPPED')
    )
);

CREATE INDEX IF NOT EXISTS idx_sync_table_stats_batch_id
    ON if_admin.sync_table_stats(batch_id);

CREATE TABLE IF NOT EXISTS if_admin.schema_snapshots (
    batch_id text PRIMARY KEY REFERENCES if_admin.sync_batches(batch_id) ON DELETE CASCADE,
    schema_hash text NOT NULL,
    snapshot jsonb NOT NULL,
    captured_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS if_admin.schema_changes (
    id bigserial PRIMARY KEY,
    batch_id text REFERENCES if_admin.sync_batches(batch_id) ON DELETE SET NULL,
    object_type text NOT NULL,
    table_name text,
    column_name text,
    change_type text NOT NULL,
    detail jsonb NOT NULL DEFAULT '{}'::jsonb,
    detected_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_schema_changes_detected_at
    ON if_admin.schema_changes(detected_at);

CREATE TABLE IF NOT EXISTS if_admin.sync_errors (
    id bigserial PRIMARY KEY,
    batch_id text REFERENCES if_admin.sync_batches(batch_id) ON DELETE SET NULL,
    source_table text,
    error_message text NOT NULL,
    error_detail text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sync_errors_batch_id
    ON if_admin.sync_errors(batch_id);

CREATE TABLE IF NOT EXISTS if_admin.sync_locks (
    lock_name text PRIMARY KEY,
    locked_by text NOT NULL,
    locked_at timestamptz NOT NULL DEFAULT now()
);
