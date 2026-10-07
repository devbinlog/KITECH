"""
Cell-Scheduler Integration Service — Facade

Delegates to sub-modules in scheduling/:
    projector      — read-side: equipment/WO -> scheduler DTO
    http_client    — HTTP transport + circuit breaker
    result_applier — write-side: ProdResult/WorkOrder persistence
    lock           — Redis distributed lock (replaces _solving bool flag)

WorkOrder contains operations directly (no Job layer).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .scheduling.projector import SchedulerProjector
from .scheduling.http_client import SchedulerHttpClient
from .scheduling.result_applier import SchedulingResultApplier
from .scheduling.lock import with_solver_lock

logger = logging.getLogger(__name__)


class SchedulerIntegrationService:
    """Facade — delegates to projector, http_client, result_applier.

    Maintained for backward compatibility. New code should use the underlying
    modules directly.

    The class-level ``_solving: bool`` flag has been removed and replaced with a
    Redis distributed lock (scheduling/lock.py) that works correctly across
    multiple uvicorn workers.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._projector = SchedulerProjector(db)
        self._http = SchedulerHttpClient()
        self._applier = SchedulingResultApplier(db)

    # ------------------------------------------------------------------
    # Equipment read methods (delegated to projector)
    # ------------------------------------------------------------------

    async def get_equipment_for_scheduler(
        self,
        equipment_ids: Optional[List[int]] = None,
        horizon_start: Optional[datetime] = None,
        horizon_end: Optional[datetime] = None,
        exclude_wo_ids: Optional[Set[int]] = None,
    ) -> List[Dict[str, Any]]:
        return await self._projector.get_equipment_for_scheduler(
            equipment_ids=equipment_ids,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            exclude_wo_ids=exclude_wo_ids,
        )

    async def _get_occupied_slots(
        self,
        equipment_ids: List[int],
        horizon_start: datetime,
        horizon_end: datetime,
        exclude_wo_ids: Optional[Set[int]] = None,
    ) -> Dict[int, List[Dict[str, Any]]]:
        return await self._projector.get_occupied_slots(
            equipment_ids=equipment_ids,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            exclude_wo_ids=exclude_wo_ids,
        )

    def _map_equipment_status(self, mes_status: str) -> str:
        return self._projector._map_equipment_status(mes_status)

    def _calculate_available_from(self, equipment) -> datetime:
        return self._projector._calculate_available_from(equipment)

    # ------------------------------------------------------------------
    # Work order read methods (delegated to projector)
    # ------------------------------------------------------------------

    async def get_work_orders_for_scheduler(
        self,
        status_filter: Optional[List[str]] = None,
        include_scheduled: bool = False,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        return await self._projector.get_work_orders_for_scheduler(
            status_filter=status_filter,
            include_scheduled=include_scheduled,
            limit=limit,
        )

    async def _get_completed_routing_ids(self, work_order_id: int) -> Set[int]:
        return await self._projector.get_completed_routing_ids(work_order_id)

    async def _get_routing_operations(
        self, product_id: int, order_quantity: int = 1
    ) -> List[Dict[str, Any]]:
        return await self._projector.get_routing_operations(product_id, order_quantity)

    # ------------------------------------------------------------------
    # Scheduling request builder (projector + assembly)
    # ------------------------------------------------------------------

    async def create_scheduling_request(
        self,
        horizon_hours: int = 24,
        include_running: bool = False,
        include_scheduled: bool = False,
        base_time: Optional[datetime] = None,
        lot_size: int = 1,
        amr_transfer_time_sec: int = 60,
    ) -> Dict[str, Any]:
        from datetime import timedelta, timezone

        from .scheduling.projector import _ensure_utc

        now = datetime.now(timezone.utc)
        horizon_start = _ensure_utc(base_time) if base_time else now
        horizon_end = horizon_start + timedelta(hours=horizon_hours)

        status_filter = ["READY"]
        if include_running:
            status_filter.append("RUNNING")

        work_orders = await self._projector.get_work_orders_for_scheduler(
            status_filter=status_filter, include_scheduled=include_scheduled
        )

        running_wo_ids: Set[int] = set()
        if include_running:
            running_wo_ids = {
                wo["mes_work_order_id"]
                for wo in work_orders
                if wo.get("mes_work_order_id") is not None and wo.get("status") == "RUNNING"
            }
            if running_wo_ids:
                logger.info(
                    "create_scheduling_request: excluding ProdResult slots for "
                    "%d RUNNING WO IDs: %s",
                    len(running_wo_ids),
                    sorted(running_wo_ids),
                )

        all_equipment = await self._projector.get_equipment_for_scheduler(
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            exclude_wo_ids=running_wo_ids if running_wo_ids else None,
        )

        amrs = []
        machines = []
        for eq in all_equipment:
            if eq.get("machine_type", "").upper() == "AMR":
                amrs.append(
                    {
                        "amr_id": eq["machine_id"],
                        "model": eq.get("machine_name", ""),
                        "status": (
                            "available"
                            if eq.get("status") not in ("MAINTENANCE", "OFFLINE")
                            else "maintenance"
                        ),
                        "current_location": eq.get("location", ""),
                        "accessible_machines": eq.get("accessible_machines", []),
                        "speed_m_per_sec": eq.get("speed_m_per_sec", 1.0),
                    }
                )
            else:
                machines.append(eq)

        # Use spec_data-backed params (loadingType/amrTransportQty from equipment
        # spec) instead of hardcoded defaults, so real scheduling honors the
        # stored AAS values. build_machine_type_params_from_machines() ignores
        # spec and is kept only for the no-DB inspection path.
        machine_type_params = await self._projector.get_machine_type_params()

        return {
            "request": {
                "scheduling_request": {
                    "request_id": f"REQ-{now.strftime('%Y%m%d%H%M%S')}",
                    "request_time": now.isoformat(),
                    "scheduling_horizon": {
                        "start": horizon_start.isoformat(),
                        "end": horizon_end.isoformat(),
                    },
                    "options": {"optimization_goal": "minimize_makespan"},
                },
            },
            "work_orders": work_orders,
            "machines": machines,
            "machine_type_params": machine_type_params,
            "amrs": amrs,
            "scheduler_config": {
                "lot_size": lot_size,
                "amr_transfer_time_sec": amr_transfer_time_sec,
            },
            "cell_layout": {},
            "constraints": {},
        }

    def _build_machine_type_params_from_machines(
        self, machines: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return self._projector.build_machine_type_params_from_machines(machines)

    async def _get_machine_type_params(self) -> Dict[str, Any]:
        return await self._projector.get_machine_type_params()

    # ------------------------------------------------------------------
    # HTTP call (delegated to http_client)
    # ------------------------------------------------------------------

    async def call_scheduler_service(
        self,
        scheduling_request: Dict[str, Any],
        solver_type: str = "OR_TOOLS",
        time_limit_sec: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await self._http.call_scheduler_service(
            scheduling_request=scheduling_request,
            solver_type=solver_type,
            time_limit_sec=time_limit_sec,
        )

    # ------------------------------------------------------------------
    # Result persistence (delegated to result_applier, under Redis lock)
    # ------------------------------------------------------------------

    async def process_scheduling_result(
        self, scheduling_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Persist scheduling result under distributed Redis lock.

        Replaces the TOCTOU-prone class-level ``_solving: bool`` flag.
        Returns HTTP 409 semantics (as a dict) if another worker holds the lock.
        """
        async with with_solver_lock() as acquired:
            if not acquired:
                logger.warning(
                    "process_scheduling_result: solver lock held by another worker — rejecting"
                )
                return {
                    "success": False,
                    "message": (
                        "A scheduling solve is already in progress. "
                        "Please retry after the current solve completes."
                    ),
                    "error": "concurrent_solve",
                }
            return await self._applier.apply(scheduling_result)

    # ------------------------------------------------------------------
    # Gantt / current schedule (delegated to projector)
    # ------------------------------------------------------------------

    async def get_current_schedule(
        self, target_date: Optional[str] = None, include_running: bool = True
    ) -> Dict[str, Any]:
        return await self._projector.get_current_schedule(
            target_date=target_date, include_running=include_running
        )


# ---------------------------------------------------------------------------
# Module-level helper (backward compat)
# ---------------------------------------------------------------------------


async def get_equipment_availability(
    db: AsyncSession, equipment_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """Helper: get equipment availability for scheduler."""
    service = SchedulerIntegrationService(db)
    return await service.get_equipment_for_scheduler(equipment_ids)
