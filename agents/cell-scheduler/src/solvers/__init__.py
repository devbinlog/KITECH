"""
Scheduler Solvers Package

Provides multiple solver implementations for manufacturing scheduling:
- OR-Tools CP-SAT (optimal for small-medium problems)
- Genetic Algorithm (good for large problems)
- Simulated Annealing (fast approximate solutions)
- Tabu Search (avoids local optima)
- ALNS (adaptive large neighborhood search for quality-focused optimization)

MES v5 Schema: Job layer removed, WorkOrder contains operations directly.
"""

from .base_solver import (
    AMRConfig,
    BaseSolver,
    Break,
    Calendar,
    MachineTypeParams,
    NcCode,
    Machine,
    OccupiedSlot,
    Operation,
    ScheduledTask,
    ScheduleResult,
    SchedulerConfig,
    SetupInterval,
    SolverConfig,
    SolverType,
    WorkOrder,
)
from .solver_factory import SolverFactory
from .ortools_solver import ORToolsSolver
from .genetic_algorithm_solver import GeneticAlgorithmSolver
from .simulated_annealing_solver import SimulatedAnnealingSolver
from .tabu_search_solver import TabuSearchSolver
from .alns_solver import ALNSSolver

__all__ = [
    # Base classes
    "BaseSolver",
    "SolverType",
    "SolverConfig",
    # Data classes (MES v5 - no Job)
    "WorkOrder",
    "Operation",
    "NcCode",
    "Machine",
    "OccupiedSlot",
    "MachineTypeParams",
    "ScheduledTask",
    "ScheduleResult",
    # New advanced data classes
    "AMRConfig",
    "Break",
    "Calendar",
    "SchedulerConfig",
    "SetupInterval",
    # Factory
    "SolverFactory",
    # Solvers
    "ORToolsSolver",
    "GeneticAlgorithmSolver",
    "SimulatedAnnealingSolver",
    "TabuSearchSolver",
    "ALNSSolver",
]
