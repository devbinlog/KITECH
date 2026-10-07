"""tracing.py — Lightweight X-Trace-Id propagation for inter-agent calls.

Compatible with OpenTelemetry semantic conventions but does not require the
otel SDK as a hard dependency. Each FastAPI service uses
`TraceIdMiddleware` to:

  1. Read incoming `X-Trace-Id` header (or generate one if absent)
  2. Attach the trace id to a contextvar so logs include it
  3. Echo the trace id on the response header

Future: swap to opentelemetry.instrumentation.fastapi for full distributed
tracing without code changes (the contextvar pattern remains compatible).

Usage:
    from shared.common.tracing import TraceIdMiddleware, get_trace_id

    app = FastAPI()
    app.add_middleware(TraceIdMiddleware)

    # In handlers:
    logger.info("processing", extra={"trace_id": get_trace_id()})
"""
from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


TRACE_ID_HEADER = "X-Trace-Id"
_trace_id_ctx: ContextVar[Optional[str]] = ContextVar("_trace_id", default=None)

logger = logging.getLogger(__name__)


def get_trace_id() -> Optional[str]:
    """Return the current request's trace id (or None outside a request)."""
    return _trace_id_ctx.get()


def _new_trace_id() -> str:
    return uuid.uuid4().hex[:16]


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Read/generate X-Trace-Id, expose via contextvar, echo on response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get(TRACE_ID_HEADER)
        trace_id = incoming or _new_trace_id()
        token = _trace_id_ctx.set(trace_id)
        try:
            response = await call_next(request)
        finally:
            _trace_id_ctx.reset(token)
        response.headers[TRACE_ID_HEADER] = trace_id
        return response


class TraceIdLogFilter(logging.Filter):
    """Inject trace_id into LogRecord so structured loggers can serialize it.

    Add to your handler:
        handler.addFilter(TraceIdLogFilter())
    Then format: '%(trace_id)s' in your formatter.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.trace_id = get_trace_id() or "-"
        return True
