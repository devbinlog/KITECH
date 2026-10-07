"""
Solver Scheduling Tests

각 솔버(OR-Tools, GA, SA, Tabu, ALNS)에 대해 실제 스케줄링을 수행하고
결과를 검증한다.  v5 API (`required_machines` 리스트) 기준.

실행:  pytest tests/test_solver_scheduling.py -v -s
"""

import sys
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── Import 경로 설정 ────────────────────────────────────────────────────────────
_workspace = Path(__file__).parent.parent.parent.parent
_src_path  = _workspace / "agents" / "cell-scheduler" / "src"
sys.path.insert(0, str(_src_path))

from solvers.base_solver import (
    WorkOrder, Operation, Machine, NcCode, OccupiedSlot,
    AMRConfig, SchedulerConfig, SolverConfig, MachineTypeParams,
)
from solvers.ortools_solver             import ORToolsSolver
from solvers.genetic_algorithm_solver   import GeneticAlgorithmSolver
from solvers.simulated_annealing_solver import SimulatedAnnealingSolver
from solvers.tabu_search_solver         import TabuSearchSolver
from solvers.alns_solver                import ALNSSolver


# ── 공통 픽스처 ─────────────────────────────────────────────────────────────────

NOW = datetime(2026, 5, 18, 8, 0, 0, tzinfo=timezone.utc)
HORIZON_START = NOW
HORIZON_END   = NOW + timedelta(hours=24)


def _nc(program_id: str, cycle_time_sec: int = 120,
        compatible_machines: list = None) -> NcCode:
    return NcCode(
        program_id=program_id,
        file_path=f"/nc/{program_id}.nc",
        cycle_time_sec=cycle_time_sec,
        compatible_machines=compatible_machines or [],
    )


def _op(op_id: str, sequence: int, required_machines: list,
        cycle_time_sec: int = 120, setup_id: str = "S1",
        predecessors: list = None, nc_program: str = None,
        compatible_machines: list = None) -> Operation:
    return Operation(
        op_id=op_id,
        op_name=op_id,
        sequence=sequence,
        predecessors=predecessors or [],
        required_machines=required_machines,
        setup_id=setup_id,
        nc_code=_nc(nc_program or op_id, cycle_time_sec, compatible_machines),
    )


def _wo(wo_id: str, ops: list, qty: int = 5, priority: int = 5,
        due_hours: float = 8.0) -> WorkOrder:
    return WorkOrder(
        wo_id=wo_id,
        product_id=f"PROD-{wo_id}",
        product_name=f"Product {wo_id}",
        order_quantity=qty,
        due_date=HORIZON_START + timedelta(hours=due_hours),
        priority=priority,
        release_date=HORIZON_START,
        customer="Test",
        operations=ops,
    )


def _machine(machine_id: str, machine_type: str, machine_name: str = None,
             setup_change_time_min: int = 5,
             current_setup_id: str = None) -> Machine:
    return Machine(
        machine_id=machine_id,
        machine_name=machine_name or machine_id,
        machine_type=machine_type,
        status="available",
        available_from=HORIZON_START,
        current_setup_id=current_setup_id,
        setup_change_time_min=setup_change_time_min,
    )


def _solver_config(time_limit: int = 3) -> SolverConfig:
    return SolverConfig(
        time_limit_sec=time_limit,
        population_size=20,
        initial_temp=50.0,
        cooling_rate=0.95,
        final_temp=0.1,
        tabu_tenure=5,
        diversification_freq=30,
        alns_destroy_rate=0.3,
        alns_segment_size=20,
    )


def _machine_type_params() -> dict:
    return {
        "CNC":  MachineTypeParams(loading_type="auto",   amr_transport_qty=1),
        "LATHE": MachineTypeParams(loading_type="manual", amr_transport_qty=1),
        "AMR":  MachineTypeParams(loading_type="amr",    amr_transport_qty=1),
    }


# ── 시나리오 빌더 ───────────────────────────────────────────────────────────────

