"""Tests for SolverFactory."""

import pytest
from datetime import datetime, timedelta, timezone

from src.solvers import (
    SolverFactory,
    SolverType,
    SolverConfig,
    WorkOrder,
    Operation,
    NcCode,
    Machine,
    MachineTypeParams,
    ORToolsSolver,
    GeneticAlgorithmSolver,
    SimulatedAnnealingSolver,
    TabuSearchSolver,
    ALNSSolver,
)


class TestSolverFactoryCreate:
    """Tests for SolverFactory.create_solver."""

    @pytest.fixture
    def sample_data(self):
        """Create minimal sample data for solver creation."""
        nc_code = NcCode(
            program_id="NC-001",
            file_path="/nc/test.nc",
            cycle_time_sec=300,
            cycle_time_confidence=0.95,
            tool_list=["T01"],
            tool_change_count=1,
            compatible_machines=["CNC"],
        )
        operation = Operation(
            op_id="OP-001",
            op_name="Test Op",
            sequence=1,
            predecessors=[],
            required_machines=["CNC"],
            setup_id="SETUP-A",
            nc_code=nc_code,
        )
        work_order = WorkOrder(
            wo_id="WO-001",
            product_id="PROD-001",
            product_name="Test Product",
            order_quantity=5,
            due_date=datetime.now(timezone.utc) + timedelta(hours=24),
            priority=5,
            release_date=datetime.now(timezone.utc),
            customer="Test",
            operations=[operation],
        )
        machine = Machine(
            machine_id="CNC-001",
            machine_name="CNC 1",
            machine_type="CNC",
            status="AVAILABLE",
            available_from=datetime.now(timezone.utc),
            current_setup_id=None,
            setup_change_time_min=5,
        )
        machine_params = {
            "CNC": MachineTypeParams(
                loading_type="AMR",
                amr_transport_qty=1,
                exchange_time_sec=60,
                load_unload_time_sec=30,
            )
        }

        return {
            "work_orders": [work_order],
            "machines": [machine],
            "machine_type_params": machine_params,
            "horizon_start": datetime.now(timezone.utc),
            "horizon_end": datetime.now(timezone.utc) + timedelta(hours=24),
        }

    def test_create_ortools_solver(self, sample_data):
        """Should create OR-Tools solver."""
        solver = SolverFactory.create_solver(
            solver_type=SolverType.OR_TOOLS,
            **sample_data,
        )

        assert isinstance(solver, ORToolsSolver)

    def test_create_ga_solver(self, sample_data):
        """Should create Genetic Algorithm solver."""
        solver = SolverFactory.create_solver(
            solver_type=SolverType.GENETIC_ALGORITHM,
            **sample_data,
        )

        assert isinstance(solver, GeneticAlgorithmSolver)

    def test_create_sa_solver(self, sample_data):
        """Should create Simulated Annealing solver."""
        solver = SolverFactory.create_solver(
            solver_type=SolverType.SIMULATED_ANNEALING,
            **sample_data,
        )

        assert isinstance(solver, SimulatedAnnealingSolver)

    def test_create_tabu_solver(self, sample_data):
        """Should create Tabu Search solver."""
        solver = SolverFactory.create_solver(
            solver_type=SolverType.TABU_SEARCH,
            **sample_data,
        )

        assert isinstance(solver, TabuSearchSolver)

    def test_create_alns_solver(self, sample_data):
        """Should create ALNS solver."""
        solver = SolverFactory.create_solver(
            solver_type=SolverType.ALNS,
            **sample_data,
        )

        assert isinstance(solver, ALNSSolver)

    def test_create_with_custom_config(self, sample_data):
        """Should accept custom configuration."""
        config = SolverConfig(time_limit_sec=120, num_workers=4)

        solver = SolverFactory.create_solver(
            solver_type=SolverType.OR_TOOLS,
            config=config,
            **sample_data,
        )

        assert solver.config.time_limit_sec == 120
        assert solver.config.num_workers == 4

    def test_create_with_constraints(self, sample_data):
        """Should accept constraints."""
        constraints = {"max_setup_changes": 3}

        solver = SolverFactory.create_solver(
            solver_type=SolverType.OR_TOOLS,
            constraints=constraints,
            **sample_data,
        )

        assert solver.constraints == constraints


