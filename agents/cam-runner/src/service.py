"""service.py — FastAPI wrapper for the cam-runner library agent.

Exposes CAM toolpath analysis (cycle time + Ap/Ae) as a thin HTTP service
on port 8011.  All domain endpoints require X-Internal-Key authentication
via the shared ``require_internal`` dependency.

Usage (container):
    uvicorn src.service:app --host 0.0.0.0 --port 8011
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Path bootstrap — allow running from the agents/cam-runner directory and
# resolve the shared package in the monorepo.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "shared"))

from common.service_base import create_app, make_capability, require_internal, error_envelope  # noqa: E402

# ---------------------------------------------------------------------------
# Lazy-import the domain library (opencamlib optional)
# ---------------------------------------------------------------------------
_SRC = Path(__file__).parent
sys.path.insert(0, str(_SRC))

from cam_runner_agent import CAMRunnerAgent  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Capabilities declaration
# ---------------------------------------------------------------------------
CAPABILITIES = [
    make_capability(
        name="analyze_cam_path",
        description=(
            "Calculate cycle time, Ap (axial depth), and Ae (radial depth) "
            "for a CAM toolpath given parsed G-code blocks."
        ),
        path="/api/v1/analyze",
        method="POST",
        input_schema_ref="#/components/schemas/AnalyzeRequest",
        idempotent=True,
    ),
]

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = create_app(
    name="cam-runner",
    version="0.1.0",
    description="CAM toolpath analysis (cycle time + Ap/Ae).",
    capabilities=CAPABILITIES,
)

# ---------------------------------------------------------------------------
# Singleton agent (constructed once at import time; stateless analysis)
# ---------------------------------------------------------------------------
_agent = CAMRunnerAgent()

# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------


class PositionDict(BaseModel):
    """3-D coordinate in G-code space (mm)."""

    X: float = Field(0.0, description="X coordinate (mm)")
    Y: float = Field(0.0, description="Y coordinate (mm)")
    Z: float = Field(0.0, description="Z coordinate (mm)")


class GcodeBlock(BaseModel):
    """Single parsed G-code block as produced by gcode-parser.

    Both the nested ``start_position`` / ``end_position`` form and the flat
    ``start_x`` / ``end_x`` form are accepted so that callers can forward
    gcode-parser output without transformation.
    """

    command: str = Field("G01", description="G-code command (e.g. G00, G01, G02, G03)")
    start_position: Optional[PositionDict] = Field(
        None, description="Start coordinate (nested form)"
    )
    end_position: Optional[PositionDict] = Field(
        None, description="End coordinate (nested form)"
    )
    start_x: Optional[float] = Field(None, description="Start X (flat form)")
    start_y: Optional[float] = Field(None, description="Start Y (flat form)")
    start_z: Optional[float] = Field(None, description="Start Z (flat form)")
    end_x: Optional[float] = Field(None, description="End X (flat form)")
    end_y: Optional[float] = Field(None, description="End Y (flat form)")
    end_z: Optional[float] = Field(None, description="End Z (flat form)")
    is_cutting: bool = Field(True, description="True for cutting moves, False for rapids")
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional G-code parameters (I, J, K for arcs; T for tool; F for feed)",
    )


class AnalyzeRequest(BaseModel):
    """Input for POST /api/v1/analyze.

    Attributes:
        gcode_blocks: List of parsed G-code blocks from gcode-parser.
        cutting_distance: Total cutting distance in mm (used for cycle time).
        rapid_distance: Total rapid-traverse distance in mm.
        feed_rate: Programmed feed rate in mm/min (default: 1000).
        dwell_time: Accumulated G04 dwell time in seconds (default: 0).
        rapid_feed_rate: Machine rapid traverse rate in mm/min (default: 5000).
        tool_change_time: Per-tool-change duration in seconds (default: 8).
    """

    gcode_blocks: List[GcodeBlock] = Field(
        ..., description="Parsed G-code blocks (from gcode-parser /parse output)"
    )
    cutting_distance: float = Field(0.0, ge=0, description="Total cutting distance (mm)")
    rapid_distance: float = Field(0.0, ge=0, description="Total rapid distance (mm)")
    feed_rate: float = Field(1000.0, gt=0, description="Feed rate (mm/min)")
    dwell_time: float = Field(0.0, ge=0, description="Accumulated dwell time (s)")
    rapid_feed_rate: float = Field(5000.0, gt=0, description="Rapid traverse rate (mm/min)")
    tool_change_time: float = Field(8.0, ge=0, description="Per tool-change duration (s)")


class CycleTimeSummary(BaseModel):
    """Cycle time breakdown in seconds and minutes."""

    cutting_time_sec: float
    rapid_time_sec: float
    dwell_time_sec: float
    tool_change_time_sec: float
    total_cycle_time_sec: float
    total_cycle_time_min: float
    tool_change_count: int
    feed_rate_used: float
    rapid_feed_rate_used: float


class ApAeSummary(BaseModel):
    """Ap/Ae statistics across all cutting segments."""

    total_paths: int
    cutting_segments: int
    tool_id: int
    tool_name: str
    cutter_type: Optional[str] = None
    cutter_diameter: Optional[float] = None
    ap_max: Optional[float] = None
    ap_min: Optional[float] = None
    ap_avg: Optional[float] = None
    ap_total: Optional[float] = None
    ae_max: Optional[float] = None
    ae_min: Optional[float] = None
    ae_avg: Optional[float] = None
    ae_total: Optional[float] = None
    cutting_distance: Optional[float] = None
    rapid_distance: Optional[float] = None
    warning: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Output of POST /api/v1/analyze.

    Attributes:
        status: "success" or "warning".
        message: Human-readable summary.
        summary: Per-tool Ap/Ae statistics.
        cycle_time: Cycle time breakdown.
        paths: First ≤20 cutting path records (for inspection).
        total_segments: Total number of G-code segments processed.
    """

    status: str
    message: str
    summary: ApAeSummary
    cycle_time: CycleTimeSummary
    paths: List[Dict[str, Any]]
    total_segments: int


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/analyze",
    response_model=AnalyzeResponse,
    dependencies=[Depends(require_internal)],
    tags=["cam"],
    summary="Analyze CAM toolpath",
)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """Calculate cycle time + Ap/Ae for a CAM toolpath.

    Use this when you have parsed G-code blocks (from gcode-parser) and need
    to estimate machining duration plus cutting engagement parameters.

    Idempotent — same input always yields the same output.

    Returns per-block cycle time (seconds), total distance (mm), and Ap
    (axial) / Ae (radial) engagement parameters for capacity planning or
    scheduler input.
    """
    logger.info(
        "analyze.start blocks=%d cutting_dist=%.1f feed=%.1f",
        len(req.gcode_blocks),
        req.cutting_distance,
        req.feed_rate,
    )

    # Convert Pydantic models back to the plain-dict format the agent expects
    raw_blocks: List[Dict[str, Any]] = []
    for blk in req.gcode_blocks:
        d: Dict[str, Any] = {"command": blk.command, "is_cutting": blk.is_cutting}
        if blk.start_position is not None:
            d["start_position"] = blk.start_position.model_dump()
        elif blk.start_x is not None:
            d["start_x"] = blk.start_x
            d["start_y"] = blk.start_y or 0.0
            d["start_z"] = blk.start_z or 0.0
        if blk.end_position is not None:
            d["end_position"] = blk.end_position.model_dump()
        elif blk.end_x is not None:
            d["end_x"] = blk.end_x
            d["end_y"] = blk.end_y or 0.0
            d["end_z"] = blk.end_z or 0.0
        if blk.parameters:
            d["parameters"] = blk.parameters
        raw_blocks.append(d)

    gcode_payload: Dict[str, Any] = {
        "gcode_blocks": raw_blocks,
        "cutting_distance": req.cutting_distance,
        "rapid_distance": req.rapid_distance,
        "feed_rate": req.feed_rate,
        "dwell_time": req.dwell_time,
    }

    try:
        result = _agent.analyze_gcode_paths(
            gcode_payload,
            rapid_feed_rate=req.rapid_feed_rate,
            tool_change_time=req.tool_change_time,
        )
    except Exception as exc:
        logger.exception("analyze.unhandled_error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_envelope(
                code="analysis_error",
                message=str(exc),
                hint="Check that gcode_blocks contain valid position data.",
            ),
        )

    if result.status == "error":
        logger.warning("analyze.domain_error: %s", result.message)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_envelope(
                code="analysis_failed",
                message=result.message,
                hint="Verify gcode_blocks are non-empty and positions are valid.",
            ),
        )

    data = result.data or {}
    summary_raw = data.get("summary", {})
    cycle_time_raw = data.get("cycle_time", {})

    logger.info(
        "analyze.done status=%s segments=%d total_cycle_time=%.2fs",
        result.status,
        summary_raw.get("total_paths", 0),
        cycle_time_raw.get("total_cycle_time_sec", 0.0),
    )

    return AnalyzeResponse(
        status=result.status,
        message=result.message,
        summary=ApAeSummary(**summary_raw),
        cycle_time=CycleTimeSummary(
            cutting_time_sec=cycle_time_raw.get("cutting_time_sec", 0.0),
            rapid_time_sec=cycle_time_raw.get("rapid_time_sec", 0.0),
            dwell_time_sec=cycle_time_raw.get("dwell_time_sec", 0.0),
            tool_change_time_sec=cycle_time_raw.get("tool_change_time_sec", 0.0),
            total_cycle_time_sec=cycle_time_raw.get("total_cycle_time_sec", 0.0),
            total_cycle_time_min=cycle_time_raw.get("total_cycle_time_min", 0.0),
            tool_change_count=cycle_time_raw.get("tool_change_count", 0),
            feed_rate_used=cycle_time_raw.get("feed_rate_used", req.feed_rate),
            rapid_feed_rate_used=cycle_time_raw.get(
                "rapid_feed_rate_used", req.rapid_feed_rate
            ),
        ),
        paths=data.get("paths", []),
        total_segments=data.get("total_segments", summary_raw.get("total_paths", 0)),
    )
