"""Scheduler Integration API Endpoints

Provides endpoints for cell-scheduler agent integration.
"""

import logging
import traceback
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.session import get_db
from ....services.scheduler_integration import SchedulerIntegrationService
from ...deps import CurrentUser

_logger = logging.getLogger(__name__)


router = APIRouter()


# Request/Response Models
class EquipmentAvailabilityRequest(BaseModel):
    equipment_ids: Optional[List[int]] = None


class SchedulingRequestParams(BaseModel):
    horizon_hours: int = 24
    include_running: bool = False


class SolveScheduleParams(BaseModel):
    horizon_hours: int = 24
    include_running: bool = False
    include_scheduled: bool = False
    solver_type: str = "OR_TOOLS"
    time_limit_sec: Optional[int] = None
    auto_apply: bool = False
    lot_size: int = 1              # lot splitting granularity (1 = no splitting)
    amr_transfer_time_sec: int = 60  # AMR travel time constant (seconds)


class SchedulingResultRequest(BaseModel):
    status: str
    scheduled_tasks: List[dict]
    statistics: Optional[dict] = None
    quality_metrics: Optional[dict] = None
    gantt_data: Optional[dict] = None


# Endpoints


@router.get("/current-schedule")
async def get_current_schedule(
    current_user: CurrentUser,
    date: Optional[str] = None, include_running: bool = True, db: AsyncSession = Depends(get_db)
):
    """현재 스케줄된 작업지시 현황 조회 (간트 차트용).

    Args:
        date: 조회할 날짜 (YYYY-MM-DD), 기본값 오늘
        include_running: 진행중인 작업지시 포함 여부
        db: 데이터베이스 세션

    Returns:
        date: 조회 날짜
        availability: 설비별 스케줄 슬롯 배열
        summary: 전체 통계

    """
    service = SchedulerIntegrationService(db)
    return await service.get_current_schedule(date, include_running)


@router.get("/equipment-availability")
async def get_equipment_availability(
    current_user: CurrentUser,
    equipment_ids: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    """설비 가용성 조회 (cell-scheduler용).

    Args:
        equipment_ids: 설비 ID 목록 (콤마 구분)
        db: 데이터베이스 세션

    Returns:
        machines: 설비 목록 (machine_id, machine_name, machine_type, status 등)
        count: 설비 수

    Raises:
        HTTPException: equipment_ids 형식 오류 시 400 에러

    """
    service = SchedulerIntegrationService(db)

    # Parse equipment_ids if provided (comma-separated)
    eq_ids = None
    if equipment_ids:
        try:
            eq_ids = [int(id.strip()) for id in equipment_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid equipment_ids format")

    machines = await service.get_equipment_for_scheduler(eq_ids)

    return {
        "machines": machines,
        "count": len(machines),
    }


@router.get("/work-orders")
async def get_work_orders_for_scheduling(
    current_user: CurrentUser,
    status: Optional[str] = "READY", limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """스케줄링용 작업지시 조회.

    Args:
        status: 작업지시 상태 필터 (콤마 구분, 기본값 READY)
        limit: 조회 개수 제한
        db: 데이터베이스 세션

    Returns:
        work_orders: 작업지시 목록 (wo_id, product, quantity, due_date, jobs 등)
        count: 작업지시 수

    """
    service = SchedulerIntegrationService(db)

    # Parse status filter (comma-separated)
    status_filter = [s.strip() for s in status.split(",")] if status else None

    work_orders = await service.get_work_orders_for_scheduler(
        status_filter=status_filter, limit=limit
    )

    return {
        "work_orders": work_orders,
        "count": len(work_orders),
    }


@router.post("/create-request")
async def create_scheduling_request(
    params: SchedulingRequestParams,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """스케줄링 요청 생성 (cell-scheduler용).

    Args:
        params: 스케줄링 파라미터 (horizon_hours, include_running)
        db: 데이터베이스 세션

    Returns:
        horizon: 스케줄링 기간 정보
        machines: 설비 데이터
        work_orders: 작업지시 데이터
        machine_type_params: 설비 타입별 파라미터

    """
    service = SchedulerIntegrationService(db)

    scheduling_request = await service.create_scheduling_request(
        horizon_hours=params.horizon_hours, include_running=params.include_running
    )

    return scheduling_request


@router.post("/process-result")
async def process_scheduling_result(
    result: SchedulingResultRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """스케줄링 결과 처리.

    cell-scheduler의 결과를 받아 작업지시에 반영.

    Args:
        result: 스케줄링 결과 (scheduled_tasks, statistics 등)
        db: 데이터베이스 세션

    Returns:
        success: 처리 성공 여부
        updated_count: 업데이트된 작업지시 수

    Raises:
        HTTPException: 처리 실패 시 400/500 에러

    """
    service = SchedulerIntegrationService(db)
    try:
        processing_result = await service.process_scheduling_result(result.model_dump())
    except Exception as e:
        _logger.error(f"process-result EXCEPTION: {type(e).__name__}: {e}")
        _logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")

    if not processing_result["success"]:
        raise HTTPException(
            status_code=400,
            detail=processing_result.get("message", "Failed to process scheduling result"),
        )

    return processing_result


@router.get("/machine-type-params")
async def get_machine_type_params(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """설비 타입별 파라미터 조회.

    Args:
        db: 데이터베이스 세션

    Returns:
        설비 타입별 loading_type, transport_qty, timing 파라미터

    """
    service = SchedulerIntegrationService(db)
    params = await service._get_machine_type_params()

    return params


@router.post("/solve")
async def solve_schedule(
    params: SolveScheduleParams,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """스케줄링 실행.

    cell-scheduler 서비스를 호출하여 스케줄링 수행.

    Args:
        params: 스케줄링 옵션
            - solver_type: OR_TOOLS (기본), GA, SA, TABU, ALNS
            - time_limit_sec: 최대 풀이 시간 (초)
            - include_scheduled: False면 기스케줄 작업지시 제외 (드리프트 방지)
            - auto_apply: True면 결과 즉시 반영, False면 결과만 반환
        db: 데이터베이스 세션

    Returns:
        scheduling_result: 스케줄링 결과
        processing_result: 반영 결과 (auto_apply=True 시)

    Raises:
        HTTPException: 스케줄러 서비스 오류 시 500 에러

    """
    service = SchedulerIntegrationService(db)

    # Create scheduling request
    scheduling_request = await service.create_scheduling_request(
        horizon_hours=params.horizon_hours,
        include_running=params.include_running,
        include_scheduled=params.include_scheduled,
        lot_size=params.lot_size,
        amr_transfer_time_sec=params.amr_transfer_time_sec,
    )

    # Call scheduler service
    result = await service.call_scheduler_service(
        scheduling_request, solver_type=params.solver_type, time_limit_sec=params.time_limit_sec
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "Scheduler service error"))

    # Only process result if auto_apply is True
    if params.auto_apply:
        processing = await service.process_scheduling_result(result)
        return {"scheduling_result": result, "processing_result": processing}
    else:
        # Return results only, without updating work orders
        return {"scheduling_result": result, "processing_result": None}
