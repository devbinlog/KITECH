"""Tests for scheduling data models and base solver utilities.

WorkOrder contains operations directly (no Job layer).
"""

import pytest
from datetime import datetime, timedelta, timezone

from src.solvers import (
    SolverType,
    SolverConfig,
    NcCode,
    Operation,
    WorkOrder,
    Machine,
    MachineTypeParams,
    ScheduledTask,
    ScheduleResult,
)


class TestSolverType:
    """Tests for SolverType enum."""

    def test_ortools_value(self):
        """Should have correct value."""
        assert SolverType.OR_TOOLS.value == "OR_TOOLS"

    def test_ga_value(self):
        """Should have correct value."""
        assert SolverType.GENETIC_ALGORITHM.value == "GA"

    def test_sa_value(self):
        """Should have correct value."""
        assert SolverType.SIMULATED_ANNEALING.value == "SA"

    def test_tabu_value(self):
        """Should have correct value."""
        assert SolverType.TABU_SEARCH.value == "TABU"

    def test_alns_value(self):
        """Should have correct value."""
        assert SolverType.ALNS.value == "ALNS"


class TestSolverConfig:
    """Tests for SolverConfig dataclass."""

    def test_defaults(self):
        """Should have sensible defaults."""
        config = SolverConfig()
        assert config.time_limit_sec == 60
        assert config.num_workers == 8

    def test_ortools_params(self):
        """Should accept OR-Tools params."""
        config = SolverConfig(time_limit_sec=120, num_workers=4)
        assert config.time_limit_sec == 120
        assert config.num_workers == 4

    def test_ga_params(self):
        """Should accept GA params."""
        config = SolverConfig(
            population_size=200,
            generations=1000,
            crossover_rate=0.9,
            mutation_rate=0.1,
        )
        assert config.population_size == 200
        assert config.generations == 1000

    def test_sa_params(self):
        """Should accept SA params."""
        config = SolverConfig(
            initial_temp=200.0,
            cooling_rate=0.99,
            final_temp=0.1,
        )
        assert config.initial_temp == 200.0
        assert config.cooling_rate == 0.99

    def test_tabu_params(self):
        """Should accept Tabu params."""
        config = SolverConfig(
            tabu_tenure=20,
            tabu_list_size=100,
            tabu_iterations=10000,
        )
        assert config.tabu_tenure == 20
        assert config.tabu_iterations == 10000

    def test_alns_params(self):
        """Should accept ALNS params."""
        config = SolverConfig(
            alns_destroy_rate=0.4,
            alns_iterations=20000,
            alns_segment_size=100,
        )
        assert config.alns_destroy_rate == 0.4
        assert config.alns_iterations == 20000


class TestNcCode:
    """Tests for NcCode dataclass."""

    def test_required_fields(self):
        """Should require program_id, file_path, cycle_time_sec."""
        nc = NcCode(
            program_id="NC-001",
            file_path="/path/to/program.nc",
            cycle_time_sec=120,
        )
        assert nc.program_id == "NC-001"
        assert nc.cycle_time_sec == 120

    def test_defaults(self):
        """Should have sensible defaults."""
        nc = NcCode(
            program_id="NC-001",
            file_path="/path.nc",
            cycle_time_sec=60,
        )
        assert nc.cycle_time_confidence == 1.0
        assert nc.tool_list == []
        assert nc.tool_change_count == 0
        assert nc.compatible_machines == []

    def test_all_fields(self):
        """Should accept all fields."""
        nc = NcCode(
            program_id="NC-001",
            file_path="/path.nc",
            cycle_time_sec=120,
            cycle_time_confidence=0.95,
            tool_list=["T01", "T02", "T03"],
            tool_change_count=3,
            compatible_machines=["CNC-001", "CNC-002"],
        )
        assert len(nc.tool_list) == 3
        assert nc.tool_change_count == 3


class TestOperation:
    """Tests for Operation dataclass."""

    @pytest.fixture
    def sample_nc_code(self):
        return NcCode(
            program_id="NC-001",
            file_path="/nc/test.nc",
            cycle_time_sec=300,
        )

    def test_create_operation(self, sample_nc_code):
        """Should create operation."""
        op = Operation(
            op_id="OP-001",
            op_name="Machining",
            sequence=10,
            predecessors=[],
            required_machines=["CNC"],
            setup_id="SETUP-A",
            nc_code=sample_nc_code,
        )
        assert op.op_id == "OP-001"
        assert op.required_machine_type == "CNC"

    def test_with_predecessors(self, sample_nc_code):
        """Should accept predecessors."""
        op = Operation(
            op_id="OP-002",
            op_name="Finishing",
            sequence=20,
            predecessors=["OP-001"],
            required_machines=["LATHE"],
            setup_id="SETUP-B",
            nc_code=sample_nc_code,
        )
        assert op.predecessors == ["OP-001"]


