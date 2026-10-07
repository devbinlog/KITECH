"""
Data Aggregation Service for NL-Driven MES

Provides multi-API result aggregation for:
- Daily production status (orders + results + equipment)
- Equipment utilization calculation (KPI)
- LOT traceability (full history)
- Dashboard KPIs
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, date, timezone
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from ..models.equipment import Equipment
from ..models.production import WorkOrder, ProdResult
from ..models.master import ProcessRouting


@dataclass
class AggregatedResult:
    """Standardized aggregated result structure"""

    data: Dict[str, Any]
    errors: List[Dict[str, str]] = field(default_factory=list)
    partial: bool = False
    output_type: str = "dashboard"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AggregationService:
    """Service for aggregating data from multiple API sources"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_daily_production_status(
        self, target_date: Optional[date] = None
    ) -> AggregatedResult:
        """
        Aggregate daily production status from orders, results, and equipment

        Combines:
        - Work orders (status distribution)
        - Production results (quantities, yield)
        - Equipment status (running, idle, error counts)

        Args:
            target_date: Target date (default: today)

        Returns:
            AggregatedResult with dashboard data
        """
        if target_date is None:
            target_date = date.today()

        errors = []
        data = {}

        # 1. Get work order statistics
        try:
            orders_data = await self._get_orders_summary(target_date)
            data["orders"] = orders_data
        except Exception as e:
            errors.append({"source": "orders", "message": str(e)})
            data["orders"] = self._get_orders_fallback()

        # 2. Get production results
        try:
            results_data = await self._get_results_summary(target_date)
            data["results"] = results_data
        except Exception as e:
            errors.append({"source": "results", "message": str(e)})
            data["results"] = self._get_results_fallback()

        # 3. Get equipment status
        try:
            equipment_data = await self._get_equipment_summary()
            data["equipment"] = equipment_data
        except Exception as e:
            errors.append({"source": "equipment", "message": str(e)})
            data["equipment"] = self._get_equipment_fallback()

        # 4. Calculate combined KPIs
        data["kpis"] = self._calculate_daily_kpis(data)
        data["date"] = target_date.isoformat()

        return AggregatedResult(
            data=data, errors=errors, partial=len(errors) > 0, output_type="dashboard"
        )

    async def _get_orders_summary(self, target_date: date) -> Dict[str, Any]:
        """Get work orders summary for a date"""
        start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        # Single query: fetch order details with product info (no duplicate count query)
        orders_query = (
            select(WorkOrder)
            .options(selectinload(WorkOrder.product))
            .where(and_(WorkOrder.created_at >= start_of_day, WorkOrder.created_at <= end_of_day))
            .order_by(WorkOrder.created_at.desc())
            .limit(50)
        )
        orders_result = await self.db.execute(orders_query)
        orders = orders_result.scalars().all()

        # Compute status counts from fetched orders (avoids a second DB round-trip)
        status_counts: Dict[str, int] = {}
        for o in orders:
            status_counts[o.status] = status_counts.get(o.status, 0) + 1

        return {
            "total": sum(status_counts.values()),
            "by_status": status_counts,
            "completed": status_counts.get("DONE", 0),
            "in_progress": status_counts.get("RUNNING", 0),
            "pending": status_counts.get("READY", 0),
            "error": status_counts.get("ERROR", 0),
            "orders": [
                {
                    "id": o.id,
                    "lot_no": o.lot_no,
                    "product_name": o.product.name if o.product else "Unknown",
                    "product_code": o.product.code if o.product else "",
                    "target_qty": o.target_qty,
                    "status": o.status,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
                for o in orders
            ],
        }

    async def _get_results_summary(self, target_date: date) -> Dict[str, Any]:
        """Get production results summary for a date"""
        start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        # Aggregate quantities
        query = select(
            func.sum(ProdResult.ok_qty).label("total_ok"),
            func.sum(ProdResult.ng_qty).label("total_ng"),
            func.count(ProdResult.id).label("result_count"),
        ).where(and_(ProdResult.start_time >= start_of_day, ProdResult.start_time <= end_of_day))
        result = await self.db.execute(query)
        row = result.first()

        total_ok = row.total_ok or 0
        total_ng = row.total_ng or 0
        total_qty = total_ok + total_ng
        yield_rate = (total_ok / total_qty * 100) if total_qty > 0 else 0.0

        return {
            "total_ok_qty": total_ok,
            "total_ng_qty": total_ng,
            "total_qty": total_qty,
            "yield_rate": round(yield_rate, 2),
            "result_count": row.result_count or 0,
        }

    async def _get_equipment_summary(self) -> Dict[str, Any]:
        """Get equipment status summary"""
        query = (
            select(Equipment.current_status, func.count(Equipment.id).label("count"))
            .where(Equipment.is_deleted.is_(False))
            .group_by(Equipment.current_status)
        )
        result = await self.db.execute(query)
        status_counts = {row.current_status: row.count for row in result.all()}

        # Get equipment list with details
        eq_query = (
            select(Equipment).where(Equipment.is_deleted.is_(False)).order_by(Equipment.eq_name)
        )
        eq_result = await self.db.execute(eq_query)
        equipments = eq_result.scalars().all()

        return {
            "total": sum(status_counts.values()),
            "by_status": status_counts,
            "running": status_counts.get("RUN", 0) + status_counts.get("RUNNING", 0),
            "idle": status_counts.get("STOP", 0) + status_counts.get("IDLE", 0),
            "error": status_counts.get("ERROR", 0),
            "equipment_list": [
                {
                    "id": eq.id,
                    "name": eq.eq_name,
                    "type": eq.equipment_type,
                    "status": eq.current_status,
                    "last_updated": eq.updated_at.isoformat() if eq.updated_at else None,
                }
                for eq in equipments
            ],
        }

    def _calculate_daily_kpis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate combined KPIs from aggregated data"""
        orders = data.get("orders", {})
        results = data.get("results", {})
        equipment = data.get("equipment", {})

        total_orders = orders.get("total", 0)
        completed_orders = orders.get("completed", 0)
        completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0.0

        total_equipment = equipment.get("total", 0)
        running_equipment = equipment.get("running", 0)
        utilization_rate = (
            (running_equipment / total_equipment * 100) if total_equipment > 0 else 0.0
        )

        return {
            "completion_rate": round(completion_rate, 2),
            "yield_rate": results.get("yield_rate", 0.0),
            "equipment_utilization": round(utilization_rate, 2),
            "total_production_qty": results.get("total_ok_qty", 0),
        }

    def _get_orders_fallback(self) -> Dict[str, Any]:
        """Fallback data when orders query fails"""
        return {
            "total": 0,
            "by_status": {},
            "completed": 0,
            "in_progress": 0,
            "pending": 0,
            "error": 0,
            "orders": [],
        }

    def _get_results_fallback(self) -> Dict[str, Any]:
        """Fallback data when results query fails"""
        return {
            "total_ok_qty": 0,
            "total_ng_qty": 0,
            "total_qty": 0,
            "yield_rate": 0.0,
            "result_count": 0,
        }

    def _get_equipment_fallback(self) -> Dict[str, Any]:
        """Fallback data when equipment query fails"""
        return {
            "total": 0,
            "by_status": {},
            "running": 0,
            "idle": 0,
            "error": 0,
            "equipment_list": [],
        }

    async def get_equipment_utilization(
        self, equipment_ids: Optional[List[int]] = None, days: int = 7
    ) -> AggregatedResult:
        """
        Calculate equipment utilization metrics

        Args:
            equipment_ids: Optional filter for specific equipment
            days: Number of days to analyze (default: 7)

        Returns:
            AggregatedResult with utilization data
        """
        errors = []
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get equipment list
        eq_query = select(Equipment).where(Equipment.is_deleted.is_(False))
        if equipment_ids:
            eq_query = eq_query.where(Equipment.id.in_(equipment_ids))

        eq_result = await self.db.execute(eq_query)
        equipments = eq_result.scalars().all()

        # Get production results per equipment.
        # Note: func.extract("epoch", ...) is PostgreSQL-specific and returns 0 on SQLite.
        # Fetch raw rows and compute run time in Python (SQLite-compatible).
        results_query = (
            select(
                ProdResult.target_equipment_id,
                ProdResult.ok_qty,
                ProdResult.ng_qty,
                ProdResult.start_time,
                ProdResult.end_time,
            )
            .where(
                and_(
                    ProdResult.start_time >= start_date,
                    ProdResult.start_time <= end_date,
                    ProdResult.target_equipment_id.isnot(None),
                )
            )
        )
        results_result = await self.db.execute(results_query)
        # Accumulate totals per equipment in Python (avoids SQLite epoch incompatibility)
        _eq_accum: Dict[int, Dict[str, Any]] = {}
        for r in results_result.all():
            eq_id = r.target_equipment_id
            if eq_id not in _eq_accum:
                _eq_accum[eq_id] = {"total_ok": 0, "total_ng": 0, "job_count": 0, "total_run_time_sec": 0}
            _eq_accum[eq_id]["total_ok"] += r.ok_qty or 0
            _eq_accum[eq_id]["total_ng"] += r.ng_qty or 0
            _eq_accum[eq_id]["job_count"] += 1
            if r.start_time and r.end_time:
                # Normalize naive datetimes from SQLite to UTC before subtraction
                st = r.start_time if r.start_time.tzinfo else r.start_time.replace(tzinfo=timezone.utc)
                et = r.end_time if r.end_time.tzinfo else r.end_time.replace(tzinfo=timezone.utc)
                _eq_accum[eq_id]["total_run_time_sec"] += max(0, (et - st).total_seconds())
        results_by_equipment = _eq_accum

        # Calculate utilization for each equipment
        total_available_time_sec = days * 24 * 60 * 60
        utilization_data = []

        for eq in equipments:
            eq_results = results_by_equipment.get(eq.id, {})
            run_time_sec = eq_results.get("total_run_time_sec", 0)
            utilization = (
                (run_time_sec / total_available_time_sec * 100)
                if total_available_time_sec > 0
                else 0
            )

            total_qty = eq_results.get("total_ok", 0) + eq_results.get("total_ng", 0)
            yield_rate = (eq_results.get("total_ok", 0) / total_qty * 100) if total_qty > 0 else 0

            utilization_data.append(
                {
                    "equipment_id": eq.id,
                    "equipment_name": eq.eq_name,
                    "equipment_type": eq.equipment_type,
                    "current_status": eq.current_status,
                    "utilization_rate": round(utilization, 2),
                    "run_time_hours": round(run_time_sec / 3600, 2),
                    "job_count": eq_results.get("job_count", 0),
                    "total_ok_qty": eq_results.get("total_ok", 0),
                    "total_ng_qty": eq_results.get("total_ng", 0),
                    "yield_rate": round(yield_rate, 2),
                }
            )

        # Sort by utilization (descending)
        utilization_data.sort(key=lambda x: x["utilization_rate"], reverse=True)

        # Calculate summary statistics
        avg_utilization = (
            sum(u["utilization_rate"] for u in utilization_data) / len(utilization_data)
            if utilization_data
            else 0
        )
        # Bottleneck: highest utilization (manufacturing constraint) — sorted desc so [0]
        bottleneck = utilization_data[0] if utilization_data else None
        # Top performer: highest yield_rate (best quality); if tied, highest utilization.
        # Explicitly distinct from bottleneck (avoids returning the same machine for both).
        top_performer_candidates = sorted(
            utilization_data, key=lambda x: (x["yield_rate"], x["utilization_rate"]), reverse=True
        ) if utilization_data else []
        top_performer = top_performer_candidates[0] if top_performer_candidates else None
        # If top_performer is the same machine as bottleneck and there are alternatives, use next
        if (
            top_performer is not None
            and bottleneck is not None
            and top_performer["equipment_id"] == bottleneck["equipment_id"]
            and len(top_performer_candidates) > 1
        ):
            top_performer = top_performer_candidates[1]

        return AggregatedResult(
            data={
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days,
                },
                "equipment_utilization": utilization_data,
                "summary": {
                    "total_equipment": len(utilization_data),
                    "average_utilization": round(avg_utilization, 2),
                    "top_performer": top_performer["equipment_name"] if top_performer else None,
                    "top_utilization": top_performer["utilization_rate"] if top_performer else 0,
                    "bottleneck": bottleneck["equipment_name"] if bottleneck else None,
                    "bottleneck_utilization": bottleneck["utilization_rate"] if bottleneck else 0,
                },
            },
            errors=errors,
            partial=len(errors) > 0,
            output_type="comparison_chart",
        )

    async def get_lot_traceability(self, lot_no: str) -> AggregatedResult:
        """
        Get full traceability history for a LOT

        Combines:
        - Work order details
        - Production results timeline
        - Equipment used
        - Routing/process information

        Args:
            lot_no: LOT number to trace

        Returns:
            AggregatedResult with traceability timeline
        """
        errors = []

        # 1. Get work order
        order_query = (
            select(WorkOrder)
            .options(
                selectinload(WorkOrder.product),
                selectinload(WorkOrder.scenario),
                selectinload(WorkOrder.results),
            )
            .where(WorkOrder.lot_no == lot_no)
        )
        order_result = await self.db.execute(order_query)
        order = order_result.scalar_one_or_none()

        if not order:
            return AggregatedResult(
                data={"error": f"LOT {lot_no} not found"},
                errors=[{"source": "order", "message": f"LOT {lot_no} not found"}],
                partial=True,
                output_type="error",
            )

        # 2. Get routing information
        routing_data = []
        if order.product_id:
            routing_query = (
                select(ProcessRouting)
                .options(
                    selectinload(ProcessRouting.std_process), selectinload(ProcessRouting.files)
                )
                .where(ProcessRouting.product_id == order.product_id)
                .order_by(ProcessRouting.sequence)
            )
            routing_result = await self.db.execute(routing_query)
            routings = routing_result.scalars().all()

            routing_data = [
                {
                    "sequence": r.sequence,
                    "process_name": r.std_process.name if r.std_process else "Unknown",
                    "process_code": r.std_process.code if r.std_process else "",
                    "files": [{"type": f.file_type, "path": f.file_path} for f in r.files],
                }
                for r in routings
            ]

        # 3. Get production results with equipment details (via join)
        # Use target_equipment_id (the FK for the assigned machine), not equipment_id
        results_query = (
            select(ProdResult, Equipment)
            .outerjoin(Equipment, ProdResult.target_equipment_id == Equipment.id)
            .where(ProdResult.work_order_id == order.id)
            .order_by(ProdResult.start_time)
        )
        results_result = await self.db.execute(results_query)
        results_with_equipment = results_result.all()

        timeline = [
            {
                "id": r.id,
                "start_time": r.start_time.isoformat() if r.start_time else None,
                "end_time": r.end_time.isoformat() if r.end_time else None,
                "ok_qty": r.ok_qty,
                "ng_qty": r.ng_qty,
                "equipment_name": eq.eq_name if eq else None,
                "equipment_type": eq.equipment_type if eq else None,
            }
            for r, eq in results_with_equipment
        ]

        # Extract results and equipment names for summary calculation
        results = [r for r, _ in results_with_equipment]
        equipment_names = [eq.eq_name for r, eq in results_with_equipment if eq is not None]

        # 4. Calculate summary
        total_ok = sum(r.ok_qty or 0 for r in results)
        total_ng = sum(r.ng_qty or 0 for r in results)
        total_qty = total_ok + total_ng
        yield_rate = (total_ok / total_qty * 100) if total_qty > 0 else 0

        return AggregatedResult(
            data={
                "lot_no": lot_no,
                "work_order": {
                    "id": order.id,
                    "status": order.status,
                    "target_qty": order.target_qty,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                },
                "product": {
                    "id": order.product.id if order.product else None,
                    "name": order.product.name if order.product else "Unknown",
                    "code": order.product.code if order.product else "",
                },
                "scenario": {
                    "id": order.scenario.id if order.scenario else None,
                    "name": order.scenario.name if order.scenario else None,
                }
                if order.scenario
                else None,
                "routing": routing_data,
                "timeline": timeline,
                "summary": {
                    "total_ok_qty": total_ok,
                    "total_ng_qty": total_ng,
                    "yield_rate": round(yield_rate, 2),
                    "process_count": len(results),
                    "equipment_used": list(set(equipment_names)),
                },
            },
            errors=errors,
            partial=len(errors) > 0,
            output_type="traceability_timeline",
        )

    async def get_kpi_dashboard(self) -> AggregatedResult:
        """
        Get aggregated KPIs for dashboard display

        Returns:
            AggregatedResult with KPI data
        """
        errors = []
        today = date.today()

        # Today's production
        try:
            today_status = await self.get_daily_production_status(today)
            today_kpis = today_status.data.get("kpis", {})
        except Exception as e:
            errors.append({"source": "today_kpis", "message": str(e)})
            today_kpis = {}

        # Week's trend
        try:
            utilization = await self.get_equipment_utilization(days=7)
            utilization_summary = utilization.data.get("summary", {})
        except Exception as e:
            errors.append({"source": "utilization", "message": str(e)})
            utilization_summary = {}

        # Active work orders count
        active_orders_query = select(func.count(WorkOrder.id)).where(
            WorkOrder.status.in_(["READY", "RUNNING"])
        )
        active_result = await self.db.execute(active_orders_query)
        active_orders = active_result.scalar() or 0

        # Equipment health - count by status
        equipment_query = select(
            func.count(Equipment.id)
            .filter(Equipment.current_status.in_(["RUN", "RUNNING"]))
            .label("running"),
            func.count(Equipment.id)
            .filter(Equipment.current_status.in_(["IDLE", "STOP", "AVAILABLE"]))
            .label("idle"),
            func.count(Equipment.id).filter(Equipment.current_status == "ERROR").label("error"),
            func.count(Equipment.id).label("total"),
        ).where(Equipment.is_deleted.is_(False))
        eq_result = await self.db.execute(equipment_query)
        eq_health = eq_result.first()

        running_eq = eq_health.running if eq_health else 0
        idle_eq = eq_health.idle if eq_health else 0
        error_eq = eq_health.error if eq_health else 0
        total_eq = eq_health.total if eq_health else 0

        return AggregatedResult(
            data={
                "today": {
                    "completion_rate": today_kpis.get("completion_rate", 0),
                    "yield_rate": today_kpis.get("yield_rate", 0),
                    "production_qty": today_kpis.get("total_production_qty", 0),
                },
                "week": {
                    "avg_utilization": utilization_summary.get("average_utilization", 0),
                    "top_performer": utilization_summary.get("top_performer"),
                    "bottleneck": utilization_summary.get("bottleneck"),
                },
                "current": {
                    "active_orders": active_orders,
                    "running_equipment": running_eq,
                    "idle_equipment": idle_eq,
                    "error_equipment": error_eq,
                    "total_equipment": total_eq,
                    # For backward compatibility
                    "healthy_equipment": running_eq + idle_eq,
                },
            },
            errors=errors,
            partial=len(errors) > 0,
            output_type="kpi_dashboard",
        )


# Helper functions for direct usage
async def aggregate_daily_status(
    db: AsyncSession, target_date: Optional[date] = None
) -> AggregatedResult:
    """Helper to get daily production status"""
    service = AggregationService(db)
    return await service.get_daily_production_status(target_date)


async def aggregate_equipment_utilization(
    db: AsyncSession, equipment_ids: Optional[List[int]] = None, days: int = 7
) -> AggregatedResult:
    """Helper to get equipment utilization"""
    service = AggregationService(db)
    return await service.get_equipment_utilization(equipment_ids, days)


async def aggregate_lot_traceability(db: AsyncSession, lot_no: str) -> AggregatedResult:
    """Helper to get LOT traceability"""
    service = AggregationService(db)
    return await service.get_lot_traceability(lot_no)


async def aggregate_kpi_dashboard(db: AsyncSession) -> AggregatedResult:
    """Helper to get KPI dashboard data"""
    service = AggregationService(db)
    return await service.get_kpi_dashboard()
