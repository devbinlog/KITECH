#!/bin/bash
# =============================================================================
# agents-workspace 서비스 상태 확인 스크립트
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/services.env" ]; then
    source "$SCRIPT_DIR/services.env"
fi

PORT_CELL_MES="${PORT_CELL_MES:-8000}"
PORT_NL_ROUTER="${PORT_NL_ROUTER:-8001}"
PORT_CELL_SCHEDULER="${PORT_CELL_SCHEDULER:-8002}"
PORT_FRONTEND="${PORT_FRONTEND:-3000}"
REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo " Service Status"
echo "=========================================="
echo ""

check_service() {
    local name=$1
    local port=$2
    local health_path=${3:-/health}
    
    if curl -s "http://127.0.0.1:$port$health_path" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name (port $port) - Running"
    else
        echo -e "${RED}✗${NC} $name (port $port) - Not running"
    fi
}

check_service "Cell-MES" $PORT_CELL_MES
check_service "NL-Router" $PORT_NL_ROUTER
check_service "Cell-Scheduler" $PORT_CELL_SCHEDULER

if curl -s "http://127.0.0.1:$PORT_FRONTEND" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} MES Frontend (port $PORT_FRONTEND) - Running"
else
    echo -e "${RED}✗${NC} MES Frontend (port $PORT_FRONTEND) - Not running"
fi

if nc -z "$REDIS_HOST" "$REDIS_PORT" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis ($REDIS_HOST:$REDIS_PORT) - Reachable"
else
    echo -e "${YELLOW}!${NC} Redis ($REDIS_HOST:$REDIS_PORT) - Not reachable"
fi

echo ""
echo "=========================================="
echo " Port Configuration"
echo "=========================================="
echo "  PORT_CELL_MES=$PORT_CELL_MES"
echo "  PORT_NL_ROUTER=$PORT_NL_ROUTER"
echo "  PORT_CELL_SCHEDULER=$PORT_CELL_SCHEDULER"
echo "  PORT_FRONTEND=$PORT_FRONTEND"
echo "  REDIS_HOST=$REDIS_HOST"
echo "  REDIS_PORT=$REDIS_PORT"
echo ""
