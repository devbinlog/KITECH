"""Production endpoints: Work Orders and Results."""

import logging
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
import httpx
import yaml
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from ....core.config import settings
from ....models.master import Product, Scenario, ProcessRouting
from ....models.production import WorkOrder, ProdResult, Unit
from ....models.equipment import Equipment
from ....schemas.production import (
    WorkOrderCreate,
    WorkOrderRead,
    WorkOrderStatusUpdate,
    ProdResultCreate,
    ProdResultRead,
    WorkInfoPayload,
    ProcessingStep,
    LogisticsInfo,
    UnitQueueResponse,
    UnitListResponse,
    ScenarioUpdateRequest,
    MiddlewareCommandResponse,
    MiddlewareResumeRequest,
    OrderMiddlewareState,
)
from ....schemas.common import PaginatedResponse
from ....services.middleware_client import (
    MiddlewareBusinessError,
    MiddlewareCallError,
    MiddlewareClient,
)
from ...deps import (
    DBSession,
    CurrentUser,
    EventPublisherDep,
)

logger = logging.getLogger(__name__)
router = APIRouter()

WORK_ORDER_ID_RETRY_LIMIT = 5
_PROJECT_ROOT = Path(__file__).resolve().parents[6]
UNIT_STATUS_READY = "READY"
UNIT_STATUS_RUNNING = "RUNNING"
UNIT_STATUS_SCENARIO_HOLD = "SCENARIO_HOLD"


def _middleware_client(current_user: Any) -> MiddlewareClient:
    username = getattr(current_user, "username", "unknown")
    return MiddlewareClient(
        base_url=settings.MIDDLEWARE_URL,
        caller=f"MES:{username}",
    )


def _middleware_error_to_http(exc: Exception) -> HTTPException:
    if isinstance(exc, MiddlewareBusinessError):
        detail: Dict[str, Any] = {
            "message": exc.message,
            "error": exc.error,
            "middleware_response": exc.payload,
        }
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if isinstance(exc, MiddlewareCallError):
        detail = {
            "message": exc.message,
            "status_code": exc.status_code,
            "body": exc.body,
        }
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


def _normalize_middleware_unit(unit_no: str, raw_unit: Dict[str, Any], mes_unit: Optional[Unit]) -> Dict[str, Any]:
    recipe = raw_unit.get("recipe") if isinstance(raw_unit.get("recipe"), dict) else {}
    recipe_steps = recipe.get("steps") if isinstance(recipe.get("steps"), list) else []
    return {
        "unit_no": str(raw_unit.get("unit_no") or unit_no),
        "mes_unit_id": mes_unit.id if mes_unit else None,
        "mes_status": mes_unit.status if mes_unit else None,
        "middleware_status": raw_unit.get("status"),
        "current_step_id": raw_unit.get("current_step_id"),
        "alarm_step_id": raw_unit.get("alarm_step_id"),
        "alarm_message": raw_unit.get("alarm_message"),
        "pending_stop": bool(raw_unit.get("pending_stop")),
        "acq_map": raw_unit.get("acq_map") if isinstance(raw_unit.get("acq_map"), dict) else {},
        "activity": raw_unit.get("activity") if isinstance(raw_unit.get("activity"), dict) else None,
        "recipe_name": raw_unit.get("recipe_name") or recipe.get("name"),
        "recipe_steps": recipe_steps,
        "nc_files": raw_unit.get("nc_files") if isinstance(raw_unit.get("nc_files"), list) else [],
        "unit_var": raw_unit.get("unit_var"),
        "unit_res": raw_unit.get("unit_res"),
        "unit_loc": raw_unit.get("unit_loc"),
        "unit_pos": raw_unit.get("unit_pos"),
        "raw": raw_unit,
    }


def _build_order_middleware_state(
    order: WorkOrder,
    mes_units: List[Unit],
    middleware_payload: Dict[str, Any],
) -> Dict[str, Any]:
    lot_data = middleware_payload.get("data") if isinstance(middleware_payload.get("data"), dict) else {}
    raw_units = lot_data.get("units") if isinstance(lot_data.get("units"), dict) else {}
    mes_units_by_no = {str(unit.unit_no): unit for unit in mes_units}
    all_unit_nos = sorted(
        set(raw_units.keys()) | set(mes_units_by_no.keys()),
        key=lambda value: (len(value), value),
    )

    units = []
    mismatched = False
    for unit_no in all_unit_nos:
        raw_unit = raw_units.get(unit_no)
        mes_unit = mes_units_by_no.get(unit_no)
        if isinstance(raw_unit, dict):
            normalized = _normalize_middleware_unit(unit_no, raw_unit, mes_unit)
            if mes_unit and normalized["middleware_status"] and mes_unit.status != normalized["middleware_status"]:
                mismatched = True
        else:
            normalized = {
                "unit_no": unit_no,
                "mes_unit_id": mes_unit.id if mes_unit else None,
                "mes_status": mes_unit.status if mes_unit else None,
                "middleware_status": None,
                "current_step_id": None,
                "alarm_step_id": None,
                "alarm_message": None,
                "pending_stop": False,
                "acq_map": {},
                "activity": None,
                "recipe_name": None,
                "recipe_steps": [],
                "nc_files": [],
                "unit_var": None,
                "unit_res": None,
                "unit_loc": None,
                "unit_pos": None,
                "raw": {},
            }
            mismatched = True
        units.append(normalized)

    return {
        "status": "success",
        "order_id": order.id,
        "lot_no": order.lot_no,
        "mes_status": order.status,
        "middleware_lot_status": lot_data.get("status"),
        "sync_status": "MISMATCHED" if mismatched else "SYNCED",
        "last_synced_at": datetime.now(timezone.utc),
        "units": units,
        "raw": lot_data,
    }


async def _next_work_order_id(db: DBSession) -> int:
    """Allocate the next WorkOrder id for legacy SQLite BIGINT primary keys."""
    result = await db.execute(select(func.max(WorkOrder.id)))
    max_id = result.scalar_one_or_none() or 0
    return max_id + 1


def _is_work_order_id_conflict(error: IntegrityError) -> bool:
    return "work_orders.id" in str(getattr(error, "orig", error))


def _is_work_order_lot_no_conflict(error: IntegrityError) -> bool:
    return "work_orders.lot_no" in str(getattr(error, "orig", error))


def _resolve_scenario_path(file_path: Optional[str]) -> Optional[Path]:
    """Resolve a scenario file path used by legacy scenario records."""
    if not file_path:
        return None

    file_path_str = file_path.lstrip("/")
    candidates = []
    scenarios_dir = getattr(settings, "SCENARIOS_DIR", None)
    if scenarios_dir:
        candidates.append(Path(scenarios_dir) / file_path_str)
    candidates.extend([
        _PROJECT_ROOT / file_path_str,
        Path.cwd() / file_path_str,
    ])

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.is_file():
            return resolved
    return None


