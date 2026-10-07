"""
실제 스케줄링 파이프라인 테스트

입력 3종:
  - aas_revised.json       : 설비 정보 (AASLoader로 파싱)
  - new_work_orders_v3.json: 최신 작업지시서 (머신 타입 기반 참조)
  - scheduler_config.json  : 솔버 설정

required_machines는 머신 타입 문자열(VMC_3AXIS_MASS, AMR, RACK 등)로
작업지시서에 직접 기재되며 솔버가 해석한다.
compatible_machines(NC 프로그램 호환 기계)만 idShort → AAS URI로 변환된다.

실행:
    uv run pytest agents/cell-scheduler/tests/test_pipeline.py -v
"""

import json
import sys
import pytest
from datetime import datetime, timezone
from pathlib import Path

# ── 경로 설정 ─────────────────────────────────────────────────────────────────
workspace = Path(__file__).parent.parent.parent.parent   # agents-workspace_260409/
src_path  = workspace / "agents" / "cell-scheduler" / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(workspace / "shared"))

AAS_FILE    = workspace / "samples" / "cell-scheduler" / "input" / "aas_revised.json"
WO_FILE     = workspace / "samples" / "cell-scheduler" / "input" / "new_work_orders_v3.json"
CFG_FILE    = workspace / "samples" / "cell-scheduler" / "input" / "scheduler_config.json"

import importlib.util as _ilu

def _load_aas_loader_module():
    spec = _ilu.spec_from_file_location(
        "aas_loader",
        src_path / "app" / "services" / "aas_loader.py",
    )
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_aas_loader_mod = _load_aas_loader_module()
AASLoader = _aas_loader_mod.AASLoader

from solvers import (                               # noqa: E402
    NcCode, Operation, WorkOrder,
    SolverFactory, SolverType, SolverConfig,
    SchedulerConfig,
)


# ── 작업지시서 파서 ───────────────────────────────────────────────────────────

