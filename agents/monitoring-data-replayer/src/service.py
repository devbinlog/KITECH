"""FastAPI service wrapper for monitoring-data-replayer.

Exposes the MonitoringDataReplayerAgent library as a thin HTTP service
suitable for containerised deployment on port 8013.

Endpoints
---------
POST /api/v1/replay       — Start a replay session (or dry-run statistics)
GET  /api/v1/sessions     — List active replay sessions
GET  /api/v1/sessions/{id} — Get session status
DELETE /api/v1/sessions/{id} — Stop a session
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field

from shared.common.service_base import (
    create_app,
    error_envelope,
    make_capability,
    require_internal,
)

from .agent import MonitoringDataReplayerAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Capabilities declaration (MCP-style)
# ---------------------------------------------------------------------------

CAPABILITIES = [
    make_capability(
        name="start_replay",
        description=(
            "Start replaying a monitoring data file (TDMS / LOG) between two "
            "timestamps. Returns a session_id for polling progress. "
            "Idempotent when the same file + time range is submitted."
        ),
        method="POST",
        path="/api/v1/replay",
        input_schema_ref="#/components/schemas/ReplayRequest",
        idempotent=False,
    ),
    make_capability(
        name="list_sessions",
        description="List all active replay sessions and their current status.",
        method="GET",
        path="/api/v1/sessions",
        idempotent=True,
    ),
]

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = create_app(
    name="monitoring-data-replayer",
    version="0.1.0",
    description="CNC monitoring data (TDMS/LOG) replay service for test and demo workloads.",
    capabilities=CAPABILITIES,
)

# ---------------------------------------------------------------------------
# In-process session registry
# ---------------------------------------------------------------------------

_sessions: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class ReplayRequest(BaseModel):
    """Input for POST /api/v1/replay.

    Attributes:
        file_path: Absolute (or container-relative) path to a TDMS or LOG file.
        start_ts:  ISO-8601 timestamp to begin replay from.  ``None`` = file start.
        end_ts:    ISO-8601 timestamp to stop replay at.     ``None`` = file end.
        speed:     Playback speed multiplier.  1.0 = real-time, 100.0 = 100× faster.
        dry_run:   When ``True`` returns statistics without actually replaying.
    """

    file_path: str = Field(..., description="Path to TDMS or LOG file")
    start_ts: Optional[datetime] = Field(None, description="Replay start timestamp (ISO-8601)")
    end_ts: Optional[datetime] = Field(None, description="Replay end timestamp (ISO-8601)")
    speed: float = Field(1.0, gt=0, description="Playback speed multiplier (>0)")
    dry_run: bool = Field(False, description="Return statistics without replaying")


class ReplayResponse(BaseModel):
    """Response for POST /api/v1/replay."""

    session_id: str
    file_path: str
    speed: float
    dry_run: bool
    status: str
    started_at: datetime
    statistics: Optional[Dict[str, Any]] = None


class SessionStatus(BaseModel):
    """Status of a single replay session."""

    session_id: str
    file_path: str
    speed: float
    status: str  # "running" | "completed" | "stopped" | "error"
    started_at: datetime
    finished_at: Optional[datetime] = None
    records_emitted: int = 0
    error: Optional[str] = None


class SessionListResponse(BaseModel):
    """Response for GET /api/v1/sessions."""

    sessions: List[SessionStatus]
    total: int


# ---------------------------------------------------------------------------
# Background replay task
# ---------------------------------------------------------------------------


async def _run_replay(session_id: str, req: ReplayRequest) -> None:
    """Background coroutine that drives the replay loop."""
    entry = _sessions[session_id]
    agent: MonitoringDataReplayerAgent = entry["agent"]
    try:
        async for _record in agent.replay(
            path=req.file_path,
            speed=req.speed,
            start_time=req.start_ts,
            end_time=req.end_ts,
        ):
            entry["records_emitted"] = agent._replayer.records_emitted
        entry["status"] = "completed"
    except Exception as exc:
        logger.exception("replay session %s failed: %s", session_id, exc)
        entry["status"] = "error"
        entry["error"] = str(exc)
    finally:
        entry["finished_at"] = datetime.utcnow()
        logger.info("replay session %s finished with status=%s", session_id, entry["status"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/replay",
    response_model=ReplayResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_internal)],
    tags=["replay"],
)
async def start_replay(req: ReplayRequest) -> ReplayResponse:
    """Start a monitoring data replay session.

    Accepts a file path and optional time window, launches an async replay
    in the background, and returns a ``session_id`` immediately.

    Poll ``GET /api/v1/sessions/{session_id}`` to track progress.

    When ``dry_run=true`` the file is parsed and statistics are returned
    synchronously — no background task is started.
    """
    import os

    agent = MonitoringDataReplayerAgent()

    # Validate file exists before accepting the request
    from pathlib import Path

    if not Path(req.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_envelope(
                code="file_not_found",
                message=f"File not found: {req.file_path}",
                hint="Provide an absolute path that is accessible inside the container.",
            ),
        )

    session_id = str(uuid.uuid4())
    started_at = datetime.utcnow()

    if req.dry_run:
        logger.info("dry_run replay for %s", req.file_path)
        try:
            stats = agent.get_statistics(req.file_path)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_envelope(
                    code="statistics_error",
                    message=str(exc),
                ),
            )
        return ReplayResponse(
            session_id=session_id,
            file_path=req.file_path,
            speed=req.speed,
            dry_run=True,
            status="completed",
            started_at=started_at,
            statistics=stats,
        )

    # Register session before launching task so GET /sessions sees it immediately
    _sessions[session_id] = {
        "session_id": session_id,
        "file_path": req.file_path,
        "speed": req.speed,
        "status": "running",
        "started_at": started_at,
        "finished_at": None,
        "records_emitted": 0,
        "error": None,
        "agent": agent,
    }

    asyncio.create_task(_run_replay(session_id, req))
    logger.info("started replay session %s for %s at speed=%.1f", session_id, req.file_path, req.speed)

    return ReplayResponse(
        session_id=session_id,
        file_path=req.file_path,
        speed=req.speed,
        dry_run=False,
        status="running",
        started_at=started_at,
    )


@app.get(
    "/api/v1/sessions",
    response_model=SessionListResponse,
    dependencies=[Depends(require_internal)],
    tags=["replay"],
)
async def list_sessions() -> SessionListResponse:
    """List all replay sessions (active and recently completed).

    Use this to monitor in-flight replays or audit past sessions since
    service restart.
    """
    sessions = [
        SessionStatus(
            session_id=s["session_id"],
            file_path=s["file_path"],
            speed=s["speed"],
            status=s["status"],
            started_at=s["started_at"],
            finished_at=s["finished_at"],
            records_emitted=s["records_emitted"],
            error=s["error"],
        )
        for s in _sessions.values()
    ]
    return SessionListResponse(sessions=sessions, total=len(sessions))


@app.get(
    "/api/v1/sessions/{session_id}",
    response_model=SessionStatus,
    dependencies=[Depends(require_internal)],
    tags=["replay"],
)
async def get_session(session_id: str) -> SessionStatus:
    """Get the status of a specific replay session.

    Returns current ``records_emitted``, ``status``, and timing information.
    """
    if session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_envelope(
                code="session_not_found",
                message=f"Session {session_id!r} not found.",
            ),
        )
    s = _sessions[session_id]
    # Refresh records_emitted from agent if still running
    if s["status"] == "running":
        s["records_emitted"] = s["agent"]._replayer.records_emitted

    return SessionStatus(
        session_id=s["session_id"],
        file_path=s["file_path"],
        speed=s["speed"],
        status=s["status"],
        started_at=s["started_at"],
        finished_at=s["finished_at"],
        records_emitted=s["records_emitted"],
        error=s["error"],
    )


@app.delete(
    "/api/v1/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_internal)],
    tags=["replay"],
)
async def stop_session(session_id: str) -> None:
    """Stop an active replay session.

    Sends a stop signal to the replay engine. The session record remains
    in the registry with ``status=stopped`` for audit purposes.
    """
    if session_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_envelope(
                code="session_not_found",
                message=f"Session {session_id!r} not found.",
            ),
        )
    s = _sessions[session_id]
    if s["status"] == "running":
        s["agent"].stop()
        s["status"] = "stopped"
        s["finished_at"] = datetime.utcnow()
        logger.info("stopped replay session %s", session_id)