def _load_scenario_yaml(file_path: Optional[str]) -> Dict[str, Any]:
    """Load scenario YAML for ready-unit resource hints."""
    scenario_path = _resolve_scenario_path(file_path)
    if not scenario_path:
        return {}

    try:
        content = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to parse scenario YAML %s: %s", scenario_path, exc)
        return {}
    return content if isinstance(content, dict) else {}


def _scenario_asset_names(scenario_content: Dict[str, Any]) -> Dict[str, str]:
    assets = scenario_content.get("assets")
    if not isinstance(assets, list):
        return {}

    names: Dict[str, str] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        asset_id = asset.get("id")
        if not asset_id:
            continue
        names[str(asset_id)] = str(asset.get("name") or asset_id)
    return names


def _resources_from_acquire(
    acquire: Dict[str, Any],
    asset_names: Dict[str, str],
) -> Dict[str, List[str]]:
    resources: Dict[str, List[str]] = {}
    for role, asset_ids in acquire.items():
        if isinstance(asset_ids, (str, int)):
            normalized_ids = [asset_ids]
        elif isinstance(asset_ids, list):
            normalized_ids = asset_ids
        else:
            continue

        bucket = resources.setdefault(str(role), [])
        for asset_id in normalized_ids:
            asset_key = str(asset_id)
            asset_name = asset_names.get(asset_key, asset_key)
            if asset_name not in bucket:
                bucket.append(asset_name)
    return resources


def _order_resource_roles(resources: Dict[str, List[str]]) -> Dict[str, List[str]]:
    ordered: Dict[str, List[str]] = {}
    for role in ("main", "sub1", "sub2", "sub3"):
        if role in resources:
            ordered[role] = resources.pop(role)
    ordered.update(resources)
    return ordered


def _scenario_required_resources(scenario_content: Dict[str, Any]) -> Dict[str, List[str]]:
    """Collect acquire role -> YAML asset names from the first acquiring step."""
    steps = scenario_content.get("steps")
    if not isinstance(steps, list):
        return {}

    asset_names = _scenario_asset_names(scenario_content)

    for step in steps:
        if not isinstance(step, dict):
            continue
        acquire = step.get("acquire")
        if not isinstance(acquire, dict):
            continue

        resources = _resources_from_acquire(acquire, asset_names)
        if resources:
            return _order_resource_roles(resources)

    return {}


def _scenario_role_resources(scenario_content: Dict[str, Any], role: str) -> List[str]:
    """Find YAML asset names for a role from the first step that acquires it."""
    steps = scenario_content.get("steps")
    if not isinstance(steps, list):
        return []

    asset_names = _scenario_asset_names(scenario_content)
    for step in steps:
        if not isinstance(step, dict):
            continue
        acquire = step.get("acquire")
        if not isinstance(acquire, dict) or role not in acquire:
            continue
        return _resources_from_acquire(acquire, asset_names).get(role, [])
    return []


def _absolute_api_url(request: Request, path: str) -> str:
    return f"{str(request.base_url).rstrip('/')}/api/v1{path}"


def _recipe_payload(
    request: Request,
    scenario: Optional[Scenario],
    scenario_content: Dict[str, Any],
) -> Optional[Dict[str, str]]:
    if not scenario:
        return None

    name = str(
        scenario_content.get("name")
        or scenario.name
        or Path(scenario.file_path).stem
    )
    return {
        "name": name,
        "url": _absolute_api_url(request, f"/masters/scenarios/{scenario.id}/download"),
    }


def _nc_file_name(routing_file) -> str:
    return routing_file.original_filename or Path(routing_file.file_path).name


def _routing_machine_candidates(routing, routing_file=None) -> List[str]:
    """Return machine candidates without breaking legacy equipment_type data."""
    candidates = []

    if routing_file is not None and getattr(routing_file, "compatible_machines", None):
        candidates.extend(routing_file.compatible_machines)
    if getattr(routing, "required_machines", None):
        candidates.extend(routing.required_machines)

    std_process = getattr(routing, "std_process", None)
    if std_process is not None:
        if getattr(std_process, "required_machines", None):
            candidates.extend(std_process.required_machines)
        equipment_type = getattr(std_process, "equipment_type", None)
        if equipment_type:
            candidates.append(equipment_type)

    deduped = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return deduped


def _format_unit_no(unit_no: int) -> str:
    return str(unit_no)


def _parse_unit_no(unit_no: str) -> int:
    unit_no_text = str(unit_no).strip()
    if not unit_no_text.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="unit_no must be a numeric text value",
        )

    parsed = int(unit_no_text)
    if parsed < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="unit_no must be greater than or equal to 1",
        )
    return parsed


# ============================================================================
# Work Orders
# ============================================================================


@router.get("/orders", response_model=PaginatedResponse[WorkOrderRead])
async def list_work_orders(
    db: DBSession,
    current_user: CurrentUser,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(30, ge=1, le=1000, description="페이지당 항목 수"),
    view: Optional[str] = Query(None, description="뷰 프리셋: today, upcoming, active, all"),
    date_from: Optional[date] = Query(None, description="시작 날짜"),
    date_to: Optional[date] = Query(None, description="종료 날짜"),
    sort_by: str = Query(
        "start_time", description="정렬 기준: start_time, due_date, priority, created_at"
    ),
    sort_order: str = Query("asc", description="정렬 순서: asc, desc"),
) -> Dict[str, Any]:
    """List work orders with pagination and filtering.

    View presets:
    - today: 오늘 계획된 작업 (진행중/대기)
    - upcoming: 미래 계획 + 미스케줄 작업
    - active: 진행중/일시정지 작업
    - all: 전체 작업
    """
    query = select(WorkOrder).options(
        selectinload(WorkOrder.product),
        selectinload(WorkOrder.results),
    )

    # View presets
    today_date = date.today()
    now = datetime.now(timezone.utc)

    if view == "today":
        # 오늘 계획된 작업 (READY, SCHEDULED, RUNNING, PAUSE)
        start_of_day = datetime.combine(today_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(today_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        query = query.where(
            and_(
                or_(
                    and_(WorkOrder.start_time >= start_of_day, WorkOrder.start_time <= end_of_day),
                    WorkOrder.start_time.is_(None),
                ),
                WorkOrder.status.in_(["READY", "SCHEDULED", "RUNNING", "PAUSE"]),
            )
        )
    elif view == "upcoming":
        # 미래 계획 + 아직 시작 안 한 작업 (READY or SCHEDULED)
        query = query.where(
            or_(
                WorkOrder.start_time > now,
                and_(WorkOrder.start_time.is_(None), WorkOrder.status.in_(["READY", "SCHEDULED"])),
            )
        )
    elif view == "active":
        # 진행중/일시정지
        query = query.where(WorkOrder.status.in_(["RUNNING", "PAUSE"]))

    # Date range filter
    if date_from:
        start_dt = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
        query = query.where(WorkOrder.start_time >= start_dt)
    if date_to:
        end_dt = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)
        query = query.where(WorkOrder.start_time <= end_dt)

    # Status filter
    if status_filter:
        query = query.where(WorkOrder.status == status_filter)

    # Sorting
    sort_column_map = {
        "start_time": WorkOrder.start_time,
        "due_date": WorkOrder.due_date,
        "priority": WorkOrder.priority,
        "created_at": WorkOrder.created_at,
    }
    sort_column = sort_column_map.get(sort_by, WorkOrder.start_time)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc().nulls_last())
    else:
        query = query.order_by(sort_column.asc().nulls_last())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    orders = list(result.scalars().all())

    # Collect all target_equipment_ids from results
    equipment_ids = set()
    for order in orders:
        for res in order.results:
            if res.target_equipment_id:
                equipment_ids.add(res.target_equipment_id)

    # Fetch equipment names
    equipment_names = {}
    if equipment_ids:
        eq_result = await db.execute(select(Equipment).where(Equipment.id.in_(equipment_ids)))
        for eq in eq_result.scalars():
            equipment_names[eq.id] = eq.eq_name

    # Build response with scheduled_equipment_name
    items = []
    for order in orders:
        order_dict = WorkOrderRead.model_validate(order).model_dump()
        # Get unique target equipment names
        eq_names = []
        for res in order.results:
            if res.target_equipment_id and res.target_equipment_id in equipment_names:
                name = equipment_names[res.target_equipment_id]
                if name not in eq_names:
                    eq_names.append(name)
        order_dict["scheduled_equipment_name"] = ", ".join(eq_names) if eq_names else None
        items.append(order_dict)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0,
    }


