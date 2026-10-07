"""Analytics endpoints: Aggregated KPIs and production metrics."""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Path, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from ...deps import DBSession, CurrentUser
from ....services.aggregation_service import (
    AggregationService,
    aggregate_daily_status,
    aggregate_equipment_utilization,
    aggregate_lot_traceability,
    aggregate_kpi_dashboard,
)
from ....services.cache_service import get_cache
from ....models.equipment import Equipment
from ....models.production import WorkOrder, ProdResult

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Response Models
# ============================================================================


class KPIResponse(BaseModel):
    """KPI data response"""

    completion_rate: float = Field(..., description="Order completion rate (%)")
    yield_rate: float = Field(..., description="Production yield rate (%)")
    equipment_utilization: float = Field(..., description="Equipment utilization rate (%)")
    total_production_qty: int = Field(..., description="Total production quantity")


class OrderSummary(BaseModel):
    """Order summary data"""

    total: int
    by_status: Dict[str, int]
    completed: int
    in_progress: int
    pending: int
    error: int


class ResultsSummary(BaseModel):
    """Production results summary"""

    total_ok_qty: int
    total_ng_qty: int
    total_qty: int
    yield_rate: float
    result_count: int


class EquipmentSummary(BaseModel):
    """Equipment status summary"""

    total: int
    by_status: Dict[str, int]
    running: int
    idle: int
    error: int


class DailyStatusResponse(BaseModel):
    """Daily production status response"""

    date: str
    orders: OrderSummary
    results: ResultsSummary
    equipment: EquipmentSummary
    kpis: KPIResponse
    errors: List[Dict[str, str]] = []
    partial: bool = False


class UtilizationItem(BaseModel):
    """Single equipment utilization data"""

    equipment_id: int
    equipment_name: str
    equipment_type: str
    current_status: str
    utilization_rate: float
    run_time_hours: float
    job_count: int
    total_ok_qty: int
    total_ng_qty: int
    yield_rate: float


class UtilizationSummary(BaseModel):
    """Utilization summary statistics"""

    total_equipment: int
    average_utilization: float
    top_performer: Optional[str]
    top_utilization: float
    bottleneck: Optional[str]
    bottleneck_utilization: float


class UtilizationResponse(BaseModel):
    """Equipment utilization response"""

    period: Dict[str, Any]
    equipment_utilization: List[UtilizationItem]
    summary: UtilizationSummary
    errors: List[Dict[str, str]] = []
    partial: bool = False


class TraceabilityTimelineItem(BaseModel):
    """Single timeline entry"""

    id: int
    start_time: Optional[str]
    end_time: Optional[str]
    ok_qty: int
    ng_qty: int
    equipment_name: Optional[str]
    equipment_type: Optional[str]


class TraceabilitySummary(BaseModel):
    """Traceability summary"""

    total_ok_qty: int
    total_ng_qty: int
    yield_rate: float
    process_count: int
    equipment_used: List[str]


class TraceabilityResponse(BaseModel):
    """LOT traceability response"""

    lot_no: str
    work_order: Dict[str, Any]
    product: Dict[str, Any]
    scenario: Optional[Dict[str, Any]]
    routing: List[Dict[str, Any]]
    timeline: List[TraceabilityTimelineItem]
    summary: TraceabilitySummary
    errors: List[Dict[str, str]] = []
    partial: bool = False


class KPIDashboardResponse(BaseModel):
    """KPI dashboard response"""

    today: Dict[str, Any]
    week: Dict[str, Any]
    current: Dict[str, Any]
    errors: List[Dict[str, str]] = []
    partial: bool = False


# ============================================================================
# Frontend-aligned Endpoints (matching frontend analyticsService paths)
# ============================================================================


def _parse_date_range(
    date_from: Optional[str], date_to: Optional[str], default_days: int = 7
) -> tuple[date, date]:
    """Parse date_from/date_to strings into date objects."""
    today = date.today()
    if date_to:
        try:
            end = date.fromisoformat(date_to)
        except ValueError:
            end = today
            logger.warning(f"Invalid date_to format: {date_to}, using today")
    else:
        end = today

    if date_from:
        try:
            start = date.fromisoformat(date_from)
        except ValueError:
            start = end - timedelta(days=default_days)
            logger.warning(f"Invalid date_from format: {date_from}, using default")
    else:
        start = end - timedelta(days=default_days)

    # Fix reversed date range
    if start > end:
        start, end = end, start
        logger.warning(f"date_from > date_to, swapped: {start} ~ {end}")

    return start, end


