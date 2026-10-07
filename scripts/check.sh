#!/usr/bin/env bash
# check.sh — Pre-commit / pre-push integrated quality check.
# Mac/Linux compatible.
#
# Usage:
#   ./scripts/check.sh           # full check (lint + types + tests)
#   ./scripts/check.sh --fast    # skip slow tests (just lint + types)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

FAST=false
for arg in "$@"; do
  case "$arg" in
    --fast) FAST=true ;;
    -h|--help)
      echo "Usage: $0 [--fast]"
      exit 0
      ;;
  esac
done

cd "$ROOT_DIR"

echo "==[1/4]== Python lint (ruff check) =="
uv run ruff check agents/ shared/ orchestrator/ || { echo "❌ ruff check failed"; exit 1; }

echo "==[2/4]== Python format (ruff format --check) =="
uv run ruff format --check agents/ shared/ orchestrator/ || { echo "❌ ruff format check failed (run 'make format' to fix)"; exit 1; }

echo "==[3/4]== TypeScript typecheck (frontend) =="
if [ -d "agents/cell-mes/frontend/node_modules" ]; then
  cd agents/cell-mes/frontend
  npx tsc --noEmit || { echo "❌ tsc failed"; exit 1; }
  cd "$ROOT_DIR"
else
  echo "⚠️  frontend/node_modules not found — run 'cd agents/cell-mes/frontend && npm install' first. Skipping tsc."
fi

if [ "$FAST" = false ]; then
  echo "==[4/4]== Backend tests (pytest) =="
  cd agents/cell-mes
  uv run pytest -q || { echo "❌ pytest failed"; exit 1; }
  cd "$ROOT_DIR"
else
  echo "==[4/4]== SKIP (--fast)"
fi

echo ""
echo "✅ All checks passed."
