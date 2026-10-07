#!/bin/bash
# =============================================================================
# agents-workspace 서비스 중지 스크립트
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/services.env" ]; then
    source "$SCRIPT_DIR/services.env"
fi

PORT_CELL_MES="${PORT_CELL_MES:-8000}"
PORT_NL_ROUTER="${PORT_NL_ROUTER:-8001}"
PORT_CELL_SCHEDULER="${PORT_CELL_SCHEDULER:-8002}"
PORT_FRONTEND="${PORT_FRONTEND:-3000}"
REDIS_CONTAINER_NAME="${REDIS_CONTAINER_NAME:-agents-workspace-redis}"
LOG_DIR="/tmp/agents-workspace"
PID_DIR="$LOG_DIR/pids"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping all services...${NC}"

stop_by_pid() {
    local name=$1
    local pid_file=$2

    if [ -f "$pid_file" ]; then
        local pid
        pid="$(cat "$pid_file")"
        if kill "$pid" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $name stopped${NC}"
        fi
        rm -f "$pid_file"
    fi
}

stop_by_pid "Cell-MES" "$PID_DIR/cell-mes.pid"
stop_by_pid "NL-Router" "$PID_DIR/nl-router.pid"
stop_by_pid "Cell-Scheduler" "$PID_DIR/cell-scheduler.pid"
stop_by_pid "MES Frontend" "$PID_DIR/cell-mes-frontend.pid"

# Fallback for uvicorn/next reload child processes.
pkill -f "port $PORT_CELL_MES" 2>/dev/null || true
pkill -f "port $PORT_NL_ROUTER" 2>/dev/null || true
pkill -f "port $PORT_CELL_SCHEDULER" 2>/dev/null || true
pkill -f "next dev.*$PORT_FRONTEND" 2>/dev/null || true

if [ "${STOP_REDIS:-false}" = "true" ] && command -v docker > /dev/null 2>&1; then
    docker stop "$REDIS_CONTAINER_NAME" > /dev/null 2>&1 && echo -e "${GREEN}✓ Docker Redis stopped${NC}" || true
fi

echo ""
echo -e "${GREEN}All services stopped.${NC}"
