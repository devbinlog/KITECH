"""Quality API endpoints."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload

from ....db.session import get_db
from ....models.quality import (
    InspectionPlan,
    InspectionResult,
    SPCChart,
    SPCDataPoint,
    NonConformance,
    NCRStatus,
)
from ....models.production import WorkOrder
from ....schemas.quality import (
    InspectionPlanCreate,
    InspectionPlanUpdate,
    InspectionPlanResponse,
    InspectionPlanWithResults,
    InspectionResultCreate,
    InspectionResultResponse,
    SPCChartWithDataPoints,
    NonConformanceCreate,
    NonConformanceUpdate,
    NonConformanceResponse,
    SPCCapabilityAnalysis,
    SPCAnalysisResult,
    QualityTraceabilityRecord,
    BatchInspectionResult,
    BatchInspectionResponse,
)
from ....services.quality_service import QualityService
from ...deps import CurrentUser, EventPublisherDep

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quality", tags=["quality"])


# Inspection Plans
@router.post("/inspection-plans", response_model=InspectionPlanResponse)
async def create_inspection_plan(
    plan_data: InspectionPlanCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> InspectionPlanResponse:
    """Create a new inspection plan."""
    inspection_plan = InspectionPlan(**plan_data.model_dump())
    db.add(inspection_plan)
    await db.commit()
    await db.refresh(inspection_plan)
    return InspectionPlanResponse.model_validate(inspection_plan)


@router.get("/inspection-plans", response_model=Dict[str, Any])
async def list_inspection_plans(
    current_user: CurrentUser,
    inspection_type: Optional[str] = Query(None, description="Filter by type"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=1000, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """List all inspection plans with pagination."""
    query = select(InspectionPlan).options(
        selectinload(InspectionPlan.product)
    ).where(InspectionPlan.is_active)

    if product_id:
        query = query.where(InspectionPlan.product_id == product_id)
    if inspection_type:
        query = query.where(InspectionPlan.inspection_type == inspection_type)

    # Count total
    count_query = select(func.count()).select_from(
        select(InspectionPlan).where(InspectionPlan.is_active).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(desc(InspectionPlan.id)).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    plans = result.scalars().all()

    items = []
    for p in plans:
        item = InspectionPlanResponse.model_validate(p).model_dump()
        if p.product:
            item["product_name"] = p.product.name
            item["product_code"] = p.product.code
        items.append(item)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0,
    }


@router.get("/inspection-plans/{product_id}", response_model=List[InspectionPlanWithResults])
async def get_inspection_plans_by_product(
    current_user: CurrentUser,
    product_id: int = Path(..., description="Product ID"),
    include_inactive: bool = Query(False, description="Include inactive plans"),
    db: AsyncSession = Depends(get_db),
) -> List[InspectionPlanWithResults]:
    """Get inspection plans for a specific product."""
    query = (
        select(InspectionPlan)
        .options(
            selectinload(InspectionPlan.inspection_results), selectinload(InspectionPlan.spc_charts)
        )
        .where(InspectionPlan.product_id == product_id)
    )

    if not include_inactive:
        query = query.where(InspectionPlan.is_active)

    result = await db.execute(query)
    plans = result.scalars().all()
    return [InspectionPlanWithResults.model_validate(plan) for plan in plans]


@router.put("/inspection-plans/{plan_id}", response_model=InspectionPlanResponse)
async def update_inspection_plan(
    current_user: CurrentUser,
    plan_id: int = Path(..., description="Inspection plan ID"),
    plan_data: InspectionPlanUpdate = ...,
    db: AsyncSession = Depends(get_db),
) -> InspectionPlanResponse:
    """Update an inspection plan."""
    result = await db.execute(select(InspectionPlan).where(InspectionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Inspection plan not found")

    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    await db.commit()
    await db.refresh(plan)
    return InspectionPlanResponse.model_validate(plan)


@router.delete("/inspection-plans/{plan_id}")
async def delete_inspection_plan(
    current_user: CurrentUser,
    plan_id: int = Path(..., description="Inspection plan ID"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Soft-delete an inspection plan (set is_active = False)."""
    result = await db.execute(select(InspectionPlan).where(InspectionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Inspection plan not found")

    plan.is_active = False
    await db.commit()
    return {"ok": True, "id": plan_id}


# Inspection Results
@router.post("/inspection-results", response_model=InspectionResultResponse)
async def create_inspection_result(
    result_data: InspectionResultCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    event_publisher: EventPublisherDep = None,
) -> InspectionResultResponse:
    """Create a new inspection result."""
    # Get inspection plan for validation
    plan_result = await db.execute(
        select(InspectionPlan).where(InspectionPlan.id == result_data.inspection_plan_id)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Inspection plan not found")

    # Calculate conformance
    measured_value = result_data.measured_value
    is_conforming = True

    if plan.lsl is not None and measured_value < plan.lsl:
        is_conforming = False
    if plan.usl is not None and measured_value > plan.usl:
        is_conforming = False

    deviation = None
    if plan.nominal is not None:
        deviation = measured_value - plan.nominal

    # Create inspection result
    result_data_dict = result_data.model_dump()
    result_data_dict.update(
        {
            "is_conforming": is_conforming,
            "deviation": deviation,
        }
    )
    inspection_result = InspectionResult(**result_data_dict)
    db.add(inspection_result)
    await db.commit()
    await db.refresh(inspection_result)

    # Trigger SPC analysis if enabled
    if plan.enable_spc:
        quality_service = QualityService(db)
        await quality_service.calculate_spc_limits(plan.id)

        # Check for violations and auto-generate NCR if needed
        spc_chart_result = await db.execute(
            select(SPCChart).where(and_(SPCChart.inspection_plan_id == plan.id, SPCChart.is_active))
        )
        spc_chart = spc_chart_result.scalar_one_or_none()

        if spc_chart:
            violations = await quality_service.check_western_electric_rules(spc_chart.id)
            if violations:
                await quality_service.auto_generate_ncr(
                    violations, plan.id, result_data.work_order_id
                )

    # Publish InspectionCompletedEvent
    if event_publisher:
        # Get work order info
        lot_no = ""
        if result_data.work_order_id:
            wo_result = await db.execute(
                select(WorkOrder).where(WorkOrder.id == result_data.work_order_id)
            )
            work_order = wo_result.scalar_one_or_none()
            if work_order:
                lot_no = work_order.lot_no

        await event_publisher.publish_inspection_completed(
            inspection_id=inspection_result.id,
            work_order_id=result_data.work_order_id or 0,
            lot_no=lot_no,
            inspection_type="IN_PROCESS",  # Default type
            result="PASS" if is_conforming else "FAIL",
            sample_size=1,
            defects_found=0 if is_conforming else 1,
            measurements={"value": measured_value, "characteristic": plan.characteristic},
            out_of_spec_items=[] if is_conforming else [plan.characteristic],
        )
        logger.info(f"InspectionCompletedEvent published for inspection {inspection_result.id}")

    return InspectionResultResponse.model_validate(inspection_result)


@router.get("/inspection-results", response_model=List[InspectionResultResponse])
async def get_inspection_results(
    current_user: CurrentUser,
    work_order_id: Optional[int] = Query(None, description="Filter by work order ID"),
    inspection_plan_id: Optional[int] = Query(None, description="Filter by inspection plan ID"),
    serial_no: Optional[str] = Query(None, description="Filter by serial number"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> List[InspectionResultResponse]:
    """Get inspection results with optional filtering."""
    query = (
        select(InspectionResult)
        .options(
            selectinload(InspectionResult.inspection_plan).selectinload(InspectionPlan.product),
            selectinload(InspectionResult.work_order).selectinload(WorkOrder.product),
        )
        .order_by(desc(InspectionResult.measured_at))
    )

    if work_order_id:
        query = query.where(InspectionResult.work_order_id == work_order_id)
    if inspection_plan_id:
        query = query.where(InspectionResult.inspection_plan_id == inspection_plan_id)
    if serial_no:
        query = query.where(InspectionResult.serial_no == serial_no)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    results = result.scalars().all()
    return [InspectionResultResponse.model_validate(r) for r in results]


@router.post("/inspection-results/batch", response_model=BatchInspectionResponse)
async def create_batch_inspection_results(
    batch_data: BatchInspectionResult,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> BatchInspectionResponse:
    """Create multiple inspection results in batch."""
    # Get inspection plan
    plan_result = await db.execute(
        select(InspectionPlan).where(InspectionPlan.id == batch_data.inspection_plan_id)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Inspection plan not found")

    created_results = []
    errors = []

    for i, result_data in enumerate(batch_data.results):
        nested = None
        try:
            measured_value = result_data["measured_value"]

            # Calculate conformance
            is_conforming = True
            deviation_from_target = None

            if plan.lsl is not None and measured_value < plan.lsl:
                is_conforming = False
            if plan.usl is not None and measured_value > plan.usl:
                is_conforming = False

            if plan.nominal is not None:
                deviation_from_target = measured_value - plan.nominal

            # Create result using savepoint so a single bad row doesn't abort the batch
            nested = await db.begin_nested()
            inspection_result = InspectionResult(
                inspection_plan_id=batch_data.inspection_plan_id,
                work_order_id=batch_data.work_order_id,
                equipment_id=batch_data.equipment_id,
                measured_value=measured_value,
                serial_no=result_data.get("serial_no"),
                lot_no=result_data.get("lot_number"),
                is_conforming=is_conforming,
                deviation=deviation_from_target,
                measurement_metadata=result_data.get("environmental_conditions", {}),
            )
            db.add(inspection_result)
            await nested.commit()
            created_results.append(inspection_result)

        except Exception as e:
            if nested is not None:
                await nested.rollback()
            errors.append(f"Row {i + 1}: {str(e)}")

    await db.commit()

    # Refresh created results
    for result in created_results:
        await db.refresh(result)

    return BatchInspectionResponse(
        created_count=len(created_results),
        failed_count=len(errors),
        created_results=[InspectionResultResponse.model_validate(r) for r in created_results],
        errors=errors,
    )


# Non-Conformance Reports (NCR)
@router.post("/ncr", response_model=NonConformanceResponse)
async def create_ncr(
    ncr_data: NonConformanceCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    event_publisher: EventPublisherDep = None,
) -> NonConformanceResponse:
    """Create a new non-conformance report."""
    # Generate NCR number
    from uuid import uuid4

    ncr_number = f"NCR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"

    # SQLite BIGINT PK doesn't auto-increment; generate ID manually with retry loop
    # to handle race conditions where two concurrent requests get the same max_id.
    ncr = None
    last_error = None
    for _attempt in range(5):
        try:
            max_id_result = await db.execute(select(func.max(NonConformance.id)))
            next_id = (max_id_result.scalar() or 0) + 1

            ncr = NonConformance(
                id=next_id,
                ncr_no=ncr_number,
                **ncr_data.model_dump(),
            )
            db.add(ncr)
            await db.commit()
            await db.refresh(ncr)
            break  # success
        except Exception as e:
            await db.rollback()
            last_error = e
            logger.warning(f"NCR creation attempt {_attempt + 1} failed: {type(e).__name__}: {e}")
    else:
        logger.error(f"NCR creation failed after retries: {type(last_error).__name__}: {last_error}")
        raise HTTPException(status_code=500, detail=f"NCR creation failed: {type(last_error).__name__}: {last_error}")

    # Publish NCRCreatedEvent
    if event_publisher:
        # Get lot_no if work_order_id is provided
        lot_no = None
        if ncr_data.work_order_id:
            wo_result = await db.execute(
                select(WorkOrder).where(WorkOrder.id == ncr_data.work_order_id)
            )
            work_order = wo_result.scalar_one_or_none()
            if work_order:
                lot_no = work_order.lot_no

        await event_publisher.publish_ncr_created(
            ncr_id=ncr.id,
            ncr_number=ncr_number,
            ncr_type=ncr_data.defect_type or "PROCESS",
            severity="MINOR",  # Default severity, not in schema
            description=ncr_data.description or "",
            affected_qty=0,  # Not in schema
            work_order_id=ncr_data.work_order_id,
            lot_no=lot_no,
            product_id=None,  # Not in schema
            equipment_id=ncr_data.machine_id,
            source="INSPECTION",
        )
        logger.info(f"NCRCreatedEvent published for NCR {ncr_number}")

    return NonConformanceResponse.model_validate(ncr)


@router.get("/ncr", response_model=List[NonConformanceResponse])
async def get_ncrs(
    current_user: CurrentUser,
    status: Optional[NCRStatus] = Query(None, description="Filter by status"),
    work_order_id: Optional[int] = Query(None, description="Filter by work order ID"),
    equipment_id: Optional[int] = Query(None, description="Filter by equipment ID"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> List[NonConformanceResponse]:
    """Get non-conformance reports with optional filtering."""
    query = select(NonConformance).options(
        selectinload(NonConformance.work_order),
        selectinload(NonConformance.equipment),
        selectinload(NonConformance.inspection_plan),
    ).order_by(desc(NonConformance.reported_at))

    if status:
        query = query.where(NonConformance.status == status)
    if work_order_id:
        query = query.where(NonConformance.work_order_id == work_order_id)
    if equipment_id:
        query = query.where(NonConformance.equipment_id == equipment_id)
    if assigned_to:
        query = query.where(NonConformance.assigned_to == assigned_to)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    ncrs = result.scalars().all()
    return [NonConformanceResponse.model_validate(ncr) for ncr in ncrs]


@router.put("/ncr/{ncr_id}", response_model=NonConformanceResponse)
async def update_ncr(
    current_user: CurrentUser,
    ncr_id: int = Path(..., description="NCR ID"),
    ncr_data: NonConformanceUpdate = ...,
    db: AsyncSession = Depends(get_db),
) -> NonConformanceResponse:
    """Update a non-conformance report."""
    result = await db.execute(select(NonConformance).where(NonConformance.id == ncr_id))
    ncr = result.scalar_one_or_none()
    if not ncr:
        raise HTTPException(status_code=404, detail="NCR not found")

    update_data = ncr_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ncr, field, value)

    # Set closed_at when status changes to CLOSED
    if ncr_data.status == NCRStatus.CLOSED and ncr.closed_at is None:
        ncr.closed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(ncr)
    return NonConformanceResponse.model_validate(ncr)


# Valid NCR status transitions: current_status -> set of allowed next statuses
_NCR_VALID_TRANSITIONS: Dict[str, set] = {
    "OPEN": {"IN_PROGRESS", "CLOSED"},
    "IN_PROGRESS": {"OPEN", "CLOSED"},
    "CLOSED": set(),  # terminal state
}


@router.patch("/ncr/{ncr_id}/status", response_model=NonConformanceResponse)
async def update_ncr_status(
    current_user: CurrentUser,
    ncr_id: int = Path(..., description="NCR ID"),
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> NonConformanceResponse:
    """Update NCR status with transition validation."""
    result = await db.execute(select(NonConformance).where(NonConformance.id == ncr_id))
    ncr = result.scalar_one_or_none()
    if not ncr:
        raise HTTPException(status_code=404, detail="NCR not found")

    new_status = payload.get("status")
    if not new_status:
        raise HTTPException(status_code=422, detail="status field is required")

    try:
        new_status_enum = NCRStatus(new_status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status: {new_status}")

    # Validate transition
    current_status_str = ncr.status.value if hasattr(ncr.status, "value") else str(ncr.status)
    allowed = _NCR_VALID_TRANSITIONS.get(current_status_str, set())
    if new_status_enum.value not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status transition: {current_status_str} -> {new_status_enum.value}",
        )

    ncr.status = new_status_enum

    if ncr.status == NCRStatus.CLOSED and ncr.closed_at is None:
        ncr.closed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(ncr)
    return NonConformanceResponse.model_validate(ncr)


# SPC Charts and Analysis
@router.get("/spc/charts/{characteristic}", response_model=List[SPCChartWithDataPoints])
async def get_spc_charts_by_characteristic(
    current_user: CurrentUser,
    characteristic: str = Path(..., description="Characteristic name"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    db: AsyncSession = Depends(get_db),
) -> List[SPCChartWithDataPoints]:
    """Get SPC charts for a specific characteristic."""
    # Build query for inspection plans with the characteristic
    plan_query = select(InspectionPlan).where(InspectionPlan.characteristic == characteristic)

    if product_id:
        plan_query = plan_query.where(InspectionPlan.product_id == product_id)

    plan_result = await db.execute(plan_query)
    plans = plan_result.scalars().all()

    if not plans:
        return []

    # Get SPC charts for these plans
    plan_ids = [plan.id for plan in plans]
    charts_query = (
        select(SPCChart)
        .options(selectinload(SPCChart.data_points))
        .where(and_(SPCChart.inspection_plan_id.in_(plan_ids), SPCChart.is_active))
        .order_by(desc(SPCChart.created_at))
    )

    charts_result = await db.execute(charts_query)
    charts = charts_result.scalars().all()

    return [SPCChartWithDataPoints.model_validate(chart) for chart in charts]


@router.get("/spc/capability", response_model=List[SPCCapabilityAnalysis])
async def get_spc_capability_analysis(
    current_user: CurrentUser,
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    characteristic: Optional[str] = Query(None, description="Filter by characteristic name"),
    db: AsyncSession = Depends(get_db),
) -> List[SPCCapabilityAnalysis]:
    """Get SPC capability analysis (Cp, Cpk, Pp, Ppk)."""
    # Build query for inspection plans
    plan_query = select(InspectionPlan).where(InspectionPlan.enable_spc)

    if product_id:
        plan_query = plan_query.where(InspectionPlan.product_id == product_id)
    if characteristic:
        plan_query = plan_query.where(InspectionPlan.characteristic == characteristic)

    plan_result = await db.execute(plan_query)
    plans = plan_result.scalars().all()

    quality_service = QualityService(db)
    capability_analyses = []

    for plan in plans:
        analysis = await quality_service.calculate_capability_indices(plan.id)
        if analysis:
            capability_analyses.append(analysis)

    return capability_analyses


@router.post("/spc/charts/{chart_id}/analyze", response_model=SPCAnalysisResult)
async def analyze_spc_chart(
    current_user: CurrentUser,
    chart_id: int = Path(..., description="SPC chart ID"),
    recent_points: int = Query(20, ge=5, le=100, description="Number of recent points to analyze"),
    db: AsyncSession = Depends(get_db),
) -> SPCAnalysisResult:
    """Perform comprehensive SPC analysis including Western Electric Rules."""
    # Get SPC chart
    chart_result = await db.execute(
        select(SPCChart)
        .options(selectinload(SPCChart.inspection_plan))
        .where(SPCChart.id == chart_id)
    )
    chart = chart_result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="SPC chart not found")

    quality_service = QualityService(db)

    # Check Western Electric Rules
    violated_rules = await quality_service.check_western_electric_rules(chart_id, recent_points)

    # Get capability analysis
    capability_analysis = await quality_service.calculate_capability_indices(
        chart.inspection_plan_id
    )

    # Count out of control points
    ooc_query = select(func.count(SPCDataPoint.id)).where(
        and_(SPCDataPoint.spc_chart_id == chart_id, SPCDataPoint.is_out_of_control)
    )
    ooc_result = await db.execute(ooc_query)
    out_of_control_count = ooc_result.scalar() or 0

    # Generate recommendations
    recommendations = []
    if violated_rules:
        recommendations.append("Investigate process for special causes of variation")
    if capability_analysis and capability_analysis.cpk and capability_analysis.cpk < 1.33:
        recommendations.append("Process capability is below acceptable level (Cpk < 1.33)")
    if out_of_control_count > 0:
        recommendations.append("Multiple out-of-control points detected - review process stability")

    return SPCAnalysisResult(
        chart_id=chart_id,
        characteristic_name=chart.inspection_plan.characteristic,
        total_points=chart.sample_count,
        out_of_control_points=out_of_control_count,
        capability_analysis=capability_analysis,
        violated_rules=violated_rules,
        trend_analysis={},  # Could be extended with trend analysis
        recommendations=recommendations,
        analysis_date=datetime.now(timezone.utc),
    )


# Quality Traceability
@router.get("/traceability/{serial_no}", response_model=QualityTraceabilityRecord)
async def get_quality_traceability(
    current_user: CurrentUser,
    serial_no: str = Path(..., description="Serial number to trace"),
    db: AsyncSession = Depends(get_db),
) -> QualityTraceabilityRecord:
    """Get complete quality traceability for a serial number."""
    quality_service = QualityService(db)
    traceability = await quality_service.get_quality_traceability(serial_no)

    if not traceability:
        raise HTTPException(
            status_code=404, detail=f"No quality records found for serial number: {serial_no}"
        )

    return traceability


# Dashboard endpoints
@router.get("/dashboard/summary")
async def get_quality_dashboard_summary(
    current_user: CurrentUser,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get quality dashboard summary statistics."""
    from_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Total inspection results
    total_query = select(func.count(InspectionResult.id)).where(
        InspectionResult.measured_at >= from_date
    )
    total_result = await db.execute(total_query)
    total_inspections = total_result.scalar() or 0

    # Conforming results
    conforming_query = select(func.count(InspectionResult.id)).where(
        and_(InspectionResult.measured_at >= from_date, InspectionResult.is_conforming)
    )
    conforming_result = await db.execute(conforming_query)
    conforming_count = conforming_result.scalar() or 0

    # Open NCRs
    open_ncr_query = select(func.count(NonConformance.id)).where(
        NonConformance.status.in_([NCRStatus.OPEN, NCRStatus.IN_PROGRESS])
    )
    open_ncr_result = await db.execute(open_ncr_query)
    open_ncrs = open_ncr_result.scalar() or 0

    # Active SPC charts
    active_charts_query = select(func.count(SPCChart.id)).where(SPCChart.is_active)
    active_charts_result = await db.execute(active_charts_query)
    active_charts = active_charts_result.scalar() or 0

    # Calculate quality metrics
    quality_rate = (conforming_count / total_inspections * 100) if total_inspections > 0 else 0

    return {
        "period_days": days,
        "total_inspections": total_inspections,
        "conforming_inspections": conforming_count,
        "quality_rate_percent": round(quality_rate, 2),
        "open_ncrs": open_ncrs,
        "active_spc_charts": active_charts,
        "summary_generated_at": datetime.now(timezone.utc).isoformat(),
    }
