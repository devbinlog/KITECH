"""service.py — Thin FastAPI wrapper around the GcodeParserAgent library.

Exposes a single POST /api/v1/parse endpoint that accepts raw G-code text and
returns block-level structured analysis. All heavy lifting is done by the
existing GcodeParserAgent; this module only handles HTTP concerns.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

# Ensure shared/ is importable when running via uvicorn from the workspace root.
# In Docker the WORKDIR is /app (workspace root), so shared/ is already on sys.path
# via PYTHONPATH or relative import; these inserts are a local-dev safety net.
_workspace_root = Path(__file__).parent.parent.parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

from shared.common.service_base import (
    create_app,
    error_envelope,
    make_capability,
    require_internal,
)

from .gcode_parser_agent import GcodeParserAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class ParseRequest(BaseModel):
    """Input for POST /api/v1/parse.

    Attributes:
        gcode: Raw G-code text (UTF-8, multi-line).
    """

    gcode: str = Field(..., min_length=1, description="Raw G-code text (UTF-8, multi-line)")


class ParseResponse(BaseModel):
    """Structured result of G-code analysis.

    Attributes:
        blocks:              Per-movement block analysis list.
        total_distance_mm:   Total toolpath distance in mm.
        machine_time_sec:    Estimated dwell/spindle time in seconds.
        rapid_distance_mm:   Distance covered by rapid (G00) moves.
        cutting_distance_mm: Distance covered by cutting moves (G01/G02/G03).
        spindle_speed:       Last observed spindle speed (RPM).
        feed_rate:           Last observed feed rate (mm/min).
        total_commands:      Number of movement commands parsed.
    """

    blocks: List[Dict[str, Any]] = Field(default_factory=list)
    total_distance_mm: float = Field(0.0, description="Total toolpath distance in mm")
    machine_time_sec: float = Field(0.0, description="Estimated dwell time in seconds")
    rapid_distance_mm: float = Field(0.0, description="Rapid-move distance in mm")
    cutting_distance_mm: float = Field(0.0, description="Cutting-move distance in mm")
    spindle_speed: float = Field(0.0, description="Last observed spindle speed (RPM)")
    feed_rate: float = Field(0.0, description="Last observed feed rate (mm/min)")
    total_commands: int = Field(0, description="Number of movement blocks parsed")


# ---------------------------------------------------------------------------
# Capabilities declaration (MCP-style)
# ---------------------------------------------------------------------------

CAPABILITIES = [
    make_capability(
        name="parse_gcode",
        description=(
            "Parse raw G-code text into block-level structured data including "
            "per-block position, depth-of-cut (Ap/Ae), distance, and cutting flags. "
            "Returns total distance, cutting distance, rapid distance, spindle speed, "
            "and feed rate. Idempotent — same input always yields same output."
        ),
        path="/api/v1/parse",
        method="POST",
        input_schema_ref="#/components/schemas/ParseRequest",
        idempotent=True,
    ),
]

# ---------------------------------------------------------------------------
# App + router
# ---------------------------------------------------------------------------

app = create_app(
    name="gcode-parser",
    version="0.1.0",
    description="G-code parser service — converts raw G-code text to structured block analysis.",
    capabilities=CAPABILITIES,
)

router = APIRouter(prefix="/api/v1")

# Lazy singleton — avoids re-initialising the agent on every request.
_parser: Optional[GcodeParserAgent] = None


def _get_parser() -> GcodeParserAgent:
    global _parser
    if _parser is None:
        _parser = GcodeParserAgent()
    return _parser


@router.post(
    "/parse",
    response_model=ParseResponse,
    dependencies=[Depends(require_internal)],
    summary="Parse G-code text into structured block-level analysis",
)
async def parse(req: ParseRequest) -> ParseResponse:
    """Parse raw G-code text into block-level structured data.

    Use this when you have a G-code program (as a plain-text string) and need
    structured movement data for scheduling, capacity planning, or toolpath
    visualisation. Idempotent — same G-code always returns the same result.

    Returns per-block position, Ap (axial depth), Ae (radial depth), distance,
    and cutting flags, plus totals for distance, rapid distance, cutting distance,
    spindle speed, and feed rate.

    Raises:
        400: If the parser reports a failure (e.g. gcodeparser library unavailable
             or malformed input that causes an unrecoverable error).
    """
    logger.info("parse.start gcode_size=%d", len(req.gcode))

    parser = _get_parser()
    result = parser.process(req.gcode)

    if result.get("status") == "error":
        errors = result.get("errors", [])
        msg = result.get("message", "G-code parsing failed")
        hint = errors[0] if errors else None
        logger.warning("parse.error message=%s", msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_envelope(code="parse_error", message=msg, hint=hint),
        )

    data: Dict[str, Any] = result.get("data") or {}
    blocks: List[Dict[str, Any]] = data.get("gcode_blocks", [])

    logger.info("parse.done blocks=%d", len(blocks))

    return ParseResponse(
        blocks=blocks,
        total_distance_mm=data.get("total_distance", 0.0),
        machine_time_sec=data.get("dwell_time", 0.0),
        rapid_distance_mm=data.get("rapid_distance", 0.0),
        cutting_distance_mm=data.get("cutting_distance", 0.0),
        spindle_speed=data.get("spindle_speed", 0.0),
        feed_rate=data.get("feed_rate", 0.0),
        total_commands=data.get("total_commands", 0),
    )


app.include_router(router)