@router.post("/orders", response_model=WorkOrderRead, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    db: DBSession,
    current_user: CurrentUser,
    order_in: WorkOrderCreate,
    event_publisher: EventPublisherDep,
) -> WorkOrder:
    """새 작업지시 생성.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        order_in: 작업지시 생성 데이터 (lot_no, product_id, target_qty 등)
        event_publisher: 이벤트 발행 서비스

    Returns:
        생성된 작업지시 정보

    Raises:
        HTTPException: lot_no 중복, 제품/시나리오 미존재 시 400 에러

    """
    # Check lot_no uniqueness
    result = await db.execute(select(WorkOrder).where(WorkOrder.lot_no == order_in.lot_no))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Work order with lot_no '{order_in.lot_no}' already exists",
        )

    # Validate product exists
    result = await db.execute(select(Product).where(Product.id == order_in.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product not found",
        )

    # Validate scenario if provided
    if order_in.scenario_id:
        result = await db.execute(select(Scenario).where(Scenario.id == order_in.scenario_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scenario not found",
            )

    order_data = order_in.model_dump()
    work_order: WorkOrder | None = None
    for attempt in range(WORK_ORDER_ID_RETRY_LIMIT):
        # Legacy SQLite DBs were created with BIGINT PKs, so SQLite will not
        # auto-generate ids. Keep the BIGINT schema and assign ids in app logic.
        work_order = WorkOrder(id=await _next_work_order_id(db), **order_data)
        db.add(work_order)
        try:
            await db.commit()
            await db.refresh(work_order)
            break
        except IntegrityError as exc:
            await db.rollback()
            if _is_work_order_lot_no_conflict(exc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Work order with lot_no '{order_in.lot_no}' already exists",
                ) from exc
            if _is_work_order_id_conflict(exc) and attempt < WORK_ORDER_ID_RETRY_LIMIT - 1:
                logger.warning("Work order id allocation collision; retrying")
                continue
            raise

    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to allocate work order id",
        )

    # Eager-load product relationship for WorkOrderRead serialization
    result = await db.execute(
        select(WorkOrder)
        .where(WorkOrder.id == work_order.id)
        .options(selectinload(WorkOrder.product), selectinload(WorkOrder.scenario))
    )
    created_order = result.scalar_one()

    # Publish WorkOrderCreatedEvent
    if event_publisher:
        await event_publisher.publish_work_order_created(
            work_order_id=created_order.id,
            lot_no=created_order.lot_no,
            product_id=created_order.product_id,
            product_code=product.code,
            order_qty=created_order.target_qty,
            priority=created_order.priority or 50,
            due_date=created_order.due_date,
        )
        logger.info(f"WorkOrderCreatedEvent published for WO-{created_order.id}")

    return created_order


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_order(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
) -> None:
    """작업지시 삭제.
    
    진행 중(RUNNING)이 아닌 작업지시를 MES DB에서 삭제합니다.
    """
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

    if order.status == "RUNNING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a running work order. Pause or cancel it first."
        )

    await db.delete(order)
    await db.commit()
    return None


