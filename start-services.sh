#!/bin/bash
# =============================================================================
# agents-workspace 서비스 시작 스크립트
# =============================================================================
# 사용법:
#   ./start-services.sh                 # MES 개발 스택 시작
#   ./start-services.sh mes-stack        # MES + Scheduler + Router + Frontend 시작
#   ./start-services.sh mes              # Cell-MES만 시작
#   ./start-services.sh router           # NL-Router만 시작
#   ./start-services.sh scheduler        # Cell-Scheduler만 시작
#   ./start-services.sh frontend         # MES Frontend만 시작
#   ./start-services.sh redis            # Docker Redis만 시작
#   ./start-services.sh mes-stack --with-redis
#   ./start-services.sh all --with-redis # Redis 포함 전체 시작
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$SCRIPT_DIR/services.env" ]; then
    source "$SCRIPT_DIR/services.env"
fi

HOST="${HOST:-127.0.0.1}"
PORT_CELL_MES="${PORT_CELL_MES:-8000}"
PORT_NL_ROUTER="${PORT_NL_ROUTER:-8001}"
PORT_CELL_SCHEDULER="${PORT_CELL_SCHEDULER:-8002}"
PORT_FRONTEND="${PORT_FRONTEND:-3000}"
REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_CONTAINER_NAME="${REDIS_CONTAINER_NAME:-agents-workspace-redis}"
REDIS_IMAGE="${REDIS_IMAGE:-redis:7-alpine}"
ENV="${ENV:-development}"
DEBUG="${DEBUG:-true}"
SECRET_KEY="${SECRET_KEY:-dev-secret-key}"
INTERNAL_SERVICE_KEY="${INTERNAL_SERVICE_KEY:-dev-internal-service-key}"
MIDDLEWARE_URL="${MIDDLEWARE_URL:-http://localhost:8100}"
RELOAD="${RELOAD:-true}"

LOG_DIR="/tmp/agents-workspace"
PID_DIR="$LOG_DIR/pids"
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

TARGET="${1:-mes-stack}"
WITH_REDIS="${WITH_REDIS:-false}"
if [ "${2:-}" = "--with-redis" ] || [ "$TARGET" = "redis" ]; then
    WITH_REDIS="true"
fi

command_exists() {
    command -v "$1" > /dev/null 2>&1
}

redis_available() {
    nc -z "$REDIS_HOST" "$REDIS_PORT" > /dev/null 2>&1
}

health_check() {
    local port=$1
    local path=${2:-/health}
    curl -s "http://127.0.0.1:$port$path" > /dev/null
}

reload_args() {
    if [ "$RELOAD" = "true" ]; then
        echo "--reload"
    fi
}

export_common_env() {
    export ENV
    export DEBUG
    export SECRET_KEY
    export INTERNAL_SERVICE_KEY
    export REDIS_URL="${REDIS_URL:-redis://$REDIS_HOST:$REDIS_PORT}"
    export CELL_MES_URL="${CELL_MES_URL:-http://localhost:$PORT_CELL_MES}"
    export NL_ROUTER_URL="${NL_ROUTER_URL:-http://localhost:$PORT_NL_ROUTER}"
    export CELL_SCHEDULER_URL="${CELL_SCHEDULER_URL:-http://localhost:$PORT_CELL_SCHEDULER}"
    export MIDDLEWARE_URL
    export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:$PORT_FRONTEND,http://127.0.0.1:$PORT_FRONTEND}"
}

ensure_redis() {
    if redis_available; then
        echo -e "${GREEN}✓ Redis reachable at $REDIS_HOST:$REDIS_PORT${NC}"
        return 0
    fi

    if [ "$WITH_REDIS" != "true" ]; then
        echo -e "${YELLOW}! Redis is not reachable at $REDIS_HOST:$REDIS_PORT${NC}"
        echo "  로컬 Redis 설치 없이 실행하려면: ./start-services.sh $TARGET --with-redis"
        echo "  이미 다른 Redis를 쓰려면 services.env에 REDIS_HOST/REDIS_PORT를 맞춰주세요."
        return 0
    fi

    if ! command_exists docker; then
        echo -e "${RED}✗ Docker is not installed, and Redis is not reachable.${NC}"
        return 1
    fi

    echo -e "${YELLOW}Starting Docker Redis on port $REDIS_PORT...${NC}"
    if docker ps --format '{{.Names}}' | grep -q "^$REDIS_CONTAINER_NAME$"; then
        echo -e "${GREEN}✓ Docker Redis already running ($REDIS_CONTAINER_NAME)${NC}"
    elif docker ps -a --format '{{.Names}}' | grep -q "^$REDIS_CONTAINER_NAME$"; then
        docker start "$REDIS_CONTAINER_NAME" > /dev/null
        echo -e "${GREEN}✓ Docker Redis started ($REDIS_CONTAINER_NAME)${NC}"
    else
        docker run -d --name "$REDIS_CONTAINER_NAME" -p "$REDIS_PORT:6379" "$REDIS_IMAGE" > /dev/null
        echo -e "${GREEN}✓ Docker Redis created ($REDIS_CONTAINER_NAME)${NC}"
    fi
}

