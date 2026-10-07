"""Common utilities for agents-workspace"""

from .logging_config import setup_logging, get_logger
from .error_handling import AgentError, ValidationError, ProcessingError, error_handler
from .tracing import (
    TRACE_ID_HEADER,
    TraceIdMiddleware,
    TraceIdLogFilter,
    get_trace_id,
)
from .service_base import (
    create_app,
    require_internal,
    make_capability,
    error_envelope,
)

__all__ = [
    "setup_logging",
    "get_logger",
    "AgentError",
    "ValidationError",
    "ProcessingError",
    "error_handler",
    # tracing
    "TRACE_ID_HEADER",
    "TraceIdMiddleware",
    "TraceIdLogFilter",
    "get_trace_id",
    # service_base
    "create_app",
    "require_internal",
    "make_capability",
    "error_envelope",
]
