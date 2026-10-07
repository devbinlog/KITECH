"""service_base.py — Shared FastAPI factory for library-agent services.

Each containerized library agent (gcode-parser, cam-runner, ...) builds its
FastAPI app via `create_app(...)` to get the standard cross-cutting concerns
applied uniformly:

  • CORS (frontend direct calls — restricted origins)
  • TraceIdMiddleware (X-Trace-Id propagation)
  • Standard `/health` (no auth)
  • `/capabilities` skeleton (MCP-style)
  • INTERNAL_SERVICE_KEY auth dependency
  • Structured logging hookup

Usage in <agent>/src/service.py:

    from shared.common.service_base import create_app, require_internal

    app = create_app(
        name="gcode-parser",
        version="0.1.0",
        description="G-code 파서 서비스",
        capabilities=[...],
    )

    @app.post("/api/v1/parse", dependencies=[Depends(require_internal)])
    async def parse(req: ParseRequest):
        ...

API design principles (see docs/architecture/api-design-principles.md):
  • Idempotent where possible
  • Pydantic request/response schemas
  • Standard error envelope ({error: {code, message, hint?}})
  • Rich docstrings (LLM tool-calling friendly)
"""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .logging_config import setup_logging
from .tracing import TraceIdMiddleware


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------


def require_internal(
    x_internal_key: str = Header(default=""),
) -> None:
    """FastAPI dependency that validates the X-Internal-Key header.

    The shared `INTERNAL_SERVICE_KEY` is read from the environment at request
    time (not import time) so test overrides work cleanly.
    """
    expected = os.getenv("INTERNAL_SERVICE_KEY", "")
    if not expected:
        # Fail closed — never accept calls when the secret is unset.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="INTERNAL_SERVICE_KEY not configured",
        )
    if x_internal_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid X-Internal-Key",
        )


# --------------------------------------------------------------------------
# Capability metadata (MCP-style)
# --------------------------------------------------------------------------


class Capability(Dict[str, Any]):
    """A single tool/endpoint exposed by this service.

    Matches MCP-style tool descriptors so future agent-orchestrator can
    register these via dynamic discovery.
    """


def make_capability(
    name: str,
    description: str,
    *,
    method: str = "POST",
    path: str,
    input_schema_ref: Optional[str] = None,
    idempotent: bool = True,
) -> Dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "endpoint": {
            "method": method.upper(),
            "path": path,
        },
        "input_schema_ref": input_schema_ref,
        "idempotent": idempotent,
    }


# --------------------------------------------------------------------------
# Standard error envelope
# --------------------------------------------------------------------------


def error_envelope(
    code: str,
    message: str,
    hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the standard error envelope used by all library agents."""
    err: Dict[str, Any] = {"code": code, "message": message}
    if hint:
        err["hint"] = hint
    return {"error": err}


# --------------------------------------------------------------------------
# App factory
# --------------------------------------------------------------------------


def create_app(
    *,
    name: str,
    version: str,
    description: str,
    capabilities: List[Dict[str, Any]],
    cors_origins: Optional[List[str]] = None,
    additional_setup: Optional[Callable[[FastAPI], None]] = None,
) -> FastAPI:
    """Factory that produces a uniformly-configured FastAPI app.

    Args:
        name: Service name (e.g. "gcode-parser")
        version: SemVer (e.g. "0.1.0")
        description: Short human description
        capabilities: List of dicts from make_capability(...)
        cors_origins: defaults to ["http://localhost:3000"]
        additional_setup: optional callback to attach extra middlewares/handlers
    """
    setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
    logger = logging.getLogger(name)

    app = FastAPI(
        title=name,
        version=version,
        description=description,
        docs_url="/docs",
        openapi_url="/api/v1/openapi.json",
    )

    # Trace propagation
    app.add_middleware(TraceIdMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or ["http://localhost:3000"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # /health — no auth
    @app.get("/health", tags=["health"])
    async def health() -> Dict[str, Any]:
        """Liveness probe. No authentication required."""
        return {"status": "ok", "service": name, "version": version}

    # /capabilities — MCP-style introspection (no auth — read-only metadata)
    @app.get("/capabilities", tags=["meta"])
    async def get_capabilities() -> Dict[str, Any]:
        """List the tools/endpoints this service exposes (MCP-style).

        Future agent-orchestrator will read this to register tools dynamically.
        """
        return {
            "service": name,
            "version": version,
            "description": description,
            "tools": capabilities,
        }

    # Default 404 envelope (shape parity)
    @app.exception_handler(HTTPException)
    async def _http_exc_handler(request, exc: HTTPException):  # type: ignore[no-redef]
        env = error_envelope(
            code=f"http_{exc.status_code}",
            message=str(exc.detail) if exc.detail else "error",
        )
        return JSONResponse(status_code=exc.status_code, content=env)

    if additional_setup is not None:
        additional_setup(app)

    logger.info("service %s v%s ready", name, version)
    return app