def parse_work_orders(raw_list: list, name_map: dict) -> list:
    """new_work_orders_v3.json 파싱.

    required_machines는 머신 타입 문자열 그대로 유지한다.
    compatible_machines(idShort)만 name_map으로 AAS URI 변환한다.
    """
    work_orders = []
    for wo_raw in raw_list:
        operations = []
        for op_raw in wo_raw.get("operations", []):
            # required_machines: 머신 타입 문자열 그대로 유지
            required_machines = op_raw.get("required_machines", [])

            # nc_code.compatible_machines: idShort → AAS URI
            nc_raw = op_raw.get("nc_code", {})
            resolved_compatible = [
                name_map.get(name, name)
                for name in nc_raw.get("compatible_machines", [])
            ]

            nc_code = NcCode(
                program_id=nc_raw.get("program_id", "UNKNOWN"),
                file_path=nc_raw.get("file_path", ""),
                cycle_time_sec=nc_raw.get("cycle_time_sec", 60),
                compatible_machines=resolved_compatible,
            )

            operations.append(Operation(
                op_id=op_raw["op_id"],
                op_name=op_raw.get("op_name", ""),
                sequence=op_raw["sequence"],
                predecessors=op_raw.get("predecessors", []),
                required_machines=required_machines,
                setup_id=op_raw.get("setup_id", "DEFAULT"),
                nc_code=nc_code,
                cycle_time_sec=op_raw.get("cycle_time_sec"),
            ))

        work_orders.append(WorkOrder(
            wo_id=wo_raw["wo_id"],
            product_id=wo_raw.get("product_id", "PROD"),
            product_name=wo_raw.get("product_name", ""),
            order_quantity=wo_raw["order_quantity"],
            release_date=datetime.fromisoformat(wo_raw["release_date"]),
            due_date=datetime.fromisoformat(wo_raw["due_date"]),
            priority=wo_raw.get("priority", 1),
            customer=wo_raw.get("customer", ""),
            operations=operations,
        ))

    return work_orders


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def cfg_json():
    assert CFG_FILE.exists(), f"scheduler_config.json 없음: {CFG_FILE}"
    with open(CFG_FILE, encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def horizon_start(cfg_json):
    return datetime.fromisoformat(cfg_json["horizon"]["start"])

@pytest.fixture(scope="module")
def horizon_end(cfg_json):
    return datetime.fromisoformat(cfg_json["horizon"]["end"])

@pytest.fixture(scope="module")
def scheduler_config(cfg_json):
    return SchedulerConfig(
        lot_size=cfg_json.get("lot_size", 1),
        amr_transfer_time_sec=cfg_json.get("amr_transfer_time_sec", 60),
    )

@pytest.fixture(scope="module")
def aas_loader():
    assert AAS_FILE.exists(), f"aas_revised.json 없음: {AAS_FILE}"
    return AASLoader(str(AAS_FILE))

@pytest.fixture(scope="module")
def machines(aas_loader, horizon_start):
    return aas_loader.load_machines(horizon_start)

@pytest.fixture(scope="module")
def machine_type_params(aas_loader):
    return aas_loader.load_machine_type_params()

@pytest.fixture(scope="module")
def amrs(aas_loader):
    return aas_loader.load_amrs()

@pytest.fixture(scope="module")
def name_map(machines, amrs):
    """idShort → AAS URI 통합 맵 (머신 + AMR)."""
    m = {machine.machine_name: machine.machine_id for machine in machines}
    # AMR: AAS URI의 마지막 id 부분이 아닌 AAS idShort를 키로 사용
    # aas.json에서 DOOSAN_MOMA의 AAS id를 amr.amr_id로 사용
    # AASLoader.load_amrs는 aas["id"]를 amr_id로, aas["idShort"]를 얻으려면 별도 접근 필요
    # → AASLoader 내부 data에서 직접 추출
    for aas in AASLoader(str(AAS_FILE)).data.get("assetAdministrationShells", []):
        amr_id = aas["id"]
        idshort = aas["idShort"]
        if any(a.amr_id == amr_id for a in amrs):
            m[idshort] = amr_id
    return m

@pytest.fixture(scope="module")
def work_orders(name_map):
    assert WO_FILE.exists(), f"new_work_orders_v3.json 없음: {WO_FILE}"
    with open(WO_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    return parse_work_orders(raw, name_map)

@pytest.fixture(scope="module")
def ortools_result(work_orders, machines, machine_type_params, amrs,
                   scheduler_config, cfg_json, horizon_start, horizon_end):
    time_limit = cfg_json.get("solver", {}).get("time_limit_sec", 60)
    solver = SolverFactory.create_solver(
        solver_type=SolverType.OR_TOOLS,
        work_orders=work_orders,
        machines=machines,
        machine_type_params=machine_type_params,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        config=SolverConfig(time_limit_sec=time_limit),
        amrs=amrs,
        scheduler_config=scheduler_config,
    )
    return solver.solve(time_limit_sec=time_limit)


# ── 1. 입력 파일 파싱 검증 ─────────────────────────────────────────────────────

class TestInputParsing:
    def test_aas_file_exists(self):
        assert AAS_FILE.exists()

    def test_wo_file_exists(self):
        assert WO_FILE.exists()

    def test_config_file_exists(self):
        assert CFG_FILE.exists()

    def test_machines_loaded(self, machines):
        assert len(machines) == 3
        names = {m.machine_name for m in machines}
        assert names == {"DH400", "NX5500", "Rack01"}

    def test_amr_loaded(self, amrs):
        assert len(amrs) == 1
        assert amrs[0].model == "MiR250"

    def test_work_orders_loaded(self, work_orders):
        assert len(work_orders) == 2
        wo_ids = {wo.wo_id for wo in work_orders}
        assert wo_ids == {"WO-A01", "WO-B01"}

    def test_work_order_quantities(self, work_orders):
        qty_map = {wo.wo_id: wo.order_quantity for wo in work_orders}
        assert qty_map["WO-A01"] == 10
        assert qty_map["WO-B01"] == 8

    def test_operations_count(self, work_orders):
        ops_map = {wo.wo_id: len(wo.operations) for wo in work_orders}
        assert ops_map["WO-A01"] == 3   # 소재투입 → 선반가공 → 제품반출
        assert ops_map["WO-B01"] == 3   # 소재투입 → 밀링가공 → 제품반출

    def test_name_map_built(self, name_map):
        assert "DH400"       in name_map
        assert "NX5500"      in name_map
        assert "Rack01"      in name_map
        assert "DOOSAN_MOMA" in name_map
        # 값이 AAS URI 형식인지 확인
        for v in name_map.values():
            assert v.startswith("https://example.com/ids/aas/")

    def test_required_machines_are_type_strings(self, work_orders):
        """required_machines가 머신 타입 문자열인지 확인 (AAS URI나 idShort가 아님)."""
        known_types = {"VMC_3AXIS_MASS", "VMC_3AXIS_PALLET", "AMR", "RACK"}
        for wo in work_orders:
            for op in wo.operations:
                for entry in op.required_machines:
                    assert entry in known_types, (
                        f"{wo.wo_id}/{op.op_id} required_machines에 알 수 없는 값: '{entry}'"
                    )

    def test_compatible_machines_resolved(self, work_orders, name_map):
        """nc_code.compatible_machines도 AAS URI로 변환됐는지 확인."""
        aas_uris = set(name_map.values())
        for wo in work_orders:
            for op in wo.operations:
                for entry in op.nc_code.compatible_machines:
                    assert entry in aas_uris, (
                        f"{wo.wo_id}/{op.op_id} compatible_machines 미변환: '{entry}'"
                    )

    def test_solver_config_parsed(self, cfg_json):
        assert "solver" in cfg_json
        assert cfg_json["solver"]["time_limit_sec"] == 60


# ── 2. 스케줄링 결과 검증 ────────────────────────────────────────────────────

class TestSchedulingResult:
    def test_solve_succeeds(self, ortools_result):
        assert ortools_result.status in ("success", "feasible"), (
            f"스케줄링 실패: status={ortools_result.status}"
        )

    def test_all_operations_scheduled(self, ortools_result, work_orders):
        """모든 작업지시의 모든 공정이 스케줄됐는지 확인."""
        scheduled = {(t.wo_id, t.op_id) for t in ortools_result.scheduled_tasks}
        for wo in work_orders:
            for op in wo.operations:
                assert (wo.wo_id, op.op_id) in scheduled, (
                    f"{wo.wo_id}/{op.op_id} 미스케줄"
                )

    def test_no_machine_overlap(self, ortools_result):
        """동일 머신에 겹치는 태스크가 없어야 함."""
        from collections import defaultdict
        machine_tasks = defaultdict(list)
        for t in ortools_result.scheduled_tasks:
            machine_tasks[t.machine_id].append(t)

        for machine_id, tasks in machine_tasks.items():
            sorted_tasks = sorted(tasks, key=lambda t: t.start_time)
            for i in range(len(sorted_tasks) - 1):
                cur, nxt = sorted_tasks[i], sorted_tasks[i + 1]
                assert cur.end_time <= nxt.start_time, (
                    f"머신 {machine_id} 겹침: "
                    f"[{cur.start_time}-{cur.end_time}] vs [{nxt.start_time}-{nxt.start_time}]"
                )

    def test_precedence_respected(self, ortools_result, work_orders):
        """선행 공정이 완료된 후 후속 공정이 시작되는지 확인."""
        task_end = {
            (t.wo_id, t.op_id): t.end_time
            for t in ortools_result.scheduled_tasks
        }
        task_start = {
            (t.wo_id, t.op_id): t.start_time
            for t in ortools_result.scheduled_tasks
        }

        for wo in work_orders:
            for op in wo.operations:
                for pred_id in op.predecessors:
                    pred_key = (wo.wo_id, pred_id)
                    op_key   = (wo.wo_id, op.op_id)
                    if pred_key in task_end and op_key in task_start:
                        assert task_end[pred_key] <= task_start[op_key], (
                            f"선행 제약 위반: {pred_key} 종료={task_end[pred_key]}, "
                            f"{op_key} 시작={task_start[op_key]}"
                        )

    def test_task_durations_positive(self, ortools_result):
        for t in ortools_result.scheduled_tasks:
            assert t.end_time > t.start_time, f"태스크 {t.wo_id}/{t.op_id} 기간 비정상"

    def test_machine_ids_are_aas_uris(self, ortools_result):
        """스케줄 결과의 machine_id가 AAS URI 형식."""
        for t in ortools_result.scheduled_tasks:
            assert t.machine_id.startswith("https://example.com/ids/aas/"), (
                f"기대치 않은 machine_id: {t.machine_id}"
            )

    def test_utilization_in_range(self, ortools_result):
        for machine_id, util in ortools_result.machine_utilization.items():
            assert 0 <= util <= 100, f"{machine_id} 가동률 범위 초과: {util}"

    def test_makespan_positive(self, ortools_result):
        assert ortools_result.total_makespan > 0

    def test_no_machine_type_mismatch(self, work_orders, machines, machine_type_params,
                                       amrs, scheduler_config, horizon_start, horizon_end):
        """required_machines 타입이 AAS 머신 목록과 일치해야 함."""
        solver = SolverFactory.create_solver(
            solver_type=SolverType.OR_TOOLS,
            work_orders=work_orders,
            machines=machines,
            machine_type_params=machine_type_params,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            config=SolverConfig(time_limit_sec=30),
            amrs=amrs,
            scheduler_config=scheduler_config,
        )
        solver.solve(time_limit_sec=30)
        assert solver.machine_type_mismatches == [], (
            f"머신 타입 불일치: {solver.machine_type_mismatches}"
        )


# ── 3. 결과 출력 확인 ─────────────────────────────────────────────────────────

class TestResultOutput:
    def test_gantt_data_structure(self, ortools_result, machines, horizon_start, horizon_end):
        """Gantt 데이터 구조 확인."""
        # BaseSolver.generate_gantt_data() 직접 호출
        solver = SolverFactory.create_solver(
            solver_type=SolverType.OR_TOOLS,
            work_orders=[],
            machines=machines,
            machine_type_params={},
            horizon_start=horizon_start,
            horizon_end=horizon_end,
        )
        solver.scheduled_tasks = ortools_result.scheduled_tasks
        solver.work_orders = []  # lateness 계산 스킵 허용
        gantt = solver.generate_gantt_data()

        assert "tasks" in gantt
        assert "resources" in gantt
        assert "start" in gantt
        assert "end" in gantt
        assert len(gantt["tasks"]) == len(ortools_result.scheduled_tasks)

    def test_scheduled_tasks_serializable(self, ortools_result):
        """to_dict() 결과가 JSON 직렬화 가능한지 확인."""
        for t in ortools_result.scheduled_tasks:
            d = t.to_dict()
            assert "wo_id" in d
            assert "op_id" in d
            assert "machine_id" in d
            assert "start_time" in d
            assert "end_time" in d
            assert "quantity" in d
            # JSON 직렬화
            json.dumps(d)

    def test_print_schedule_summary(self, ortools_result, machines):
        """스케줄 요약 출력 (콘솔 확인용, 실패하지 않음)."""
        tasks = ortools_result.scheduled_tasks
        id_to_name = {m.machine_id: m.machine_name for m in machines}

        print(f"\n{'='*60}")
        print(f"스케줄링 결과  status={ortools_result.status}")
        print(f"  총 태스크: {len(tasks)}")
        print(f"  makespan: {ortools_result.total_makespan}초 "
              f"({ortools_result.total_makespan/3600:.2f}시간)")
        print(f"  풀이 시간: {ortools_result.solve_time_sec:.3f}초")
        print(f"\n  [태스크 목록]")
        for t in sorted(tasks, key=lambda x: x.start_time):
            mname = id_to_name.get(t.machine_id, t.machine_id)
            print(f"    {t.wo_id}/{t.op_id:8s}  머신={mname:10s}  "
                  f"시작={t.start_time:6d}s  종료={t.end_time:6d}s  "
                  f"({(t.end_time-t.start_time)/60:.1f}분)")
        print(f"\n  [머신별 가동률]")
        for mid, util in ortools_result.machine_utilization.items():
            mname = id_to_name.get(mid, mid)
            print(f"    {mname}: {util:.1f}%")
        print(f"{'='*60}")
