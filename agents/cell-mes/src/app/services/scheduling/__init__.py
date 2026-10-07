"""Scheduling sub-package.

Decomposed from the god-object scheduler_integration.py.

Modules:
    projector    -- read-side: equipment/WO -> scheduler DTO
    http_client  -- HTTP transport + circuit breaker
    result_applier -- write-side: ProdResult/WorkOrder persistence
    lock         -- Redis distributed lock (replaces class-level _solving flag)
"""

from .projector import SchedulerProjector
from .http_client import SchedulerHttpClient
from .result_applier import SchedulingResultApplier
from .lock import with_solver_lock, is_solving, force_release

__all__ = [
    "SchedulerProjector",
    "SchedulerHttpClient",
    "SchedulingResultApplier",
    "with_solver_lock",
    "is_solving",
    "force_release",
]
