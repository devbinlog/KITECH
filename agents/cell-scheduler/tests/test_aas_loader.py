"""
AAS Loader 테스트

AASLoader가 aas.json의 schedulerInfo 서브모델에서 스케줄러 입력 객체를
올바르게 파싱하는지 검증한다.

실행 방법 (프로젝트 루트 agents-workspace_260409/ 기준):
    uv run pytest agents/cell-scheduler/tests/test_aas_loader.py -v
"""

import sys
import pytest
from pathlib import Path
from datetime import datetime, timezone

# ── 경로 설정 ─────────────────────────────────────────────────────────────────
workspace = Path(__file__).parent.parent.parent.parent   # agents-workspace_260409/
src_path  = workspace / "agents" / "cell-scheduler" / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(workspace / "shared"))

AAS_FILE = workspace / "samples" / "cell-scheduler" / "input" / "aas_revised.json"

# services/__init__.py 가 SchedulerService(상대 임포트 깊이 문제)를 끌어들이므로
# aas_loader 모듈만 importlib 로 독립 로드한다.
import importlib.util as _ilu                            # noqa: E402

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

from solvers import (                                   # noqa: E402
    Machine, AMRConfig, MachineTypeParams, SchedulerConfig,
    Calendar, Break,
    SolverFactory, SolverType, SolverConfig,
    WorkOrder, Operation, NcCode,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def loader():
    assert AAS_FILE.exists(), f"aas.json 없음: {AAS_FILE}"
    return AASLoader(str(AAS_FILE))


@pytest.fixture(scope="module")
def horizon_start():
    return datetime(2025, 1, 17, 8, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def machines(loader, horizon_start):
    return loader.load_machines(horizon_start)


@pytest.fixture(scope="module")
def machine_type_params(loader):
    return loader.load_machine_type_params()


@pytest.fixture(scope="module")
def amrs(loader):
    return loader.load_amrs()


# ── 1. AASLoader 기본 로드 ─────────────────────────────────────────────────────

class TestAASLoaderInit:
    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            AASLoader("/nonexistent/aas.json")

    def test_loads_without_error(self, loader):
        assert loader is not None

    def test_submodel_lookup_built(self, loader):
        # schedulerInfo 포함 전체 서브모델이 id 맵에 있어야 함
        assert len(loader._sm_by_id) >= 8   # 기존 8개 + 새 4개 = 12개


# ── 2. load_machines ──────────────────────────────────────────────────────────

class TestLoadMachines:
    def test_returns_three_machines(self, machines):
        # DH400, NX5500, Rack01 → 3개
        assert len(machines) == 3

    def test_machine_ids_are_aas_uris(self, machines):
        for m in machines:
            assert m.machine_id.startswith("https://example.com/ids/aas/")

    def test_machine_names_match_aas_idshort(self, machines):
        names = {m.machine_name for m in machines}
        assert names == {"DH400", "NX5500", "Rack01"}

    def test_machine_types_assigned(self, machines):
        type_map = {m.machine_name: m.machine_type for m in machines}
        assert type_map["DH400"]   == "VMC_3AXIS_MASS"
        assert type_map["NX5500"]  == "VMC_3AXIS_PALLET"
        assert type_map["Rack01"]  == "RACK"

    def test_status_defaults_to_available(self, machines):
        for m in machines:
            assert m.status == "available"

    def test_available_from_equals_horizon_start(self, machines, horizon_start):
        for m in machines:
            assert m.available_from == horizon_start

    def test_dh400_setup_time(self, machines):
        dh400 = next(m for m in machines if m.machine_name == "DH400")
        assert dh400.setup_change_time_min == 15

    def test_nx5500_setup_time(self, machines):
        nx5500 = next(m for m in machines if m.machine_name == "NX5500")
        assert nx5500.setup_change_time_min == 5

    def test_rack01_setup_time_zero(self, machines):
        rack = next(m for m in machines if m.machine_name == "Rack01")
        assert rack.setup_change_time_min == 0

    def test_dh400_calendar_parsed(self, machines):
        dh400 = next(m for m in machines if m.machine_name == "DH400")
        cal = dh400.calendar
        assert isinstance(cal, Calendar)
        assert cal.shift_start.hour == 8
        assert cal.shift_end.hour == 20
        assert len(cal.breaks) == 1
        assert cal.breaks[0].start.hour == 12
        assert cal.breaks[0].end.hour == 13

    def test_nx5500_calendar_no_breaks(self, machines):
        nx5500 = next(m for m in machines if m.machine_name == "NX5500")
        assert nx5500.calendar is not None
        assert nx5500.calendar.breaks == []

    def test_rack01_calendar_is_24h(self, machines):
        rack = next(m for m in machines if m.machine_name == "Rack01")
        assert rack.calendar is not None
        assert rack.calendar.shift_start.hour == 0
        assert rack.calendar.shift_end.hour == 23

    def test_occupied_slots_empty(self, machines):
        for m in machines:
            assert m.occupied_slots == []


# ── 3. load_machine_type_params ───────────────────────────────────────────────

class TestLoadMachineTypeParams:
    def test_returns_three_types(self, machine_type_params):
        assert len(machine_type_params) == 3

    def test_keys_match_machine_types(self, machine_type_params):
        assert set(machine_type_params.keys()) == {
            "VMC_3AXIS_MASS", "VMC_3AXIS_PALLET", "RACK"
        }

    def test_dh400_params(self, machine_type_params):
        p = machine_type_params["VMC_3AXIS_MASS"]
        assert p.loading_type == "buffer_exchange"
        assert p.amr_transport_qty == 3
        assert p.exchange_time_sec == 45
        assert p.load_unload_time_sec == 0

    def test_nx5500_params(self, machine_type_params):
        p = machine_type_params["VMC_3AXIS_PALLET"]
        assert p.loading_type == "pallet_single"
        assert p.amr_transport_qty == 1
        assert p.load_unload_time_sec == 30

    def test_rack_params(self, machine_type_params):
        p = machine_type_params["RACK"]
        assert p.loading_type == "direct"
        assert p.amr_transport_qty == 1


# ── 4. load_amrs ──────────────────────────────────────────────────────────────

class TestLoadAMRs:
    def test_returns_one_amr(self, amrs):
        assert len(amrs) == 1

    def test_amr_id_is_aas_uri(self, amrs):
        assert amrs[0].amr_id.startswith("https://example.com/ids/aas/")

    def test_amr_model(self, amrs):
        assert amrs[0].model == "MiR250"

    def test_amr_speed(self, amrs):
        assert amrs[0].speed_m_per_sec == 1.0

    def test_amr_accessible_machines_count(self, amrs):
        # DH400, NX5500, Rack01 → 3개
        assert len(amrs[0].accessible_machines) == 3

    def test_amr_accessible_machines_are_aas_uris(self, amrs):
        for mid in amrs[0].accessible_machines:
            assert mid.startswith("https://example.com/ids/aas/")

    def test_amr_status(self, amrs):
        assert amrs[0].status == "available"


# ── 5. 스케줄러 통합 테스트 ──────────────────────────────────────────────────

class TestSchedulerWithAAS:
    """AAS에서 로드한 machines/params로 실제 스케줄링이 동작하는지 검증."""

    @pytest.fixture
    def sample_work_orders(self, machines):
        """AAS의 실제 machine_id를 참조하는 작업지시 2건 생성."""
        dh400_id  = next(m.machine_id for m in machines if m.machine_name == "DH400")
        nx5500_id = next(m.machine_id for m in machines if m.machine_name == "NX5500")

        return [
            WorkOrder(
                wo_id="WO-AAS-001",
                product_id="PROD-001",
                product_name="테스트 부품 A",
                order_quantity=1,
                due_date=datetime(2025, 1, 17, 20, 0, 0, tzinfo=timezone.utc),
                priority=1,
                release_date=datetime(2025, 1, 17, 8, 0, 0, tzinfo=timezone.utc),
                customer="테스트",
                operations=[
                    Operation(
                        op_id="OP10",
                        op_name="황삭 밀링",
                        sequence=1,
                        predecessors=[],
                        required_machines=["VMC_3AXIS_MASS"],
                        setup_id="TS-MASS-001",
                        nc_code=NcCode(
                            program_id="NC-001",
                            file_path="",
                            cycle_time_sec=180,
                            compatible_machines=[dh400_id],
                        ),
                    )
                ],
            ),
            WorkOrder(
                wo_id="WO-AAS-002",
                product_id="PROD-002",
                product_name="테스트 부품 B",
                order_quantity=1,
                due_date=datetime(2025, 1, 17, 20, 0, 0, tzinfo=timezone.utc),
                priority=2,
                release_date=datetime(2025, 1, 17, 8, 0, 0, tzinfo=timezone.utc),
                customer="테스트",
                operations=[
                    Operation(
                        op_id="OP10",
                        op_name="팔레트 가공",
                        sequence=1,
                        predecessors=[],
                        required_machines=["VMC_3AXIS_PALLET"],
                        setup_id="TS-PLT-001",
                        nc_code=NcCode(
                            program_id="NC-002",
                            file_path="",
                            cycle_time_sec=240,
                            compatible_machines=[nx5500_id],
                        ),
                    )
                ],
            ),
        ]

    def test_ortools_solve_succeeds(self, sample_work_orders, machines, machine_type_params,
                                    amrs, horizon_start):
        horizon_end = datetime(2025, 1, 17, 20, 0, 0, tzinfo=timezone.utc)

        solver = SolverFactory.create_solver(
            solver_type=SolverType.OR_TOOLS,
            work_orders=sample_work_orders,
            machines=machines,
            machine_type_params=machine_type_params,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            config=SolverConfig(time_limit_sec=10),
            amrs=amrs,
            scheduler_config=SchedulerConfig(),
        )
        result = solver.solve(time_limit_sec=10)

        assert result.status in ("success", "feasible")
        assert len(result.scheduled_tasks) == 2

    def test_scheduled_tasks_use_aas_machine_ids(self, sample_work_orders, machines,
                                                  machine_type_params, amrs, horizon_start):
        """스케줄 결과의 machine_id가 AAS URI 형식인지 확인."""
        horizon_end = datetime(2025, 1, 17, 20, 0, 0, tzinfo=timezone.utc)
        aas_machine_ids = {m.machine_id for m in machines}

        solver = SolverFactory.create_solver(
            solver_type=SolverType.GENETIC_ALGORITHM,
            work_orders=sample_work_orders,
            machines=machines,
            machine_type_params=machine_type_params,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            config=SolverConfig(time_limit_sec=5),
            amrs=amrs,
            scheduler_config=SchedulerConfig(),
        )
        result = solver.solve(time_limit_sec=5)

        for task in result.scheduled_tasks:
            assert task.machine_id in aas_machine_ids, (
                f"task.machine_id='{task.machine_id}' 가 AAS 머신 목록에 없음"
            )

    def test_machine_type_mismatch_empty(self, sample_work_orders, machines,
                                         machine_type_params, amrs, horizon_start):
        """required_machines의 타입이 AAS machineType과 일치하므로 mismatch가 없어야 함."""
        horizon_end = datetime(2025, 1, 17, 20, 0, 0, tzinfo=timezone.utc)

        solver = SolverFactory.create_solver(
            solver_type=SolverType.OR_TOOLS,
            work_orders=sample_work_orders,
            machines=machines,
            machine_type_params=machine_type_params,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            config=SolverConfig(time_limit_sec=10),
            amrs=amrs,
            scheduler_config=SchedulerConfig(),
        )
        solver.solve(time_limit_sec=10)

        assert solver.machine_type_mismatches == [], (
            f"machine_type mismatch 발생: {solver.machine_type_mismatches}"
        )
