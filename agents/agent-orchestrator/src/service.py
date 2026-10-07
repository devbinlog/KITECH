"""agent-orchestrator FastAPI service entry."""
from fastapi import FastAPI
from shared.common.service_base import create_app, make_capability
from .core.llm_provider import get_llm_status
from .api.v1 import chat, sessions

CAPABILITIES = [
    make_capability(
        name="chat_with_agent",
        description=(
            "자연어 질의를 받아 LangGraph reasoning + tool 호출로 답변 생성. "
            "다단계 reasoning 지원."
        ),
        path="/api/v1/chat",
        method="POST",
        idempotent=False,
    ),
]

app: FastAPI = create_app(
    name="agent-orchestrator",
    version="0.1.0",
    description=(
        "LangGraph-based agent orchestrator with multi-step reasoning + dynamic tool loading."
    ),
    capabilities=CAPABILITIES,
    cors_origins=["http://localhost:3000"],
)


# /health override to include LLM status
@app.get("/health/full")
async def health_full():
    """Extended health check including LLM provider status."""
    return {
        "status": "ok",
        "service": "agent-orchestrator",
        "llm_status": get_llm_status(),
    }


app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
# WebSocket router registered without prefix (path defined inside router)
app.include_router(chat.ws_router)