def build_basic_scenario():
    """기본 시나리오: WO 3개, CNC 2대, LATHE 1대."""
    machines = [
        _machine("M1", "CNC",   "DH400"),
        _machine("M2", "CNC",   "DH500"),
        _machine("M3", "LATHE", "LA100"),
    ]
    work_orders = [
        _wo("WO-A", [
            _op("OP-A1", 1, ["CNC"],   cycle_time_sec=100, setup_id="S1"),
            _op("OP-A2", 2, ["LATHE"], cycle_time_sec=80,  setup_id="S1",
                predecessors=["OP-A1"]),
        ], qty=3, priority=1),
        _wo("WO-B", [
            _op("OP-B1", 1, ["CNC"],   cycle_time_sec=90,  setup_id="S2"),
        ], qty=4, priority=3),
        _wo("WO-C", [
            _op("OP-C1", 1, ["LATHE"], cycle_time_sec=60,  setup_id="S1"),
            _op("OP-C2", 2, ["CNC"],   cycle_time_sec=120, setup_id="S1",
                predecessors=["OP-C1"]),
        ], qty=2, priority=2),
    ]
    return work_orders, machines


def build_lot_split_scenario():
    """lot 분할 시나리오: qty=6, lot_size=2 → lot 3개."""
    machines = [_machine("M1", "CNC")]
    work_orders = [
        _wo("WO-LOT", [
            _op("OP1", 1, ["CNC"], cycle_time_sec=60),
        ], qty=6, priority=5),
    ]
    scheduler_cfg = SchedulerConfig(lot_size=2, amr_transfer_time_sec=0)
    return work_orders, machines, scheduler_cfg


def build_amr_scenario():
    """AMR 시나리오: AMR이 accessible_machines를 만족해야 배정됨."""
    machines = [
        _machine("EQ-01", "CNC", "DH400"),
        _machine("EQ-02", "CNC", "NX550"),
    ]
    amrs = [
        AMRConfig(
            amr_id="AMR-01",
            model="MiR100",
            accessible_machines=["EQ-01", "EQ-02"],
            speed_m_per_sec=1.0,
        )
    ]
    work_orders = [
        _wo("WO-AMR", [
            _op("OP1", 1, ["CNC", "AMR"], cycle_time_sec=120, setup_id="S1"),
        ], qty=2, priority=3),
    ]
    scheduler_cfg = SchedulerConfig(lot_size=1, amr_transfer_time_sec=30)
    return work_orders, machines, amrs, scheduler_cfg


def build_setup_time_scenario():
    """setup 시간 시나리오: 서로 다른 setup_id를 가진 WO 2개가 같은 기계 공유."""
    machines = [_machine("M1", "CNC", setup_change_time_min=10, current_setup_id="S1")]
    work_orders = [
        _wo("WO-X", [_op("OPX", 1, ["CNC"], cycle_time_sec=100, setup_id="S1")], qty=2),
        _wo("WO-Y", [_op("OPY", 1, ["CNC"], cycle_time_sec=100, setup_id="S2")], qty=2),
    ]
    return work_orders, machines


def build_occupied_slot_scenario():
    """기존 점유 슬롯 회피: M1에 [0, 600] 슬롯이 이미 있음."""
    from solvers.base_solver import OccupiedSlot
    m1 = _machine("M1", "CNC")
    m1.occupied_slots = [OccupiedSlot(start=0, end=600)]
    machines = [m1]
    work_orders = [
        _wo("WO-OCC", [_op("OP1", 1, ["CNC"], cycle_time_sec=120)], qty=3, priority=5),
    ]
    return work_orders, machines


# ── 공통 검증 헬퍼 ──────────────────────────────────────────────────────────────

def assert_valid_result(result, solver_name: str, expected_min_tasks: int = 1):
    """스케줄 결과 기본 유효성 검사."""
    print(f"\n[{solver_name}] status={result.status} "
          f"tasks={len(result.scheduled_tasks)} "
          f"makespan={result.total_makespan/60:.1f}min "
          f"solve={result.solve_time_sec:.2f}s")

    for t in result.scheduled_tasks:
        print(f"  {t.wo_id} {t.op_id} lot{t.sublot_no} "
              f"machine={t.machine_id} "
              f"{t.start_time//60}~{t.end_time//60}min qty={t.quantity}")

    assert result.status in ("feasible", "optimal", "success"), \
        f"{solver_name}: unexpected status={result.status}"
    assert len(result.scheduled_tasks) >= expected_min_tasks, \
        f"{solver_name}: too few tasks ({len(result.scheduled_tasks)})"
    assert result.total_makespan > 0, f"{solver_name}: makespan=0"

    # 같은 기계에서 task 간 겹침 없는지 확인
    by_machine: dict = {}
    for t in result.scheduled_tasks:
        by_machine.setdefault(t.machine_id, []).append(t)
    for mid, tasks in by_machine.items():
        tasks_sorted = sorted(tasks, key=lambda x: x.start_time)
        for i in range(len(tasks_sorted) - 1):
            a, b = tasks_sorted[i], tasks_sorted[i + 1]
            assert a.end_time <= b.start_time, \
                f"{solver_name}: overlap on {mid}: [{a.start_time},{a.end_time}) vs [{b.start_time},{b.end_time})"


