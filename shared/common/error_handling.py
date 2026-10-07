"""
Standardized error handling for agents-workspace.

Usage:
    from shared.common import AgentError, ValidationError, error_handler

    @error_handler
    def process_data(data):
        if not data:
            raise ValidationError("Data cannot be empty")
        # ... processing

    # Or manual handling
    try:
        result = risky_operation()
    except AgentError as e:
        logger.error(f"Operation failed: {e}", extra=e.to_dict())
        return {"status": "error", "error": str(e), "code": e.code}
"""

import functools
import traceback
from typing import Any, Callable, Dict
from datetime import datetime, timezone
import logging


logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Base exception for all agent errors"""

    code: str = "AGENT_ERROR"
    http_status: int = 500

    def __init__(self, message: str, details: Dict[str, Any] = None, cause: Exception = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/response"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }

    def to_response(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "status": "error",
            "error": {"code": self.code, "message": self.message, **self.details},
        }


class ValidationError(AgentError):
    """Input validation failed"""

    code = "VALIDATION_ERROR"
    http_status = 400


class ProcessingError(AgentError):
    """Processing/computation failed"""

    code = "PROCESSING_ERROR"
    http_status = 500


class ConfigurationError(AgentError):
    """Configuration/setup error"""

    code = "CONFIGURATION_ERROR"
    http_status = 500


class ResourceNotFoundError(AgentError):
    """Requested resource not found"""

    code = "NOT_FOUND"
    http_status = 404


class ExternalServiceError(AgentError):
    """External service call failed"""

    code = "EXTERNAL_SERVICE_ERROR"
    http_status = 502


def error_handler(func: Callable) -> Callable:
    """
    Decorator for standardized error handling.

    Catches exceptions and converts them to consistent error responses.

    Usage:
        @error_handler
        def process(data):
            ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            return func(*args, **kwargs)
        except AgentError as e:
            logger.error(f"{e.code}: {e.message}", extra={"error": e.to_dict()}, exc_info=True)
            return e.to_response()
        except Exception as e:
            logger.error(
                f"Unexpected error: {str(e)}",
                extra={"traceback": traceback.format_exc()},
                exc_info=True,
            )
            return {"status": "error", "error": {"code": "INTERNAL_ERROR", "message": str(e)}}

    return wrapper


async def async_error_handler(func: Callable) -> Callable:
    """Async version of error_handler"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            return await func(*args, **kwargs)
        except AgentError as e:
            logger.error(f"{e.code}: {e.message}", extra={"error": e.to_dict()})
            return e.to_response()
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return {"status": "error", "error": {"code": "INTERNAL_ERROR", "message": str(e)}}

    return wrapper