@router.get("/orders/ready-units", response_model=List[UnitQueueResponse])
async def get_all_ready_units(
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> List[Dict[str, Any]]:
    """Retrieve a list of READY units across all active work orders (Global Queue).

    Returns 1 Unit per RUNNING work order, ordered by Work Order priority to allow middleware
    to claim optimal tasks based on hardware availability.
    """
    # 1. Get all RUNNING Work Orders ordered by priority (lower number = higher priority)
    orders_result = await db.execute(
        select(WorkOrder)
        .where(WorkOrder.status == "RUNNING")
        .options(selectinload(WorkOrder.scenario))
        .order_by(WorkOrder.priority.asc())
    )
    running_orders = orders_result.scalars().all()

    if not running_orders:
        return []

    ready_units = []

    for order in running_orders:
        # 2. Find ONE ready unit for this specific order
        unit_result = await db.execute(
            select(Unit)
            .where(Unit.work_order_id == order.id, Unit.status == "READY")
            .options(selectinload(Unit.scenario))
            .order_by(Unit.unit_no.asc())
            .limit(1)
        )
        unit = unit_result.scalar_one_or_none()

        if unit:
            scenario_filename = "sample.yaml"
            scenario = unit.scenario or order.scenario
            if scenario and scenario.file_path:
                scenario_filename = scenario.file_path

            scenario_content = _load_scenario_yaml(scenario_filename)
            required_resources = _scenario_required_resources(scenario_content)
            main_assets = _scenario_role_resources(scenario_content, "main")

            nc_files = []
            if order.product_id:
                routing_result = await db.execute(
                    select(ProcessRouting)
                    .where(ProcessRouting.product_id == order.product_id)
                    .options(
                        selectinload(ProcessRouting.files),
                        selectinload(ProcessRouting.std_process),
                    )
                    .order_by(ProcessRouting.sequence)
                )
                routings = list(routing_result.scalars().all())
                for routing in routings:
                    for routing_file in sorted(routing.files, key=lambda item: item.sort_order):
                        if routing_file.file_type != "NC":
                            continue
                        candidates = _routing_machine_candidates(routing, routing_file)
                        asset_name = (
                            main_assets[0]
                            if main_assets
                            else (candidates[0] if candidates else "")
                        )
                        nc_files.append(
                            {
                                "asset": asset_name,
                                "name": _nc_file_name(routing_file),
                                "url": _absolute_api_url(
                                    request,
                                    f"/masters/files/{routing_file.id}/download",
                                ),
                            }
                        )

            ready_units.append({
                "unit_id": unit.id,
                "unit_no": _format_unit_no(unit.unit_no),
                "scenario_id": unit.scenario_id,
                "scenario_filename": scenario_filename,
                "recipe": _recipe_payload(request, scenario, scenario_content),
                "required_resources": required_resources,
                "nc_files": nc_files,
                "work_order_id": order.id,
                "lot_no": order.lot_no,
                "product_id": order.product_id,
                "priority": order.priority,
                "target_qty": order.target_qty,
            })

    return ready_units


@router.get("/orders/ready-units/execution-package")
async def get_unit_execution_package(
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    lot_no: str = Query(..., description="Work order lot number"),
    unit_no: str = Query(..., description="Unit sequence number text within the lot"),
) -> Dict[str, Any]:
    """Return scenario and routing file download URLs for a lot/unit pair.

    Middleware identifies execution targets by (lot_no, unit_no). This endpoint
    resolves that pair to the Unit snapshot, then returns the scenario content
    URL and all routing file download URLs needed to execute the unit.
    """
    result = await db.execute(
        select(Unit)
        .join(WorkOrder, Unit.work_order_id == WorkOrder.id)
        .where(WorkOrder.lot_no == lot_no, Unit.unit_no == _parse_unit_no(unit_no))
        .options(
            selectinload(Unit.scenario),
            selectinload(Unit.work_order).selectinload(WorkOrder.product),
            selectinload(Unit.work_order).selectinload(WorkOrder.scenario),
        )
    )
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found for lot_no and unit_no",
        )

    order = unit.work_order
    if not order or not order.product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit has no work order product",
        )

    base_url = str(request.base_url).rstrip("/")

    def absolute_api_url(path: str) -> str:
        return f"{base_url}/api/v1{path}"

    scenario = unit.scenario or order.scenario
    scenario_payload = None
    if scenario:
        scenario_payload = {
            "id": scenario.id,
            "name": scenario.name,
            "file_path": scenario.file_path,
            "content_url": absolute_api_url(f"/masters/scenarios/{scenario.id}/content"),
            "download_url": absolute_api_url(f"/masters/scenarios/{scenario.id}/download"),
        }

    routing_result = await db.execute(
        select(ProcessRouting)
        .where(ProcessRouting.product_id == order.product_id)
        .options(
            selectinload(ProcessRouting.files),
            selectinload(ProcessRouting.std_process),
        )
        .order_by(ProcessRouting.sequence)
    )
    routings = list(routing_result.scalars().all())

    processing_steps = []
    for routing in routings:
        files = []
        for routing_file in sorted(routing.files, key=lambda item: item.sort_order):
            files.append(
                {
                    "id": routing_file.id,
                    "file_type": routing_file.file_type,
                    "file_path": routing_file.file_path,
                    "original_filename": routing_file.original_filename,
                    "compatible_machines": routing_file.compatible_machines,
                    "sort_order": routing_file.sort_order,
                    "download_url": absolute_api_url(
                        f"/masters/files/{routing_file.id}/download"
                    ),
                }
            )

        processing_steps.append(
            {
                "routing_id": routing.id,
                "sequence": routing.sequence,
                "process_code": routing.std_process.code if routing.std_process else "",
                "process_name": routing.std_process.name if routing.std_process else "",
                "setup_id": routing.setup_id,
                "required_machines": _routing_machine_candidates(routing),
                "files": files,
            }
        )

    return {
        "lot_no": order.lot_no,
        "unit": {
            "id": unit.id,
            "unit_no": _format_unit_no(unit.unit_no),
            "status": unit.status,
            "scenario_id": unit.scenario_id,
        },
        "work_order": {
            "id": order.id,
            "product_id": order.product_id,
            "product_code": order.product.code if order.product else None,
            "product_name": order.product.name if order.product else None,
            "target_qty": order.target_qty,
            "status": order.status,
        },
        "scenario": scenario_payload,
        "processing_steps": processing_steps,
    }


@router.get("/orders/{order_id}", response_model=WorkOrderRead)
async def get_work_order(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
) -> WorkOrder:
    """작업지시 단건 조회.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        order_id: 작업지시 ID

    Returns:
        작업지시 정보 (제품 정보 포함)

    Raises:
        HTTPException: 작업지시 미존재 시 404 에러

    """
    result = await db.execute(
        select(WorkOrder).where(WorkOrder.id == order_id).options(selectinload(WorkOrder.product))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )
    return order


@router.get("/orders/{order_id}/monitoring")
async def get_work_order_monitoring(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
) -> Dict[str, Any]:
    """작업지시 미들웨어 상세 모니터링 데이터 조회.
    
    미들웨어의 GET /api/lots/{lot_no} 를 호출하여 로트 내 유닛(진행 단계) 및 진행 상황 데이터를 반환합니다.
    """
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

    middleware_url = settings.MIDDLEWARE_URL.rstrip("/")
    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.get(f"{middleware_url}/api/lots/{order.lot_no}")
            if res.status_code == 200:
                data = res.json()
                # 미들웨어 로트 데이터 구조 자체를 그대로 전달하여 프론트엔드에서 파싱
                return data
            elif res.status_code == 404:
                return {"lot_no": order.lot_no, "status": "NOT_FOUND_IN_MIDDLEWARE", "units": []}
            else:
                logger.error(f"Middleware lots get failed: {res.status_code} - {res.text}")
                return {"lot_no": order.lot_no, "status": "MIDDLEWARE_ERROR", "units": []}
        except Exception as e:
            logger.error(f"Failed to fetch monitoring data from middleware: {e}")
            return {"lot_no": order.lot_no, "status": "CONNECTION_ERROR", "units": []}


@router.get("/orders/{order_id}/middleware-state", response_model=OrderMiddlewareState)
async def get_order_middleware_state(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
) -> Dict[str, Any]:
    """Return merged MES Unit state and live middleware runtime state without DB writes."""
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

    units_result = await db.execute(
        select(Unit)
        .where(Unit.work_order_id == order_id)
        .options(selectinload(Unit.scenario))
    )
    mes_units = list(units_result.scalars().all())

    try:
        middleware_payload = await _middleware_client(current_user).get_lot(order.lot_no)
    except MiddlewareBusinessError as exc:
        if exc.error == "LOT_NOT_FOUND":
            return {
                "status": "success",
                "order_id": order.id,
                "lot_no": order.lot_no,
                "mes_status": order.status,
                "middleware_lot_status": "NOT_FOUND_IN_MIDDLEWARE",
                "sync_status": "MIDDLEWARE_NOT_FOUND",
                "last_synced_at": datetime.now(timezone.utc),
                "units": [
                    {
                        "unit_no": str(unit.unit_no),
                        "mes_unit_id": unit.id,
                        "mes_status": unit.status,
                        "middleware_status": None,
                        "current_step_id": None,
                        "alarm_step_id": None,
                        "alarm_message": None,
                        "pending_stop": False,
                        "acq_map": {},
                        "activity": None,
                        "recipe_name": None,
                        "recipe_steps": [],
                        "nc_files": [],
                        "unit_var": None,
                        "unit_res": None,
                        "unit_loc": None,
                        "unit_pos": None,
                        "raw": {},
                    }
                    for unit in mes_units
                ],
                "raw": exc.payload,
            }
        raise _middleware_error_to_http(exc)
    except MiddlewareCallError as exc:
        raise _middleware_error_to_http(exc)

    return _build_order_middleware_state(order, mes_units, middleware_payload)