def make_solvers(work_orders, machines, config=None, amrs=None, scheduler_cfg=None):
    """모든 솔버 인스턴스를 같은 인자로 생성."""
    kwargs = dict(
        work_orders=work_orders,
        machines=machines,
        machine_type_params=_machine_type_params(),
        horizon_start=HORIZON_START,
        horizon_end=HORIZON_END,
        config=config or _solver_config(),
        amrs=amrs or [],
        scheduler_config=scheduler_cfg or SchedulerConfig(lot_size=1),
    )
    return {
        "OR-Tools": ORToolsSolver(**kwargs),
        "GA":       GeneticAlgorithmSolver(**kwargs),
        "SA":       SimulatedAnnealingSolver(**kwargs),
        "Tabu":     TabuSearchSolver(**kwargs),
        "ALNS":     ALNSSolver(**kwargs),
    }


# ── 테스트: 기본 시나리오 ────────────────────────────────────────────────────────

@pytest.mark.parametrize("solver_name", ["OR-Tools", "GA", "SA", "Tabu", "ALNS"])
def test_basic_scheduling(solver_name):
    """3개 WO, 다중 기계 타입, 선행 제약을 모든 솔버가 풀 수 있어야 한다."""
    wos, machines = build_basic_scenario()
    solvers = make_solvers(wos, machines)
    solver = solvers[solver_name]
    result = solver.solve(time_limit_sec=3)

    # WO-A: 2ops, WO-B: 1op, WO-C: 2ops → 최소 5 tasks
    assert_valid_result(result, solver_name, expected_min_tasks=5)

    # 선행 제약 검증: 각 lot별로 OP-A2는 반드시 OP-A1보다 늦어야 함 (lot-pipelining 허용)
    a1_tasks = [t for t in result.scheduled_tasks if t.wo_id == "WO-A" and t.op_id == "OP-A1"]
    a2_tasks = [t for t in result.scheduled_tasks if t.wo_id == "WO-A" and t.op_id == "OP-A2"]
    if a1_tasks and a2_tasks:
        sublot_nos = {t.sublot_no for t in a1_tasks} | {t.sublot_no for t in a2_tasks}
        for sublot_no in sublot_nos:
            a1_lot = [t for t in a1_tasks if t.sublot_no == sublot_no]
            a2_lot = [t for t in a2_tasks if t.sublot_no == sublot_no]
            if a1_lot and a2_lot:
                assert max(t.end_time for t in a1_lot) <= min(t.start_time for t in a2_lot), \
                    f"{solver_name}: OP-A2 lot{sublot_no} starts before OP-A1 lot{sublot_no} finishes"


# ── 테스트: lot 분할 ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("solver_name", ["GA", "SA", "Tabu", "ALNS"])
def test_lot_splitting(solver_name):
    """qty=6, lot_size=2 → lot 3개로 분할되어 task 3개여야 한다 (메타휴리스틱 전용)."""
    wos, machines, sched_cfg = build_lot_split_scenario()
    kwargs = dict(
        work_orders=wos,
        machines=machines,
        machine_type_params=_machine_type_params(),
        horizon_start=HORIZON_START,
        horizon_end=HORIZON_END,
        config=_solver_config(),
        amrs=[],
        scheduler_config=sched_cfg,
    )
    solver_cls = {
        "GA":   GeneticAlgorithmSolver,
        "SA":   SimulatedAnnealingSolver,
        "Tabu": TabuSearchSolver,
        "ALNS": ALNSSolver,
    }[solver_name]
    result = solver_cls(**kwargs).solve(time_limit_sec=3)

    print(f"\n[{solver_name}/lot-split] tasks={len(result.scheduled_tasks)}")
    for t in result.scheduled_tasks:
        print(f"  lot{t.sublot_no} qty={t.quantity} {t.start_time//60}~{t.end_time//60}min")

    assert result.status in ("feasible", "optimal", "success")
    # lot_size=2, qty=6 → 3 lots
    lot_count = len([t for t in result.scheduled_tasks if t.wo_id == "WO-LOT"])
    assert lot_count == 3, f"{solver_name}: expected 3 lots, got {lot_count}"
    quantities = sorted(t.quantity for t in result.scheduled_tasks if t.wo_id == "WO-LOT")
    assert quantities == [2, 2, 2], f"{solver_name}: wrong quantities {quantities}"


