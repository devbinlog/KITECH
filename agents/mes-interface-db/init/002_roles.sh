#!/bin/sh
set -eu

: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${MES_INTERFACE_SYNC_PASSWORD:?MES_INTERFACE_SYNC_PASSWORD is required}"
: "${MES_INTERFACE_APS_READER_PASSWORD:?MES_INTERFACE_APS_READER_PASSWORD is required}"

MES_INTERFACE_SYNC_USER="${MES_INTERFACE_SYNC_USER:-if_sync_writer}"
MES_INTERFACE_APS_READER_USER="${MES_INTERFACE_APS_READER_USER:-aps_user}"

psql \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set=db_name="$POSTGRES_DB" \
  --set=sync_user="$MES_INTERFACE_SYNC_USER" \
  --set=sync_password="$MES_INTERFACE_SYNC_PASSWORD" \
  --set=aps_reader_user="$MES_INTERFACE_APS_READER_USER" \
  --set=aps_reader_password="$MES_INTERFACE_APS_READER_PASSWORD" \
  --set=ON_ERROR_STOP=1 <<'SQL'
SELECT format('CREATE ROLE %I LOGIN', :'sync_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'sync_user')
\gexec

SELECT format('CREATE ROLE %I LOGIN', :'aps_reader_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'aps_reader_user')
\gexec

SELECT format('ALTER ROLE %I PASSWORD %L', :'sync_user', :'sync_password')
\gexec

SELECT format('ALTER ROLE %I PASSWORD %L', :'aps_reader_user', :'aps_reader_password')
\gexec

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'db_name', :'sync_user')
\gexec

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'db_name', :'aps_reader_user')
\gexec

SELECT format('GRANT USAGE, CREATE ON SCHEMA mes_src TO %I', :'sync_user')
\gexec

SELECT format('GRANT USAGE, CREATE ON SCHEMA mes_if TO %I', :'sync_user')
\gexec

SELECT format('GRANT USAGE ON SCHEMA if_admin TO %I', :'sync_user')
\gexec

SELECT format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA if_admin TO %I', :'sync_user')
\gexec

SELECT format('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA if_admin TO %I', :'sync_user')
\gexec

SELECT format('GRANT USAGE ON SCHEMA mes_if TO %I', :'aps_reader_user')
\gexec

SELECT format('GRANT SELECT ON ALL TABLES IN SCHEMA mes_if TO %I', :'aps_reader_user')
\gexec

SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA mes_src GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO %I',
    :'sync_user',
    :'sync_user'
)
\gexec

SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA mes_if GRANT SELECT ON TABLES TO %I',
    :'sync_user',
    :'aps_reader_user'
)
\gexec
SQL