start_mes() {
    export_common_env
    ensure_redis

    echo -e "${YELLOW}Starting Cell-MES on port $PORT_CELL_MES...${NC}"
    cd "$SCRIPT_DIR/agents/cell-mes"
    pkill -f "port $PORT_CELL_MES" 2>/dev/null || true
    sleep 1
    nohup uv run uvicorn src.app.main:app --host "$HOST" --port "$PORT_CELL_MES" $(reload_args) > "$LOG_DIR/cell-mes.log" 2>&1 &
    echo $! > "$PID_DIR/cell-mes.pid"
    sleep 3
    if health_check "$PORT_CELL_MES"; then
        echo -e "${GREEN}✓ Cell-MES running on :$PORT_CELL_MES${NC}"
    else
        echo -e "${RED}✗ Cell-MES failed to start${NC}"
        tail -10 "$LOG_DIR/cell-mes.log"
        return 1
    fi
}

start_router() {
    export_common_env
    ensure_redis

    echo -e "${YELLOW}Starting NL-Router on port $PORT_NL_ROUTER...${NC}"
    cd "$SCRIPT_DIR/agents/nl-router"
    pkill -f "port $PORT_NL_ROUTER" 2>/dev/null || true
    sleep 1
    nohup uv run uvicorn src.app.main:app --host "$HOST" --port "$PORT_NL_ROUTER" $(reload_args) > "$LOG_DIR/nl-router.log" 2>&1 &
    echo $! > "$PID_DIR/nl-router.pid"
    sleep 3
    if health_check "$PORT_NL_ROUTER"; then
        echo -e "${GREEN}✓ NL-Router running on :$PORT_NL_ROUTER${NC}"
    else
        echo -e "${RED}✗ NL-Router failed to start${NC}"
        tail -10 "$LOG_DIR/nl-router.log"
        return 1
    fi
}

start_scheduler() {
    export_common_env
    ensure_redis

    echo -e "${YELLOW}Starting Cell-Scheduler on port $PORT_CELL_SCHEDULER...${NC}"
    cd "$SCRIPT_DIR/agents/cell-scheduler"
    pkill -f "port $PORT_CELL_SCHEDULER" 2>/dev/null || true
    sleep 1
    nohup uv run uvicorn src.app.main:app --host "$HOST" --port "$PORT_CELL_SCHEDULER" $(reload_args) > "$LOG_DIR/cell-scheduler.log" 2>&1 &
    echo $! > "$PID_DIR/cell-scheduler.pid"
    sleep 3
    if health_check "$PORT_CELL_SCHEDULER"; then
        echo -e "${GREEN}✓ Cell-Scheduler running on :$PORT_CELL_SCHEDULER${NC}"
    else
        echo -e "${RED}✗ Cell-Scheduler failed to start${NC}"
        tail -10 "$LOG_DIR/cell-scheduler.log"
        return 1
    fi
}

start_frontend() {
    export_common_env
    export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:$PORT_CELL_MES}"
    export NEXT_PUBLIC_AGENT_NAME="${NEXT_PUBLIC_AGENT_NAME:-cell-mes}"
    export NEXT_PUBLIC_AGENT_ORCHESTRATOR_URL="${NEXT_PUBLIC_AGENT_ORCHESTRATOR_URL:-http://localhost:8020}"
    export NEXT_PUBLIC_AGENT_WS_TOKEN="${NEXT_PUBLIC_AGENT_WS_TOKEN:-$INTERNAL_SERVICE_KEY}"

    echo -e "${YELLOW}Starting MES Frontend on port $PORT_FRONTEND...${NC}"
    cd "$SCRIPT_DIR/agents/cell-mes/frontend"
    pkill -f "next dev.*$PORT_FRONTEND" 2>/dev/null || true
    sleep 1
    nohup npm run dev -- --hostname "$HOST" --port "$PORT_FRONTEND" > "$LOG_DIR/cell-mes-frontend.log" 2>&1 &
    echo $! > "$PID_DIR/cell-mes-frontend.pid"
    sleep 4
    if curl -s "http://127.0.0.1:$PORT_FRONTEND" > /dev/null; then
        echo -e "${GREEN}✓ MES Frontend running on :$PORT_FRONTEND${NC}"
    else
        echo -e "${RED}✗ MES Frontend failed to start${NC}"
        tail -10 "$LOG_DIR/cell-mes-frontend.log"
        return 1
    fi
}

print_summary() {
    echo ""
    echo "=========================================="
    echo " Services started"
    echo "=========================================="
    echo ""
    echo "Services:"
    echo "  MES Frontend:   http://localhost:$PORT_FRONTEND"
    echo "  Cell-MES:       http://localhost:$PORT_CELL_MES"
    echo "  NL-Router:      http://localhost:$PORT_NL_ROUTER"
    echo "  Cell-Scheduler: http://localhost:$PORT_CELL_SCHEDULER"
    echo "  Redis:          redis://$REDIS_HOST:$REDIS_PORT"
    echo ""
    echo "Logs: $LOG_DIR/"
}

case "$TARGET" in
    mes)
        start_mes
        ;;
    router)
        start_router
        ;;
    scheduler)
        start_scheduler
        ;;
    frontend)
        start_frontend
        ;;
    redis)
        ensure_redis
        ;;
    mes-stack)
        echo "=========================================="
        echo " Starting MES Local Stack"
        echo "=========================================="
        if [ "$WITH_REDIS" = "true" ]; then
            ensure_redis
        fi
        start_mes
        start_scheduler
        start_router
        start_frontend
        print_summary
        ;;
    all)
        echo "=========================================="
        echo " Starting All Services"
        echo "=========================================="
        if [ "$WITH_REDIS" = "true" ]; then
            ensure_redis
        fi
        start_mes
        start_router
        start_scheduler
        start_frontend
        print_summary
        ;;
    *)
        echo "Usage: $0 [mes-stack|mes|router|scheduler|frontend|redis|all] [--with-redis]"
        exit 1
        ;;
esac