# ── 테스트: AMR 배정 ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("solver_name", ["GA", "SA", "Tabu", "ALNS"])
def test_amr_assignment(solver_name):
    """AMR이 required_machines에 포함되면 AMR 자원도 배정돼야 한다."""
    wos, machines, amrs, sched_cfg = build_amr_scenario()
    kwargs = dict(
        work_orders=wos,
        machines=machines,
        machine_type_params=_machine_type_params(),
        horizon_start=HORIZON_START,
        horizon_end=HORIZON_END,
        config=_solver_config(),
        amrs=amrs,
        scheduler_config=sched_cfg,
    )
    solver_cls = {
        "GA":   GeneticAlgorithmSolver,
        "SA":   SimulatedAnnealingSolver,
        "Tabu": TabuSearchSolver,
        "ALNS": ALNSSolver,
    }[solver_name]
    result = solver_cls(**kwargs).solve(time_limit_sec=3)

    assert_valid_result(result, solver_name + "/AMR", expected_min_tasks=1)

    # AMR-01이 assigned_machines에 포함되어야 함
    amr_assigned = any(
        "AMR-01" in t.assigned_machines.values()
        for t in result.scheduled_tasks
    )
    assert amr_assigned, f"{solver_name}: AMR-01 not assigned in any task"


# ── 테스트: setup 시간 반영 ──────────────────────────────────────────────────────

@pytest.mark.parametrize("solver_name", ["GA", "SA", "Tabu", "ALNS"])
def test_setup_time(solver_name):
    """setup_id가 다른 WO는 setup_change_time_min(10분) 패널티가 발생해야 한다."""
    wos, machines = build_setup_time_scenario()
    kwargs = dict(
        work_orders=wos,
        machines=machines,
        machine_type_params=_machine_type_params(),
        horizon_start=HORIZON_START,
        horizon_end=HORIZON_END,
        config=_solver_config(),
        amrs=[],
        scheduler_config=SchedulerConfig(lot_size=1),
    )
    solver_cls = {
        "GA":   GeneticAlgorithmSolver,
        "SA":   SimulatedAnnealingSolver,
        "Tabu": TabuSearchSolver,
        "ALNS": ALNSSolver,
    }[solver_name]
    result = solver_cls(**kwargs).solve(time_limit_sec=3)
    assert_valid_result(result, solver_name + "/setup", expected_min_tasks=2)

    # setup_intervals 또는 task.setup_time > 0 이 있어야 함
    has_setup = (
        any(t.setup_time > 0 for t in result.scheduled_tasks) or
        len(result.setup_intervals) > 0
    )
    print(f"\n[{solver_name}/setup] setup_intervals={len(result.setup_intervals)} "
          f"task.setup_time>0: {sum(1 for t in result.scheduled_tasks if t.setup_time>0)}")
    assert has_setup, f"{solver_name}: no setup time recorded despite S1→S2 change"


# ── 테스트: 점유 슬롯 회피 ───────────────────────────────────────────────────────

@pytest.mark.parametrize("solver_name", ["GA", "SA", "Tabu", "ALNS"])
def test_occupied_slot_avoidance(solver_name):
    """기존 점유 슬롯(0~600초)이 있을 때 스케줄이 그 이후에 배치돼야 한다."""
    wos, machines = build_occupied_slot_scenario()
    kwargs = dict(
        work_orders=wos,
        machines=machines,
        machine_type_params=_machine_type_params(),
        horizon_start=HORIZON_START,
        horizon_end=HORIZON_END,
        config=_solver_config(),
        amrs=[],
        scheduler_config=SchedulerConfig(lot_size=1),
    )
    solver_cls = {
        "GA":   GeneticAlgorithmSolver,
        "SA":   SimulatedAnnealingSolver,
        "Tabu": TabuSearchSolver,
        "ALNS": ALNSSolver,
    }[solver_name]
    result = solver_cls(**kwargs).solve(time_limit_sec=3)
    assert_valid_result(result, solver_name + "/occ-slot", expected_min_tasks=1)

    m1_tasks = [t for t in result.scheduled_tasks if t.machine_id == "M1"]
    for t in m1_tasks:
        assert t.start_time >= 600, \
            f"{solver_name}: task starts at {t.start_time}s, inside occupied slot [0,600)"


