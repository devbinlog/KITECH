"""service.py — FastAPI wrapper for the STEP PMI Reader library.

Exposes the StepPmiReaderAgent as a containerised HTTP service on port 8012.

Endpoints:
    POST /api/v1/extract  — Extract PMI data from an uploaded STEP file.
                             Requires X-Internal-Key header (Depends(require_internal)).
    GET  /health           — Liveness probe (no auth).
    GET  /capabilities     — MCP-style tool descriptor (no auth).
"""
from __future__ import annotations

import logging
import sys
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from fastapi import Depends, File, HTTPException, UploadFile, status

# ---------------------------------------------------------------------------
# Shared service base (path is available both in-container and in uv workspace)
# ---------------------------------------------------------------------------
try:
    from shared.common.service_base import create_app, make_capability, require_internal, error_envelope
except ImportError:
    # Fallback: allow tests that add the repo root to sys.path
    sys.path.insert(0, str(Path(__file__).parents[3]))
    from shared.common.service_base import create_app, make_capability, require_internal, error_envelope  # noqa: F811

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Capabilities declaration
# ---------------------------------------------------------------------------

CAPABILITIES = [
    make_capability(
        name="extract_pmi",
        description=(
            "Extract PMI (Product Manufacturing Information) from a STEP AP242 file. "
            "Returns datums, geometric tolerances (GD&T), dimensional tolerances, "
            "surface finish specifications, and annotations."
        ),
        path="/api/v1/extract",
        method="POST",
        input_schema_ref="#/components/schemas/Body_extract_pmi_api_v1_extract_post",
        idempotent=True,
    )
]

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = create_app(
    name="step-pmi-reader",
    version="0.1.0",
    description="STEP AP242 PMI (Product Manufacturing Information) extraction service",
    capabilities=CAPABILITIES,
)


# ---------------------------------------------------------------------------
# Domain endpoint
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/extract",
    tags=["pmi"],
    dependencies=[Depends(require_internal)],
)
async def extract_pmi(
    file: UploadFile = File(..., description="STEP file (.stp / .step) to extract PMI from"),
) -> Dict[str, Any]:
    """Extract PMI data from an uploaded STEP AP242 file.

    Reads the multipart-uploaded STEP file, passes it to StepPmiReaderAgent,
    and returns the structured PMI payload.  The result is idempotent — the
    same file always produces the same output.

    Returns a dict with keys:
        status    — "success"
        message   — Human-readable summary
        data      — PMI dict (file_name, schema, summary, datums,
                    geometric_tolerances, dimensional_tolerances,
                    surface_finishes, annotations)

    Raises:
        400  if the uploaded file is empty or cannot be read.
        422  if the file parameter is missing (FastAPI validation).
        500  if PMI extraction fails unexpectedly.
    """
    # Read upload into a temp file so the agent can use its file-path branch
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_envelope("empty_file", "Uploaded file is empty"),
        )

    # Lazy import — OCC only available inside the container.
    # On the host (pytest without pythonocc-core) this endpoint is never
    # reached in tests, so the ImportError stays silent.
    try:
        from src.step_pmi_reader_agent import StepPmiReaderAgent
    except ImportError:
        # In case the module path differs (container vs workspace)
        sys.path.insert(0, str(Path(__file__).parent))
        from step_pmi_reader_agent import StepPmiReaderAgent  # type: ignore[no-redef]

    suffix = Path(file.filename or "upload.stp").suffix or ".stp"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        agent = StepPmiReaderAgent()
        result = agent.process(tmp_path)
    except Exception as exc:
        logger.error("PMI extraction error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_envelope("extraction_failed", str(exc)),
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    if result.get("status") != "success":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_envelope("extraction_failed", result.get("message", "unknown error")),
        )

    logger.info(
        "extract_pmi.done file=%s schema=%s",
        result["data"].get("file_name"),
        result["data"].get("schema"),
    )
    return result
