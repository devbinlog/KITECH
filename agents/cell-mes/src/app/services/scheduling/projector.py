"""Read-side projection: equipment/WO -> scheduler DTO.

Extracted from SchedulerIntegrationService (original lines 88-551, 985-1024, 1135-1270).

All methods are read-only DB queries — no mutations.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.downtime import Downtime
from ...models.equipment import Equipment
from ...models.master import ProcessRouting
from ...models.production import ProdResult, WorkOrder

logger = logging.getLogger(__name__)


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalize a datetime to UTC (SQLite returns naive datetimes)."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _parse_calendar(spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert spec_data calendar (AAS schedulerInfo shape) into scheduler shape.

    Accepts AAS idShort keys (camelCase: shiftStart/shiftEnd/breaks/start/end)
    or snake_case. Returns ``{"shift_start", "shift_end", "breaks": [{"start",
    "end"}]}`` matching the scheduler's CalendarSchema, or ``None`` when absent
    or incomplete (so the machine is treated as 24h-available, as before).
    """
    cal = spec.get("calendar")
    if not isinstance(cal, dict):
        return None

    shift_start = cal.get("shiftStart") or cal.get("shift_start")
    shift_end = cal.get("shiftEnd") or cal.get("shift_end")
    if not shift_start or not shift_end:
        return None

    raw_breaks = cal.get("breaks") or []
    if isinstance(raw_breaks, dict):  # AAS collections may serialize as a dict
        raw_breaks = list(raw_breaks.values())

    breaks: List[Dict[str, str]] = []
    for br in raw_breaks:
        if not isinstance(br, dict):
            continue
        b_start = br.get("start") or br.get("startTime")
        b_end = br.get("end") or br.get("endTime")
        if b_start and b_end:
            breaks.append({"start": b_start, "end": b_end})

    return {"shift_start": shift_start, "shift_end": shift_end, "breaks": breaks}