class TestWorkOrder:
    """Tests for WorkOrder dataclass (operations directly)."""

    @pytest.fixture
    def sample_operation(self):
        nc = NcCode(program_id="NC-001", file_path="/nc/test.nc", cycle_time_sec=300)
        return Operation(
            op_id="OP-001",
            op_name="Machining",
            sequence=10,
            predecessors=[],
            required_machines=["CNC"],
            setup_id="SETUP-A",
            nc_code=nc,
        )

    def test_create_work_order(self, sample_operation):
        """Should create work order with operations directly."""
        wo = WorkOrder(
            wo_id="WO-001",
            product_id="PROD-001",
            product_name="Test Product",
            order_quantity=10,
            due_date=datetime.now(timezone.utc) + timedelta(days=1),
            priority=5,
            release_date=datetime.now(timezone.utc),
            customer="Test Customer",
            operations=[sample_operation],
        )

        assert wo.wo_id == "WO-001"
        assert wo.priority == 5
        assert len(wo.operations) == 1

    def test_priority_range(self, sample_operation):
        """Priority can be various values."""
        for priority in [1, 3, 5, 7, 10]:
            wo = WorkOrder(
                wo_id=f"WO-{priority}",
                product_id="PROD-001",
                product_name="Test",
                order_quantity=10,
                due_date=datetime.now(timezone.utc) + timedelta(days=1),
                priority=priority,
                release_date=datetime.now(timezone.utc),
                customer="Test",
                operations=[sample_operation],
            )
            assert wo.priority == priority

    def test_multiple_operations(self, sample_operation):
        """Should accept multiple operations."""
        nc2 = NcCode(program_id="NC-002", file_path="/nc/test2.nc", cycle_time_sec=200)
        op2 = Operation(
            op_id="OP-002",
            op_name="Finishing",
            sequence=20,
            predecessors=["OP-001"],
            required_machines=["LATHE"],
            setup_id="SETUP-B",
            nc_code=nc2,
        )

        wo = WorkOrder(
            wo_id="WO-001",
            product_id="PROD-001",
            product_name="Test Product",
            order_quantity=10,
            due_date=datetime.now(timezone.utc) + timedelta(days=1),
            priority=5,
            release_date=datetime.now(timezone.utc),
            customer="Test Customer",
            operations=[sample_operation, op2],
        )

        assert len(wo.operations) == 2


class TestMachine:
    """Tests for Machine dataclass."""

    def test_create_machine(self):
        """Should create machine."""
        machine = Machine(
            machine_id="CNC-001",
            machine_name="CNC Machine 1",
            machine_type="CNC",
            status="AVAILABLE",
            available_from=datetime.now(timezone.utc),
            current_setup_id=None,
            setup_change_time_min=5,
        )

        assert machine.machine_id == "CNC-001"
        assert machine.machine_type == "CNC"
        assert machine.status == "AVAILABLE"

    def test_with_setup(self):
        """Should accept current setup."""
        machine = Machine(
            machine_id="CNC-001",
            machine_name="CNC Machine 1",
            machine_type="CNC",
            status="RUNNING",
            available_from=datetime.now(timezone.utc),
            current_setup_id="SETUP-A",
            setup_change_time_min=5,
        )

        assert machine.current_setup_id == "SETUP-A"


class TestMachineTypeParams:
    """Tests for MachineTypeParams dataclass."""

    def test_create_params(self):
        """Should create machine type params."""
        params = MachineTypeParams(
            loading_type="AMR",
            amr_transport_qty=2,
            exchange_time_sec=60,
            load_unload_time_sec=30,
        )

        assert params.loading_type == "AMR"
        assert params.amr_transport_qty == 2

    def test_defaults(self):
        """Should have correct defaults."""
        params = MachineTypeParams(
            loading_type="MANUAL",
            amr_transport_qty=1,
        )

        assert params.exchange_time_sec == 0
        assert params.load_unload_time_sec == 0


class TestScheduledTask:
    """Tests for ScheduledTask dataclass (MES v5 - no job_id)."""

    def test_create_task(self):
        """Should create scheduled task without job_id."""
        task = ScheduledTask(
            wo_id="WO-001",
            op_id="OP-001",
            machine_id="CNC-001",
            start_time=0,
            end_time=300,
            quantity=5,
        )

        assert task.wo_id == "WO-001"
        assert task.start_time == 0
        assert task.end_time == 300

    def test_to_dict(self):
        """Should convert to dictionary without job_id."""
        task = ScheduledTask(
            wo_id="WO-001",
            op_id="OP-001",
            machine_id="CNC-001",
            start_time=0,
            end_time=300,
            quantity=5,
            setup_time=30,
        )

        d = task.to_dict()
        assert d["wo_id"] == "WO-001"
        assert d["op_id"] == "OP-001"
        assert d["start_time"] == 0
        assert d["end_time"] == 300
        assert "job_id" not in d  # MES v5: no job_id

    def test_with_setup_time(self):
        """Should accept setup time."""
        task = ScheduledTask(
            wo_id="WO-001",
            op_id="OP-001",
            machine_id="CNC-001",
            start_time=0,
            end_time=300,
            quantity=5,
            setup_time=60,
        )

        assert task.setup_time == 60


class TestScheduleResult:
    """Tests for ScheduleResult dataclass."""

    def test_create_result(self):
        """Should create schedule result."""
        result = ScheduleResult(
            status="success",
            scheduled_tasks=[],
            objective_value=1000.0,
            solve_time_sec=5.5,
            total_makespan=3600,
            machine_utilization={"CNC-001": 85.0},
            bottleneck_machines=["CNC-001"],
        )

        assert result.status == "success"
        assert result.total_makespan == 3600

    def test_with_tasks(self):
        """Should accept scheduled tasks."""
        task = ScheduledTask(
            wo_id="WO-001",
            op_id="OP-001",
            machine_id="CNC-001",
            start_time=0,
            end_time=300,
            quantity=5,
        )

        result = ScheduleResult(
            status="success",
            scheduled_tasks=[task],
            objective_value=300.0,
            solve_time_sec=1.0,
            total_makespan=300,
            machine_utilization={"CNC-001": 100.0},
            bottleneck_machines=["CNC-001"],
        )

        assert len(result.scheduled_tasks) == 1

    def test_error_result(self):
        """Should represent error state."""
        result = ScheduleResult(
            status="error",
            scheduled_tasks=[],
            objective_value=float("inf"),
            solve_time_sec=0.0,
            total_makespan=0,
            machine_utilization={},
            bottleneck_machines=[],
            solver_info={"error": "No feasible solution"},
        )

        assert result.status == "error"
        assert "error" in result.solver_info
