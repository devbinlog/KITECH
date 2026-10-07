#!/usr/bin/env bash
# seed-mes-db.sh — Re-create cell-mes SQLite DB from latest migrations + fixtures.
# Both Mac and Linux compatible.
#
# Usage:
#   ./scripts/seed-mes-db.sh              # default — reset & seed
#   ./scripts/seed-mes-db.sh --reset-only # only delete DB
#   ./scripts/seed-mes-db.sh --no-reset   # skip reset, only seed
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DB_PATH="${ROOT_DIR}/agents/cell-mes/data/mes.db"
ARCHIVE_DIR="${ROOT_DIR}/agents/cell-mes/data/_archive"

RESET=true
SEED=true

for arg in "$@"; do
  case "$arg" in
    --reset-only) SEED=false ;;
    --no-reset)   RESET=false ;;
    -h|--help)
      echo "Usage: $0 [--reset-only|--no-reset]"
      exit 0
      ;;
  esac
done

mkdir -p "${ARCHIVE_DIR}"

if [ "$RESET" = true ] && [ -f "$DB_PATH" ]; then
  ts="$(date +%Y%m%d_%H%M%S)"
  backup="${ARCHIVE_DIR}/mes.db.bak.${ts}"
  echo "[seed-mes-db] backing up existing DB → ${backup}"
  cp -v "$DB_PATH" "$backup"
  rm -v "$DB_PATH"
fi

if [ "$SEED" = true ]; then
  echo "[seed-mes-db] running alembic migrations..."
  cd "${ROOT_DIR}/agents/cell-mes"
  uv run alembic upgrade head

  if [ -f "tests/fixtures/seed.py" ]; then
    echo "[seed-mes-db] applying seed fixtures..."
    uv run python tests/fixtures/seed.py
  else
    echo "[seed-mes-db] no seed.py — skipping fixtures"
  fi
fi

echo "[seed-mes-db] done. DB at ${DB_PATH}"
