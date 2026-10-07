"""
Solver Factory

Factory pattern for creating scheduling solver instances.
Provides a unified interface for instantiating different solver types.
"""

import logging
from typing import Dict, List, Any, Type
from datetime import datetime

from .base_solver import (
    AMRConfig,
    BaseSolver,
    SchedulerConfig,
    SolverConfig,
    SolverType,
    WorkOrder,
    Machine,
    MachineTypeParams,
)
from .ortools_solver import ORToolsSolver
from .genetic_algorithm_solver import GeneticAlgorithmSolver
from .simulated_annealing_solver import SimulatedAnnealingSolver
from .tabu_search_solver import TabuSearchSolver
from .alns_solver import ALNSSolver

logger = logging.getLogger(__name__)


class SolverFactory:
    """
    Factory for creating scheduler solver instances

    Supports:
    - OR-Tools CP-SAT (optimal for small-medium problems)
    - Genetic Algorithm (good for large problems)
    - Simulated Annealing (fast approximate solutions)
    - Tabu Search (avoids local optima)
    - ALNS (adaptive large neighborhood search)
    """

    _solver_registry: Dict[SolverType, Type[BaseSolver]] = {
        SolverType.OR_TOOLS: ORToolsSolver,
        SolverType.GENETIC_ALGORITHM: GeneticAlgorithmSolver,
        SolverType.SIMULATED_ANNEALING: SimulatedAnnealingSolver,
        SolverType.TABU_SEARCH: TabuSearchSolver,
        SolverType.ALNS: ALNSSolver,
    }

    @classmethod
    def create_solver(
        cls,
        solver_type: SolverType,
        work_orders: List[WorkOrder],
        machines: List[Machine],
        machine_type_params: Dict[str, MachineTypeParams],
        horizon_start: datetime,
        horizon_end: datetime,
        constraints: Dict[str, Any] = None,
        config: SolverConfig = None,
        amrs: List[AMRConfig] = None,
        scheduler_config: SchedulerConfig = None,
    ) -> BaseSolver:
        """
        Create a solver instance

        Args:
            solver_type: Type of solver to create
            work_orders: List of work orders to schedule
            machines: List of available machines
            machine_type_params: Machine type parameters
            horizon_start: Scheduling horizon start
            horizon_end: Scheduling horizon end
            constraints: Additional constraints
            config: Solver configuration

        Returns:
            Configured solver instance

        Raises:
            ValueError: If solver type is not supported
        """
        if solver_type not in cls._solver_registry:
            raise ValueError(f"Unknown solver type: {solver_type}")

        solver_class = cls._solver_registry[solver_type]

        logger.info(f"Creating solver: {solver_type.value}")

        return solver_class(
            work_orders=work_orders,
            machines=machines,
            machine_type_params=machine_type_params,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            constraints=constraints,
            config=config or SolverConfig(),
            amrs=amrs or [],
            scheduler_config=scheduler_config or SchedulerConfig(),
        )

    @classmethod
    def get_solver_type(cls, type_str: str) -> SolverType:
        """
        Parse solver type from string

        Args:
            type_str: Solver type string (e.g., "OR_TOOLS", "GA", "SA", "TABU")

        Returns:
            SolverType enum value

        Raises:
            ValueError: If solver type string is not recognized
        """
        type_map = {
            "OR_TOOLS": SolverType.OR_TOOLS,
            "ORTOOLS": SolverType.OR_TOOLS,
            "CP_SAT": SolverType.OR_TOOLS,
            "GA": SolverType.GENETIC_ALGORITHM,
            "GENETIC": SolverType.GENETIC_ALGORITHM,
            "GENETIC_ALGORITHM": SolverType.GENETIC_ALGORITHM,
            "SA": SolverType.SIMULATED_ANNEALING,
            "SIMULATED_ANNEALING": SolverType.SIMULATED_ANNEALING,
            "ANNEALING": SolverType.SIMULATED_ANNEALING,
            "TABU": SolverType.TABU_SEARCH,
            "TABU_SEARCH": SolverType.TABU_SEARCH,
            "TS": SolverType.TABU_SEARCH,
            "ALNS": SolverType.ALNS,
            "LNS": SolverType.ALNS,
            "ADAPTIVE_LNS": SolverType.ALNS,
        }

        normalized = type_str.upper().strip()
        if normalized not in type_map:
            raise ValueError(
                f"Unknown solver type: {type_str}. Supported types: {list(type_map.keys())}"
            )

        return type_map[normalized]

    @classmethod
    def get_available_solvers(cls) -> List[Dict[str, Any]]:
        """
        Get information about all available solvers

        Returns:
            List of solver information dictionaries
        """
        solvers = []

        for solver_type, solver_class in cls._solver_registry.items():
            # Create a minimal instance to get info
            info = {
                "type": solver_type.value,
                "name": solver_type.name,
                "class": solver_class.__name__,
            }

            # Get detailed info from solver class docstring
            if solver_class.__doc__:
                info["description"] = solver_class.__doc__.strip().split("\n")[0]

            solvers.append(info)

        return solvers

    @classmethod
    def get_default_config(cls, solver_type: SolverType) -> SolverConfig:
        """
        Get default configuration for a solver type

        Args:
            solver_type: Solver type

        Returns:
            SolverConfig with appropriate defaults
        """
        config = SolverConfig()

        if solver_type == SolverType.OR_TOOLS:
            config.time_limit_sec = 60
            config.num_workers = 8

        elif solver_type == SolverType.GENETIC_ALGORITHM:
            config.time_limit_sec = 120
            config.population_size = 100
            config.generations = 500
            config.crossover_rate = 0.8
            config.mutation_rate = 0.2

        elif solver_type == SolverType.SIMULATED_ANNEALING:
            config.time_limit_sec = 60
            config.initial_temp = 100.0
            config.final_temp = 0.1
            config.cooling_rate = 0.95
            config.sa_iterations = 10000

        elif solver_type == SolverType.TABU_SEARCH:
            config.time_limit_sec = 90
            config.tabu_tenure = 10
            config.tabu_iterations = 5000
            config.diversification_freq = 100

        elif solver_type == SolverType.ALNS:
            config.time_limit_sec = 120
            config.alns_destroy_rate = 0.3
            config.alns_iterations = 10000
            config.alns_segment_size = 100
            # ALNS uses SA acceptance, so configure those too
            config.initial_temp = 100.0
            config.final_temp = 0.1
            config.cooling_rate = 0.99

        return config

    @classmethod
    def recommend_solver(
        cls,
        num_operations: int,
        num_machines: int,
        time_available_sec: int = 60,
        need_optimal: bool = False,
    ) -> SolverType:
        """
        Recommend a solver based on problem characteristics

        Args:
            num_operations: Number of operations to schedule
            num_machines: Number of machines available
            time_available_sec: Time available for solving
            need_optimal: Whether optimal solution is required

        Returns:
            Recommended SolverType
        """
        # Estimate problem complexity
        complexity = num_operations * num_machines

        # OR-Tools is best for small problems or when optimality is required
        if need_optimal or complexity < 100:
            return SolverType.OR_TOOLS

        # For very large problems with limited time, use SA (fastest)
        if complexity > 1000 and time_available_sec < 30:
            return SolverType.SIMULATED_ANNEALING

        # For large problems with sufficient time, use ALNS (best quality)
        if complexity > 500 and time_available_sec >= 60:
            return SolverType.ALNS

        # For large problems with moderate time, use GA
        if complexity > 500:
            return SolverType.GENETIC_ALGORITHM

        # For medium complexity with complex constraints, use Tabu Search
        return SolverType.TABU_SEARCH
