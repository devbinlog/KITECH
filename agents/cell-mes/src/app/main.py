"""FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .api.v1.api import api_router
from .db.session import AsyncSessionLocal
from .services.polling_service import poll_all_equipments
from .services.dispatch_service import run_dispatch_loop

logger = logging.getLogger(__name__)


async def _background_polling_loop():
    """미들웨어에서 설비 상태를 주기적으로 폴링하는 백그라운드 루프."""
    interval = settings.EQUIPMENT_POLL_INTERVAL_SEC
    logger.info("설비 폴링 시작 (간격: %ds)", interval)
    while True:
        try:
            async with AsyncSessionLocal() as db:
                updated = await poll_all_equipments(db)
                if updated:
                    logger.debug("%d개 설비 상태 갱신 완료", len(updated))
        except asyncio.CancelledError:
            # 앱 종료 시 정상 취소
            break
        except Exception as e:
            # 폴링 오류는 로그만 남기고 루프 계속 유지
            logger.warning("폴링 루프 오류 (재시도 예정): %s", e)
        await asyncio.sleep(interval)
    logger.info("설비 폴링 루프 종료")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: 백그라운드 폴링 및 디스패치 데몬 태스크 시작
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    polling_task = asyncio.create_task(_background_polling_loop())
    dispatch_task = asyncio.create_task(run_dispatch_loop())
    yield
    # Shutdown: 태스크 정상 종료
    polling_task.cancel()
    dispatch_task.cancel()
    try:
        await polling_task
        await dispatch_task
    except asyncio.CancelledError:
        pass
    print(f"Shutting down {settings.APP_NAME}")


from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Manufacturing Execution System for smart factory production management",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Upload directory setup
UPLOAD_DIR = settings.UPLOAD_DIR
if not os.path.isabs(UPLOAD_DIR):
    UPLOAD_DIR = os.path.join(os.getcwd(), UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# CORS middleware
# "*" 와일드카드 사용 시 credentials=False 필요 (브라우저 보안 정책)
_allow_all = "*" in settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else settings.CORS_ORIGINS,
    allow_credentials=not _allow_all,  # 와일드카드 시 credentials 비활성화
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/capabilities", tags=["meta"])
async def get_capabilities():
    """Expose tools for agent-orchestrator's dynamic tool_loader."""
    return {
        "service": "cell-mes",
        "version": settings.APP_VERSION,
        "description": "Manufacturing Execution System backend",
        "tools": [
            # Master data
            {
                "name": "list_products",
                "description": "Get list of products with optional filtering. Use when user asks about product catalog.",
                "endpoint": {"method": "GET", "path": "/api/v1/masters/products"},
                "idempotent": True,
            },
            {
                "name": "list_equipments",
                "description": "Get list of factory equipment with status. Use for equipment monitoring queries.",
                "endpoint": {"method": "GET", "path": "/api/v1/masters/equipments"},
                "idempotent": True,
            },
            {
                "name": "list_routings",
                "description": "Get manufacturing routings (process flows) for a product by product_id.",
                "endpoint": {"method": "GET", "path": "/api/v1/masters/products/{product_id}/routings"},
                "idempotent": True,
            },
            {
                "name": "list_scenarios",
                "description": "Get logistics scenarios (n8n workflows) defined in MES.",
                "endpoint": {"method": "GET", "path": "/api/v1/masters/scenarios"},
                "idempotent": True,
            },
            # Production
            {
                "name": "list_work_orders",
                "description": "Get production work orders. Filter by status/date for queries about ongoing production.",
                "endpoint": {"method": "GET", "path": "/api/v1/production/orders"},
                "idempotent": True,
            },
            {
                "name": "list_production_results",
                "description": "Get production results / actuals. Use for performance/throughput queries.",
                "endpoint": {"method": "GET", "path": "/api/v1/production/results"},
                "idempotent": True,
            },
            # Quality
            {
                "name": "list_inspection_results",
                "description": "Get quality inspection results. Use for quality / defect / SPC queries.",
                "endpoint": {"method": "GET", "path": "/api/v1/inspection-results"},
                "idempotent": True,
            },
            {
                "name": "list_ncrs",
                "description": "Get Non-Conformance Reports (NCR). Use for quality issues / corrective action queries.",
                "endpoint": {"method": "GET", "path": "/api/v1/ncr"},
                "idempotent": True,
            },
            # Analytics
            {
                "name": "get_equipment_utilization",
                "description": "Calculate equipment utilization rate over a time range. Use for OEE / availability queries.",
                "endpoint": {"method": "GET", "path": "/api/v1/analytics/equipment-utilization"},
                "idempotent": True,
            },
            # Alarms
            {
                "name": "list_alarms",
                "description": "Get equipment alarms (active or historical).",
                "endpoint": {"method": "GET", "path": "/api/v1/alarms"},
                "idempotent": True,
            },
        ],
    }
