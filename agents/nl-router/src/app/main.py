"""NL Router FastAPI Application"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import query, ws
from ..nl_router_agent import get_nl_router
from ..skills import get_skill_registry
from ..ws import get_websocket_manager
from ..middleware import get_rate_limiter
from ..context import get_conversation_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting NL Router...")

    # Initialize components
    nl_router = get_nl_router(use_llm=True)
    skill_registry = get_skill_registry()
    ws_manager = get_websocket_manager()
    conv_manager = get_conversation_manager()
    get_rate_limiter()

    # Start background tasks
    await ws_manager.start()
    await conv_manager.start()

    logger.info(f"Loaded {len(skill_registry.list_all())} skills")
    logger.info("NL Router started successfully")

    yield

    # Shutdown
    logger.info("Shutting down NL Router...")
    await conv_manager.stop()
    await ws_manager.stop()
    await nl_router.close()
    logger.info("NL Router shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="NL Router Gateway",
    description="""
    Natural Language Router Gateway for NL-Driven MES

    This service processes natural language queries and:
    1. Classifies user intent
    2. Extracts relevant entities
    3. Routes to appropriate MES APIs
    4. Generates UI schemas for dynamic rendering

    ## Example Queries
    - "오늘 생산 현황 보여줘"
    - "CNC-001 설비 상태 어때?"
    - "이번 주 수율 추이"
    - "LOT-001 이력 조회"
    - "설비별 가동률 비교"
    """,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware - 개발 환경: 모든 출처 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # "*" 사용 시 credentials=False 필요
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query.router, prefix="/api/v1/nlm", tags=["NL Query"])
app.include_router(ws.router, tags=["WebSocket"])


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "service": "NL Router Gateway",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/capabilities")
async def capabilities() -> Dict[str, Any]:
    """
    Declare the stateless capabilities of this service.

    agent-orchestrator's tool_loader uses this endpoint to auto-register
    classify_intent as a callable tool.
    """
    return {
        "service": "nl-router",
        "version": "0.2.0",
        "description": "Natural language intent classification (stateless)",
        "tools": [
            {
                "name": "classify_intent",
                "description": (
                    "사용자 자연어 입력의 의도(intent)를 분류. "
                    "agent-orchestrator의 planner가 보조적으로 사용 가능."
                ),
                "endpoint": {"method": "POST", "path": "/api/v1/nlm/classify"},
                "idempotent": True,
            }
        ],
    }


@app.get("/api/v1/nlm/skills")
async def list_skills() -> Dict[str, Any]:
    """List available skills"""
    skill_registry = get_skill_registry()
    skills = skill_registry.list_all()

    return {
        "total": len(skills),
        "skills": [
            {
                "name": s.name,
                "description": s.description,
                "intents": [i.value for i in s.intents],
                "required_entities": s.required_entities,
                "optional_entities": s.optional_entities,
                "output_type": s.output_type.value,
            }
            for s in skills
        ],
    }


@app.get("/api/v1/nlm/intents")
async def list_intents() -> Dict[str, Any]:
    """List supported intents"""
    from ..understanding.intents import Intent, INTENT_METADATA

    return {
        "intents": [
            {
                "name": intent.value,
                "description": INTENT_METADATA.get(intent, {}).get("description", ""),
            }
            for intent in Intent
            if intent != Intent.UNKNOWN
        ]
    }
