"""HTTP client for cell-scheduler service.

Extracted from SchedulerIntegrationService (original lines 1026-1133).

Handles:
- HTTP POST to scheduler /api/v1/schedule/solve
- Circuit breaker integration
- Solver time-limit resolution
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from ...core.config import settings
from ..circuit_breaker import CircuitConfig, get_circuit_breaker

logger = logging.getLogger(__name__)

SCHEDULER_SERVICE_URL = settings.SCHEDULER_BASE_URL
SCHEDULER_TIMEOUT = settings.SCHEDULER_TIMEOUT

# Per-solver time limits (seconds).
SOLVER_TIME_LIMITS: Dict[str, int] = {
    "OR_TOOLS": 60,
    "GA": 60,
    "SA": 30,
    "TABU": 60,
    "ALNS": 300,
}

_SCHEDULER_CB_ENDPOINT = "scheduler"
_SCHEDULER_CB_CONFIG = CircuitConfig(
    failure_threshold=3,
    success_threshold=2,
    timeout_seconds=30,
    half_open_max_calls=2,
)


def _get_scheduler_cb():
    """Return the global circuit breaker pre-configured for the scheduler endpoint."""
    cb = get_circuit_breaker()
    cb.configure(_SCHEDULER_CB_ENDPOINT, _SCHEDULER_CB_CONFIG)
    return cb


class SchedulerHttpClient:
    """Thin HTTP client for the cell-scheduler service."""

    async def call_scheduler_service(
        self,
        scheduling_request: Dict[str, Any],
        solver_type: str = "OR_TOOLS",
        time_limit_sec: Optional[int] = None,
    ) -> Dict[str, Any]:
        """POST a scheduling request to the cell-scheduler service.

        Args:
            scheduling_request: Complete scheduling request dict.
            solver_type: Solver identifier (OR_TOOLS, GA, SA, TABU, ALNS).
            time_limit_sec: Override solver time limit. If None, uses SOLVER_TIME_LIMITS.

        Returns:
            Scheduler response dict; on error returns ``{"status": "error", ...}``.
        """
        effective_time_limit = (
            time_limit_sec
            if time_limit_sec is not None
            else SOLVER_TIME_LIMITS.get(solver_type.upper(), 60)
        )
        logger.info(
            "call_scheduler_service: solver=%s, time_limit=%ds",
            solver_type,
            effective_time_limit,
        )

        cb = _get_scheduler_cb()
        if not cb.allow(_SCHEDULER_CB_ENDPOINT):
            logger.warning("Circuit breaker OPEN for 'scheduler' — rejecting request")
            return {
                "status": "error",
                "error": "스케줄러 서비스 일시 중단 (circuit open)",
                "scheduled_tasks": [],
            }

        try:
            request_data = {
                "work_orders": scheduling_request.get("work_orders", []),
                "machines": scheduling_request.get("machines", []),
                "machine_type_params": scheduling_request.get("machine_type_params", {}).get(
                    "machine_types", {}
                ),
                "scheduling_horizon": (
                    scheduling_request.get("request", {})
                    .get("scheduling_request", {})
                    .get("scheduling_horizon", {})
                ),
                "constraints": scheduling_request.get("constraints", {}),
                "options": {
                    "solver_type": solver_type,
                    "time_limit_sec": effective_time_limit,
                },
                "amrs": scheduling_request.get("amrs", []),
                "scheduler_config": scheduling_request.get(
                    "scheduler_config",
                    {"lot_size": 1, "amr_transfer_time_sec": 60},
                ),
            }

            async with httpx.AsyncClient(timeout=float(SCHEDULER_TIMEOUT)) as client:
                response = await client.post(
                    f"{SCHEDULER_SERVICE_URL}/api/v1/schedule/solve",
                    json=request_data,
                )
                response.raise_for_status()
                result = response.json()

            cb.record_success(_SCHEDULER_CB_ENDPOINT)
            sched_request_id = result.get("request_id")
            logger.info(
                "Scheduler returned status=%s%s",
                result.get("status"),
                f", request_id={sched_request_id}" if sched_request_id else "",
            )
            return result

        except httpx.HTTPStatusError as exc:
            error_msg = f"HTTP {exc.response.status_code}"
            cb.record_failure(_SCHEDULER_CB_ENDPOINT, error_msg)
            logger.error("Scheduler HTTP error: %s", exc.response.status_code)
            return {
                "status": "error",
                "error": "스케줄러 서비스 응답 오류",
                "scheduled_tasks": [],
            }
        except httpx.TimeoutException:
            cb.record_failure(_SCHEDULER_CB_ENDPOINT, "timeout")
            logger.error("Scheduler service timeout")
            return {
                "status": "error",
                "error": "스케줄러 서비스 시간 초과",
                "scheduled_tasks": [],
            }
        except httpx.RequestError as exc:
            cb.record_failure(_SCHEDULER_CB_ENDPOINT, str(exc))
            logger.error("Scheduler request error: %s", exc)
            return {
                "status": "error",
                "error": "스케줄러 서비스 연결 실패",
                "scheduled_tasks": [],
            }
        except Exception as exc:
            cb.record_failure(_SCHEDULER_CB_ENDPOINT, str(exc))
            logger.error("Scheduler error: %s", exc)
            return {
                "status": "error",
                "error": str(exc),
                "scheduled_tasks": [],
            }
