"""api/v1/sessions.py — Session/trace inspection endpoints."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from shared.common.service_base import require_internal
from ...core.checkpoint import load_session_trace

logger = logging.getLogger(__name__)

router = APIRouter()

# UUIDv4 pattern — shared with chat.py to avoid divergence
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _error_envelope(code: str, detail: str) -> Dict[str, Any]:
    return {"code": code, "detail": detail}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class MessageRecord(BaseModel):
    type: str
    content: str


class SessionTraceResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]
    tools_used: List[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/sessions/{session_id}/trace",
    response_model=SessionTraceResponse,
)
async def get_session_trace(
    session_id: str,
    _: None = Depends(require_internal),
) -> SessionTraceResponse:
    """Retrieve the stored conversation trace for a session.

    Reads checkpointed state from SqliteSaver and returns the message
    history and tool invocations for the given thread_id.

    Rejects 'default' and any non-UUIDv4 session_id to prevent IDOR.
    """
    if session_id == "default" or not UUID_RE.match(session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_envelope("invalid_session_id", "session_id must be UUIDv4"),
        )

    try:
        trace = await load_session_trace(session_id)
    except Exception as exc:
        logger.exception("load_session_trace failed for %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load session trace: {exc}",
        ) from exc

    return SessionTraceResponse(
        session_id=session_id,
        messages=trace.get("messages", []),
        tools_used=trace.get("tools_used", []),
    )