# ── 테스트: OR-Tools 기본 + nc_code compatible_machines ─────────────────────────

def test_ortools_basic():
    """OR-Tools가 기본 시나리오에서 feasible 해를 반환해야 한다."""
    wos, machines = build_basic_scenario()
    solver = ORToolsSolver(
        work_orders=wos,
        machines=machines,
        machine_type_params=_machine_type_params(),
        horizon_start=HORIZON_START,
        horizon_end=HORIZON_END,
        config=SolverConfig(time_limit_sec=5),
        scheduler_config=SchedulerConfig(lot_size=1),
    )
    result = solver.solve()
    assert_valid_result(result, "OR-Tools/basic", expected_min_tasks=5)


def test_ortools_compatible_machines_name_resolution():
    """OR-Tools: compatible_machines에 기계 이름을 써도 후보가 정상 필터링돼야 한다."""
    machines = [
        _machine("EQ-10", "CNC", "DH400"),
        _machine("EQ-11", "CNC", "NX550"),
    ]
    # compatible_machines에 기계 이름(ID 아님)을 사용
    nc = NcCode(
        program_id="NC-X",
        file_path="/nc/x.nc",
        cycle_time_sec=90,
        compatible_machines=["DH400"],  # 이름으로 지정 (EQ-10이 해당)
    )
    wos = [WorkOrder(
        wo_id="WO-NC",
        product_id="P1",
        product_name="P1",
        order_quantity=1,
        due_date=HORIZON_START + timedelta(hours=8),
        priority=5,
        release_date=HORIZON_START,
        customer="T",
        operations=[Operation(
            op_id="OP1",
            op_name="OP1",
            sequence=1,
            predecessors=[],
            required_machines=["CNC"],
            setup_id="S1",
            nc_code=nc,
        )],
    )]
    solver = ORToolsSolver(
        work_orders=wos,
        machines=machines,
        machine_type_params=_machine_type_params(),
        horizon_start=HORIZON_START,
        horizon_end=HORIZON_END,
        config=SolverConfig(time_limit_sec=5),
        scheduler_config=SchedulerConfig(lot_size=1),
    )
    result = solver.solve()
    assert result.status in ("feasible", "optimal", "success"), \
        f"OR-Tools: expected feasible but got {result.status}"
    # EQ-10(DH400)에만 배정되어야 함
    assigned = {t.machine_id for t in result.scheduled_tasks}
    assert "EQ-10" in assigned, "OR-Tools: expected EQ-10 (DH400) to be assigned"
    assert "EQ-11" not in assigned, "OR-Tools: EQ-11 (NX550) should not be assigned"


# ── 테스트: 전체 솔버 동일 시나리오 비교 ────────────────────────────────────────

def test_all_solvers_same_scenario():
    """모든 솔버가 동일한 시나리오에서 유효한 해를 반환하고 결과를 비교한다."""
    wos, machines = build_basic_scenario()
    solvers = make_solvers(wos, machines)

    results = {}
    for name, solver in solvers.items():
        results[name] = solver.solve(time_limit_sec=3)

    print("\n── 솔버별 결과 비교 ──")
    print(f"{'Solver':<15} {'Status':<12} {'Tasks':>6} {'Makespan(min)':>14} {'Solve(s)':>9}")
    print("-" * 60)
    for name, r in results.items():
        print(f"{name:<15} {r.status:<12} {len(r.scheduled_tasks):>6} "
              f"{r.total_makespan/60:>14.1f} {r.solve_time_sec:>9.2f}")

    for name, result in results.items():
        assert result.status in ("feasible", "optimal", "success"), \
            f"{name}: unexpected status={result.status}"
        assert len(result.scheduled_tasks) >= 5, \
            f"{name}: too few tasks ({len(result.scheduled_tasks)})"
