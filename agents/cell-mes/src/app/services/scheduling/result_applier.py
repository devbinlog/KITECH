"""Write-side: persist scheduling results to ProdResult / WorkOrder.

Extracted from SchedulerIntegrationService (original lines 552-839).

Uses the Redis distributed lock (lock.py) instead of the class-level
``_solving: bool`` flag.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Set

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.production import ProdResult, WorkOrder

logger = logging.getLogger(__name__)


def _ensure_utc(dt) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class SchedulingResultApplier:
    """Persists a scheduler response into the MES database.

    The distributed solver lock must be held by the **caller** before invoking
    ``apply()``.  The facade (SchedulerIntegrationService.process_scheduling_result)
    is responsible for acquiring it.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def apply(self, scheduling_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a scheduling result: delete stale ProdResults, insert new ones,
        update WorkOrder timestamps.

        Returns a summary dict with ``success``, ``updated_orders``,
        ``created_results``, and ``errors`` keys.
        """
        if scheduling_result.get("status") != "success":
            return {
                "success": False,
                "message": f"Scheduling failed: {scheduling_result.get('status')}",
                "error": scheduling_result.get("error"),
            }

        scheduled_tasks = scheduling_result.get("scheduled_tasks", [])
        updated_orders: List[Dict[str, Any]] = []
        created_results: List[Dict[str, Any]] = []

        # Step 1: delete stale future ProdResults for work orders in this result
        now_utc = datetime.now(timezone.utc)
        wo_ids_in_result: Set[int] = set()
        for task in scheduled_tasks:
            wo_id_str = task.get("wo_id", "")
            if wo_id_str.startswith("WO-"):
                try:
                    wo_ids_in_result.add(int(wo_id_str.replace("WO-", "")))
                except ValueError:
                    pass

        if wo_ids_in_result:
            del_stmt = delete(ProdResult).where(
                ProdResult.work_order_id.in_(wo_ids_in_result),
                ProdResult.end_time > now_utc,
            )
            del_result = await self.db.execute(del_stmt)
            deleted_count = del_result.rowcount
            if deleted_count:
                logger.info(
                    "apply: deleted %d stale future ProdResults for %d WO(s)",
                    deleted_count,
                    len(wo_ids_in_result),
                )

        # Step 2: resolve horizon_start
        gantt_data = scheduling_result.get("gantt_data") or {}
        horizon_start_str = gantt_data.get("start", "")
        if horizon_start_str:
            horizon_start = datetime.fromisoformat(horizon_start_str.replace("Z", "+00:00"))
        else:
            logger.warning(
                "Scheduling result missing gantt_data.start — using current time as fallback"
            )
            horizon_start = datetime.now(timezone.utc)

        # Step 3: group and aggregate lot-level tasks per (wo_id, op_id)
        wo_tasks: Dict[str, List[Dict]] = {}
        for task in scheduled_tasks:
            wo_id = task.get("wo_id", "")
            wo_tasks.setdefault(wo_id, []).append(task)

        wo_tasks = {
            wo_id: self._aggregate_lots(tasks) for wo_id, tasks in wo_tasks.items()
        }

        # Step 4: batch-load work orders
        order_ids = []
        for wo_id_str in wo_tasks:
            if wo_id_str.startswith("WO-"):
                try:
                    order_ids.append(int(wo_id_str.replace("WO-", "")))
                except ValueError:
                    continue

        if order_ids:
            q = select(WorkOrder).where(WorkOrder.id.in_(order_ids))
            result = await self.db.execute(q)
            orders_map = {o.id: o for o in result.scalars().all()}
        else:
            orders_map = {}

        errors: List[str] = []

        # Step 5: insert ProdResults + update WorkOrders
        for wo_id_str, tasks in wo_tasks.items():
            if not wo_id_str.startswith("WO-"):
                continue

            try:
                mes_order_id = int(wo_id_str.replace("WO-", ""))
                order = orders_map.get(mes_order_id)

                if not order:
                    logger.warning("Work order not found: %d", mes_order_id)
                    errors.append(f"WO {wo_id_str}: not found in database")
                    continue

                wo_start = None
                wo_end = None
                wo_insert_count = 0

                for task in tasks:
                    task_start = horizon_start + timedelta(seconds=task.get("start_time", 0))
                    task_end = horizon_start + timedelta(seconds=task.get("end_time", 0))

                    if wo_start is None or task_start < wo_start:
                        wo_start = task_start
                    if wo_end is None or task_end > wo_end:
                        wo_end = task_end

                    op_id_str = task.get("op_id", "")
                    process_routing_id = None
                    if op_id_str.startswith("OP-"):
                        try:
                            process_routing_id = int(op_id_str.replace("OP-", ""))
                        except ValueError:
                            pass

                    machine_id_str = task.get("machine_id", "")
                    target_equipment_id = None
                    if machine_id_str.startswith("EQ-"):
                        try:
                            target_equipment_id = int(machine_id_str.replace("EQ-", ""))
                        except ValueError:
                            logger.warning("Invalid machine_id format: %s", machine_id_str)

                    nested = None
                    try:
                        nested = await self.db.begin_nested()
                        prod_result = ProdResult(
                            work_order_id=order.id,
                            process_routing_id=process_routing_id,
                            target_equipment_id=target_equipment_id,
                            start_time=task_start,
                            end_time=task_end,
                            ok_qty=0,
                            ng_qty=0,
                        )
                        self.db.add(prod_result)
                        await nested.commit()
                        wo_insert_count += 1
                        created_results.append(
                            {
                                "work_order_id": mes_order_id,
                                "op_id": op_id_str,
                                "machine_id": machine_id_str,
                                "start_time": task_start.isoformat(),
                                "end_time": task_end.isoformat(),
                            }
                        )
                    except Exception as prod_err:
                        if nested is not None:
                            await nested.rollback()
                        err_msg = (
                            f"WO {wo_id_str} op {op_id_str}: ProdResult create failed — {prod_err}"
                        )
                        logger.error(err_msg)
                        errors.append(err_msg)

                if wo_insert_count == 0:
                    logger.warning(
                        "WO %s: all %d ProdResult inserts failed — skipping WO timestamp update",
                        wo_id_str,
                        len(tasks),
                    )
                    continue

                order.start_time = wo_start
                order.end_time = wo_end
                if order.status == "READY":
                    order.status = "SCHEDULED"
                self.db.add(order)

                assigned_machines = list(
                    dict.fromkeys(t.get("machine_id", "") for t in tasks if t.get("machine_id"))
                )
                updated_orders.append(
                    {
                        "mes_order_id": mes_order_id,
                        "lot_no": order.lot_no,
                        "scheduled_start": wo_start.isoformat() if wo_start else None,
                        "scheduled_end": wo_end.isoformat() if wo_end else None,
                        "operations_count": len(tasks),
                        "machine_id": (
                            ", ".join(assigned_machines) if assigned_machines else None
                        ),
                    }
                )

                logger.info(
                    "Updated WO %d: %s – %s, %d/%d operations inserted",
                    mes_order_id,
                    wo_start,
                    wo_end,
                    wo_insert_count,
                    len(tasks),
                )

            except ValueError as exc:
                logger.warning("Skipping WO %s: invalid ID — %s", wo_id_str, exc)
                errors.append(f"WO {wo_id_str}: invalid ID format — {exc}")
                continue

        if errors:
            logger.warning(
                "apply: %d error(s) during ProdResult creation: %s",
                len(errors),
                "; ".join(errors),
            )

        try:
            await self.db.commit()
            logger.info(
                "Committed %d WO updates, %d prod results",
                len(updated_orders),
                len(created_results),
            )
        except Exception as exc:
            await self.db.rollback()
            logger.error("Failed to commit scheduling results: %s", exc)
            return {
                "success": False,
                "message": f"Database commit failed: {exc}",
                "error": str(exc),
            }

        return {
            "success": True,
            "message": f"Updated {len(updated_orders)} work orders with scheduling data",
            "updated_orders": updated_orders,
            "created_results": created_results,
            "error_count": len(errors),
            "errors": errors if errors else None,
            "statistics": scheduling_result.get("statistics", {}),
            "quality_metrics": scheduling_result.get("quality_metrics", {}),
        }

    @staticmethod
    def _aggregate_lots(tasks: List[Dict]) -> List[Dict]:
        """Aggregate lot-level tasks to one entry per (wo_id, op_id)."""
        op_map: Dict[str, Dict] = {}
        for t in tasks:
            op_id = t.get("op_id", "")
            if op_id not in op_map:
                op_map[op_id] = dict(t)
                op_map[op_id]["quantity"] = t.get("quantity", 0)
            else:
                agg = op_map[op_id]
                agg["start_time"] = min(
                    agg["start_time"], t.get("start_time", agg["start_time"])
                )
                agg["end_time"] = max(
                    agg["end_time"], t.get("end_time", agg["end_time"])
                )
                agg["quantity"] = agg.get("quantity", 0) + t.get("quantity", 0)
        return list(op_map.values())