class SchedulerProjector:
    """Read-only projection of MES data into scheduler-compatible DTOs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Equipment projection
    # ------------------------------------------------------------------

    async def get_equipment_for_scheduler(
        self,
        equipment_ids: Optional[List[int]] = None,
        horizon_start: Optional[datetime] = None,
        horizon_end: Optional[datetime] = None,
        exclude_wo_ids: Optional[Set[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Return equipment list in cell-scheduler compatible format."""
        query = select(Equipment).where(Equipment.is_deleted.is_(False))
        if equipment_ids:
            query = query.where(Equipment.id.in_(equipment_ids))

        result = await self.db.execute(query)
        equipments = result.scalars().all()

        occupied_map: Dict[int, List[Dict[str, Any]]] = {}
        if horizon_start and horizon_end:
            occupied_map = await self.get_occupied_slots(
                [eq.id for eq in equipments],
                horizon_start,
                horizon_end,
                exclude_wo_ids=exclude_wo_ids,
            )

        # AAS references other machines by aas_id; the solver matches against
        # machine_id ("EQ-{id}"). Build a lookup so we can translate references.
        aas_id_to_machine_id = {
            eq.aas_id: f"EQ-{eq.id}" for eq in equipments if eq.aas_id
        }

        scheduler_machines = []
        for eq in equipments:
            scheduler_status = self._map_equipment_status(eq.current_status)
            available_from = self._calculate_available_from(eq)

            machine_type = eq.equipment_type.upper() if eq.equipment_type else "GENERAL"
            spec = eq.spec_data or {}
            raw_machine_type = spec.get("machine_type") or spec.get("machineType")
            if raw_machine_type:
                machine_type = str(raw_machine_type).upper()

            setup_change_time = 5
            raw_setup = spec.get("setup_change_time_min") or spec.get("setupChangeTimeMin")
            if raw_setup is not None:
                setup_change_time = raw_setup

            current_setup_id = None
            if eq.last_data and "current_setup_id" in eq.last_data:
                current_setup_id = eq.last_data["current_setup_id"]
            if current_setup_id is None:
                current_setup_id = spec.get("currentSetupId") or spec.get(
                    "current_setup_id"
                )

            location = spec.get("location", "")
            accessible_machines = (
                spec.get("accessible_machines")
                or spec.get("accessibleMachines")
                or []
            )
            if isinstance(accessible_machines, dict):
                accessible_machines = list(accessible_machines.values())
            # Translate AAS-id references to scheduler machine_ids ("EQ-{id}").
            # Unknown entries (already EQ-ids, or not in this set) pass through.
            accessible_machines = [
                aas_id_to_machine_id.get(m, m) for m in accessible_machines
            ]

            speed_m_per_sec = (
                spec.get("speed_m_per_sec")
                or spec.get("speedMPerSec")
                or 1.0
            )

            calendar = _parse_calendar(spec)

            scheduler_machines.append(
                {
                    "machine_id": f"EQ-{eq.id}",
                    "machine_name": eq.eq_name,
                    "machine_type": machine_type,
                    "status": scheduler_status,
                    "available_from": available_from.isoformat(),
                    "current_setup_id": current_setup_id,
                    "setup_change_time_min": setup_change_time,
                    "occupied_slots": occupied_map.get(eq.id, []),
                    "mes_equipment_id": eq.id,
                    "aas_id": eq.aas_id,
                    "location": location,
                    "accessible_machines": accessible_machines,
                    "speed_m_per_sec": speed_m_per_sec,
                    "calendar": calendar,
                }
            )

        return scheduler_machines

    async def get_occupied_slots(
        self,
        equipment_ids: List[int],
        horizon_start: datetime,
        horizon_end: datetime,
        exclude_wo_ids: Optional[Set[int]] = None,
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Query ProdResult + Downtime records that occupy equipment during the horizon.

        Returns equipment_id -> list of {start, end, wo_id} in seconds from
        horizon_start for scheduler compatibility.
        """
        from sqlalchemy import and_, or_

        horizon_start = _ensure_utc(horizon_start)
        horizon_end = _ensure_utc(horizon_end)

        # Include all ProdResults from start of scheduling day to avoid past overlaps.
        day_start = horizon_start.replace(hour=0, minute=0, second=0, microsecond=0)

        query = (
            select(ProdResult)
            .where(
                and_(
                    ProdResult.target_equipment_id.in_(equipment_ids),
                    ProdResult.start_time.isnot(None),
                    ProdResult.end_time.isnot(None),
                    ProdResult.start_time < horizon_end,
                    ProdResult.end_time > day_start,
                )
            )
            .order_by(ProdResult.start_time)
        )

        if exclude_wo_ids:
            query = query.where(ProdResult.work_order_id.notin_(exclude_wo_ids))
            logger.debug(
                "get_occupied_slots: excluding ProdResults for %d WO IDs: %s",
                len(exclude_wo_ids),
                sorted(exclude_wo_ids),
            )

        result = await self.db.execute(query)
        prod_results = result.scalars().all()

        occupied: Dict[int, List[Dict[str, Any]]] = {}
        for pr in prod_results:
            eq_id = pr.target_equipment_id
            pr_start = _ensure_utc(pr.start_time)
            pr_end = _ensure_utc(pr.end_time)
            start_sec = max(0, int((pr_start - horizon_start).total_seconds()))
            end_sec = max(start_sec, int((pr_end - horizon_start).total_seconds()))
            occupied.setdefault(eq_id, []).append(
                {"start": start_sec, "end": end_sec, "wo_id": f"WO-{pr.work_order_id}"}
            )

        downtime_query = (
            select(Downtime)
            .where(
                and_(
                    Downtime.equipment_id.in_(equipment_ids),
                    Downtime.start_time < horizon_end,
                    or_(
                        Downtime.end_time > day_start,
                        Downtime.end_time.is_(None),
                    ),
                )
            )
            .order_by(Downtime.start_time)
        )

        dt_result = await self.db.execute(downtime_query)
        downtimes = dt_result.scalars().all()

        for dt in downtimes:
            eq_id = dt.equipment_id
            dt_start = _ensure_utc(dt.start_time)
            dt_end = _ensure_utc(dt.end_time) or horizon_end
            start_sec = max(0, int((dt_start - horizon_start).total_seconds()))
            end_sec = max(start_sec, int((dt_end - horizon_start).total_seconds()))
            occupied.setdefault(eq_id, []).append(
                {"start": start_sec, "end": end_sec, "wo_id": f"DT-{dt.id}"}
            )

        logger.info(
            "Found %d occupied slots (incl. %d downtimes) across %d equipments",
            sum(len(v) for v in occupied.values()),
            len(downtimes),
            len(occupied),
        )
        return occupied

    def _map_equipment_status(self, mes_status: str) -> str:
        """Map MES equipment status to scheduler-compatible status."""
        status_map = {
            "AVAILABLE": "AVAILABLE",
            "RUNNING": "RUNNING",
            "RUN": "RUNNING",
            "IDLE": "AVAILABLE",
            "STOP": "AVAILABLE",
            "ERROR": "ERROR",
            "MAINTENANCE": "MAINTENANCE",
            "OFFLINE": "OFFLINE",
        }
        return status_map.get(mes_status, "OFFLINE")

    def _calculate_available_from(self, equipment: Equipment) -> datetime:
        """Estimate when equipment will become available."""
        now = datetime.now(timezone.utc)
        if equipment.current_status in ["AVAILABLE", "IDLE", "STOP"]:
            return now
        elif equipment.current_status in ["RUN", "RUNNING"]:
            if equipment.last_data and "estimated_end_time" in equipment.last_data:
                return _ensure_utc(
                    datetime.fromisoformat(equipment.last_data["estimated_end_time"])
                )
            return now + timedelta(minutes=30)
        elif equipment.current_status == "MAINTENANCE":
            if equipment.spec_data and "maintenance_end" in equipment.spec_data:
                return _ensure_utc(
                    datetime.fromisoformat(equipment.spec_data["maintenance_end"])
                )
            return now + timedelta(hours=2)
        else:
            return now + timedelta(hours=1)

    # ------------------------------------------------------------------
    # Work order projection
    # ------------------------------------------------------------------

    async def get_work_orders_for_scheduler(
        self,
        status_filter: Optional[List[str]] = None,
        include_scheduled: bool = False,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Return work orders in cell-scheduler compatible format."""
        from sqlalchemy import or_

        if status_filter is None:
            status_filter = ["READY"]

        query = (
            select(WorkOrder)
            .options(selectinload(WorkOrder.product))
            .where(WorkOrder.status.in_(status_filter))
        )

        if not include_scheduled:
            query = query.where(
                or_(
                    WorkOrder.start_time.is_(None),
                    WorkOrder.status == "RUNNING",
                )
            )

        query = query.order_by(WorkOrder.priority.desc(), WorkOrder.created_at).limit(limit)

        result = await self.db.execute(query)
        orders = result.scalars().all()

        scheduler_work_orders = []
        for order in orders:
            operations_data = await self.get_routing_operations(order.product_id, order.target_qty)

            if order.status == "RUNNING" and operations_data:
                completed_routing_ids = await self.get_completed_routing_ids(order.id)
                if completed_routing_ids:
                    operations_data = [
                        op for op in operations_data
                        if op.get("process_routing_id") not in completed_routing_ids
                    ]
                    logger.info(
                        "WO-%d (RUNNING): filtered out %d completed routing steps, %d remaining",
                        order.id,
                        len(completed_routing_ids),
                        len(operations_data),
                    )

            if not operations_data:
                logger.info("WO-%d: skipping — no schedulable operations remaining", order.id)
                continue

            raw_release = order.start_time if order.start_time else datetime.now(timezone.utc)
            if raw_release.tzinfo is None:
                raw_release = raw_release.replace(tzinfo=timezone.utc)
            release_date = max(raw_release, datetime.now(timezone.utc))

            wo_data = {
                "wo_id": f"WO-{order.id}",
                "product_id": f"PROD-{order.product_id}",
                "product_name": order.product.name if order.product else "Unknown",
                "order_quantity": order.target_qty,
                "due_date": (
                    order.due_date.replace(tzinfo=timezone.utc)
                    if order.due_date and not order.due_date.tzinfo
                    else order.due_date or (datetime.now(timezone.utc) + timedelta(days=7))
                ).isoformat(),
                "priority": order.priority if order.priority else 5,
                "release_date": release_date.isoformat(),
                "customer": order.remarks or "Internal",
                "operations": operations_data,
                "mes_work_order_id": order.id,
                "lot_no": order.lot_no,
                "scenario_id": order.scenario_id,
                "status": order.status,
            }
            scheduler_work_orders.append(wo_data)

        return scheduler_work_orders

    async def get_completed_routing_ids(self, work_order_id: int) -> Set[int]:
        """Return set of process_routing_ids already completed for a work order."""
        now = datetime.now(timezone.utc)
        query = select(ProdResult).where(
            ProdResult.work_order_id == work_order_id,
            ProdResult.process_routing_id.isnot(None),
            ProdResult.end_time.isnot(None),
        )
        result = await self.db.execute(query)
        prod_results = result.scalars().all()

        completed_ids: Set[int] = set()
        for pr in prod_results:
            pr_end = _ensure_utc(pr.end_time)
            if pr_end <= now:
                completed_ids.add(pr.process_routing_id)
        return completed_ids

    async def get_routing_operations(
        self, product_id: int, order_quantity: int = 1
    ) -> List[Dict[str, Any]]:
        """Return routing operations for a product in scheduler-compatible format."""
        query = (
            select(ProcessRouting)
            .options(
                selectinload(ProcessRouting.std_process),
                selectinload(ProcessRouting.files),
            )
            .where(ProcessRouting.product_id == product_id)
            .order_by(ProcessRouting.sequence)
        )

        result = await self.db.execute(query)
        routings = result.scalars().all()

        if not routings:
            return []

        operations = []
        prev_op_id = None

        for routing in routings:
            op_id = f"OP-{routing.id}"
            nc_file = next((f for f in routing.files if f.file_type == "NC"), None)

            cycle_time = 60
            if routing.cycle_time_sec is not None:
                cycle_time = routing.cycle_time_sec
            elif routing.std_process and routing.std_process.cycle_time_sec is not None:
                cycle_time = routing.std_process.cycle_time_sec

            nc_code = {
                "program_id": (
                    nc_file.file_path.split("/")[-1] if nc_file else f"NC-{routing.id}"
                ),
                "file_path": nc_file.file_path if nc_file else "",
                "cycle_time_sec": cycle_time,
                "cycle_time_confidence": 0.9,
                "tool_list": [],
                "tool_change_count": 0,
                "compatible_machines": (nc_file.compatible_machines or []) if nc_file else [],
            }

            if routing.required_machines:
                machines_list = [str(machine).upper() for machine in routing.required_machines]
            elif routing.std_process and routing.std_process.required_machines:
                machines_list = [
                    str(machine).upper() for machine in routing.std_process.required_machines
                ]
            elif routing.std_process and routing.std_process.equipment_type:
                machines_list = [routing.std_process.equipment_type.upper()]
            elif routing.std_process and routing.std_process.code:
                machines_list = [routing.std_process.code.upper()]
            else:
                machines_list = ["GENERAL"]

            operation = {
                "op_id": op_id,
                "op_name": (
                    routing.std_process.name
                    if routing.std_process
                    else f"Operation {routing.sequence}"
                ),
                "sequence": routing.sequence,
                "predecessors": [prev_op_id] if prev_op_id else [],
                "required_machines": machines_list,
                "setup_id": routing.setup_id or f"SETUP-{routing.std_process_id}",
                "nc_code": nc_code,
                "cycle_time_sec": cycle_time,
                "process_routing_id": routing.id,
            }
            operations.append(operation)
            prev_op_id = op_id

        return operations

    # ------------------------------------------------------------------
    # Machine type params
    # ------------------------------------------------------------------

    def build_machine_type_params_from_machines(
        self, machines: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build machine type parameters from pre-loaded machines list (no DB query)."""
        machine_types: Dict[str, Any] = {}
        for m in machines:
            machine_type = m.get("machine_type", "GENERAL")
            if machine_type not in machine_types:
                machine_types[machine_type] = {
                    "loading_type": "manual",
                    "amr_transport_qty": 1,
                    "exchange_time_sec": 30,
                    "load_unload_time_sec": 60,
                }
        return {"machine_types": machine_types}

    async def get_machine_type_params(self) -> Dict[str, Any]:
        """Get machine type parameters from equipment spec_data via DB query."""
        query = select(Equipment).where(Equipment.is_deleted.is_(False))
        result = await self.db.execute(query)
        equipments = result.scalars().all()

        machine_types: Dict[str, Any] = {}
        for eq in equipments:
            machine_type = eq.equipment_type.upper() if eq.equipment_type else "GENERAL"
            spec = eq.spec_data or {}
            raw_machine_type = spec.get("machine_type") or spec.get("machineType")
            if raw_machine_type:
                machine_type = str(raw_machine_type).upper()

            # AMRs are transported, not machined — they carry no machine-type
            # params and shouldn't appear as a machine_type entry.
            if machine_type == "AMR":
                continue

            if machine_type not in machine_types:
                machine_types[machine_type] = {
                    "loading_type": "manual",
                    "amr_transport_qty": 1,
                    "exchange_time_sec": 30,
                    "load_unload_time_sec": 60,
                }
                if spec:
                    # Prefer the nested AAS shape (machineTypeParams.*), falling
                    # back to top-level keys for the legacy "lifted" flattening.
                    # Accept both camelCase (AAS idShort) and snake_case.
                    mtp = (
                        spec.get("machineTypeParams")
                        or spec.get("machine_type_params")
                        or {}
                    )
                    loading_type = (
                        mtp.get("loadingType")
                        or mtp.get("loading_type")
                        or spec.get("loadingType")
                        or spec.get("loading_type")
                    )
                    if loading_type:
                        machine_types[machine_type]["loading_type"] = loading_type
                    amr_qty = (
                        mtp.get("amrTransportQty")
                        or mtp.get("amr_transport_qty")
                        or spec.get("amrTransportQty")
                        or spec.get("amr_transport_qty")
                    )
                    if amr_qty is not None:
                        machine_types[machine_type]["amr_transport_qty"] = amr_qty

        return {"machine_types": machine_types}

    # ------------------------------------------------------------------
    # Gantt / current schedule query
    # ------------------------------------------------------------------

    async def get_current_schedule(
        self,
        target_date: Optional[str] = None,
        include_running: bool = True,
    ) -> Dict[str, Any]:
        """Return current schedule in Gantt chart format."""
        from sqlalchemy import and_, or_

        if target_date:
            try:
                start_of_day = _ensure_utc(
                    datetime.fromisoformat(target_date)
                ).replace(hour=0, minute=0, second=0, microsecond=0)
            except ValueError:
                start_of_day = datetime.now(timezone.utc).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
        else:
            start_of_day = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        end_of_day = start_of_day + timedelta(days=1)

        status_filter = (
            ["READY", "SCHEDULED", "RUNNING", "PAUSE", "DONE"]
            if include_running
            else ["READY", "SCHEDULED"]
        )

        query = (
            select(WorkOrder)
            .options(selectinload(WorkOrder.product))
            .where(
                and_(
                    WorkOrder.status.in_(status_filter),
                    WorkOrder.start_time.isnot(None),
                    or_(
                        and_(
                            WorkOrder.start_time >= start_of_day,
                            WorkOrder.start_time < end_of_day,
                        ),
                        and_(
                            WorkOrder.end_time >= start_of_day,
                            WorkOrder.end_time < end_of_day,
                        ),
                        and_(
                            WorkOrder.start_time < start_of_day,
                            WorkOrder.end_time >= end_of_day,
                        ),
                    ),
                )
            )
            .order_by(WorkOrder.start_time)
        )

        result = await self.db.execute(query)
        orders = list(result.scalars().all())

        eq_query = select(Equipment).where(Equipment.is_deleted.is_(False))
        eq_result = await self.db.execute(eq_query)
        equipments = list(eq_result.scalars().all())

        availability = []
        wo_ids = [o.id for o in orders]
        if wo_ids:
            from sqlalchemy import and_

            pr_query = select(ProdResult).where(
                and_(
                    ProdResult.work_order_id.in_(wo_ids),
                    ProdResult.target_equipment_id.isnot(None),
                    ProdResult.start_time.isnot(None),
                    ProdResult.end_time.isnot(None),
                    ProdResult.start_time < end_of_day,
                    ProdResult.end_time > start_of_day,
                )
            )
            pr_result = await self.db.execute(pr_query)
            prod_results = list(pr_result.scalars().all())
        else:
            prod_results = []

        equipment_results: Dict[int, List[ProdResult]] = {eq.id: [] for eq in equipments}
        for pr in prod_results:
            if pr.target_equipment_id in equipment_results:
                equipment_results[pr.target_equipment_id].append(pr)

        wo_map = {o.id: o for o in orders}

        for eq in equipments:
            eq_results = equipment_results.get(eq.id, [])
            schedule_slots = []
            for pr in eq_results:
                wo = wo_map.get(pr.work_order_id)
                if wo:
                    schedule_slots.append(
                        {
                            "slot_start": (
                                pr.start_time.isoformat() if pr.start_time else None
                            ),
                            "slot_end": (
                                pr.end_time.isoformat() if pr.end_time else None
                            ),
                            "status": wo.status,
                            "work_order_id": wo.id,
                            "lot_no": wo.lot_no,
                            "product": wo.product.name if wo.product else None,
                            "operation_id": pr.process_routing_id,
                        }
                    )
            if schedule_slots:
                availability.append(
                    {
                        "equipment_id": f"EQ-{eq.id}",
                        "equipment_name": eq.eq_name,
                        "equipment_type": eq.equipment_type,
                        "schedule": schedule_slots,
                        "summary": {
                            "total_slots": len(schedule_slots),
                            "running_slots": len(
                                [s for s in schedule_slots if s["status"] == "RUNNING"]
                            ),
                        },
                    }
                )

        return {
            "date": start_of_day.strftime("%Y-%m-%d"),
            "availability": availability,
            "summary": {
                "total_equipments": len(equipments),
                "total_scheduled_orders": len(orders),
                "running_orders": len([o for o in orders if o.status == "RUNNING"]),
            },
        }