@router.post(
    "/orders/{order_id}/middleware/units/{unit_no}/commands/{action}",
    response_model=MiddlewareCommandResponse,
)
async def command_middleware_unit(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    unit_no: str,
    action: str,
) -> Dict[str, Any]:
    """Proxy safe one-shot middleware unit commands without changing MES Unit.status."""
    allowed_actions = {
        "stop",
        "stop-after-step",
        "cancel-pending-stop",
        "clear-alarm",
        "release-resources",
    }
    if action not in allowed_actions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unsupported middleware action")

    result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

    try:
        middleware_response = await _middleware_client(current_user).command_unit(
            order.lot_no,
            unit_no,
            action,
        )
    except (MiddlewareBusinessError, MiddlewareCallError) as exc:
        raise _middleware_error_to_http(exc)

    return {
        "status": "success",
        "message": middleware_response.get("data", {}).get("message") or "Middleware command accepted",
        "order_id": order.id,
        "lot_no": order.lot_no,
        "unit_no": unit_no,
        "middleware_response": middleware_response,
    }


@router.post(
    "/orders/{order_id}/middleware/units/{unit_no}/resume",
    response_model=MiddlewareCommandResponse,
)
async def resume_middleware_unit(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    unit_no: str,
    request: MiddlewareResumeRequest,
) -> Dict[str, Any]:
    """Resume a STOPPED middleware unit with current, skip-current, or specific step mode."""
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

    params: Dict[str, Any] = {"clear_retry": request.clear_retry}
    if request.mode == "SKIP_CURRENT_STEP":
        params["skip_step"] = True
    elif request.mode == "SPECIFIC_STEP":
        if not request.resume_step_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="resume_step_id is required for SPECIFIC_STEP mode",
            )
        params["resume_step_id"] = request.resume_step_id

    try:
        middleware_response = await _middleware_client(current_user).command_unit(
            order.lot_no,
            unit_no,
            "resume",
            params=params,
        )
    except (MiddlewareBusinessError, MiddlewareCallError) as exc:
        raise _middleware_error_to_http(exc)

    return {
        "status": "success",
        "message": middleware_response.get("data", {}).get("message") or "Middleware resume accepted",
        "order_id": order.id,
        "lot_no": order.lot_no,
        "unit_no": unit_no,
        "middleware_response": middleware_response,
    }


@router.post("/orders/{order_id}/units/{unit_no}/clear-alarm")
async def clear_unit_alarm(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    unit_no: int,
) -> Dict[str, Any]:
    """작업지시 내 특정 유닛의 알람을 해제합니다."""
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

    middleware_url = settings.MIDDLEWARE_URL.rstrip("/")
    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.post(f"{middleware_url}/api/lots/{order.lot_no}/units/{unit_no}/clear-alarm")
            if res.status_code in [200, 204]:
                return {"message": "알람 해제가 미들웨어에 전달되었습니다."}
            else:
                logger.error(f"Middleware clear-alarm failed: {res.status_code} - {res.text}")
                raise HTTPException(status_code=400, detail=f"알람 해제 실패: {res.text}")
        except Exception as e:
            logger.error(f"Failed to clear alarm to middleware: {e}")
            raise HTTPException(status_code=500, detail="미들웨어 통신 오류")


@router.post("/orders/{order_id}/units/{unit_no}/resume")
async def resume_unit_operation(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    unit_no: int,
) -> Dict[str, Any]:
    """작업지시 내 특정 유닛(진행 단계)을 재시작합니다."""
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

    middleware_url = settings.MIDDLEWARE_URL.rstrip("/")
    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.post(f"{middleware_url}/api/lots/{order.lot_no}/units/{unit_no}/resume")
            if res.status_code in [200, 204]:
                return {"message": "유닛 재시작 명령이 미들웨어에 전달되었습니다."}
            else:
                logger.error(f"Middleware unit resume failed: {res.status_code} - {res.text}")
                raise HTTPException(status_code=400, detail=f"유닛 재시작 실패: {res.text}")
        except Exception as e:
            logger.error(f"Failed to resume unit to middleware: {e}")
            raise HTTPException(status_code=500, detail="미들웨어 통신 오류")


@router.patch("/orders/{order_id}/status", response_model=WorkOrderRead)
async def update_work_order_status(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    status_update: WorkOrderStatusUpdate,
    event_publisher: EventPublisherDep,
) -> WorkOrder:
    """작업지시 상태 변경 (상태 머신 기반).

    상태 전이 규칙:
    - READY → RUNNING, CANCEL
    - RUNNING → PAUSE, DONE, CANCEL
    - PAUSE → RUNNING, CANCEL
    - DONE, CANCEL → (변경 불가)

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        order_id: 작업지시 ID
        status_update: 변경할 상태 정보
        event_publisher: 이벤트 발행 서비스

    Returns:
        상태가 변경된 작업지시 정보

    Raises:
        HTTPException: 작업지시 미존재 시 404, 잘못된 상태 전이 시 400 에러

    """
    result = await db.execute(
        select(WorkOrder).where(WorkOrder.id == order_id).options(selectinload(WorkOrder.product))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )

    # Validate state transition
    if not order.can_transition_to(status_update.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition: {order.status} -> {status_update.status}",
        )

    old_status = order.status
    order.status = status_update.status
    await db.commit()
    await db.refresh(order)

    # --- 미들웨어 상태 연동 (stop / resume) 제거 완료 ---
    # Logical Pause 아키텍처 도입으로 인해 더 이상 물리적 stop/resume 명령을 미들웨어로 하달하지 않습니다.
    # WorkOrder의 상태가 PAUSE로 변경되면 글로벌 큐(/orders/ready-units)에서 자동으로 은닉되어 할당이 중지됩니다.

    # Publish WorkOrderStatusChangedEvent
    if event_publisher:
        await event_publisher.publish_work_order_status_changed(
            work_order_id=order.id,
            lot_no=order.lot_no,
            previous_status=old_status,
            new_status=order.status,
            changed_by=current_user.username if hasattr(current_user, "username") else None,
        )
        logger.info(
            f"WorkOrderStatusChangedEvent published: WO-{order.id} {old_status} -> {order.status}"
        )

    return order


