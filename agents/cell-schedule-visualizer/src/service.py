"""service.py — Thin FastAPI wrapper for cell-schedule-visualizer.

Exposes POST /api/v1/render which accepts a manufacturing schedule result
(gantt_data + quality metrics) and returns a PNG Gantt chart rendered via
matplotlib (Agg backend — thread-safe, headless).

All rendering is done in-process using BytesIO so no temp files are created,
guaranteeing stateless, idempotent behaviour.
"""
from __future__ import annotations

import io
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Force the non-interactive Agg backend BEFORE importing pyplot.
# matplotlib is not thread-safe with interactive backends.
import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

# Ensure shared/ is importable when running via uvicorn from the workspace root.
_workspace_root = Path(__file__).parent.parent.parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

from shared.common.service_base import (
    create_app,
    error_envelope,
    make_capability,
    require_internal,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class GanttTaskInput(BaseModel):
    """A single task row in the Gantt chart.

    Attributes:
        name:             Task / Work-order label displayed on the chart.
        start:            ISO-8601 datetime string for task start.
        end:              ISO-8601 datetime string for task end.
        resource:         Machine / resource identifier (Y-axis label).
        priority:         Numeric priority (1 = highest). Used for Z-order.
        color:            Hex colour string (e.g. '#4ECDC4'). Falls back to
                          a default palette if omitted.
        quantity:         Number of units produced in this slot.
        duration_minutes: Duration in minutes (informational).
    """

    name: str = Field(..., description="Work-order / task label")
    start: str = Field(..., description="ISO-8601 start datetime")
    end: str = Field(..., description="ISO-8601 end datetime")
    resource: str = Field(..., description="Machine / resource ID")
    priority: int = Field(1, description="Priority (1 = highest)")
    color: str = Field("#4ECDC4", description="Hex colour for the bar")
    quantity: int = Field(0, description="Units produced")
    duration_minutes: float = Field(0.0, description="Duration in minutes")


class GanttDataInput(BaseModel):
    """Top-level gantt_data block matching CellScheduler output.

    Attributes:
        tasks:     Ordered list of scheduled task bars.
        resources: Ordered list of machine/resource names for Y-axis.
        start:     ISO-8601 chart start (leftmost X boundary).
        end:       ISO-8601 chart end (rightmost X boundary).
    """

    tasks: List[GanttTaskInput] = Field(default_factory=list)
    resources: List[str] = Field(default_factory=list)
    start: str = Field("", description="Chart start datetime (ISO-8601)")
    end: str = Field("", description="Chart end datetime (ISO-8601)")


class RenderRequest(BaseModel):
    """Input for POST /api/v1/render.

    Accepts the gantt_data block produced by CellScheduler.solve() and
    optional rendering hints.

    Attributes:
        gantt_data:  Gantt data block (tasks, resources, start, end).
        title:       Optional chart title.
        width_inch:  Figure width in inches (default 14).
        height_inch: Figure height in inches (default 7).
        format:      Output format: 'png' (default) or 'svg'.
    """

    gantt_data: GanttDataInput = Field(..., description="Gantt chart data from CellScheduler")
    title: str = Field("Manufacturing Schedule", description="Chart title")
    width_inch: float = Field(14.0, gt=0, description="Figure width in inches")
    height_inch: float = Field(7.0, gt=0, description="Figure height in inches")
    format: str = Field("png", pattern="^(png|svg)$", description="Output format: png or svg")


# ---------------------------------------------------------------------------
# Rendering logic
# ---------------------------------------------------------------------------

# Fallback colour palette when task.color is not supplied
_DEFAULT_COLOURS = [
    "#4ECDC4",
    "#FF6B6B",
    "#FFE66D",
    "#A8E6CF",
    "#FF8B94",
    "#B5EAD7",
    "#C7CEEA",
    "#FFDAC1",
]


def _render_gantt(req: RenderRequest) -> bytes:
    """Render the Gantt chart and return raw image bytes.

    Uses matplotlib with the Agg backend — fully headless and safe to call
    from async context (heavy work is synchronous but non-blocking at the
    process level for typical schedule sizes).

    Args:
        req: Validated RenderRequest with gantt_data and rendering hints.

    Returns:
        Raw bytes of the rendered image (PNG or SVG).
    """
    from datetime import datetime

    gantt = req.gantt_data
    resources = gantt.resources if gantt.resources else sorted({t.resource for t in gantt.tasks})

    # Map resource name → y index
    resource_index: Dict[str, int] = {r: i for i, r in enumerate(resources)}
    n_resources = max(len(resources), 1)

    fig, ax = plt.subplots(figsize=(req.width_inch, req.height_inch))

    def _parse_dt(s: str) -> float:
        """Convert ISO-8601 string to matplotlib date float."""
        import matplotlib.dates as mdates

        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return mdates.date2num(dt)

    legend_handles: Dict[str, Any] = {}

    for idx, task in enumerate(gantt.tasks):
        y_pos = resource_index.get(task.resource, 0)
        colour = task.color if task.color else _DEFAULT_COLOURS[idx % len(_DEFAULT_COLOURS)]

        try:
            x_start = _parse_dt(task.start)
            x_end = _parse_dt(task.end)
        except Exception:
            logger.warning("render: skipping task '%s' — unparseable datetime", task.name)
            continue

        width = x_end - x_start
        if width <= 0:
            logger.warning("render: skipping task '%s' — zero/negative duration", task.name)
            continue

        bar = mpatches.FancyBboxPatch(
            (x_start, y_pos - 0.4),
            width,
            0.8,
            boxstyle="round,pad=0.01",
            facecolor=colour,
            edgecolor="white",
            linewidth=0.8,
            zorder=task.priority,
        )
        ax.add_patch(bar)

        # Label inside bar
        x_mid = x_start + width / 2
        ax.text(
            x_mid,
            y_pos,
            task.name,
            ha="center",
            va="center",
            fontsize=7,
            color="black",
            fontweight="bold",
            clip_on=True,
        )

        if task.resource not in legend_handles:
            legend_handles[task.resource] = mpatches.Patch(color=colour, label=task.resource)

    # Axes formatting
    import matplotlib.dates as mdates

    ax.set_yticks(range(n_resources))
    ax.set_yticklabels(resources, fontsize=9)
    ax.set_ylim(-0.8, n_resources - 0.2)

    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
    fig.autofmt_xdate(rotation=30)

    if gantt.start and gantt.end:
        try:
            ax.set_xlim(_parse_dt(gantt.start), _parse_dt(gantt.end))
        except Exception:
            pass

    ax.set_title(req.title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Time", fontsize=10)
    ax.set_ylabel("Machine", fontsize=10)
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    if legend_handles:
        ax.legend(
            handles=list(legend_handles.values()),
            loc="upper right",
            fontsize=8,
            framealpha=0.9,
        )

    fig.tight_layout()

    buf = io.BytesIO()
    fmt = req.format.lower()
    fig.savefig(buf, format=fmt, dpi=150, bbox_inches="tight")
    plt.close(fig)

    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Capabilities declaration
# ---------------------------------------------------------------------------

CAPABILITIES = [
    make_capability(
        name="render_schedule",
        description=(
            "Render a manufacturing schedule Gantt chart to PNG or SVG. "
            "Accepts gantt_data (tasks, resources, start, end) from CellScheduler.solve() "
            "and returns raw image bytes. Idempotent — same input always yields same output."
        ),
        path="/api/v1/render",
        method="POST",
        input_schema_ref="#/components/schemas/RenderRequest",
        idempotent=True,
    ),
]

# ---------------------------------------------------------------------------
# App + router
# ---------------------------------------------------------------------------

app = create_app(
    name="cell-schedule-visualizer",
    version="0.1.0",
    description=(
        "Gantt chart rendering service — converts CellScheduler output "
        "to PNG/SVG images via matplotlib."
    ),
    capabilities=CAPABILITIES,
)

router = APIRouter(prefix="/api/v1")

_CONTENT_TYPES: Dict[str, str] = {
    "png": "image/png",
    "svg": "image/svg+xml",
}


@router.post(
    "/render",
    dependencies=[Depends(require_internal)],
    summary="Render schedule Gantt chart to PNG or SVG",
    response_class=Response,
    responses={
        200: {
            "content": {"image/png": {}, "image/svg+xml": {}},
            "description": "Rendered Gantt chart image bytes.",
        },
        400: {"description": "Rendering failed — invalid or empty gantt_data."},
        401: {"description": "Missing or invalid X-Internal-Key header."},
    },
)
async def render(req: RenderRequest) -> Response:
    """Render a Gantt chart for a manufacturing schedule.

    Accepts the gantt_data block from CellScheduler.solve() and returns
    raw image bytes in the requested format (PNG or SVG). Stateless —
    no files are written; rendering happens in-memory via BytesIO.

    Use this when you need a visual representation of a CellScheduler result
    for dashboards, reports, or operator interfaces. Idempotent — same
    gantt_data always produces the same image.

    Args:
        req: RenderRequest with gantt_data, optional title, dimensions, and format.

    Returns:
        Response with raw image bytes and appropriate Content-Type header.

    Raises:
        400: If rendering fails (e.g. all tasks have invalid datetimes).
    """
    fmt = req.format.lower()
    logger.info(
        "render.start tasks=%d resources=%d format=%s",
        len(req.gantt_data.tasks),
        len(req.gantt_data.resources),
        fmt,
    )

    try:
        image_bytes = _render_gantt(req)
    except Exception as exc:
        logger.exception("render.error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_envelope(
                code="render_error",
                message="Gantt chart rendering failed",
                hint=str(exc),
            ),
        )

    content_type = _CONTENT_TYPES.get(fmt, "image/png")
    logger.info("render.done bytes=%d content_type=%s", len(image_bytes), content_type)
    return Response(content=image_bytes, media_type=content_type)


app.include_router(router)
