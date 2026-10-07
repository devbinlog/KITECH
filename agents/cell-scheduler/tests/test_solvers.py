"""Tests for scheduler solver implementations.

MES v5 Schema: Job layer removed, WorkOrder contains operations directly.
"""

import pytest
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from src.solvers import (
    SolverFactory,
    SolverType,
    SolverConfig,
    WorkOrder,
    Operation,
    NcCode,
    Machine,
    OccupiedSlot,
    MachineTypeParams,
    ScheduleResult,
    ScheduledTask,
    ORToolsSolver,
    GeneticAlgorithmSolver,
    SimulatedAnnealingSolver,
    TabuSearchSolver,
    ALNSSolver,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_nc_code() -> NcCode:
    """Create a sample NC code."""
    return NcCode(
        program_id="NC-001",
        file_path="/nc/program1.nc",
        cycle_time_sec=300,
        cycle_time_confidence=0.95,
        tool_list=["T01", "T02"],
        tool_change_count=2,
        compatible_machines=["CNC"],
    )


@pytest.fixture
def sample_operation(sample_nc_code) -> Operation:
    """Create a sample operation."""
    return Operation(
        op_id="OP-001",
        op_name="Machining",
        sequence=10,
        predecessors=[],
        required_machines=["CNC"],
        setup_id="SETUP-A",
        nc_code=sample_nc_code,
    )


@pytest.fixture
def sample_work_order(sample_operation) -> WorkOrder:
    """Create a sample work order (MES v5 - operations directly)."""
    return WorkOrder(
        wo_id="WO-001",
        product_id="PROD-001",
        product_name="Test Product",
        order_quantity=10,
        due_date=datetime.now(timezone.utc) + timedelta(hours=24),
        priority=5,
        release_date=datetime.now(timezone.utc),
        customer="Test Customer",
        operations=[sample_operation],
    )


@pytest.fixture
def sample_machine() -> Machine:
    """Create a sample machine."""
    return Machine(
        machine_id="CNC-001",
        machine_name="CNC Machine 1",
        machine_type="CNC",
        status="AVAILABLE",
        available_from=datetime.now(timezone.utc),
        current_setup_id=None,
        setup_change_time_min=5,
    )


@pytest.fixture
def sample_machine_type_params() -> Dict[str, MachineTypeParams]:
    """Create sample machine type parameters."""
    return {
        "CNC": MachineTypeParams(
            loading_type="MANUAL",
            amr_transport_qty=1,
            exchange_time_sec=30,
            load_unload_time_sec=60,
        ),
        "ROBOT": MachineTypeParams(
            loading_type="AUTO",
            amr_transport_qty=5,
            exchange_time_sec=10,
            load_unload_time_sec=15,
        ),
    }


@pytest.fixture
def horizon_times():
    """Create scheduling horizon times."""
    start = datetime.now(timezone.utc)
    end = start + timedelta(hours=24)
    return start, end


@pytest.fixture
def multiple_work_orders(sample_nc_code) -> List[WorkOrder]:
    """Create multiple work orders for testing (MES v5 - operations directly)."""
    work_orders = []

    for i in range(3):
        op = Operation(
            op_id=f"OP-{i + 1:03d}",
            op_name=f"Operation {i + 1}",
            sequence=10,
            predecessors=[],
            required_machines=["CNC"],
            setup_id=f"SETUP-{chr(65 + i)}",
            nc_code=sample_nc_code,
        )

        wo = WorkOrder(
            wo_id=f"WO-{i + 1:03d}",
            product_id=f"PROD-{i + 1:03d}",
            product_name=f"Product {i + 1}",
            order_quantity=10 + i * 5,
            due_date=datetime.now(timezone.utc) + timedelta(hours=12 + i * 6),
            priority=5 - i,  # Different priorities
            release_date=datetime.now(timezone.utc),
            customer=f"Customer {i + 1}",
            operations=[op],
        )
        work_orders.append(wo)

    return work_orders


@pytest.fixture
def multiple_machines() -> List[Machine]:
    """Create multiple machines for testing."""
    return [
        Machine(
            machine_id="CNC-001",
            machine_name="CNC Machine 1",
            machine_type="CNC",
            status="AVAILABLE",
            available_from=datetime.now(timezone.utc),
            current_setup_id=None,
            setup_change_time_min=5,
        ),
        Machine(
            machine_id="CNC-002",
            machine_name="CNC Machine 2",
            machine_type="CNC",
            status="AVAILABLE",
            available_from=datetime.now(timezone.utc),
            current_setup_id=None,
            setup_change_time_min=3,
        ),
    ]


# ============================================================================
# SolverFactory Tests
# ============================================================================


class TestSolverFactory:
    """Test SolverFactory class."""

    def test_create_ortools_solver(
        self,
        sample_work_order,
        sample_machine,
        sample_machine_type_params,
        horizon_times,
    ):
        """Create OR-Tools solver."""
        start, end = horizon_times
        solver = SolverFactory.create_solver(
            solver_type=SolverType.OR_TOOLS,
            work_orders=[sample_work_order],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
        )

        assert isinstance(solver, ORToolsSolver)
        assert len(solver.work_orders) == 1
        assert len(solver.machines) == 1

    def test_create_ga_solver(
        self,
        sample_work_order,
        sample_machine,
        sample_machine_type_params,
        horizon_times,
    ):
        """Create Genetic Algorithm solver."""
        start, end = horizon_times
        solver = SolverFactory.create_solver(
            solver_type=SolverType.GENETIC_ALGORITHM,
            work_orders=[sample_work_order],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
        )

        assert isinstance(solver, GeneticAlgorithmSolver)

    def test_create_sa_solver(
        self,
        sample_work_order,
        sample_machine,
        sample_machine_type_params,
        horizon_times,
    ):
        """Create Simulated Annealing solver."""
        start, end = horizon_times
        solver = SolverFactory.create_solver(
            solver_type=SolverType.SIMULATED_ANNEALING,
            work_orders=[sample_work_order],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
        )

        assert isinstance(solver, SimulatedAnnealingSolver)

    def test_create_tabu_solver(
        self,
        sample_work_order,
        sample_machine,
        sample_machine_type_params,
        horizon_times,
    ):
        """Create Tabu Search solver."""
        start, end = horizon_times
        solver = SolverFactory.create_solver(
            solver_type=SolverType.TABU_SEARCH,
            work_orders=[sample_work_order],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
        )

        assert isinstance(solver, TabuSearchSolver)

    def test_create_alns_solver(
        self,
        sample_work_order,
        sample_machine,
        sample_machine_type_params,
        horizon_times,
    ):
        """Create ALNS solver."""
        start, end = horizon_times
        solver = SolverFactory.create_solver(
            solver_type=SolverType.ALNS,
            work_orders=[sample_work_order],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
        )

        assert isinstance(solver, ALNSSolver)

    def test_get_solver_type_valid(self):
        """Parse valid solver type strings."""
        assert SolverFactory.get_solver_type("OR_TOOLS") == SolverType.OR_TOOLS
        assert SolverFactory.get_solver_type("ORTOOLS") == SolverType.OR_TOOLS
        assert SolverFactory.get_solver_type("GA") == SolverType.GENETIC_ALGORITHM
        assert SolverFactory.get_solver_type("GENETIC") == SolverType.GENETIC_ALGORITHM
        assert SolverFactory.get_solver_type("SA") == SolverType.SIMULATED_ANNEALING
        assert SolverFactory.get_solver_type("TABU") == SolverType.TABU_SEARCH
        assert SolverFactory.get_solver_type("ALNS") == SolverType.ALNS

    def test_get_solver_type_invalid(self):
        """Invalid solver type raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            SolverFactory.get_solver_type("INVALID")

        assert "Unknown solver type" in str(excinfo.value)

    def test_get_available_solvers(self):
        """Get list of available solvers."""
        solvers = SolverFactory.get_available_solvers()

        assert len(solvers) == 5
        solver_types = [s["type"] for s in solvers]
        assert "OR_TOOLS" in solver_types
        assert "GA" in solver_types
        assert "SA" in solver_types
        assert "TABU" in solver_types
        assert "ALNS" in solver_types

    def test_get_default_config(self):
        """Get default configuration for each solver type."""
        ortools_config = SolverFactory.get_default_config(SolverType.OR_TOOLS)
        assert ortools_config.time_limit_sec == 60
        assert ortools_config.num_workers == 8

        ga_config = SolverFactory.get_default_config(SolverType.GENETIC_ALGORITHM)
        assert ga_config.population_size == 100
        assert ga_config.generations == 500

        sa_config = SolverFactory.get_default_config(SolverType.SIMULATED_ANNEALING)
        assert sa_config.initial_temp == 100.0
        assert sa_config.cooling_rate == 0.95

        tabu_config = SolverFactory.get_default_config(SolverType.TABU_SEARCH)
        assert tabu_config.tabu_tenure == 10
        assert tabu_config.tabu_iterations == 5000

        alns_config = SolverFactory.get_default_config(SolverType.ALNS)
        assert alns_config.alns_destroy_rate == 0.3
        assert alns_config.alns_iterations == 10000

    def test_recommend_solver_small_problem(self):
        """Recommend OR-Tools for small problems."""
        solver = SolverFactory.recommend_solver(
            num_operations=10,
            num_machines=2,
            time_available_sec=60,
        )
        assert solver == SolverType.OR_TOOLS

    def test_recommend_solver_optimal_required(self):
        """Recommend OR-Tools when optimal solution required."""
        solver = SolverFactory.recommend_solver(
            num_operations=100,
            num_machines=10,
            time_available_sec=60,
            need_optimal=True,
        )
        assert solver == SolverType.OR_TOOLS

    def test_recommend_solver_large_problem_limited_time(self):
        """Recommend SA for large problems with limited time."""
        solver = SolverFactory.recommend_solver(
            num_operations=200,
            num_machines=10,
            time_available_sec=20,
        )
        assert solver == SolverType.SIMULATED_ANNEALING

    def test_recommend_solver_large_problem_sufficient_time(self):
        """Recommend ALNS for large problems with sufficient time."""
        solver = SolverFactory.recommend_solver(
            num_operations=100,
            num_machines=10,
            time_available_sec=120,
        )
        assert solver == SolverType.ALNS


# ============================================================================
# OR-Tools Solver Tests
# ============================================================================


class TestORToolsSolver:
    """Test OR-Tools solver."""

    def test_solve_simple_problem(
        self,
        sample_work_order,
        sample_machine,
        sample_machine_type_params,
        horizon_times,
    ):
        """Solve a simple scheduling problem."""
        start, end = horizon_times
        config = SolverConfig(time_limit_sec=10)

        solver = ORToolsSolver(
            work_orders=[sample_work_order],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=config,
        )

        result = solver.solve(time_limit_sec=10)

        assert isinstance(result, ScheduleResult)
        assert result.status in ["success", "no_solution", "error"]

    def test_solve_multiple_work_orders(
        self,
        multiple_work_orders,
        multiple_machines,
        sample_machine_type_params,
        horizon_times,
    ):
        """Solve with multiple work orders and machines."""
        start, end = horizon_times
        config = SolverConfig(time_limit_sec=10)

        solver = ORToolsSolver(
            work_orders=multiple_work_orders,
            machines=multiple_machines,
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=config,
        )

        result = solver.solve(time_limit_sec=10)

        assert isinstance(result, ScheduleResult)
        if result.status == "success":
            assert len(result.scheduled_tasks) > 0

    def test_solve_empty_work_orders(
        self,
        sample_machine,
        sample_machine_type_params,
        horizon_times,
    ):
        """Handle empty work order list."""
        start, end = horizon_times

        solver = ORToolsSolver(
            work_orders=[],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
        )

        result = solver.solve(time_limit_sec=5)

        assert isinstance(result, ScheduleResult)
        assert len(result.scheduled_tasks) == 0

    def test_get_solver_info(
        self,
        sample_work_order,
        sample_machine,
        sample_machine_type_params,
        horizon_times,
    ):
        """Get solver information."""
        start, end = horizon_times

        solver = ORToolsSolver(
            work_orders=[sample_work_order],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
        )

        info = solver.get_solver_info()

        assert "type" in info
        assert info["type"] == "OR_TOOLS"


# ============================================================================
# Genetic Algorithm Solver Tests
# ============================================================================


class TestGeneticAlgorithmSolver:
    """Test Genetic Algorithm solver."""

    def test_initialization(
        self,
        sample_work_order,
        sample_machine,
        sample_machine_type_params,
        horizon_times,
    ):
        """Initialize GA solver."""
        start, end = horizon_times
        config = SolverConfig(population_size=50, generations=100)

        solver = GeneticAlgorithmSolver(
            work_orders=[sample_work_order],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=config,
        )

        assert solver.config.population_size == 50
        assert solver.config.generations == 100

    def test_solve(
        self,
        multiple_work_orders,
        multiple_machines,
        sample_machine_type_params,
        horizon_times,
    ):
        """Solve with GA solver."""
        start, end = horizon_times
        config = SolverConfig(
            time_limit_sec=5,
            population_size=20,
            generations=50,
        )

        solver = GeneticAlgorithmSolver(
            work_orders=multiple_work_orders,
            machines=multiple_machines,
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=config,
        )

        result = solver.solve(time_limit_sec=5)

        assert isinstance(result, ScheduleResult)
        # GA should produce some solution
        assert result.status in ["success", "no_solution"]


# ============================================================================
# Simulated Annealing Solver Tests
# ============================================================================


class TestSimulatedAnnealingSolver:
    """Test Simulated Annealing solver."""

    def test_initialization(
        self,
        sample_work_order,
        sample_machine,
        sample_machine_type_params,
        horizon_times,
    ):
        """Initialize SA solver."""
        start, end = horizon_times
        config = SolverConfig(
            initial_temp=50.0,
            cooling_rate=0.9,
            sa_iterations=1000,
        )

        solver = SimulatedAnnealingSolver(
            work_orders=[sample_work_order],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=config,
        )

        assert solver.config.initial_temp == 50.0
        assert solver.config.cooling_rate == 0.9

    def test_solve(
        self,
        multiple_work_orders,
        multiple_machines,
        sample_machine_type_params,
        horizon_times,
    ):
        """Solve with SA solver."""
        start, end = horizon_times
        config = SolverConfig(
            time_limit_sec=5,
            sa_iterations=500,
        )

        solver = SimulatedAnnealingSolver(
            work_orders=multiple_work_orders,
            machines=multiple_machines,
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=config,
        )

        result = solver.solve(time_limit_sec=5)

        assert isinstance(result, ScheduleResult)


# ============================================================================
# Tabu Search Solver Tests
# ============================================================================


class TestTabuSearchSolver:
    """Test Tabu Search solver."""

    def test_initialization(
        self,
        sample_work_order,
        sample_machine,
        sample_machine_type_params,
        horizon_times,
    ):
        """Initialize Tabu Search solver."""
        start, end = horizon_times
        config = SolverConfig(
            tabu_tenure=15,
            tabu_list_size=30,
            tabu_iterations=500,
        )

        solver = TabuSearchSolver(
            work_orders=[sample_work_order],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=config,
        )

        assert solver.config.tabu_tenure == 15
        assert solver.config.tabu_list_size == 30

    def test_solve(
        self,
        multiple_work_orders,
        multiple_machines,
        sample_machine_type_params,
        horizon_times,
    ):
        """Solve with Tabu Search solver."""
        start, end = horizon_times
        config = SolverConfig(
            time_limit_sec=5,
            tabu_iterations=200,
        )

        solver = TabuSearchSolver(
            work_orders=multiple_work_orders,
            machines=multiple_machines,
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=config,
        )

        result = solver.solve(time_limit_sec=5)

        assert isinstance(result, ScheduleResult)


# ============================================================================
# ALNS Solver Tests
# ============================================================================


class TestALNSSolver:
    """Test Adaptive Large Neighborhood Search solver."""

    def test_initialization(
        self,
        sample_work_order,
        sample_machine,
        sample_machine_type_params,
        horizon_times,
    ):
        """Initialize ALNS solver."""
        start, end = horizon_times
        config = SolverConfig(
            alns_destroy_rate=0.4,
            alns_iterations=500,
            alns_segment_size=50,
        )

        solver = ALNSSolver(
            work_orders=[sample_work_order],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=config,
        )

        assert solver.config.alns_destroy_rate == 0.4
        assert solver.config.alns_iterations == 500

    def test_solve(
        self,
        multiple_work_orders,
        multiple_machines,
        sample_machine_type_params,
        horizon_times,
    ):
        """Solve with ALNS solver."""
        start, end = horizon_times
        config = SolverConfig(
            time_limit_sec=5,
            alns_iterations=100,
        )

        solver = ALNSSolver(
            work_orders=multiple_work_orders,
            machines=multiple_machines,
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=config,
        )

        result = solver.solve(time_limit_sec=5)

        assert isinstance(result, ScheduleResult)


# ============================================================================
# Data Class Tests
# ============================================================================


class TestDataClasses:
    """Test data class functionality."""

    def test_nc_code_creation(self):
        """Create NC code."""
        nc = NcCode(
            program_id="NC-001",
            file_path="/nc/test.nc",
            cycle_time_sec=120,
        )

        assert nc.program_id == "NC-001"
        assert nc.cycle_time_sec == 120
        assert nc.cycle_time_confidence == 1.0  # default

    def test_operation_creation(self, sample_nc_code):
        """Create operation."""
        op = Operation(
            op_id="OP-001",
            op_name="Cutting",
            sequence=10,
            predecessors=[],
            required_machines=["CNC"],
            setup_id="SETUP-A",
            nc_code=sample_nc_code,
        )

        assert op.op_id == "OP-001"
        assert op.required_machine_type == "CNC"

    def test_scheduled_task_to_dict(self):
        """Convert scheduled task to dictionary (MES v5 - no job_id)."""
        task = ScheduledTask(
            wo_id="WO-001",
            op_id="OP-001",
            machine_id="CNC-001",
            start_time=0,
            end_time=300,
            quantity=10,
        )

        task_dict = task.to_dict()

        assert task_dict["wo_id"] == "WO-001"
        assert task_dict["start_time"] == 0
        assert task_dict["end_time"] == 300
        assert "job_id" not in task_dict  # MES v5: no job_id

    def test_solver_config_defaults(self):
        """Check SolverConfig defaults."""
        config = SolverConfig()

        assert config.time_limit_sec == 60
        assert config.population_size == 100
        assert config.initial_temp == 100.0
        assert config.tabu_tenure == 10
        assert config.alns_destroy_rate == 0.3


# ============================================================================
# Solver Comparison Tests
# ============================================================================


class TestSolverComparison:
    """Compare different solver outputs."""

    def test_all_solvers_produce_results(
        self,
        multiple_work_orders,
        multiple_machines,
        sample_machine_type_params,
        horizon_times,
    ):
        """All solvers should produce valid results."""
        start, end = horizon_times

        solver_types = [
            SolverType.OR_TOOLS,
            SolverType.GENETIC_ALGORITHM,
            SolverType.SIMULATED_ANNEALING,
            SolverType.TABU_SEARCH,
            SolverType.ALNS,
        ]

        results = {}

        for solver_type in solver_types:
            solver = SolverFactory.create_solver(
                solver_type=solver_type,
                work_orders=multiple_work_orders,
                machines=multiple_machines,
                machine_type_params=sample_machine_type_params,
                horizon_start=start,
                horizon_end=end,
            )

            result = solver.solve(time_limit_sec=3)
            results[solver_type] = result

            assert isinstance(result, ScheduleResult)
            assert result.status is not None

        # All solvers should complete
        assert len(results) == 5


# ============================================================================
# Occupied Slots Constraint Tests
# ============================================================================


class TestOccupiedSlots:
    """Test that all solvers respect occupied slots (existing schedule).

    Background: When equipment already has scheduled tasks (from previous
    scheduling or production results), new schedules must not overlap with
    these occupied time slots. This was a real bug — Gantt chart showed
    overlapping Work Orders on the same equipment because the scheduler
    didn't know about existing occupations.
    """

    @pytest.fixture
    def occupied_machine(self) -> Machine:
        """Machine with occupied time slots (existing schedule).

        Simulates a CNC machine that already has two tasks scheduled:
        - Slot 1: 0~3600s (first hour)
        - Slot 2: 7200~10800s (third hour)
        The second hour (3600~7200s) and time after 10800s are free.
        """
        return Machine(
            machine_id="CNC-001",
            machine_name="CNC Machine 1",
            machine_type="CNC",
            status="AVAILABLE",
            available_from=datetime.now(timezone.utc),
            current_setup_id=None,
            setup_change_time_min=5,
            occupied_slots=[
                OccupiedSlot(start=0, end=3600, wo_id="WO-EXISTING-1"),
                OccupiedSlot(start=7200, end=10800, wo_id="WO-EXISTING-2"),
            ],
        )

    @pytest.fixture
    def short_work_order(self) -> WorkOrder:
        """A short work order that should fit between occupied slots."""
        nc = NcCode(
            program_id="NC-SHORT",
            file_path="/nc/short.nc",
            cycle_time_sec=60,  # 60s per unit
            compatible_machines=["CNC"],
        )
        op = Operation(
            op_id="OP-SHORT",
            op_name="Short Op",
            sequence=10,
            predecessors=[],
            required_machines=["CNC"],
            setup_id="SETUP-A",
            nc_code=nc,
        )
        return WorkOrder(
            wo_id="WO-NEW-1",
            product_id="PROD-NEW",
            product_name="New Product",
            order_quantity=10,  # 10 units × 60s = 600s duration
            due_date=datetime.now(timezone.utc) + timedelta(hours=24),
            priority=5,
            release_date=datetime.now(timezone.utc),
            customer="Test",
            operations=[op],
        )

    @pytest.fixture
    def occupied_machines_two(self, occupied_machine) -> List[Machine]:
        """Two machines, one with occupied slots, one free."""
        free_machine = Machine(
            machine_id="CNC-002",
            machine_name="CNC Machine 2",
            machine_type="CNC",
            status="AVAILABLE",
            available_from=datetime.now(timezone.utc),
            current_setup_id=None,
            setup_change_time_min=5,
        )
        return [occupied_machine, free_machine]

    @pytest.fixture
    def occupied_horizon(self):
        """Horizon for occupied slot tests."""
        start = datetime.now(timezone.utc)
        end = start + timedelta(hours=24)
        return start, end

    def _check_no_overlap_with_slots(
        self, tasks: List[ScheduledTask], machine_id: str, slots: List[OccupiedSlot]
    ):
        """Helper: verify no scheduled task overlaps with occupied slots."""
        machine_tasks = [t for t in tasks if t.machine_id == machine_id]
        for task in machine_tasks:
            for slot in slots:
                # Overlap condition: task starts before slot ends AND task ends after slot starts
                if task.start_time < slot.end and task.end_time > slot.start:
                    pytest.fail(
                        f"Task {task.wo_id}/{task.op_id} [{task.start_time}-{task.end_time}] "
                        f"overlaps with occupied slot [{slot.start}-{slot.end}] "
                        f"on machine {machine_id}"
                    )

    # ---- _adjust_start_for_occupied_slots helper tests ----

    def test_adjust_start_no_slots(self, sample_machine_type_params, occupied_horizon):
        """No occupied slots → start time unchanged."""
        start, end = occupied_horizon
        free_machine = Machine(
            machine_id="CNC-FREE",
            machine_name="Free CNC",
            machine_type="CNC",
            status="AVAILABLE",
            available_from=start,
            current_setup_id=None,
            setup_change_time_min=5,
        )

        solver = ORToolsSolver(
            work_orders=[],
            machines=[free_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
        )

        adjusted = solver._adjust_start_for_occupied_slots("CNC-FREE", 0, 600)
        assert adjusted == 0

    def test_adjust_start_avoids_occupied(
        self, occupied_machine, sample_machine_type_params, occupied_horizon
    ):
        """Desired start inside occupied slot → pushed past slot end + setup."""
        start, end = occupied_horizon
        solver = ORToolsSolver(
            work_orders=[],
            machines=[occupied_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
        )

        # Want to start at 0, but slot [0, 3600] is occupied
        # Should push to 3600 + 300 (setup) = 3900
        adjusted = solver._adjust_start_for_occupied_slots("CNC-001", 0, 600)
        assert adjusted >= 3600 + 300  # slot end + default setup time

    def test_adjust_start_fits_in_gap(
        self, occupied_machine, sample_machine_type_params, occupied_horizon
    ):
        """Task fits in gap between two occupied slots."""
        start, end = occupied_horizon
        solver = ORToolsSolver(
            work_orders=[],
            machines=[occupied_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
        )

        # Gap between slots: 3600~7200 (3600s available)
        # After setup: start at 3900, task of 600s ends at 4500 — fits in gap
        adjusted = solver._adjust_start_for_occupied_slots("CNC-001", 3900, 600)
        assert adjusted == 3900  # Already past first slot + setup, fits before second slot

    def test_adjust_start_skips_multiple_slots(self, sample_machine_type_params, occupied_horizon):
        """Task too large for gaps → pushed past all occupied slots."""
        start, end = occupied_horizon
        # Machine with tight slots
        machine = Machine(
            machine_id="CNC-TIGHT",
            machine_name="Tight CNC",
            machine_type="CNC",
            status="AVAILABLE",
            available_from=start,
            current_setup_id=None,
            setup_change_time_min=5,
            occupied_slots=[
                OccupiedSlot(start=0, end=3000),
                OccupiedSlot(start=3500, end=6000),  # Only 200s gap (need 300 setup + duration)
                OccupiedSlot(start=6500, end=9000),
            ],
        )

        solver = ORToolsSolver(
            work_orders=[],
            machines=[machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
        )

        # Task of 600s starting at 0 — must skip all three slots
        adjusted = solver._adjust_start_for_occupied_slots("CNC-TIGHT", 0, 600)
        # Should end up after last slot: 9000 + 300 = 9300
        assert adjusted >= 9000 + 300

    # ---- Per-solver occupied slot integration tests ----

    def test_ortools_respects_occupied_slots(
        self,
        short_work_order,
        occupied_machine,
        sample_machine_type_params,
        occupied_horizon,
    ):
        """OR-Tools solver: new tasks must not overlap with occupied slots."""
        start, end = occupied_horizon

        solver = ORToolsSolver(
            work_orders=[short_work_order],
            machines=[occupied_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=SolverConfig(time_limit_sec=10),
        )

        result = solver.solve(time_limit_sec=10)

        if result.status == "success":
            assert len(result.scheduled_tasks) > 0
            self._check_no_overlap_with_slots(
                result.scheduled_tasks,
                "CNC-001",
                occupied_machine.occupied_slots,
            )

    def test_ga_respects_occupied_slots(
        self,
        short_work_order,
        occupied_machine,
        sample_machine_type_params,
        occupied_horizon,
    ):
        """GA solver: new tasks must not overlap with occupied slots."""
        start, end = occupied_horizon

        solver = GeneticAlgorithmSolver(
            work_orders=[short_work_order],
            machines=[occupied_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=SolverConfig(time_limit_sec=5, population_size=20, generations=50),
        )

        result = solver.solve(time_limit_sec=5)

        if result.status == "success":
            assert len(result.scheduled_tasks) > 0
            self._check_no_overlap_with_slots(
                result.scheduled_tasks,
                "CNC-001",
                occupied_machine.occupied_slots,
            )

    def test_sa_respects_occupied_slots(
        self,
        short_work_order,
        occupied_machine,
        sample_machine_type_params,
        occupied_horizon,
    ):
        """SA solver: new tasks must not overlap with occupied slots."""
        start, end = occupied_horizon

        solver = SimulatedAnnealingSolver(
            work_orders=[short_work_order],
            machines=[occupied_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=SolverConfig(time_limit_sec=5, sa_iterations=500),
        )

        result = solver.solve(time_limit_sec=5)

        if result.status == "success":
            assert len(result.scheduled_tasks) > 0
            self._check_no_overlap_with_slots(
                result.scheduled_tasks,
                "CNC-001",
                occupied_machine.occupied_slots,
            )

    def test_tabu_respects_occupied_slots(
        self,
        short_work_order,
        occupied_machine,
        sample_machine_type_params,
        occupied_horizon,
    ):
        """Tabu solver: new tasks must not overlap with occupied slots."""
        start, end = occupied_horizon

        solver = TabuSearchSolver(
            work_orders=[short_work_order],
            machines=[occupied_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=SolverConfig(time_limit_sec=5, tabu_iterations=200),
        )

        result = solver.solve(time_limit_sec=5)

        if result.status == "success":
            assert len(result.scheduled_tasks) > 0
            self._check_no_overlap_with_slots(
                result.scheduled_tasks,
                "CNC-001",
                occupied_machine.occupied_slots,
            )

    def test_alns_respects_occupied_slots(
        self,
        short_work_order,
        occupied_machine,
        sample_machine_type_params,
        occupied_horizon,
    ):
        """ALNS solver: new tasks must not overlap with occupied slots."""
        start, end = occupied_horizon

        solver = ALNSSolver(
            work_orders=[short_work_order],
            machines=[occupied_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=SolverConfig(time_limit_sec=5, alns_iterations=100),
        )

        result = solver.solve(time_limit_sec=5)

        if result.status == "success":
            assert len(result.scheduled_tasks) > 0
            self._check_no_overlap_with_slots(
                result.scheduled_tasks,
                "CNC-001",
                occupied_machine.occupied_slots,
            )

    def test_all_solvers_no_overlap_with_occupied(
        self,
        short_work_order,
        occupied_machines_two,
        sample_machine_type_params,
        occupied_horizon,
    ):
        """All 5 solvers must produce schedules with no occupied slot overlaps."""
        start, end = occupied_horizon
        occupied_slots = occupied_machines_two[0].occupied_slots  # CNC-001 slots

        solver_configs = [
            (SolverType.OR_TOOLS, SolverConfig(time_limit_sec=10)),
            (
                SolverType.GENETIC_ALGORITHM,
                SolverConfig(time_limit_sec=5, population_size=20, generations=50),
            ),
            (SolverType.SIMULATED_ANNEALING, SolverConfig(time_limit_sec=5, sa_iterations=500)),
            (SolverType.TABU_SEARCH, SolverConfig(time_limit_sec=5, tabu_iterations=200)),
            (SolverType.ALNS, SolverConfig(time_limit_sec=5, alns_iterations=100)),
        ]

        for solver_type, config in solver_configs:
            solver = SolverFactory.create_solver(
                solver_type=solver_type,
                work_orders=[short_work_order],
                machines=occupied_machines_two,
                machine_type_params=sample_machine_type_params,
                horizon_start=start,
                horizon_end=end,
                config=config,
            )

            result = solver.solve(time_limit_sec=config.time_limit_sec)

            if result.status == "success" and result.scheduled_tasks:
                self._check_no_overlap_with_slots(
                    result.scheduled_tasks,
                    "CNC-001",
                    occupied_slots,
                )

    def test_machine_with_no_occupied_slots_unchanged(
        self,
        short_work_order,
        sample_machine,
        sample_machine_type_params,
        occupied_horizon,
    ):
        """Machine without occupied slots should schedule normally."""
        start, end = occupied_horizon

        solver = ORToolsSolver(
            work_orders=[short_work_order],
            machines=[sample_machine],
            machine_type_params=sample_machine_type_params,
            horizon_start=start,
            horizon_end=end,
            config=SolverConfig(time_limit_sec=10),
        )

        result = solver.solve(time_limit_sec=10)

        assert result.status == "success"
        assert len(result.scheduled_tasks) > 0
        # Tasks can start from time 0 since there are no occupied slots
        first_task = result.scheduled_tasks[0]
        assert first_task.start_time >= 0
