"""
Base Solver Interface

Abstract base class for all scheduling solvers providing:
- Unified interface for different optimization algorithms
- Common data structures for scheduling problems
- Consistent result format across solvers

MES v5 Schema: Job layer removed, WorkOrder contains operations directly.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, time as dtime
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# New Advanced Data Classes (AMR, Calendar, SchedulerConfig, SetupInterval)
# ============================================================================


@dataclass
class Break:
    """Shift break interval"""
    start: dtime
    end: dtime


@dataclass
class Calendar:
    """Equipment shift calendar"""
    shift_start: dtime
    shift_end: dtime
    breaks: List[Break] = field(default_factory=list)


@dataclass
class AMRConfig:
    """Autonomous Mobile Robot configuration"""
    amr_id: str
    model: str = ""
    status: str = "available"
    current_location: str = ""
    accessible_machines: List[str] = field(default_factory=list)
    speed_m_per_sec: float = 1.0


@dataclass
class SchedulerConfig:
    """Global scheduler configuration"""
    lot_size: int = 1                  # lot splitting granularity (1 = no splitting)
    amr_transfer_time_sec: int = 60    # AMR travel time constant


@dataclass
class SetupInterval:
    """Setup time interval for visualization"""
    machine_id: str
    wo_id: str
    start_time: int   # seconds from horizon_start
    end_time: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "machine_id": self.machine_id,
            "wo_id": self.wo_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_sec": self.end_time - self.start_time,
        }


class SolverType(str, Enum):
    """Available solver types"""

    OR_TOOLS = "OR_TOOLS"
    GENETIC_ALGORITHM = "GA"
    SIMULATED_ANNEALING = "SA"
    TABU_SEARCH = "TABU"
    ALNS = "ALNS"


@dataclass
class SolverConfig:
    """Solver configuration parameters"""

    time_limit_sec: int = 60

    # OR-Tools specific
    num_workers: int = 8
    log_search_progress: bool = False

    # Genetic Algorithm specific
    population_size: int = 100
    generations: int = 500
    crossover_rate: float = 0.8
    mutation_rate: float = 0.2
    elitism_ratio: float = 0.1

    # Simulated Annealing specific
    initial_temp: float = 100.0
    final_temp: float = 0.1
    cooling_rate: float = 0.95
    sa_iterations: int = 10000

    # Tabu Search specific
    # tabu_tenure: tabu 리스트 크기/유지 기간 (실제 사용되는 파라미터)
    tabu_tenure: int = 10
    # tabu_iterations: 최대 반복 횟수 상한 (시간 제한과 OR 조건)
    tabu_iterations: int = 5000
    # tabu_list_size: deprecated alias of tabu_tenure (하위 호환)
    tabu_list_size: int = 50
    diversification_freq: int = 100

    # ALNS specific
    alns_destroy_rate: float = 0.3  # Percentage of solution to destroy (0 < x <= 1)
    alns_iterations: int = 10000
    alns_segment_size: int = 100  # Iterations between weight updates

    # Common — random seed (None = OS entropy, 정수 = 재현 가능)
    random_seed: Optional[int] = 42

    def __post_init__(self):
        """Validate and clamp parameter values to safe ranges after initialization."""
        # time_limit_sec must be positive; default to 60 if None or invalid
        if not isinstance(self.time_limit_sec, int) or self.time_limit_sec <= 0:
            self.time_limit_sec = 60
        # tabu_list_size는 deprecated — 기본값(50)이 아닐 때만 tabu_tenure로 동기화
        if isinstance(self.tabu_list_size, int) and self.tabu_list_size != 50:
            if self.tabu_tenure == 10:  # tabu_tenure가 기본값이면 list_size로 덮어씀
                self.tabu_tenure = self.tabu_list_size
            logger.warning(
                "SolverConfig.tabu_list_size is deprecated, use tabu_tenure instead. "
                "Synced tabu_tenure=%d", self.tabu_tenure,
            )
        # ALNS destroy rate must be in (0, 1]
        if not isinstance(self.alns_destroy_rate, (int, float)) or not (0 < self.alns_destroy_rate <= 1):
            self.alns_destroy_rate = 0.3
        # ALNS iterations must be positive
        if not isinstance(self.alns_iterations, int) or self.alns_iterations <= 0:
            self.alns_iterations = 10000
        # ALNS segment size must be positive
        if not isinstance(self.alns_segment_size, int) or self.alns_segment_size <= 0:
            self.alns_segment_size = 100
        # SA temperatures must be positive
        if not isinstance(self.initial_temp, (int, float)) or self.initial_temp <= 0:
            self.initial_temp = 100.0
        if not isinstance(self.final_temp, (int, float)) or self.final_temp <= 0:
            self.final_temp = 0.1
        # Ensure initial_temp > final_temp
        if self.initial_temp <= self.final_temp:
            self.initial_temp = max(self.final_temp * 10, 100.0)


# ============================================================================
# Data Classes (shared across all solvers) - MES v5 Schema
# ============================================================================


@dataclass
class NcCode:
    """NC program information"""

    program_id: str
    file_path: str
    cycle_time_sec: int
    cycle_time_confidence: float = 1.0
    tool_list: List[str] = field(default_factory=list)
    tool_change_count: int = 0
    compatible_machines: List[str] = field(default_factory=list)


@dataclass
class Operation:
    """Work operation - directly under WorkOrder (no Job layer)"""

    op_id: str
    op_name: str
    sequence: int
    predecessors: List[str]
    required_machines: List[str]   # list of machine IDs, machine types, or "AMR"
    setup_id: str
    nc_code: NcCode
    cycle_time_sec: Optional[int] = None  # promoted from nc_code for simpler access

    def get_cycle_time(self) -> int:
        """Get cycle time, preferring direct value over nc_code"""
        if self.cycle_time_sec is not None:
            return self.cycle_time_sec
        return self.nc_code.cycle_time_sec

    @property
    def required_machine_type(self) -> str:
        """Backward compat: returns first non-AMR entry as primary machine type"""
        for entry in self.required_machines:
            if entry.upper() != "AMR":
                return entry
        return self.required_machines[0] if self.required_machines else ""


@dataclass
class WorkOrder:
    """Work order - MES v5 Schema (operations directly, no jobs layer)"""

    wo_id: str
    product_id: str
    product_name: str
    order_quantity: int
    due_date: datetime
    priority: int
    release_date: datetime
    customer: str
    # MES v5: operations directly under work order
    operations: List[Operation]
    # MES work_orders.lot_no — 작업지시의 고유 별칭 (분할 순번 sublot_no와 무관)
    lot_no: str = ""


@dataclass
class OccupiedSlot:
    """Time slot already occupied on a machine (existing schedule)"""

    start: int  # seconds from horizon start
    end: int  # seconds from horizon start
    wo_id: Optional[str] = None


@dataclass
class Machine:
    """Machine/Equipment"""

    machine_id: str
    machine_name: str
    machine_type: str
    status: str
    available_from: datetime
    current_setup_id: Optional[str]
    setup_change_time_min: int
    occupied_slots: List[OccupiedSlot] = field(default_factory=list)
    calendar: Optional[Calendar] = None


@dataclass
class MachineTypeParams:
    """Machine type parameters"""

    loading_type: str
    amr_transport_qty: int
    exchange_time_sec: int = 0
    load_unload_time_sec: int = 0


@dataclass
class ScheduledTask:
    """Scheduled task result - MES v5 (no job_id)"""

    wo_id: str
    op_id: str
    machine_id: str       # primary (first non-AMR) assigned machine
    start_time: int       # seconds from horizon start
    end_time: int
    quantity: int
    setup_time: int = 0
    sublot_no: int = 1   # 작업지시 qty를 lot_size로 분할한 조각의 순번 (1,2,3,…)
    lot_no: str = ""     # MES work_orders.lot_no — 이 task가 속한 작업지시의 별칭
    op_name: str = ""
    assigned_machines: Dict[str, str] = field(default_factory=dict)  # entry → machine_id
    amr_transfer_sec: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScheduleResult:
    """Complete scheduling result"""

    status: str  # "success", "no_solution", "error"
    scheduled_tasks: List[ScheduledTask]
    objective_value: float
    solve_time_sec: float
    total_makespan: int
    machine_utilization: Dict[str, float]
    bottleneck_machines: List[str]
    solver_info: Dict[str, Any] = field(default_factory=dict)
    infeasible_wos: List[str] = field(default_factory=list)
    setup_intervals: List[SetupInterval] = field(default_factory=list)
    # Lexicographic objective components (공통 evaluate() 산출 — 솔버 간 비교용)
    weighted_tardiness_sec: int = 0    # tier-1: Σ weight·max(0, 완료−납기)
    weighted_completion_sec: int = 0   # tier-2: Σ weight·완료시간 (우선순위)
    total_setup_sec: int = 0           # tier-4: Σ setup_time

    @property
    def makespan_sec(self) -> int:
        return self.total_makespan

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "scheduled_tasks": [t.to_dict() for t in self.scheduled_tasks],
            "objective_value": self.objective_value,
            "solve_time_sec": self.solve_time_sec,
            "total_makespan": self.total_makespan,
            "machine_utilization": self.machine_utilization,
            "bottleneck_machines": self.bottleneck_machines,
            "solver_info": self.solver_info,
            "infeasible_wos": self.infeasible_wos,
            "setup_intervals": [s.to_dict() for s in self.setup_intervals],
            "weighted_tardiness_sec": self.weighted_tardiness_sec,
            "weighted_completion_sec": self.weighted_completion_sec,
            "total_setup_sec": self.total_setup_sec,
        }


# ============================================================================
# Base Solver Class
# ============================================================================


class BaseSolver(ABC):
    """
    Abstract base class for scheduling solvers

    All solver implementations must inherit from this class and implement:
    - solve(): Main solving method
    - get_solver_info(): Return solver metadata
    """

    def __init__(
        self,
        work_orders: List[WorkOrder],
        machines: List[Machine],
        machine_type_params: Dict[str, MachineTypeParams],
        horizon_start: datetime,
        horizon_end: datetime,
        constraints: Dict[str, Any] = None,
        config: SolverConfig = None,
        amrs: List[AMRConfig] = None,
        scheduler_config: SchedulerConfig = None,
    ):
        self.work_orders = work_orders
        self.machines = machines
        self.machine_type_params = machine_type_params
        self.horizon_start = horizon_start
        self.horizon_end = horizon_end
        self.horizon_seconds = int((horizon_end - horizon_start).total_seconds())
        self.constraints = constraints or {}
        self.config = config or SolverConfig()
        self.amrs = amrs or []
        self.scheduler_config = scheduler_config or SchedulerConfig()

        self.scheduled_tasks: List[ScheduledTask] = []
        self.machine_type_mismatches: List[str] = []

        # Build occupied-slot lookup per machine for O(n log n) conflict checks
        self._occupied_slots_map: Dict[str, List[OccupiedSlot]] = {}
        for machine in self.machines:
            if machine.occupied_slots:
                sorted_slots = sorted(machine.occupied_slots, key=lambda s: s.start)
                self._occupied_slots_map[machine.machine_id] = self._merge_overlapping_slots(sorted_slots)

        # ── Shared decoder: lookup maps ────────────────────────────────────────
        self.mach_map: Dict[str, Machine] = {m.machine_id: m for m in self.machines}
        self.amr_map: Dict[str, AMRConfig] = {a.amr_id: a for a in self.amrs}
        self.type_map: Dict[str, List[str]] = {}
        self.name_map: Dict[str, str] = {}
        for m in self.machines:
            self.type_map.setdefault(m.machine_type, []).append(m.machine_id)
            self.name_map[m.machine_name] = m.machine_id
        self.lot_sizes: Dict[str, List[int]] = {
            wo.wo_id: self._compute_lot_sizes(wo.order_quantity)
            for wo in self.work_orders
        }
        self.wo_ops: Dict[str, List[Operation]] = {
            wo.wo_id: sorted(wo.operations, key=lambda o: o.sequence)
            for wo in self.work_orders
        }

    @abstractmethod
    def solve(self, time_limit_sec: int = None) -> ScheduleResult:
        """
        Solve the scheduling problem

        Args:
            time_limit_sec: Maximum time to spend solving (overrides config if provided)

        Returns:
            ScheduleResult with scheduled tasks and statistics
        """
        pass

    @abstractmethod
    def get_solver_info(self) -> Dict[str, Any]:
        """
        Get solver information and metadata

        Returns:
            Dictionary with solver name, version, capabilities, etc.
        """
        pass

    def _calculate_makespan(self) -> int:
        """Calculate total makespan in seconds"""
        if not self.scheduled_tasks:
            return 0
        return max(task.end_time for task in self.scheduled_tasks)

    # ── 공통 목적함수 평가 (lexicographic: tardiness → makespan → setup) ──────────

    def evaluate(self, tasks: List["ScheduledTask"]) -> Dict[str, int]:
        """모든 솔버 공통 평가지표. 비교표·objective_value·_fitness가 이 함수만 사용.

        lexicographic 우선순위(앞일수록 우선):
          1순위 weighted_tardiness  (납기 준수)
          2순위 weighted_completion (우선순위 가중 완료시간 — 고객 우선순위 주문 먼저 완료)
          3순위 makespan            (처리량/설비 회전)
          4순위 total_setup         (셋업 최소)
        weight = max_pri − priority + 1 (priority=1 이 가장 높은 가중치).
        ※ MTO·고객 우선순위 관례상 priority(가중완료)를 makespan보다 위에 둔다.
          처리량 우선(MTS) 공장이라면 2·3순위를 맞바꾼다.

        objective: 위 지표들을 BIG 진법으로 인코딩한 단일 정수.
        Python 임의정밀 정수라 오버플로 없이 엄밀한 lexicographic 비교가 된다.
        (OR-Tools는 int64 한계 때문에 이 스칼라 대신 계층적 순차 최적화를 쓴다.)
        """
        makespan = max((t.end_time for t in tasks), default=0)
        weighted_tardiness = 0
        weighted_completion = 0
        sum_weights = 0
        if self.work_orders:
            max_pri = max(wo.priority for wo in self.work_orders)
            for wo in self.work_orders:
                weight = max_pri - wo.priority + 1
                sum_weights += weight
                end_t = max((t.end_time for t in tasks if t.wo_id == wo.wo_id), default=0)
                due_s = int((wo.due_date - self.horizon_start).total_seconds())
                weighted_tardiness += weight * max(0, end_t - due_s)
                weighted_completion += weight * end_t
        total_setup = sum(getattr(t, "setup_time", 0) for t in tasks)
        # BIG > 하위 tier(makespan, weighted_completion, total_setup)의 가능한 상한.
        # tardiness는 최상위 digit이라 BIG를 넘어도 무방(임의정밀 정수).
        big = (sum_weights + len(self.machines) + 2) * self.horizon_seconds + 1
        objective = (((weighted_tardiness * big + weighted_completion) * big)
                     + makespan) * big + total_setup
        return {
            "weighted_tardiness": weighted_tardiness,
            "makespan": makespan,
            "weighted_completion": weighted_completion,
            "total_setup": total_setup,
            "objective": objective,
        }

    # ── 공통 가동률 (활성 구간 가용시간 분모, AMR 제외, idle 포함) ────────────────

    def _available_seconds(self, machine: "Machine", window_end: int) -> int:
        """[0, window_end] 구간에서 머신의 가용시간(초).

        캘린더(교대/휴식)가 있으면 그 가용시간만, 없으면 window_end 전체.
        window_end 는 horizon_start 기준 초.
        """
        if window_end <= 0:
            return 0
        cal = machine.calendar
        if cal is None:
            return window_end
        hs = self.horizon_start
        tz = hs.tzinfo
        end_dt = hs + timedelta(seconds=window_end)
        total = 0.0
        day = hs.replace(hour=0, minute=0, second=0, microsecond=0)
        for _ in range(800):  # 안전 상한
            if day >= end_dt:
                break
            shift_s = datetime.combine(day.date(), cal.shift_start, tzinfo=tz)
            shift_e = datetime.combine(day.date(), cal.shift_end, tzinfo=tz)
            s = max(shift_s, hs)
            e = min(shift_e, end_dt)
            if e > s:
                seg = (e - s).total_seconds()
                for brk in cal.breaks:
                    bs = datetime.combine(day.date(), brk.start, tzinfo=tz)
                    be = datetime.combine(day.date(), brk.end, tzinfo=tz)
                    os_ = max(bs, s)
                    oe = min(be, e)
                    if oe > os_:
                        seg -= (oe - os_).total_seconds()
                total += max(0.0, seg)
            day += timedelta(days=1)
        return int(total)

    def compute_utilization(self, tasks: List["ScheduledTask"], makespan: int) -> Dict[str, float]:
        """가동률(%) = busy / 활성구간 가용시간. OR-Tools·메타 공통.

        - 자원 집합: self.machines (가공 머신 + RACK), AMR 제외
        - idle 머신도 0%로 포함 (유휴 설비 노출)
        - 분모: _available_seconds(m, makespan) — 캘린더 없으면 makespan
        """
        if makespan <= 0:
            return {}
        amr_ids = set(self.amr_map)
        busy: Dict[str, int] = {}
        for t in tasks:
            dur = t.end_time - t.start_time
            for res_id in t.assigned_machines.values():
                if res_id in amr_ids:
                    continue
                busy[res_id] = busy.get(res_id, 0) + dur
        util: Dict[str, float] = {}
        for m in self.machines:
            avail = self._available_seconds(m, makespan)
            if avail > 0:
                util[m.machine_id] = round(100.0 * busy.get(m.machine_id, 0) / avail, 2)
        return util

    def _calculate_utilization(self) -> Dict[str, float]:
        """OR-Tools 경로 호환 래퍼 — 공통 compute_utilization으로 위임."""
        return self.compute_utilization(self.scheduled_tasks, self._calculate_makespan())

    def _find_bottlenecks(self) -> List[str]:
        """Find bottleneck machines (highest utilization)"""
        utilization = self._calculate_utilization()
        if not utilization:
            return []
        avg_util = sum(utilization.values()) / len(utilization)
        return [m for m, u in utilization.items() if u > avg_util * 1.2]

    @staticmethod
    def _merge_overlapping_slots(slots: List[OccupiedSlot]) -> List[OccupiedSlot]:
        """
        Merge overlapping or adjacent occupied slots into a single slot.

        Assumes slots are already sorted by start time.

        Args:
            slots: Sorted list of OccupiedSlot instances

        Returns:
            New list with overlapping slots merged
        """
        if not slots:
            return slots

        merged: List[OccupiedSlot] = [OccupiedSlot(start=slots[0].start, end=slots[0].end, wo_id=slots[0].wo_id)]
        for slot in slots[1:]:
            last = merged[-1]
            if slot.start <= last.end:
                # Overlapping or adjacent — extend the last merged slot
                merged[-1] = OccupiedSlot(start=last.start, end=max(last.end, slot.end), wo_id=last.wo_id)
            else:
                merged.append(OccupiedSlot(start=slot.start, end=slot.end, wo_id=slot.wo_id))

        return merged

    def _adjust_start_for_occupied_slots(
        self, machine_id: str, desired_start: int, duration: int, setup_time: int = 300
    ) -> int:
        """
        Adjust a desired start time to avoid occupied slots on a machine.

        Shifts the task forward until it fits in a gap between existing occupations.
        Used by greedy-decode solvers (GA, SA, Tabu, ALNS).

        Args:
            machine_id: Machine to check
            desired_start: Earliest desired start (seconds from horizon start)
            duration: Task duration in seconds
            setup_time: Setup buffer in seconds (default 300 = 5 min)

        Returns:
            Adjusted start time that does not overlap any occupied slot
        """
        slots = self._occupied_slots_map.get(machine_id)
        if not slots:
            return desired_start

        start = desired_start
        task_end = start + duration

        for slot in slots:
            # If task finishes before this slot starts, no conflict
            if task_end <= slot.start:
                break
            # If task starts after this slot ends (+ setup), skip to next slot
            if start >= slot.end + setup_time:
                continue
            # Overlap — push start past this slot's end + setup
            start = slot.end + setup_time
            task_end = start + duration

        return start

    def _get_compatible_machines(self, operation: Operation) -> List[Machine]:
        """Get machines compatible with operation's primary (first non-AMR) required type.

        Uses required_machine_type property which returns the first non-AMR entry
        from required_machines list for backward compatibility with greedy solvers.
        """
        primary_type = operation.required_machine_type
        required_type = primary_type.upper()

        # Try exact case-insensitive match first
        compatible = [m for m in self.machines if m.machine_type.upper() == required_type]

        # Fallback: if no match, use all machines and track the mismatch
        if not compatible:
            logger.error(
                f"No machines found for machine type '{primary_type}' "
                f"(op_id='{operation.op_id}'). Available types: "
                f"{sorted(set(m.machine_type for m in self.machines))}. "
                f"Falling back to all {len(self.machines)} machines."
            )
            self.machine_type_mismatches.append(primary_type)
            return self.machines

        return compatible

    def _get_operation_duration(self, operation: Operation, quantity: int) -> int:
        """Calculate operation duration in seconds"""
        cycle_time = operation.get_cycle_time()
        if cycle_time is None and operation.nc_code:
            cycle_time = operation.nc_code.cycle_time_sec
        if cycle_time:
            return cycle_time * quantity
        return 3600 * quantity  # Default 1 hour per unit

    def _ensure_precedence_order(self, indices: list, operations: list) -> list:
        """Reorder operation indices so predecessors always come before dependents.

        The permutation controls machine-time priority, but we ensure no operation
        is scheduled before its predecessors within the same WO.

        Args:
            indices: List of operation indices (or (op_idx, machine_id) tuples)
            operations: The operation pool/list to look up op info from

        Returns:
            Reordered list with same elements, predecessors first.
        """
        # Support both plain index lists and (op_idx, machine_id) tuples
        def get_idx(item):
            return item[0] if isinstance(item, tuple) else item

        scheduled_ops: set = set()
        result = []
        remaining = list(indices)
        max_passes = len(remaining) + 1
        pass_count = 0

        while remaining and pass_count < max_passes:
            next_remaining = []
            progress = False
            for item in remaining:
                idx = get_idx(item)
                op = operations[idx]
                predecessors_met = all(
                    f"{op.wo_id}:{pred_id}" in scheduled_ops
                    for pred_id in op.predecessors
                )
                if predecessors_met:
                    result.append(item)
                    scheduled_ops.add(f"{op.wo_id}:{op.op_id}")
                    progress = True
                else:
                    next_remaining.append(item)
            remaining = next_remaining
            pass_count += 1
            if not progress:
                # Circular dependency or missing predecessors - append remaining as-is
                result.extend(remaining)
                break

        return result

    # ── Shared Greedy Decoder (ported from scheduler_advanced v3) ─────────────

    def _compute_lot_sizes(self, qty: int) -> List[int]:
        if qty <= 0:
            return []
        ls = max(1, self.scheduler_config.lot_size)  # 0/음수 방어
        n = (qty + ls - 1) // ls
        sizes = [ls] * (n - 1)
        sizes.append(qty - ls * (n - 1))
        return sizes

    def _is_amr_entry(self, entry: str) -> bool:
        return entry.upper() == "AMR" or entry in self.amr_map

    def _resolve_mach_candidates(self, entry: str, compat: List[str]) -> List[str]:
        """entry(타입/ID) → 후보 machine_id 목록. compat은 이름 또는 ID 혼용 가능."""
        if entry in self.mach_map:
            return [entry]
        cands = list(self.type_map.get(entry, []))
        if compat:
            compat_ids: Set[str] = set()
            for c in compat:
                if c in self.mach_map:
                    compat_ids.add(c)
                elif c in self.name_map:
                    compat_ids.add(self.name_map[c])
            cands = [c for c in cands if c in compat_ids]
        return cands

    def _resolve_amr_candidates(self, entry: str) -> List[str]:
        if entry in self.amr_map:
            return [entry]
        return list(self.amr_map.keys())

    def _avail_sec(self, m: Machine) -> int:
        return max(0, int((m.available_from - self.horizon_start).total_seconds()))

    def _push_past_break(
        self, start: int, duration: int, mach: Machine
    ) -> Tuple[int, int]:
        """캘린더(교대/휴식) 제약을 반영해 (new_start, new_end) 반환."""
        if mach.calendar is None:
            return start, start + duration
        hs = self.horizon_start
        tz = hs.tzinfo  # horizon이 tz-aware면 combine 결과에도 tz 부여
        for _ in range(800):
            day = (hs + timedelta(seconds=start)).date()
            shift_s = int((datetime.combine(day, mach.calendar.shift_start, tzinfo=tz) - hs).total_seconds())
            shift_e = int((datetime.combine(day, mach.calendar.shift_end, tzinfo=tz) - hs).total_seconds())
            if start < shift_s:
                start = shift_s
                continue
            if start >= shift_e:
                next_day = day + timedelta(days=1)
                start = int((datetime.combine(next_day, mach.calendar.shift_start, tzinfo=tz) - hs).total_seconds())
                continue
            pushed = False
            for brk in mach.calendar.breaks:
                brk_s = int((datetime.combine(day, brk.start, tzinfo=tz) - hs).total_seconds())
                brk_e = int((datetime.combine(day, brk.end, tzinfo=tz) - hs).total_seconds())
                if start < brk_e and start + duration > brk_s:
                    start = brk_e
                    pushed = True
                    break
            if pushed:
                continue
            if start + duration <= shift_e:
                return start, start + duration
            next_day = day + timedelta(days=1)
            start = int((datetime.combine(next_day, mach.calendar.shift_start, tzinfo=tz) - hs).total_seconds())
        return start, start + duration

    def _decode(
        self, chromosome: List[int]
    ) -> Tuple[List[ScheduledTask], List[SetupInterval], int]:
        """
        chromosome: WO 인덱스의 순열(self.work_orders 기준).
        각 WO의 모든 lot을 greedy 배정한다.
        반환: (scheduled_tasks, setup_intervals, makespan_sec)
        """
        resource_free: Dict[str, int] = {
            m.machine_id: self._avail_sec(m) for m in self.machines
        }
        resource_free.update({a.amr_id: 0 for a in self.amrs})

        op_end:     Dict[Tuple[str, str, int], int] = {}   # (wo_id, op_id, sublot_no) → end
        binding:    Dict[Tuple[str, int, str], str] = {}   # (wo_id, sublot_no, entry) → machine_id
        setup_done: Set[Tuple[str, str]]            = set() # (wo_id, machine_id)

        tasks:     List[ScheduledTask] = []
        setup_ivs: List[SetupInterval] = []

        # 루프 구조: lot_pass(바깥) → op_round(중간) → wo_idx(안쪽)
        #
        # [lot_pass 바깥] lot 순서를 지킨다.
        #   같은 WO의 lot N+1은 lot N이 완전히 끝난 뒤에만 시작 가능.
        #   lot_pass가 바깥이면 lot1 전체가 끝난 뒤 lot2 진입이 보장된다.
        #
        # [op_round 중간] 같은 lot 내에서 WO 간 공정 단위 파이프라이닝.
        #   op_round=0(LOAD): WO110 → WO109 순서로 배정 →
        #     WO110이 MILL로 이동하는 순간 AMR·RACK이 비어 WO109 LOAD 즉시 시작 가능.
        #   op_round=1(MILL): WO110 → WO109 배정 → 다른 VMC에서 병렬 가공.
        max_lots = max(
            (len(self.lot_sizes[self.work_orders[idx].wo_id]) for idx in chromosome),
            default=0,
        )
        max_ops = max(
            (len(self.wo_ops[self.work_orders[idx].wo_id]) for idx in chromosome),
            default=0,
        )
        # (wo_id, sublot_no) → 직전 공정 / 직전 공정 종료 시각 추적
        prev_op_track:  Dict[Tuple[str, int], Optional[Operation]] = {}
        prev_end_track: Dict[Tuple[str, int], int]                 = {}
        # (wo_id, sublot_no) → 해당 lot 마지막 공정의 종료 시각 (lot 완료 시각)
        lot_last_end:   Dict[Tuple[str, int], int]                 = {}

        for lot_pass in range(max_lots):
            for op_round in range(max_ops):
                for wo_idx in chromosome:
                    wo       = self.work_orders[wo_idx]
                    lot_list = self.lot_sizes[wo.wo_id]
                    if lot_pass >= len(lot_list):
                        continue
                    ops = self.wo_ops[wo.wo_id]
                    if op_round >= len(ops):
                        continue
                    sublot_no = lot_pass + 1
                    lot_qty  = lot_list[lot_pass]
                    release  = max(0, int((wo.release_date - self.horizon_start).total_seconds()))

                    key      = (wo.wo_id, sublot_no)
                    prev_op  = prev_op_track.get(key)
                    prev_end = prev_end_track.get(key, 0)
                    op       = ops[op_round]

                    compat = (op.nc_code.compatible_machines
                              if op.nc_code and op.nc_code.compatible_machines else [])

                    # 1. 자원 배정 (non-AMR 먼저)
                    assigned: Dict[str, str] = {}
                    for entry in op.required_machines:
                        if self._is_amr_entry(entry):
                            continue
                        bkey = (wo.wo_id, sublot_no, entry)
                        if bkey in binding:
                            assigned[entry] = binding[bkey]
                        else:
                            cands = self._resolve_mach_candidates(entry, compat)
                            if not cands:
                                logger.warning("No candidates for entry '%s' op %s", entry, op.op_id)
                                continue
                            pick = min(cands, key=lambda m: resource_free.get(m, 0))
                            assigned[entry] = pick
                            binding[bkey]   = pick

                    # AMR 배정 (접근성 hard 제약 — OR-Tools와 동일)
                    for entry in op.required_machines:
                        if not self._is_amr_entry(entry):
                            continue
                        bkey = (wo.wo_id, sublot_no, entry)
                        if bkey in binding:
                            assigned[entry] = binding[bkey]
                        else:
                            amr_cands = self._resolve_amr_candidates(entry)
                            non_amr   = [v for k, v in assigned.items()
                                         if not self._is_amr_entry(k)]
                            accessible = [
                                a for a in amr_cands
                                if all(m in self.amr_map[a].accessible_machines for m in non_amr)
                            ]
                            if not accessible:
                                logger.warning(
                                    "AMR accessibility violation: no accessible AMR for op %s "
                                    "(non-AMR machines=%s, candidates=%s). Skipping AMR assignment.",
                                    op.op_id, non_amr, amr_cands,
                                )
                                self.machine_type_mismatches.append(f"amr:{entry}")
                                continue
                            pick = min(accessible, key=lambda a: resource_free.get(a, 0))
                            assigned[entry] = pick
                            binding[bkey]   = pick

                    # 2. Setup time — 임시 배치 (resource_free 누적용),
                    # 최종 위치는 task start 확정 후 재배치(공백 제거)한다.
                    setup_sec = 0
                    this_op_setups: Dict[str, Tuple[int, int]] = {}  # m_id → (sv_idx, duration)
                    for entry, m_id in list(assigned.items()):
                        if self._is_amr_entry(entry):
                            continue
                        skey = (wo.wo_id, m_id)
                        if skey in setup_done:
                            continue
                        mach = self.mach_map.get(m_id)
                        if mach and mach.setup_change_time_min > 0:
                            need = (mach.current_setup_id is None
                                    or mach.current_setup_id != op.setup_id)
                            if need:
                                st       = mach.setup_change_time_min * 60
                                sv_start = resource_free.get(m_id, 0)
                                sv_end   = sv_start + st
                                resource_free[m_id] = sv_end
                                setup_sec = max(setup_sec, st)
                                this_op_setups[m_id] = (len(setup_ivs), st)
                                setup_ivs.append(SetupInterval(
                                    machine_id=m_id,
                                    wo_id=wo.wo_id,
                                    start_time=sv_start,
                                    end_time=sv_end,
                                ))
                        setup_done.add(skey)

                    # 3. 선행 제약
                    pred_end = release if prev_op is None else prev_end
                    if sublot_no > 1:
                        # lot N+1의 첫 공정은 lot N 전체가 완전히 끝난 뒤에만 시작
                        if op_round == 0:
                            pred_end = max(pred_end,
                                           lot_last_end.get((wo.wo_id, sublot_no - 1), 0))
                        # 같은 공정의 이전 lot이 끝난 뒤에만 시작 (lot 간 파이프라인)
                        pred_end = max(pred_end,
                                       op_end.get((wo.wo_id, op.op_id, sublot_no - 1), 0))

                    # 4. AMR 이동 시간 + duration
                    has_amr      = any(self._is_amr_entry(e) for e in op.required_machines)
                    prev_has_amr = (any(self._is_amr_entry(e) for e in prev_op.required_machines)
                                    if prev_op else False)
                    amr_sec = (self.scheduler_config.amr_transfer_time_sec
                               if has_amr and not prev_has_amr else 0)
                    try:
                        cycle_time = op.get_cycle_time()
                    except AttributeError:
                        cycle_time = 3600  # nc_code 없는 경우 기본 1시간
                    duration = lot_qty * cycle_time + amr_sec

                    # 5. 시작 시각 (연속 점유 고려)
                    shared   = (set(prev_op.required_machines) & set(op.required_machines)
                                if prev_op else set())
                    all_free = (max([pred_end] + [resource_free.get(r, 0) for r in assigned.values()])
                                if assigned else pred_end)
                    start    = max(prev_end, all_free) if shared else all_free

                    # 6. 캘린더 보정
                    primary_mach = next(
                        (self.mach_map[v]
                         for k, v in assigned.items()
                         if not self._is_amr_entry(k) and v in self.mach_map),
                        None,
                    )
                    start, end = (self._push_past_break(start, duration, primary_mach)
                                  if primary_mach else (start, start + duration))

                    # 7. 기존 점유 슬롯 충돌 회피 (캘린더 보정 후에 체크)
                    adjusted = start
                    for res_id in assigned.values():
                        adjusted = max(adjusted, self._adjust_start_for_occupied_slots(
                            res_id, adjusted, duration, setup_time=0
                        ))
                    if adjusted != start:
                        # 점유 슬롯 때문에 start가 밀렸으면 캘린더 재보정
                        start, end = (self._push_past_break(adjusted, duration, primary_mach)
                                      if primary_mach else (adjusted, adjusted + duration))

                    # 7b. Setup 재배치 — task start 직전으로 옮겨 공백 제거.
                    # 캘린더·점유슬롯 보정으로 start가 임시 sv_end보다 뒤로 밀린 경우
                    # setup이 일찍 끝나고 빈 구간이 생기는 문제를 막는다.
                    for m_id, (sv_idx, st_dur) in this_op_setups.items():
                        orig = setup_ivs[sv_idx]
                        new_start = start - st_dur
                        # 안전 가드: 머신의 원래 free 시점(=orig.start_time)보다
                        # 더 일찍은 옮기지 않는다(과거 점유와 겹치지 않도록).
                        if new_start <= orig.start_time:
                            continue
                        setup_ivs[sv_idx] = SetupInterval(
                            machine_id=m_id,
                            wo_id=wo.wo_id,
                            start_time=new_start,
                            end_time=start,
                        )

                    # 8. 상태 갱신
                    for res_id in assigned.values():
                        resource_free[res_id] = end
                    op_end[(wo.wo_id, op.op_id, sublot_no)] = end

                    primary_id = next(
                        (v for k, v in assigned.items() if not self._is_amr_entry(k)),
                        next(iter(assigned.values()), "unknown"),
                    )

                    tasks.append(ScheduledTask(
                        wo_id=wo.wo_id,
                        op_id=op.op_id,
                        machine_id=primary_id,
                        start_time=start,
                        end_time=end,
                        quantity=lot_qty,
                        setup_time=setup_sec,
                        sublot_no=sublot_no,   # 분할 조각 순번
                        lot_no=wo.lot_no,      # 작업지시 별칭
                        op_name=op.op_name,
                        assigned_machines=dict(assigned),
                        amr_transfer_sec=amr_sec,
                    ))

                    prev_op_track[key]  = op
                    prev_end_track[key] = end
                    lot_last_end[(wo.wo_id, sublot_no)] = end  # 마지막 공정일수록 덮어쓰여 최종값이 남음

        makespan = max((t.end_time for t in tasks), default=0)
        return tasks, setup_ivs, makespan

    def _makespan(self, chromosome: List[int]) -> int:
        _, _, ms = self._decode(chromosome)
        return ms

    def _fitness(self, chromosome: List[int]):
        """공통 lexicographic objective 스칼라 (작을수록 좋음).

        모든 메타휴리스틱(GA·SA·Tabu·ALNS)이 공유. evaluate()와 동일 정의:
          1순위 weighted_tardiness → 2순위 makespan → 3순위 total_setup.
        Python 임의정밀 정수라 BIG 진법 인코딩에도 오버플로가 없고, 부등호·뺄셈
        (SA/ALNS의 Δ)이 모두 lexicographic 순서와 일치한다.
        """
        tasks, _, _ = self._decode(chromosome)
        return self.evaluate(tasks)["objective"]

    def _initial_solution(self) -> List[int]:
        """priority 오름차순(우선순위 높은 순) 초기해."""
        return sorted(range(len(self.work_orders)),
                      key=lambda i: self.work_orders[i].priority)

    def _decode_utilization(
        self, tasks: List[ScheduledTask], makespan: int
    ) -> Dict[str, float]:
        """공통 compute_utilization으로 위임 (OR-Tools 경로와 동일 계산)."""
        return self.compute_utilization(tasks, makespan)

    def _build_result(
        self, best: List[int], solve_time: float, status: str = "success"
    ) -> ScheduleResult:
        if not best:
            return ScheduleResult(
                status="no_solution",
                scheduled_tasks=[],
                objective_value=0.0,
                solve_time_sec=solve_time,
                total_makespan=0,
                machine_utilization={},
                bottleneck_machines=[],
            )
        tasks, setup_ivs, makespan = self._decode(best)
        tasks.sort(key=lambda t: (t.start_time, t.wo_id, t.sublot_no))
        self.scheduled_tasks = tasks  # generate_gantt_data / estimate_schedule_quality용
        util  = self.compute_utilization(tasks, makespan)
        avg_u = sum(util.values()) / max(len(util), 1) if util else 0
        bottlenecks = [m for m, u in util.items() if u > avg_u * 1.2]
        ev = self.evaluate(tasks)
        return ScheduleResult(
            status=status,
            scheduled_tasks=tasks,
            objective_value=float(ev["weighted_tardiness"]),  # tier-1 (읽기 쉬운 헤드라인)
            solve_time_sec=solve_time,
            total_makespan=makespan,
            machine_utilization=util,
            bottleneck_machines=bottlenecks,
            setup_intervals=setup_ivs,
            weighted_tardiness_sec=ev["weighted_tardiness"],
            weighted_completion_sec=ev["weighted_completion"],
            total_setup_sec=ev["total_setup"],
        )

    def generate_gantt_data(self) -> Dict[str, Any]:
        """Generate Gantt chart data for visualization"""
        gantt_tasks = []

        for task in self.scheduled_tasks:
            start_dt = self.horizon_start + timedelta(seconds=task.start_time)
            end_dt = self.horizon_start + timedelta(seconds=task.end_time)

            wo = next((w for w in self.work_orders if w.wo_id == task.wo_id), None)
            priority = wo.priority if wo else 5
            priority_color = {
                1: "#FF6B6B",
                2: "#FF6B6B",  # High priority - red
                3: "#FFE66D",
                4: "#FFE66D",  # Medium - yellow
                5: "#4ECDC4",
                6: "#4ECDC4",  # Normal - teal
            }.get(priority, "#95E1D3")

            gantt_tasks.append(
                {
                    "name": f"{task.wo_id} / {task.op_id}",
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "resource": task.machine_id,
                    "priority": priority,
                    "color": priority_color,
                    "quantity": task.quantity,
                    "duration_minutes": (task.end_time - task.start_time) / 60,
                }
            )

        resources = sorted(set(task.machine_id for task in self.scheduled_tasks))

        return {
            "tasks": gantt_tasks,
            "resources": resources,
            "start": self.horizon_start.isoformat(),
            "end": self.horizon_end.isoformat(),
        }

    def estimate_schedule_quality(self) -> Dict[str, Any]:
        """Estimate overall schedule quality metrics"""
        if not self.scheduled_tasks:
            return {
                "status": "no_schedule",
                "makespan_hours": 0,
                "total_lateness_hours": 0,
                "avg_machine_utilization": 0,
                "bottleneck_machines": [],
                "schedule_efficiency": 0,
                "machine_type_mismatch_count": len(self.machine_type_mismatches),
            }

        # Calculate lateness for each work order
        total_lateness = 0
        wo_lateness = {}

        for wo in self.work_orders:
            wo_tasks = [t for t in self.scheduled_tasks if t.wo_id == wo.wo_id]
            if wo_tasks:
                last_task = max(wo_tasks, key=lambda x: x.end_time)
                end_time = self.horizon_start + timedelta(seconds=last_task.end_time)
                lateness_seconds = max(0, (end_time - wo.due_date).total_seconds())
                wo_lateness[wo.wo_id] = lateness_seconds / 3600
                total_lateness += lateness_seconds

        makespan = self._calculate_makespan()
        utilization = self._calculate_utilization()
        avg_utilization = sum(utilization.values()) / len(utilization) if utilization else 0
        ev = self.evaluate(self.scheduled_tasks)

        return {
            "status": "scheduled",
            "makespan_hours": round(makespan / 3600, 2),
            "total_lateness_hours": round(total_lateness / 3600, 2),
            # lexicographic 목적함수 컴포넌트 (솔버 간 동일 정의)
            "weighted_tardiness_hours": round(ev["weighted_tardiness"] / 3600, 2),
            "weighted_completion_minutes": round(ev["weighted_completion"] / 60, 2),
            "total_setup_minutes": round(ev["total_setup"] / 60, 2),
            "avg_machine_utilization": round(avg_utilization, 2),
            "machine_utilization": utilization,
            "bottleneck_machines": self._find_bottlenecks(),
            "schedule_efficiency": round(avg_utilization, 2),
            "per_wo_lateness": {k: round(v, 2) for k, v in wo_lateness.items()},
            "total_scheduled_tasks": len(self.scheduled_tasks),
            "total_work_orders": len(self.work_orders),
            "total_machines": len(self.machines),
            "machine_type_mismatch_count": len(self.machine_type_mismatches),
        }