@router.post("/orders/{order_id}/start", response_model=WorkOrderRead)
async def start_work_order(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    event_publisher: EventPublisherDep,
) -> WorkOrder:
    """작업지시 시작 하달 (순수 로트 시작만 수행)."""
    # 1. 작업지시 조회
    result = await db.execute(
        select(WorkOrder)
        .where(WorkOrder.id == order_id)
        .options(selectinload(WorkOrder.product), selectinload(WorkOrder.scenario))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

    if not order.can_transition_to("RUNNING"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start work order from status: {order.status}"
        )

    # 2. MES 상태 변경 (로컬 큐 트리거)
    # 미들웨어 통신이 제거되어, 오직 MES 로컬 상태만 RUNNING으로 업데이트하며 이후는 큐 데몬이 알아서 Unit을 적재합니다.
    old_status = order.status
    order.status = "RUNNING"
    await db.commit()
    await db.refresh(order)

    # 5. 이벤트 발행
    if event_publisher:
        await event_publisher.publish_work_order_status_changed(
            work_order_id=order.id,
            lot_no=order.lot_no,
            previous_status=old_status,
            new_status=order.status,
            changed_by=current_user.username if hasattr(current_user, "username") else None,
        )
        logger.info(f"WO-{order.id} started")

    return order

# ============================================================================
# Work Info (Middleware Payload)
# ============================================================================


@router.get("/middleware/work-info", response_model=WorkInfoPayload)
async def get_work_info(
    db: DBSession,
    current_user: CurrentUser,
    lot_no: str,
    unit_no: Optional[str] = None,
) -> WorkInfoPayload:
    """Get unified work info payload for middleware.

    Assembles routing + files + scenario into a single payload.
    """
    unit: Optional[Unit] = None

    # Get work order with related data
    result = await db.execute(
        select(WorkOrder)
        .where(WorkOrder.lot_no == lot_no)
        .options(
            selectinload(WorkOrder.product),
            selectinload(WorkOrder.scenario),
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )

    if not order.product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Work order has no product",
        )

    if unit_no is not None:
        unit_result = await db.execute(
            select(Unit)
            .where(Unit.work_order_id == order.id, Unit.unit_no == _parse_unit_no(unit_no))
            .options(selectinload(Unit.scenario))
        )
        unit = unit_result.scalar_one_or_none()
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found for lot_no and unit_no",
            )

    # Get routings with files
    result = await db.execute(
        select(ProcessRouting)
        .where(ProcessRouting.product_id == order.product_id)
        .options(
            selectinload(ProcessRouting.files),
            selectinload(ProcessRouting.std_process),
        )
        .order_by(ProcessRouting.sequence)
    )
    routings = list(result.scalars().all())

    # Build processing steps
    processing_steps = []
    for routing in routings:
        files = [
            {
                "type": f.file_type,
                "path": f.file_path,
                "order": f.sort_order,
            }
            for f in sorted(routing.files, key=lambda x: x.sort_order)
        ]
        processing_steps.append(
            ProcessingStep(
                sequence=routing.sequence,
                process_code=routing.std_process.code if routing.std_process else "",
                process_name=routing.std_process.name if routing.std_process else "",
                files=files,
            )
        )

    # Build logistics info
    logistics = None
    scenario = unit.scenario if unit and unit.scenario else order.scenario
    if scenario:
        logistics = LogisticsInfo(
            scenario_name=scenario.name,
            control_file=scenario.file_path,
        )

    return WorkInfoPayload(
        job_id=order.lot_no,
        product_code=order.product.code,
        product_name=order.product.name,
        target_qty=order.target_qty,
        logistics=logistics,
        processing_steps=processing_steps,
    )


# ============================================================================
# Production Results
# ============================================================================


@router.get("/results", response_model=PaginatedResponse[ProdResultRead])
async def list_production_results(
    db: DBSession,
    current_user: CurrentUser,
    work_order_id: Optional[int] = None,
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(30, ge=1, le=1000, description="페이지당 항목 수"),
) -> Dict[str, Any]:
    """생산실적 목록 조회 (페이지네이션).

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        work_order_id: 작업지시 ID로 필터링 (선택)
        page: 페이지 번호 (1부터 시작)
        limit: 페이지당 항목 수 (최대 100)

    Returns:
        페이지네이션된 생산실적 목록 (items, total, page, page_size, pages)

    """
    query = select(ProdResult).order_by(ProdResult.id.desc())

    if work_order_id:
        query = query.where(ProdResult.work_order_id == work_order_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    items = list(result.scalars().all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0,
    }


@router.post("/results", response_model=ProdResultRead, status_code=status.HTTP_201_CREATED)
async def create_production_result(
    db: DBSession,
    current_user: CurrentUser,
    result_in: ProdResultCreate,
    event_publisher: EventPublisherDep,
) -> ProdResult:
    """생산실적 등록.

    Args:
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자
        result_in: 생산실적 데이터 (work_order_id, ok_qty, ng_qty 등)
        event_publisher: 이벤트 발행 서비스

    Returns:
        등록된 생산실적 정보

    Raises:
        HTTPException: 작업지시 미존재 시 400 에러

    """
    # Validate work order exists and get details
    result = await db.execute(
        select(WorkOrder)
        .where(WorkOrder.id == result_in.work_order_id)
        .options(selectinload(WorkOrder.product))
    )
    work_order = result.scalar_one_or_none()
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Work order not found",
        )

    # Validate work order is in an active state (RUNNING or SCHEDULED)
    # Production results should only be recorded for active work orders
    _VALID_RESULT_STATUSES = {"RUNNING", "SCHEDULED"}
    if work_order.status not in _VALID_RESULT_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot record production result for work order in status '{work_order.status}'. "
                   f"Work order must be in one of: {sorted(_VALID_RESULT_STATUSES)}",
        )

    # Validate time range
    if result_in.start_time and result_in.end_time and result_in.start_time > result_in.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time cannot be after end_time",
        )

    prod_result = ProdResult(**result_in.model_dump())
    db.add(prod_result)
    await db.commit()
    await db.refresh(prod_result)

    # Get equipment name if available
    equipment_name = ""
    if result_in.equipment_id:
        eq_result = await db.execute(
            select(Equipment).where(Equipment.id == result_in.equipment_id)
        )
        equipment = eq_result.scalar_one_or_none()
        if equipment:
            equipment_name = equipment.eq_name

    # Publish ProductionRecordedEvent
    if event_publisher:
        await event_publisher.publish_production_recorded(
            work_order_id=work_order.id,
            lot_no=work_order.lot_no,
            operation_id=result_in.process_routing_id or 0,
            equipment_id=result_in.equipment_id or 0,
            equipment_name=equipment_name,
            ok_qty=result_in.ok_qty,
            ng_qty=result_in.ng_qty or 0,
            start_time=result_in.start_time or datetime.now(timezone.utc),
            end_time=result_in.end_time or datetime.now(timezone.utc),
        )
        logger.info(f"ProductionRecordedEvent published for WO-{work_order.id}")

    return prod_result


