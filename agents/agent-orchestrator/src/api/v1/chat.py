"""api/v1/chat.py — HTTP POST /chat and WebSocket /ws/chat endpoints."""
from __future__ import annotations

import hmac
import logging
import os
import re
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from shared.common.service_base import require_internal

logger = logging.getLogger(__name__)

router = APIRouter()
ws_router = APIRouter()

# UUIDv4 pattern — case-insensitive
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _error_envelope(code: str, detail: str) -> Dict[str, Any]:
    return {"code": code, "detail": detail}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    session_id: Optional[str] = Field(
        None, description="UUIDv4 conversation thread ID (auto-generated if omitted)."
    )
    message: str = Field(..., description="User's natural language query.")


class ChatResponse(BaseModel):
    """Response body for POST /chat."""

    session_id: str
    answer: str
    tools_used: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# HTTP endpoint
# ---------------------------------------------------------------------------


@router.post("/chat", response_model=ChatResponse)
async def chat_http(
    req: ChatRequest,
    _: None = Depends(require_internal),
) -> ChatResponse:
    """Run a single-turn agent invocation via LangGraph.

    Accepts a user message, runs the compiled agent graph with the given
    session_id as thread_id (for checkpointing), and returns the final
    AI answer along with a list of tools invoked during reasoning.
    """
    sid = req.session_id or str(uuid.uuid4())
    if not UUID_RE.match(sid):
        raise HTTPException(
            status_code=400,
            detail=_error_envelope("invalid_session_id", "session_id must be UUIDv4"),
        )

    # Lazy import — graph/builder may not exist yet (other sub-agent)
    try:
        from ...graph.builder import get_compiled_graph  # type: ignore[import]
        from langchain_core.messages import HumanMessage
    except ImportError as exc:
        logger.warning("graph.builder not available: %s", exc)
        return ChatResponse(
            session_id=sid,
            answer="Agent graph not yet available.",
            tools_used=[],
        )

    try:
        graph = await get_compiled_graph()
    except Exception as exc:
        logger.exception("graph init failed")
        return ChatResponse(
            session_id=sid,
            answer=f"Graph initialization error: {exc}",
            tools_used=[],
        )

    config = {"configurable": {"thread_id": sid}}
    state_input: Dict[str, Any] = {
        "messages": [HumanMessage(content=req.message)]
    }

    try:
        final_state = await graph.ainvoke(state_input, config=config)
    except Exception as exc:
        logger.exception("graph.ainvoke failed")
        return ChatResponse(
            session_id=sid,
            answer=f"Inference error: {exc}",
            tools_used=[],
        )

    messages = final_state.get("messages", [])
    answer = ""
    if messages:
        last = messages[-1]
        answer = getattr(last, "content", str(last))

    tools_used: List[str] = final_state.get("tools_used", [])

    return ChatResponse(
        session_id=sid,
        answer=answer,
        tools_used=tools_used,
    )


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@ws_router.websocket("/ws/chat")
async def chat_ws(ws: WebSocket) -> None:
    """WebSocket endpoint for streaming agent responses.

    Authentication: pass INTERNAL_SERVICE_KEY via header X-Internal-Key
    or query parameter ?key=<value> (query param suits browser WebSocket).

    Message protocol (client -> server):
        {"session_id": "...", "message": "..."}

    Message protocol (server -> client):
        {"type": "chunk", "data": {...}}   — incremental output
        {"type": "done"}                   — stream complete
        {"type": "error", "error": "..."}  — error
    """
    expected = os.getenv("INTERNAL_SERVICE_KEY", "")
    if not expected:
        await ws.close(code=1008, reason="server: INTERNAL_SERVICE_KEY not configured")
        return

    key = (
        ws.headers.get("x-internal-key", "")
        or ws.query_params.get("key", "")
    )
    if not key or not hmac.compare_digest(key, expected):
        await ws.close(code=1008, reason="invalid X-Internal-Key")
        return

    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            raw_sid: Optional[str] = data.get("session_id")
            message: str = data.get("message", "")

            if not message:
                await ws.send_json({"type": "error", "error": "message field required"})
                continue

            sid = raw_sid or str(uuid.uuid4())
            if not UUID_RE.match(sid):
                await ws.send_json(
                    {
                        "type": "error",
                        "error": "session_id must be UUIDv4",
                        "code": "invalid_session_id",
                    }
                )
                continue

            from ...core.streaming import stream_agent_response  # lazy

            async for chunk in stream_agent_response(sid, message):
                await ws.send_json({"type": "chunk", "data": chunk})
            await ws.send_json({"type": "done"})
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.exception("ws/chat error")
        try:
            await ws.send_json({"type": "error", "error": str(exc)})
        except Exception:
            pass
