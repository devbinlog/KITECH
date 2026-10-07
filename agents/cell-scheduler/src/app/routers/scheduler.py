"""Scheduler API Router

Defines API endpoints for scheduling operations.
"""

import logging
import uuid
from fastapi import APIRouter, HTTPException

from ..schemas import (
    ScheduleRequest,
    ScheduleResponse,
    SolverListResponse,
    SolverInfoSchema,
    ErrorResponse,
)
from ..services.scheduler_service import SchedulerService
from ..services.aas_loader import AASLoader
from ..services.event_publisher import get_event_publisher
from ..config import settings
from ..output_saver import save_schedule_output

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/schedule", tags=["scheduling"])

# AAS 로더: AAS_PATH 설정 시 활성화
_aas_loader: AASLoader | None = None
if settings.AAS_PATH:
    try:
        _aas_loader = AASLoader(settings.AAS_PATH)
        logger.info(f"AAS loader initialized from: {settings.AAS_PATH}")
    except FileNotFoundError as e:
        logger.warning(f"AAS_PATH configured but file not found: {e}. Falling back to request data.")

# Service instance
scheduler_service = SchedulerService(aas_loader=_aas_loader)
event_publisher = get_event_publisher()


@router.post(
    "/solve",
    response_model=ScheduleResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Solver error"},
    },
    summary="Solve scheduling problem",
    description="Execute scheduling optimization with specified solver and parameters",
)
async def solve_schedule(request: ScheduleRequest) -> ScheduleResponse:
    """스케줄링 문제 풀이.

    작업지시, 설비, 솔버 옵션을 받아 최적화된 스케줄을 반환합니다.

    Args:
        request: 스케줄링 요청 (work_orders, machines, options)

    Returns:
        스케줄링 결과 (scheduled_tasks, statistics, gantt_data)

    Raises:
        HTTPException: 유효성 검증 실패 시 400, 솔버 오류 시 500

    """
    # Validate request
    if not request.work_orders:
        raise HTTPException(status_code=400, detail="At least one work order is required")
    if not request.machines and not scheduler_service.aas_loader:
        raise HTTPException(
            status_code=400,
            detail="At least one machine is required (or configure AAS_PATH to load from AAS)",
        )
    if request.scheduling_horizon.end <= request.scheduling_horizon.start:
        raise HTTPException(
            status_code=400,
            detail="Scheduling horizon end must be after start",
        )

    # Enhanced validation: collect all errors before failing
    validation_errors = []
    for wo in request.work_orders:
        if not wo.operations:
            validation_errors.append(f"Work order '{wo.wo_id}' has no operations")
            continue

        seen_op_ids = set()
        for op in wo.operations:
            if op.nc_code.cycle_time_sec <= 0:
                validation_errors.append(
                    f"Work order '{wo.wo_id}', operation '{op.op_id}': "
                    f"cycle_time_sec must be > 0 (got {op.nc_code.cycle_time_sec})"
                )
            if op.op_id in seen_op_ids:
                validation_errors.append(
                    f"Work order '{wo.wo_id}': duplicate operation ID '{op.op_id}'"
                )
            seen_op_ids.add(op.op_id)

        if wo.due_date < wo.release_date:
            logger.warning(
                "Work order '%s': due_date (%s) < release_date (%s) — already overdue, "
                "will appear as tardy in schedule",
                wo.wo_id,
                wo.due_date.isoformat(),
                wo.release_date.isoformat(),
            )

    if validation_errors:
        raise HTTPException(status_code=400, detail=validation_errors)

    request_id = str(uuid.uuid4())
    solver_type = request.options.solver_type.value

    try:
        logger.info(
            f"[{request_id}] Solving schedule: {len(request.work_orders)} work orders, "
            f"{len(request.machines)} machines, solver={solver_type}"
        )

        result = await scheduler_service.solve(request)

        logger.info(
            f"[{request_id}] Schedule complete: {len(result.scheduled_tasks)} tasks, "
            f"makespan={result.statistics.makespan_hours}h"
        )

        # Publish ScheduleCompletedEvent
        await event_publisher.publish_schedule_completed(
            request_id=request_id,
            success=True,
            solver_type=solver_type,
            makespan_hours=result.statistics.makespan_hours,
            total_jobs_scheduled=result.statistics.total_tasks,
            total_machines_used=len(result.gantt_data.resources) if result.gantt_data else 0,
            objective_value=result.statistics.objective_value,
            solve_time_sec=result.statistics.solve_time_sec,
            schedule_summary={
                "status": result.status,
                "bottleneck_machines": result.statistics.bottleneck_machines,
                "machine_utilization": result.statistics.machine_utilization,
            },
        )
        logger.info(f"[{request_id}] ScheduleCompletedEvent published")

        final_result = result.model_copy(update={"request_id": request_id})
        save_schedule_output(final_result.model_dump(), solver_type)
        return final_result

    except ValueError as e:
        logger.error(f"[{request_id}] Validation error: {e}")
        # Publish failed event
        await event_publisher.publish_schedule_completed(
            request_id=request_id,
            success=False,
            solver_type=solver_type,
            error_message=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"[{request_id}] Solver error: {e}", exc_info=True)
        # Publish failed event
        await event_publisher.publish_schedule_completed(
            request_id=request_id,
            success=False,
            solver_type=solver_type,
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Solver error: {str(e)}")


@router.get(
    "/solvers",
    response_model=SolverListResponse,
    summary="List available solvers",
    description="Get information about all available scheduling solvers",
)
async def list_solvers() -> SolverListResponse:
    """사용 가능한 솔버 목록 조회.

    Returns:
        솔버 목록 (type, name, description, best_for, characteristics)

    """
    solvers = scheduler_service.get_available_solvers()

    return SolverListResponse(
        solvers=[
            SolverInfoSchema(
                type=s["type"],
                name=s["name"],
                version=s.get("version", "1.0"),
                description=s.get("description", ""),
                best_for=s.get("best_for", ""),
                characteristics=s.get("characteristics", {}),
                default_params=s.get("default_params", {}),
            )
            for s in solvers
        ]
    )


@router.get(
    "/solver/{solver_type}",
    response_model=SolverInfoSchema,
    responses={
        404: {"model": ErrorResponse, "description": "Solver not found"},
    },
    summary="Get solver info",
    description="Get detailed information about a specific solver",
)
async def get_solver_info(solver_type: str) -> SolverInfoSchema:
    """특정 솔버 정보 조회.

    Args:
        solver_type: 솔버 타입 (OR_TOOLS, GA, SA, TABU)

    Returns:
        솔버 상세 정보 (type, name, description, characteristics 등)

    Raises:
        HTTPException: 솔버 미존재 시 404 에러

    """
    solvers = scheduler_service.get_available_solvers()

    for solver in solvers:
        if solver["type"].upper() == solver_type.upper():
            return SolverInfoSchema(
                type=solver["type"],
                name=solver["name"],
                version=solver.get("version", "1.0"),
                description=solver.get("description", ""),
                best_for=solver.get("best_for", ""),
                characteristics=solver.get("characteristics", {}),
                default_params=solver.get("default_params", {}),
            )

    raise HTTPException(
        status_code=404,
        detail=f"Solver '{solver_type}' not found. Available: OR_TOOLS, GA, SA, TABU, ALNS",
    )