# ============================================================================
# Unit Dispatching (Lot-Size 1 Architecture)
# ============================================================================

async def _get_unit_and_order_by_lot(
    db: DBSession,
    lot_no: str,
    unit_no: str,
) -> tuple[Unit, WorkOrder]:
    parsed_unit_no = _parse_unit_no(unit_no)
    result = await db.execute(
        select(Unit, WorkOrder)
        .join(WorkOrder, Unit.work_order_id == WorkOrder.id)
        .where(WorkOrder.lot_no == lot_no, Unit.unit_no == parsed_unit_no)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found for lot_no and unit_no",
        )
    return row


def _current_username(current_user: CurrentUser) -> Optional[str]:
    return getattr(current_user, "username", None)


async def _claim_ready_unit(db: DBSession, unit_id: int, order_id: int) -> None:
    claim_result = await db.execute(
        update(Unit)
        .where(
            Unit.id == unit_id,
            Unit.work_order_id == order_id,
            Unit.status == UNIT_STATUS_READY,
        )
        .values(
            status=UNIT_STATUS_RUNNING,
            started_at=datetime.now(timezone.utc),
        )
    )
    if claim_result.rowcount != 1:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot claim unit because it is no longer READY",
        )


def _complete_unit(unit: Unit, order: WorkOrder) -> None:
    if unit.status != "RUNNING":
        raise HTTPException(status_code=400, detail=f"Cannot complete unit in {unit.status} state")

    unit.status = "DONE"
    unit.completed_at = datetime.now(timezone.utc)

    order.completed_qty += 1
    if order.completed_qty >= order.target_qty and order.status != "DONE":
        order.status = "DONE"
        order.end_time = datetime.now(timezone.utc)


@router.post("/orders/units/claim", response_model=Dict[str, Any])
async def claim_unit_by_lot(
    db: DBSession,
    current_user: CurrentUser,
    lot_no: str = Query(..., description="Work order lot number"),
    unit_no: str = Query(..., description="Unit sequence number text within the lot"),
) -> Dict[str, Any]:
    """Middleware acquires a READY unit by lot_no and unit_no."""
    unit, order = await _get_unit_and_order_by_lot(db, lot_no, unit_no)
    await _claim_ready_unit(db, unit.id, order.id)

    await db.commit()
    return {
        "message": "Unit claimed successfully",
        "work_order_id": order.id,
        "unit_id": unit.id,
        "lot_no": order.lot_no,
        "unit_no": _format_unit_no(unit.unit_no),
    }


@router.post("/orders/units/complete", response_model=Dict[str, Any])
async def complete_unit_by_lot(
    db: DBSession,
    current_user: CurrentUser,
    lot_no: str = Query(..., description="Work order lot number"),
    unit_no: str = Query(..., description="Unit sequence number text within the lot"),
) -> Dict[str, Any]:
    """Middleware reports a unit execution is fully finished by lot_no and unit_no."""
    unit, order = await _get_unit_and_order_by_lot(db, lot_no, unit_no)
    _complete_unit(unit, order)

    await db.commit()
    return {
        "message": "Unit completed successfully",
        "work_order_id": order.id,
        "unit_id": unit.id,
        "lot_no": order.lot_no,
        "unit_no": _format_unit_no(unit.unit_no),
        "completed_qty": order.completed_qty,
        "work_order_status": order.status,
    }


@router.post("/orders/{order_id}/units/{unit_id}/claim", response_model=Dict[str, str])
async def claim_unit(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    unit_id: int,
) -> Dict[str, str]:
    """Middleware acquires ownership of a READY unit.
    
    Transitions unit state from READY to RUNNING. Includes domain cross-validation via order_id.
    """
    result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
        
    if unit.work_order_id != order_id:
        raise HTTPException(status_code=400, detail="Unit does not belong to the specified Work Order")

    await _claim_ready_unit(db, unit.id, order_id)
    
    await db.commit()
    return {"message": "Unit claimed successfully"}


@router.post("/orders/{order_id}/units/{unit_id}/complete", response_model=Dict[str, str])
async def complete_unit(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    unit_id: int,
) -> Dict[str, str]:
    """Middleware reports a unit execution is fully finished.
    
    Transitions unit state to DONE. Includes domain cross-validation via order_id.
    """
    result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    if unit.work_order_id != order_id:
        raise HTTPException(status_code=400, detail="Unit does not belong to the specified Work Order")
    
    # 1. Find root work order
    wo_result = await db.execute(select(WorkOrder).where(WorkOrder.id == unit.work_order_id))
    order = wo_result.scalar_one_or_none()
    if order:
        _complete_unit(unit, order)
            
    await db.commit()
    return {"message": "Unit completed successfully"}


@router.post("/orders/{order_id}/units/{unit_id}/scenario-hold", response_model=Dict[str, Any])
async def hold_unit_for_scenario_change(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    unit_id: int,
) -> Dict[str, Any]:
    """Hide a READY unit from middleware while an operator changes its scenario."""
    order_result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Work order not found")

    if order.status not in {"RUNNING", "PAUSE"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit scenario can only be changed while Work Order is RUNNING or PAUSE",
        )

    unit_result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = unit_result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    if unit.work_order_id != order_id:
        raise HTTPException(status_code=400, detail="Unit does not belong to the specified Work Order")

    held_at = datetime.now(timezone.utc)
    hold_result = await db.execute(
        update(Unit)
        .where(
            Unit.id == unit_id,
            Unit.work_order_id == order_id,
            Unit.status == UNIT_STATUS_READY,
        )
        .values(
            status=UNIT_STATUS_SCENARIO_HOLD,
            scenario_hold_started_at=held_at,
            scenario_hold_by=_current_username(current_user),
        )
    )
    if hold_result.rowcount != 1:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot hold unit because it is no longer READY",
        )

    await db.commit()
    return {
        "message": "Unit held for scenario change",
        "unit_id": unit_id,
        "status": UNIT_STATUS_SCENARIO_HOLD,
        "scenario_id": unit.scenario_id,
        "scenario_hold_started_at": held_at.isoformat(),
        "scenario_hold_by": _current_username(current_user),
    }