@router.get("/kpi/summary")
async def get_kpi_summary(
    db: DBSession,
    current_user: CurrentUser,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """KPI summary with OEE metrics for the analytics dashboard."""
    start, end = _parse_date_range(date_from, date_to)
    service = AggregationService(db)

    # Aggregate production data over the date range
    total_ok = 0
    total_ng = 0
    total_target = 0
    trend_data = []
    # Accumulate daily availability readings to compute period average,
    # instead of using a real-time equipment snapshot (which reflects only the
    # current moment and not the actual availability over the reporting period).
    period_availability_sum = 0.0
    period_days_counted = 0

    current = start
    while current <= end:
        daily = await service.get_daily_production_status(current)
        results = daily.data.get("results", {})
        orders = daily.data.get("orders", {})
        kpis = daily.data.get("kpis", {})

        day_ok = results.get("total_ok_qty", 0)
        day_ng = results.get("total_ng_qty", 0)
        total_ok += day_ok
        total_ng += day_ng

        # Sum target quantities from orders
        for o in orders.get("orders", []):
            total_target += o.get("target_qty", 0)

        # Availability for this day: use equipment utilization KPI (period-based),
        # not a real-time snapshot of current running equipment.
        day_availability = kpis.get("equipment_utilization", 0)
        period_availability_sum += day_availability
        period_days_counted += 1

        # Performance: actual vs target (capped at 100%)
        day_performance = min(kpis.get("completion_rate", 0), 100)
        day_quality = results.get("yield_rate", 0)
        day_oee = round(day_availability * day_performance * day_quality / 10000, 1)

        trend_data.append(
            {
                "date": current.isoformat(),
                "oee": day_oee,
                "availability": round(day_availability, 1),
                "performance": round(day_performance, 1),
                "quality": round(day_quality, 1),
            }
        )
        current += timedelta(days=1)

    # Period-average availability (mean of daily utilization rates)
    availability = round(
        period_availability_sum / period_days_counted if period_days_counted > 0 else 0, 1
    )

    total_qty = total_ok + total_ng
    # quality_rate: 0 when no production (not 100 — returning 100 is misleading and inflates OEE)
    quality_rate = round((total_ok / total_qty * 100) if total_qty > 0 else 0, 1)
    performance_rate = min(
        round((total_ok / total_target * 100) if total_target > 0 else 0, 1),
        100,
    )
    # OEE: use ratio-of-sums over the period (not mean-of-daily-ratios)
    # availability is already the period mean of equipment utilization readings
    overall_oee = round(availability * performance_rate * quality_rate / 10000, 1)
    defect_rate = round((total_ng / total_qty * 100) if total_qty > 0 else 0, 2)

    return {
        "overall_oee": overall_oee,
        "availability": availability,
        "performance": performance_rate,
        "quality": quality_rate,
        "total_production": total_ok,
        "defect_rate": defect_rate,
        "downtime_hours": 0,
        "trend_data": trend_data,
    }


@router.get("/equipment/utilization")
async def get_equipment_utilization_frontend(
    db: DBSession,
    current_user: CurrentUser,
    equipment_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    period: str = Query("daily"),
) -> List[Dict[str, Any]]:
    """Equipment utilization list for the equipment analytics page."""
    start, end = _parse_date_range(date_from, date_to)
    # +1 to include both start and end dates in the count (e.g. Mon-Fri = 5 days, not 4)
    days = (end - start).days + 1

    eq_ids = [equipment_id] if equipment_id else None
    result = await aggregate_equipment_utilization(db, eq_ids, days)
    utilization_list = result.data.get("equipment_utilization", [])

    # Transform to frontend expected format
    total_hours = days * 24
    output = []
    for item in utilization_list:
        run_hours = item.get("run_time_hours", 0)
        util_rate = item.get("utilization_rate", 0)
        idle_hours = round(total_hours - run_hours, 2)
        error_hours = round(total_hours * 0.02, 2)  # estimate

        output.append(
            {
                "equipment_id": item["equipment_id"],
                "equipment_name": item["equipment_name"],
                "equipment_type": item["equipment_type"],
                "planned_time": total_hours,
                "running_time": run_hours,
                "idle_time": max(0, idle_hours - error_hours),
                "maintenance_time": 0,
                "error_time": error_hours,
                "utilization_rate": util_rate,
                "availability_rate": round(100 - (error_hours / total_hours * 100), 1)
                if total_hours > 0
                else 100,
                "equipment": {
                    "id": item["equipment_id"],
                    "eq_name": item["equipment_name"],
                    "equipment_type": item["equipment_type"],
                    "current_status": item.get("current_status", "STOP"),
                },
            }
        )
    return output


@router.get("/equipment/efficiency")
async def get_equipment_efficiency(
    db: DBSession,
    current_user: CurrentUser,
    equipment_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Individual equipment efficiency details."""
    if not equipment_id:
        return {
            "equipment_name": "",
            "planned_time": 0,
            "actual_time": 0,
            "downtime_breakdown": [],
            "efficiency_trend": [],
            "maintenance_schedule": [],
        }

    start, end = _parse_date_range(date_from, date_to)

    # Get equipment info
    eq_result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    eq = eq_result.scalar_one_or_none()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")

    # Get production results for this equipment in the date range
    start_dt = datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(end, datetime.max.time()).replace(tzinfo=timezone.utc)

    results_query = (
        select(ProdResult)
        .where(
            and_(
                ProdResult.target_equipment_id == equipment_id,
                ProdResult.start_time >= start_dt,
                ProdResult.start_time <= end_dt,
            )
        )
        .order_by(ProdResult.start_time)
    )
    results_result = await db.execute(results_query)
    results = list(results_result.scalars().all())

    days = (end - start).days or 7
    planned_time = days * 24

    def _to_utc(dt: datetime) -> datetime:
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    actual_time = sum(
        (_to_utc(r.end_time) - _to_utc(r.start_time)).total_seconds() / 3600
        for r in results
        if r.start_time and r.end_time
    )

    # Build efficiency trend by day
    efficiency_trend = []
    current = start
    while current <= end:
        day_start = datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = datetime.combine(current, datetime.max.time()).replace(tzinfo=timezone.utc)
        day_results = [
            r for r in results if r.start_time and day_start <= _to_utc(r.start_time) <= day_end
        ]
        day_hours = sum(
            (_to_utc(r.end_time) - _to_utc(r.start_time)).total_seconds() / 3600
            for r in day_results
            if r.start_time and r.end_time
        )
        efficiency_trend.append(
            {
                "date": current.isoformat(),
                "efficiency": round(day_hours / 24 * 100, 1),
                "utilization": round(day_hours / 24 * 100, 1),
            }
        )
        current += timedelta(days=1)

    return {
        "equipment_name": eq.eq_name,
        "planned_time": round(planned_time, 1),
        "actual_time": round(actual_time, 1),
        "downtime_breakdown": [
            {"reason": "대기", "duration": round(planned_time - actual_time, 1), "count": days},
        ]
        if planned_time > actual_time
        else [],
        "efficiency_trend": efficiency_trend,
        "maintenance_schedule": [],
    }


@router.get("/production/trends")
async def get_production_trends_frontend(
    db: DBSession,
    current_user: CurrentUser,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    period: str = Query("daily"),
) -> Dict[str, Any]:
    """Production trends for the analytics dashboard charts."""
    start, end = _parse_date_range(date_from, date_to)
    service = AggregationService(db)

    production_volume = []
    quality_trends = []
    cycle_time_trends = []

    current = start
    while current <= end:
        daily = await service.get_daily_production_status(current)
        results = daily.data.get("results", {})
        orders = daily.data.get("orders", {})

        total_ok = results.get("total_ok_qty", 0)
        total_ng = results.get("total_ng_qty", 0)
        total_qty = total_ok + total_ng
        target = sum(o.get("target_qty", 0) for o in orders.get("orders", []))

        production_volume.append(
            {
                "date": current.isoformat(),
                "planned": target,
                "actual": total_ok,
                "efficiency": round(total_ok / target, 2) if target > 0 else 0,
            }
        )

        quality_trends.append(
            {
                "date": current.isoformat(),
                "pass_rate": round((total_ok / total_qty * 100) if total_qty > 0 else 100, 1),
                "defect_rate": round((total_ng / total_qty * 100) if total_qty > 0 else 0, 1),
                "rework_rate": 0,
            }
        )

        cycle_time_trends.append(
            {
                "date": current.isoformat(),
                "avg_cycle_time": 0,
                "planned_cycle_time": 0,
                "variance": 0,
            }
        )

        current += timedelta(days=1)

    return {
        "production_volume": production_volume,
        "quality_trends": quality_trends,
        "cycle_time_trends": cycle_time_trends,
    }


@router.get("/resources")
async def get_resource_utilization(
    db: DBSession,
    current_user: CurrentUser,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Resource utilization for the analytics dashboard."""
    start, end = _parse_date_range(date_from, date_to)
    # +1 to include both start and end dates in the count
    days = (end - start).days + 1

    result = await aggregate_equipment_utilization(db, None, days)
    utilization_list = result.data.get("equipment_utilization", [])
    total_hours = days * 24

    equipment_utilization = [
        {
            "equipment_name": item["equipment_name"],
            "utilization_rate": item["utilization_rate"],
            "available_hours": total_hours,
            "used_hours": item["run_time_hours"],
            "maintenance_hours": 0,
        }
        for item in utilization_list
    ]

    # Simulated workforce utilization (no real shift data in the system)
    workforce_utilization = [
        {
            "shift": "주간 (08:00-20:00)",
            "planned_hours": days * 12,
            "worked_hours": days * 11,
            "overtime_hours": days * 0.5,
            "efficiency": 91.7,
        },
        {
            "shift": "야간 (20:00-08:00)",
            "planned_hours": days * 12,
            "worked_hours": days * 10,
            "overtime_hours": days * 0.3,
            "efficiency": 83.3,
        },
    ]

    return {
        "equipment_utilization": equipment_utilization,
        "workforce_utilization": workforce_utilization,
        "material_consumption": [],
    }


@router.get("/lot-trace")
async def list_lot_traces(
    db: DBSession,
    current_user: CurrentUser,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Paginated lot trace list."""
    query = select(WorkOrder).options(selectinload(WorkOrder.product))

    if date_from:
        try:
            start = datetime.combine(date.fromisoformat(date_from), datetime.min.time()).replace(tzinfo=timezone.utc)
            query = query.where(WorkOrder.created_at >= start)
        except ValueError:
            pass
    if date_to:
        try:
            end = datetime.combine(date.fromisoformat(date_to), datetime.max.time()).replace(tzinfo=timezone.utc)
            query = query.where(WorkOrder.created_at <= end)
        except ValueError:
            pass

    query = query.order_by(WorkOrder.created_at.desc())

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    orders = list(result.scalars().all())

    items = [
        {
            "lot_no": o.lot_no,
            "product_name": o.product.name if o.product else "Unknown",
            "product_code": o.product.code if o.product else "",
            "target_qty": o.target_qty,
            "completed_qty": o.completed_qty,
            "status": o.status,
            "start_time": o.start_time.isoformat() if o.start_time else None,
            "end_time": o.end_time.isoformat() if o.end_time else None,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0,
    }


@router.get("/lot-trace/{lot_no}")
async def get_lot_trace_detail(
    db: DBSession,
    current_user: CurrentUser,
    lot_no: str = Path(...),
) -> Dict[str, Any]:
    """Single lot trace detail."""
    result = await aggregate_lot_traceability(db, lot_no)
    if result.output_type == "error":
        raise HTTPException(status_code=404, detail=f"LOT {lot_no} not found")

    data = result.data
    return {
        "lot_no": data["lot_no"],
        "product_name": data.get("product", {}).get("name", ""),
        "product_code": data.get("product", {}).get("code", ""),
        "target_qty": data.get("work_order", {}).get("target_qty", 0),
        "completed_qty": data.get("summary", {}).get("total_ok_qty", 0),
        "status": data.get("work_order", {}).get("status", ""),
        "start_time": None,
        "end_time": None,
        "created_at": data.get("work_order", {}).get("created_at"),
    }


@router.get("/lot-trace/{lot_no}/history")
async def get_lot_trace_history(
    db: DBSession,
    current_user: CurrentUser,
    lot_no: str = Path(...),
) -> Dict[str, Any]:
    """Lot processing history with quality checkpoints."""
    result = await aggregate_lot_traceability(db, lot_no)
    if result.output_type == "error":
        raise HTTPException(status_code=404, detail=f"LOT {lot_no} not found")

    data = result.data
    timeline = data.get("timeline", [])
    routing = data.get("routing", [])

    process_flow = []
    for i, entry in enumerate(timeline):
        process_name = routing[i]["process_name"] if i < len(routing) else f"공정 {i + 1}"
        process_flow.append(
            {
                "process_name": process_name,
                "equipment_name": entry.get("equipment_name", ""),
                "start_time": entry.get("start_time", ""),
                "end_time": entry.get("end_time"),
                "duration": None,
                "status": "완료" if entry.get("end_time") else "진행중",
                "parameters": {},
            }
        )

    lot_info = {
        "lot_no": data["lot_no"],
        "product_name": data.get("product", {}).get("name", ""),
        "product_code": data.get("product", {}).get("code", ""),
        "target_qty": data.get("work_order", {}).get("target_qty", 0),
        "completed_qty": data.get("summary", {}).get("total_ok_qty", 0),
        "status": data.get("work_order", {}).get("status", ""),
        "start_time": None,
        "end_time": None,
        "created_at": data.get("work_order", {}).get("created_at"),
    }

    return {
        "lot_info": lot_info,
        "process_flow": process_flow,
        "quality_checkpoints": [],
    }


# ============================================================================
# Legacy Endpoints (used by NL-Router and internal services)
# ============================================================================


@router.get("/daily-status", response_model=DailyStatusResponse)
async def get_daily_status(
    db: DBSession,
    current_user: CurrentUser,
    target_date: Optional[str] = Query(
        None, description="Target date in YYYY-MM-DD format (default: today)"
    ),
) -> Dict[str, Any]:
    """Get aggregated daily production status.

    Combines data from:
    - Work orders (status distribution, counts)
    - Production results (quantities, yield rate)
    - Equipment status (running, idle, error counts)

    Returns KPIs including completion rate, yield rate, and equipment utilization.
    """
    # Parse date
    if target_date:
        # Handle "today" and "yesterday" strings from NL-Router
        if target_date.lower() == "today":
            parsed_date = date.today()
        elif target_date.lower() == "yesterday":
            parsed_date = date.today() - timedelta(days=1)
        else:
            try:
                parsed_date = date.fromisoformat(target_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD, 'today', or 'yesterday'",
                )
    else:
        parsed_date = date.today()

    # Check cache
    cache = get_cache()
    cache_key = f"analytics:daily:{parsed_date.isoformat()}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Aggregate data
    result = await aggregate_daily_status(db, parsed_date)

    # Cache result
    await cache.set(cache_key, result.data)

    return {
        **result.data,
        "errors": result.errors,
        "partial": result.partial,
    }


@router.get("/equipment-utilization", response_model=UtilizationResponse)
async def get_equipment_utilization(
    db: DBSession,
    current_user: CurrentUser,
    equipment_ids: Optional[str] = Query(
        None, description="Comma-separated equipment IDs to filter"
    ),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze (1-90)"),
) -> Dict[str, Any]:
    """Get equipment utilization metrics.

    Calculates utilization rate, run time, and yield for each equipment
    over the specified period.

    Includes:
    - Per-equipment utilization metrics
    - Summary with top performer and bottleneck identification
    """
    # Parse equipment IDs
    eq_ids = None
    if equipment_ids:
        try:
            eq_ids = [int(x.strip()) for x in equipment_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid equipment_ids format. Use comma-separated integers",
            )

    # Check cache
    cache = get_cache()
    cache_key = f"analytics:utilization:{equipment_ids or 'all'}:{days}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Aggregate data
    result = await aggregate_equipment_utilization(db, eq_ids, days)

    # Cache result
    await cache.set(cache_key, result.data)

    return {
        **result.data,
        "errors": result.errors,
        "partial": result.partial,
    }


@router.get("/kpis", response_model=KPIDashboardResponse)
async def get_kpi_dashboard(
    db: DBSession,
    current_user: CurrentUser,
) -> Dict[str, Any]:
    """Get aggregated KPIs for dashboard display.

    Returns:
    - Today's KPIs (completion rate, yield rate, production qty)
    - Weekly trends (average utilization, top/bottom performers)
    - Current status (active orders, equipment health)

    """
    # Check cache
    cache = get_cache()
    cache_key = "analytics:kpis:dashboard"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Aggregate data
    result = await aggregate_kpi_dashboard(db)

    # Cache with shorter TTL (5 minutes)
    await cache.set(cache_key, result.data, ttl=300)

    return {
        **result.data,
        "errors": result.errors,
        "partial": result.partial,
    }


@router.get("/traceability/{lot_no}", response_model=TraceabilityResponse)
async def get_lot_traceability(
    db: DBSession,
    current_user: CurrentUser,
    lot_no: str,
) -> Dict[str, Any]:
    """Get full traceability history for a LOT.

    Combines:
    - Work order details (status, target quantity)
    - Product information (name, code)
    - Process routing (sequence of operations)
    - Production timeline (results with equipment used)
    - Summary (yield, equipment list)

    Use this for quality tracing and production history lookup.
    """
    # Check cache
    cache = get_cache()
    cache_key = f"lot:history:{lot_no}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Get traceability data
    result = await aggregate_lot_traceability(db, lot_no)

    if result.output_type == "error":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"LOT {lot_no} not found")

    # Cache result
    await cache.set(cache_key, result.data)

    return {
        **result.data,
        "errors": result.errors,
        "partial": result.partial,
    }


@router.get("/trends")
async def get_production_trends(
    db: DBSession,
    current_user: CurrentUser,
    metric: str = Query("yield", description="Metric to trend: yield, production, utilization"),
    days: int = Query(7, ge=1, le=30, description="Number of days (1-30)"),
    group_by: Optional[str] = Query(None, description="Group by: equipment, product, day"),
) -> Dict[str, Any]:
    """Get trend data for charts.

    Supports multiple metrics and grouping options for
    flexible chart rendering.
    """
    # Validate metric
    valid_metrics = ["yield", "production", "utilization", "completion"]
    if metric not in valid_metrics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid metric. Must be one of: {', '.join(valid_metrics)}",
        )

    # Check cache
    cache = get_cache()
    cache_key = f"analytics:trends:{metric}:{days}:{group_by or 'none'}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Get trend data
    service = AggregationService(db)

    # Generate daily data points
    trend_data = []
    today = date.today()

    for i in range(days):
        target = today - timedelta(days=days - 1 - i)
        try:
            daily = await service.get_daily_production_status(target)
            kpis = daily.data.get("kpis", {})
            results = daily.data.get("results", {})

            data_point = {
                "date": target.isoformat(),
            }

            if metric == "yield":
                data_point["value"] = kpis.get("yield_rate", 0)
            elif metric == "production":
                data_point["value"] = results.get("total_ok_qty", 0)
            elif metric == "utilization":
                data_point["value"] = kpis.get("equipment_utilization", 0)
            elif metric == "completion":
                data_point["value"] = kpis.get("completion_rate", 0)

            trend_data.append(data_point)
        except Exception:
            # Skip days with errors
            trend_data.append(
                {
                    "date": target.isoformat(),
                    "value": None,
                }
            )

    result = {
        "metric": metric,
        "days": days,
        "group_by": group_by,
        "data": trend_data,
    }

    # Cache result
    await cache.set(cache_key, result)

    return result