class TestSolverFactoryGetType:
    """Tests for SolverFactory.get_solver_type."""

    def test_ortools_variations(self):
        """Should recognize OR-Tools variations."""
        assert SolverFactory.get_solver_type("OR_TOOLS") == SolverType.OR_TOOLS
        assert SolverFactory.get_solver_type("ORTOOLS") == SolverType.OR_TOOLS
        assert SolverFactory.get_solver_type("CP_SAT") == SolverType.OR_TOOLS

    def test_ga_variations(self):
        """Should recognize GA variations."""
        assert SolverFactory.get_solver_type("GA") == SolverType.GENETIC_ALGORITHM
        assert SolverFactory.get_solver_type("GENETIC") == SolverType.GENETIC_ALGORITHM
        assert SolverFactory.get_solver_type("GENETIC_ALGORITHM") == SolverType.GENETIC_ALGORITHM

    def test_sa_variations(self):
        """Should recognize SA variations."""
        assert SolverFactory.get_solver_type("SA") == SolverType.SIMULATED_ANNEALING
        assert (
            SolverFactory.get_solver_type("SIMULATED_ANNEALING") == SolverType.SIMULATED_ANNEALING
        )
        assert SolverFactory.get_solver_type("ANNEALING") == SolverType.SIMULATED_ANNEALING

    def test_tabu_variations(self):
        """Should recognize Tabu Search variations."""
        assert SolverFactory.get_solver_type("TABU") == SolverType.TABU_SEARCH
        assert SolverFactory.get_solver_type("TABU_SEARCH") == SolverType.TABU_SEARCH
        assert SolverFactory.get_solver_type("TS") == SolverType.TABU_SEARCH

    def test_alns_variations(self):
        """Should recognize ALNS variations."""
        assert SolverFactory.get_solver_type("ALNS") == SolverType.ALNS
        assert SolverFactory.get_solver_type("LNS") == SolverType.ALNS
        assert SolverFactory.get_solver_type("ADAPTIVE_LNS") == SolverType.ALNS

    def test_case_insensitive(self):
        """Should be case insensitive."""
        assert SolverFactory.get_solver_type("or_tools") == SolverType.OR_TOOLS
        assert SolverFactory.get_solver_type("Ga") == SolverType.GENETIC_ALGORITHM
        assert SolverFactory.get_solver_type("tabu") == SolverType.TABU_SEARCH

    def test_whitespace_handling(self):
        """Should handle whitespace."""
        assert SolverFactory.get_solver_type("  OR_TOOLS  ") == SolverType.OR_TOOLS

    def test_unknown_type_raises(self):
        """Should raise ValueError for unknown type."""
        with pytest.raises(ValueError) as exc_info:
            SolverFactory.get_solver_type("UNKNOWN")

        assert "Unknown solver type" in str(exc_info.value)


class TestSolverFactoryAvailableSolvers:
    """Tests for SolverFactory.get_available_solvers."""

    def test_returns_list(self):
        """Should return list of solver info."""
        solvers = SolverFactory.get_available_solvers()

        assert isinstance(solvers, list)
        assert len(solvers) == 5  # 5 solver types

    def test_solver_info_structure(self):
        """Each solver info should have required fields."""
        solvers = SolverFactory.get_available_solvers()

        for solver in solvers:
            assert "type" in solver
            assert "name" in solver
            assert "class" in solver

    def test_all_solver_types_included(self):
        """All solver types should be included."""
        solvers = SolverFactory.get_available_solvers()
        types = [s["type"] for s in solvers]

        assert SolverType.OR_TOOLS.value in types
        assert SolverType.GENETIC_ALGORITHM.value in types
        assert SolverType.SIMULATED_ANNEALING.value in types
        assert SolverType.TABU_SEARCH.value in types
        assert SolverType.ALNS.value in types


class TestSolverFactoryDefaultConfig:
    """Tests for SolverFactory.get_default_config."""

    def test_ortools_defaults(self):
        """Should return OR-Tools specific defaults."""
        config = SolverFactory.get_default_config(SolverType.OR_TOOLS)

        assert config.time_limit_sec == 60
        assert config.num_workers == 8

    def test_ga_defaults(self):
        """Should return GA specific defaults."""
        config = SolverFactory.get_default_config(SolverType.GENETIC_ALGORITHM)

        assert config.time_limit_sec == 120
        assert config.population_size == 100
        assert config.generations == 500
        assert config.crossover_rate == 0.8
        assert config.mutation_rate == 0.2

    def test_sa_defaults(self):
        """Should return SA specific defaults."""
        config = SolverFactory.get_default_config(SolverType.SIMULATED_ANNEALING)

        assert config.initial_temp == 100.0
        assert config.final_temp == 0.1
        assert config.cooling_rate == 0.95

    def test_tabu_defaults(self):
        """Should return Tabu specific defaults."""
        config = SolverFactory.get_default_config(SolverType.TABU_SEARCH)

        assert config.tabu_tenure == 10
        assert config.tabu_iterations == 5000
        assert config.tabu_list_size == 50

    def test_alns_defaults(self):
        """Should return ALNS specific defaults."""
        config = SolverFactory.get_default_config(SolverType.ALNS)

        assert config.alns_destroy_rate == 0.3
        assert config.alns_iterations == 10000
        assert config.alns_segment_size == 100


class TestSolverFactoryRecommend:
    """Tests for SolverFactory.recommend_solver."""

    def test_small_problem_ortools(self):
        """Should recommend OR-Tools for small problems."""
        recommended = SolverFactory.recommend_solver(
            num_operations=10,
            num_machines=3,
            time_available_sec=60,
        )

        assert recommended == SolverType.OR_TOOLS

    def test_optimal_required_ortools(self):
        """Should recommend OR-Tools when optimal is required."""
        recommended = SolverFactory.recommend_solver(
            num_operations=100,
            num_machines=20,
            time_available_sec=60,
            need_optimal=True,
        )

        assert recommended == SolverType.OR_TOOLS

    def test_large_problem_limited_time_sa(self):
        """Should recommend SA for large problems with limited time."""
        recommended = SolverFactory.recommend_solver(
            num_operations=100,
            num_machines=20,
            time_available_sec=20,
        )

        assert recommended == SolverType.SIMULATED_ANNEALING

    def test_large_problem_sufficient_time_alns(self):
        """Should recommend ALNS for large problems with sufficient time."""
        recommended = SolverFactory.recommend_solver(
            num_operations=100,
            num_machines=10,
            time_available_sec=120,
        )

        assert recommended == SolverType.ALNS

    def test_medium_complexity_ga(self):
        """Should recommend GA for large problems with moderate time."""
        recommended = SolverFactory.recommend_solver(
            num_operations=50,
            num_machines=15,
            time_available_sec=45,
        )

        # Either GA or Tabu for medium complexity
        assert recommended in [SolverType.GENETIC_ALGORITHM, SolverType.TABU_SEARCH]