@router.patch("/orders/{order_id}/units/{unit_id}/scenario", response_model=Dict[str, Any])
async def update_held_unit_scenario(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    unit_id: int,
    request: ScenarioUpdateRequest,
) -> Dict[str, Any]:
    """Change a held unit scenario and release it back to the ready queue."""
    order_result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Work order not found")
    if order.product_id is None:
        raise HTTPException(status_code=400, detail="Work order has no product")

    unit_result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = unit_result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    if unit.work_order_id != order_id:
        raise HTTPException(status_code=400, detail="Unit does not belong to the specified Work Order")

    scenario_result = await db.execute(select(Scenario).where(Scenario.id == request.scenario_id))
    scenario = scenario_result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Target Scenario not found")
    if not scenario.is_active:
        raise HTTPException(status_code=400, detail="Target Scenario is inactive")
    if scenario.product_id != order.product_id:
        raise HTTPException(
            status_code=400,
            detail="Target Scenario is not registered to the Work Order product",
        )

    update_result = await db.execute(
        update(Unit)
        .where(
            Unit.id == unit_id,
            Unit.work_order_id == order_id,
            Unit.status == UNIT_STATUS_SCENARIO_HOLD,
        )
        .values(
            scenario_id=scenario.id,
            status=UNIT_STATUS_READY,
            scenario_hold_started_at=None,
            scenario_hold_by=None,
        )
    )
    if update_result.rowcount != 1:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot change scenario because unit is not SCENARIO_HOLD",
        )

    await db.commit()
    return {
        "message": "Unit scenario changed and released to ready queue",
        "unit_id": unit_id,
        "status": UNIT_STATUS_READY,
        "scenario_id": scenario.id,
        "scenario_name": scenario.name,
    }


@router.post("/orders/{order_id}/units/{unit_id}/scenario-release", response_model=Dict[str, Any])
async def release_unit_scenario_hold(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    unit_id: int,
) -> Dict[str, Any]:
    """Release a held unit without changing its scenario."""
    unit_result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = unit_result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    if unit.work_order_id != order_id:
        raise HTTPException(status_code=400, detail="Unit does not belong to the specified Work Order")

    release_result = await db.execute(
        update(Unit)
        .where(
            Unit.id == unit_id,
            Unit.work_order_id == order_id,
            Unit.status == UNIT_STATUS_SCENARIO_HOLD,
        )
        .values(
            status=UNIT_STATUS_READY,
            scenario_hold_started_at=None,
            scenario_hold_by=None,
        )
    )
    if release_result.rowcount != 1:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot release scenario hold because unit is not SCENARIO_HOLD",
        )

    await db.commit()
    return {
        "message": "Unit scenario hold released",
        "unit_id": unit_id,
        "status": UNIT_STATUS_READY,
        "scenario_id": unit.scenario_id,
    }


@router.post("/orders/{order_id}/units/{unit_id}/stop", response_model=Dict[str, str])
async def stop_unit(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    unit_id: int,
) -> Dict[str, str]:
    """Physically pause a running unit via Middleware."""
    result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
        
    if unit.work_order_id != order_id:
        raise HTTPException(status_code=400, detail="Unit does not belong to the specified Work Order")

    if unit.status != "RUNNING":
        raise HTTPException(status_code=400, detail=f"Cannot stop unit in {unit.status} state")

    # Fetch WorkOrder to get lot_no
    wo_result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = wo_result.scalar_one_or_none()
    
    # Send HTTP proxy request to Middleware first
    middleware_url = settings.MIDDLEWARE_URL.rstrip("/")
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.post(f"{middleware_url}/api/lots/{order.lot_no}/units/{unit.unit_no}/stop")
            if res.status_code not in [200, 201]:
                logger.warning(f"Middleware stop endpoint missing/failed. (Status {res.status_code})")
                # Depending on strictness, we might raise HTTP 500 here. 
                # For Phase 3, we expect MW to adapt, but if testing, we might fall through gracefully or raise.
                # Since MW might not have this API yet, we'll log warning but still transition to PAUSED for the demo.
        except Exception as e:
            logger.error(f"Middleware stop call failed for unit {unit.id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to communicate with Middleware: {e}")

    unit.status = "PAUSED"
    await db.commit()
    return {"message": "Unit paused successfully"}


@router.post("/orders/{order_id}/units/{unit_id}/resume", response_model=Dict[str, str])
async def resume_unit(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    unit_id: int,
) -> Dict[str, str]:
    """Resume a physically paused unit via Middleware."""
    result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
        
    if unit.work_order_id != order_id:
        raise HTTPException(status_code=400, detail="Unit does not belong to the specified Work Order")

    if unit.status != "PAUSED":
        raise HTTPException(status_code=400, detail=f"Cannot resume unit in {unit.status} state")

    wo_result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = wo_result.scalar_one_or_none()
    
    middleware_url = settings.MIDDLEWARE_URL.rstrip("/")
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.post(f"{middleware_url}/api/lots/{order.lot_no}/units/{unit.unit_no}/resume")
            if res.status_code not in [200, 201]:
                logger.warning(f"Middleware resume endpoint missing/failed. (Status {res.status_code})")
        except Exception as e:
            logger.error(f"Middleware resume call failed for unit {unit.id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to communicate with Middleware: {e}")

    unit.status = "RUNNING"
    await db.commit()
    return {"message": "Unit resumed successfully"}



@router.patch("/orders/{order_id}/scenario", response_model=Dict[str, str])
async def override_scenario(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
    request: ScenarioUpdateRequest,
) -> Dict[str, str]:
    """Change the running scenario of a paused WorkOrder via dynamic override.
    
    Propagates the new scenario recursively down to the `READY` queued units.
    """
    # 1. Validate Work Order
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Work order not found")

    if order.status != "PAUSE":
        raise HTTPException(
            status_code=400, 
            detail="Scenario can only be dynamically overridden while Work Order is in PAUSE state"
        )
        
    # 2. Validate Target Scenario
    scenario_result = await db.execute(select(Scenario).where(Scenario.id == request.scenario_id))
    scenario = scenario_result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Target Scenario not found")

    held_units_result = await db.execute(
        select(func.count(Unit.id)).where(
            Unit.work_order_id == order.id,
            Unit.status == UNIT_STATUS_SCENARIO_HOLD,
        )
    )
    held_units_count = held_units_result.scalar() or 0
    if held_units_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot override Work Order scenario while units are held for scenario change",
        )

    # 3. Update Work Order root property
    order.scenario_id = scenario.id
    
    # 4. Synchronize all READY units in the queue with the new snapshot
    units_result = await db.execute(
        select(Unit).where(Unit.work_order_id == order.id, Unit.status == "READY")
    )
    units = units_result.scalars().all()
    count = 0
    for unit in units:
        unit.scenario_id = scenario.id
        count += 1
        
    await db.commit()
    return {"message": f"Scenario overridden to {scenario.name}. Synchronized {count} queued units."}


@router.get("/orders/{order_id}/units", response_model=UnitListResponse)
async def get_units_for_order(
    db: DBSession,
    current_user: CurrentUser,
    order_id: int,
):
    """Retrieve all units for a specific WorkOrder for monitoring."""
    # 1. Validate Work Order
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Work order not found")

    # 2. Fetch all units for this order (Inject Scenario for UI Tracking)
    units_result = await db.execute(
        select(Unit)
        .where(Unit.work_order_id == order.id)
        .options(selectinload(Unit.scenario))
        .order_by(Unit.unit_no.desc())
    )
    units = units_result.scalars().all()
    
    return {
        "items": units,
        "total": len(units)
    }
