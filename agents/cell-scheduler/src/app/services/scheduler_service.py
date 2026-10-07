"""
Scheduler Service

Business logic for scheduling operations.
Bridges API layer with solver implementations.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

from ...solvers import (
    SolverFactory,
    SolverType,
    SolverConfig,
    WorkOrder,
    Operation,
    NcCode,
    Machine,
    OccupiedSlot,
    MachineTypeParams,
    AMRConfig,
    SchedulerConfig,
    Calendar,
    Break,
)
from ..schemas import (
    ScheduleRequest,
    ScheduleResponse,
    ScheduledTaskSchema,
    ScheduleStatisticsSchema,
    QualityMetricsSchema,
    GanttDataSchema,
    GanttTaskSchema,
    SolverInfoSchema,
    SetupIntervalSchema,
)
from .aas_loader import AASLoader

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for scheduling operations

    Handles:
    - Request parsing and validation
    - Solver creation and execution
    - Response formatting

    aas_loader가 주입되면 machines/amrs/machine_type_params/scheduler_config를
    AAS에서 로드하고, 없으면 요청 바디의 데이터를 사용합니다.
    """

    def __init__(self, aas_loader: Optional[AASLoader] = None):
        self.factory = SolverFactory()
        self.aas_loader = aas_loader

    async def solve(self, request: ScheduleRequest) -> ScheduleResponse:
        """
        Solve a scheduling request

        Args:
            request: ScheduleRequest with work orders and options.
                     machines/amrs/config는 AAS 로더가 있으면 AAS에서, 없으면 request에서 로드.

        Returns:
            ScheduleResponse with scheduled tasks and statistics
        """
        logger.info(f"Processing scheduling request with {len(request.work_orders)} work orders")

        # Convert request to solver data structures
        work_orders = self._parse_work_orders(request.work_orders)

        if self.aas_loader:
            logger.info("Loading machines/AMRs/config from AAS")
            machines = self.aas_loader.load_machines(request.scheduling_horizon.start)
            machine_type_params = self.aas_loader.load_machine_type_params()
            amrs = self.aas_loader.load_amrs()
            scheduler_config = self.aas_loader.load_scheduler_config()
        else:
            machines = self._parse_machines(request.machines)
            machine_type_params = self._parse_machine_type_params(request.machine_type_params)
            amrs = self._parse_amrs(request.amrs)
            scheduler_config = self._parse_scheduler_config(request.scheduler_config)

        horizon_start = request.scheduling_horizon.start
        horizon_end = request.scheduling_horizon.end

        # Get solver type and config
        requested = request.options.solver_type.value
        if requested == "AUTO":
            total_ops = sum(len(wo.operations) for wo in work_orders)
            solver_type = self.recommend_solver(total_ops)
            logger.info(
                f"AUTO solver: {total_ops} ops → selected {solver_type.value}"
            )
        else:
            solver_type = SolverFactory.get_solver_type(requested)
        config = self._create_config(request.options)

        # Create and run solver
        solver = SolverFactory.create_solver(
            solver_type=solver_type,
            work_orders=work_orders,
            machines=machines,
            machine_type_params=machine_type_params,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            constraints=request.constraints,
            config=config,
            amrs=amrs,
            scheduler_config=scheduler_config,
        )

        import time as _time
        _solve_start = _time.time()
        result = await asyncio.to_thread(solver.solve, time_limit_sec=config.time_limit_sec)
        _elapsed = _time.time() - _solve_start

        # OR-Tools fallback: if no_solution, retry with GA using remaining budget.
        if result.status == "no_solution" and solver_type == SolverType.OR_TOOLS:
            remaining_time = max(1, config.time_limit_sec - int(_elapsed))
            logger.warning(
                f"OR-Tools returned no_solution after {_elapsed:.1f}s — "
                f"falling back to Genetic Algorithm solver (remaining budget: {remaining_time}s)"
            )
            original_solver_info = dict(result.solver_info or {})
            ga_solver = SolverFactory.create_solver(
                solver_type=SolverType.GENETIC_ALGORITHM,
                work_orders=work_orders,
                machines=machines,
                machine_type_params=machine_type_params,
                horizon_start=horizon_start,
                horizon_end=horizon_end,
                constraints=request.constraints,
                config=config,
                amrs=amrs,
                scheduler_config=scheduler_config,
            )
            result = await asyncio.to_thread(ga_solver.solve, time_limit_sec=remaining_time)
            result.solver_info["fallback_used"] = True
            result.solver_info["original_solver"] = original_solver_info
            result.solver_info["or_tools_elapsed_sec"] = round(_elapsed, 2)
            solver = ga_solver

        # Generate additional data
        gantt_data = solver.generate_gantt_data()
        quality_metrics = solver.estimate_schedule_quality()

        # machine_id → machine_name 매핑 (간트차트 Y축 표시용)
        machine_name_map = {m.machine_id: m.machine_name for m in machines}

        # Format response
        return self._format_response(result, gantt_data, quality_metrics, machine_name_map)

    @staticmethod
    def recommend_solver(total_ops: int) -> SolverType:
        """
        Recommend a solver based on problem size (total operations count).

        Thresholds:
          <30 ops  → OR_TOOLS (exact, fast for small problems)
          30-100   → GA (good quality/speed balance for medium problems)
          >100     → SA (fast approximate for large problems)
        """
        if total_ops < 30:
            return SolverType.OR_TOOLS
        elif total_ops <= 100:
            return SolverType.GENETIC_ALGORITHM
        else:
            return SolverType.SIMULATED_ANNEALING

    def get_available_solvers(self) -> List[Dict[str, Any]]:
        """Get list of available solvers with their info"""
        solvers = []

        for solver_type in SolverType:
            config = SolverFactory.get_default_config(solver_type)

            # Create minimal solver info
            info = {
                "type": solver_type.value,
                "name": solver_type.name.replace("_", " ").title(),
                "version": "1.0",
                "description": self._get_solver_description(solver_type),
                "best_for": self._get_solver_best_for(solver_type),
                "characteristics": self._get_solver_characteristics(solver_type),
                "default_params": {
                    "time_limit_sec": config.time_limit_sec,
                },
            }

            # Add solver-specific params
            if solver_type == SolverType.OR_TOOLS:
                info["default_params"]["num_workers"] = config.num_workers
            elif solver_type == SolverType.GENETIC_ALGORITHM:
                info["default_params"].update(
                    {
                        "population_size": config.population_size,
                        "generations": config.generations,
                        "crossover_rate": config.crossover_rate,
                        "mutation_rate": config.mutation_rate,
                    }
                )
            elif solver_type == SolverType.SIMULATED_ANNEALING:
                info["default_params"].update(
                    {
                        "initial_temp": config.initial_temp,
                        "cooling_rate": config.cooling_rate,
                    }
                )
            elif solver_type == SolverType.TABU_SEARCH:
                info["default_params"].update(
                    {
                        "tabu_tenure": config.tabu_tenure,
                        "tabu_iterations": config.tabu_iterations,
                    }
                )
            elif solver_type == SolverType.ALNS:
                info["default_params"].update(
                    {
                        "alns_iterations": config.alns_iterations,
                        "alns_destroy_rate": config.alns_destroy_rate,
                        "alns_segment_size": config.alns_segment_size,
                    }
                )

            solvers.append(info)

        return solvers

    def _parse_work_orders(self, wo_schemas) -> List[WorkOrder]:
        """Convert work order schemas to domain objects (MES v5 schema)"""
        work_orders = []

        for wo in wo_schemas:
            operations = []
            for op in wo.operations:
                nc_code = None
                if op.nc_code is not None:
                    nc_code = NcCode(
                        program_id=op.nc_code.program_id,
                        file_path=op.nc_code.file_path or "",
                        cycle_time_sec=op.nc_code.cycle_time_sec,
                        cycle_time_confidence=op.nc_code.cycle_time_confidence or 0.9,
                        tool_list=op.nc_code.tool_list or [],
                        tool_change_count=op.nc_code.tool_change_count or 0,
                        compatible_machines=op.nc_code.compatible_machines or [],
                    )

                # required_machines: use new list field; fallback to empty list
                req_machines = list(op.required_machines) if op.required_machines else []

                operations.append(
                    Operation(
                        op_id=op.op_id,
                        op_name=op.op_name,
                        sequence=op.sequence,
                        predecessors=op.predecessors or [],
                        required_machines=req_machines,
                        setup_id=op.setup_id or "",
                        nc_code=nc_code,
                        cycle_time_sec=op.cycle_time_sec,
                    )
                )

            work_orders.append(
                WorkOrder(
                    wo_id=wo.wo_id,
                    product_id=wo.product_id,
                    product_name=wo.product_name,
                    order_quantity=wo.order_quantity,
                    due_date=wo.due_date,
                    priority=wo.priority,
                    release_date=wo.release_date,
                    customer=wo.customer or "",
                    operations=operations,
                    lot_no=getattr(wo, "lot_no", "") or "",
                )
            )

        return work_orders

    def _parse_machines(self, machine_schemas) -> List[Machine]:
        """Convert machine schemas to domain objects"""
        from datetime import time as dtime
        machines = []
        for m in machine_schemas:
            calendar = None
            if m.calendar is not None:
                cal = m.calendar
                sh, sm = (int(x) for x in cal.shift_start.split(":"))
                eh, em = (int(x) for x in cal.shift_end.split(":"))
                breaks = []
                for b in cal.breaks:
                    bsh, bsm = (int(x) for x in b.start.split(":"))
                    beh, bem = (int(x) for x in b.end.split(":"))
                    breaks.append(Break(
                        start=dtime(bsh, bsm),
                        end=dtime(beh, bem),
                    ))
                calendar = Calendar(
                    shift_start=dtime(sh, sm),
                    shift_end=dtime(eh, em),
                    breaks=breaks,
                )
            machines.append(Machine(
                machine_id=m.machine_id,
                machine_name=m.machine_name,
                machine_type=m.machine_type,
                status=m.status,
                available_from=m.available_from,
                current_setup_id=m.current_setup_id,
                setup_change_time_min=m.setup_change_time_min,
                occupied_slots=[
                    OccupiedSlot(start=s.start, end=s.end, wo_id=s.wo_id)
                    for s in m.occupied_slots
                ],
                calendar=calendar,
            ))
        return machines

    def _parse_amrs(self, amr_schemas) -> List[AMRConfig]:
        """Convert AMR schemas to domain objects"""
        return [
            AMRConfig(
                amr_id=a.amr_id,
                model=a.model or "",
                status=a.status,
                current_location=a.current_location or "",
                accessible_machines=a.accessible_machines or [],
                speed_m_per_sec=a.speed_m_per_sec,
            )
            for a in (amr_schemas or [])
        ]

    def _parse_scheduler_config(self, config_schema) -> SchedulerConfig:
        """Convert scheduler config schema to domain object"""
        if config_schema is None:
            return SchedulerConfig()
        return SchedulerConfig(
            lot_size=config_schema.lot_size,
            amr_transfer_time_sec=config_schema.amr_transfer_time_sec,
        )

    def _parse_machine_type_params(
        self, params_schemas: Dict[str, Any]
    ) -> Dict[str, MachineTypeParams]:
        """Convert machine type params schemas to domain objects"""
        return {
            key: MachineTypeParams(
                loading_type=val.loading_type,
                amr_transport_qty=val.amr_transport_qty,
                exchange_time_sec=val.exchange_time_sec,
                load_unload_time_sec=val.load_unload_time_sec,
            )
            for key, val in params_schemas.items()
        }

    def _create_config(self, options) -> SolverConfig:
        """Create solver config from options"""
        config = SolverConfig(time_limit_sec=options.time_limit_sec if options.time_limit_sec is not None else 60)

        if options.num_workers is not None:
            config.num_workers = options.num_workers
        if options.population_size is not None:
            config.population_size = options.population_size
        if options.generations is not None:
            config.generations = options.generations
        if options.crossover_rate is not None:
            config.crossover_rate = options.crossover_rate
        if options.mutation_rate is not None:
            config.mutation_rate = options.mutation_rate
        if options.initial_temp is not None:
            config.initial_temp = options.initial_temp
        if options.cooling_rate is not None:
            config.cooling_rate = options.cooling_rate
        if options.tabu_tenure is not None:
            config.tabu_tenure = options.tabu_tenure
        if options.tabu_iterations is not None:
            config.tabu_iterations = options.tabu_iterations
        # ALNS-specific params
        if getattr(options, "alns_destroy_rate", None) is not None:
            config.alns_destroy_rate = options.alns_destroy_rate
        if getattr(options, "alns_iterations", None) is not None:
            config.alns_iterations = options.alns_iterations
        if getattr(options, "alns_segment_size", None) is not None:
            config.alns_segment_size = options.alns_segment_size

        return config

    def _format_response(
        self,
        result,
        gantt_data: Dict[str, Any],
        quality_metrics: Dict[str, Any],
        machine_name_map: Dict[str, str] = {},
    ) -> ScheduleResponse:
        """Format solver result into API response"""
        # Scheduled tasks (MES v5 - no job_id)
        scheduled_tasks = [
            ScheduledTaskSchema(
                wo_id=t.wo_id,
                op_id=t.op_id,
                machine_id=t.machine_id,
                start_time=t.start_time,
                end_time=t.end_time,
                quantity=t.quantity,
                setup_time=getattr(t, "setup_time", 0),
                sublot_no=getattr(t, "sublot_no", 1),
                lot_no=getattr(t, "lot_no", ""),
                op_name=getattr(t, "op_name", ""),
                assigned_machines=getattr(t, "assigned_machines", {}),
                amr_transfer_sec=getattr(t, "amr_transfer_sec", 0),
            )
            for t in result.scheduled_tasks
        ]

        # Statistics - handle inf values for JSON serialization
        objective_val = result.objective_value
        if objective_val == float("inf") or objective_val == float("-inf"):
            objective_val = 0.0

        statistics = ScheduleStatisticsSchema(
            total_tasks=len(result.scheduled_tasks),
            makespan_seconds=result.total_makespan,
            makespan_hours=round(result.total_makespan / 3600, 2),
            machine_utilization=result.machine_utilization,
            bottleneck_machines=result.bottleneck_machines,
            solve_time_sec=round(result.solve_time_sec, 3),
            objective_value=objective_val,
            weighted_tardiness_sec=getattr(result, "weighted_tardiness_sec", 0),
            weighted_completion_sec=getattr(result, "weighted_completion_sec", 0),
            total_setup_sec=getattr(result, "total_setup_sec", 0),
        )

        # Quality metrics
        quality = QualityMetricsSchema(
            status=quality_metrics.get("status", "unknown"),
            makespan_hours=quality_metrics.get("makespan_hours", 0),
            total_lateness_hours=quality_metrics.get("total_lateness_hours", 0),
            avg_machine_utilization=quality_metrics.get("avg_machine_utilization", 0),
            machine_utilization=quality_metrics.get("machine_utilization", {}),
            bottleneck_machines=quality_metrics.get("bottleneck_machines", []),
            schedule_efficiency=quality_metrics.get("schedule_efficiency", 0),
            per_wo_lateness=quality_metrics.get("per_wo_lateness", {}),
            total_scheduled_tasks=quality_metrics.get("total_scheduled_tasks", 0),
            total_work_orders=quality_metrics.get("total_work_orders", 0),
            total_machines=quality_metrics.get("total_machines", 0),
            weighted_tardiness_hours=quality_metrics.get("weighted_tardiness_hours", 0.0),
            weighted_completion_minutes=quality_metrics.get("weighted_completion_minutes", 0.0),
            total_setup_minutes=quality_metrics.get("total_setup_minutes", 0.0),
        )

        # Gantt data
        gantt = GanttDataSchema(
            tasks=[
                GanttTaskSchema(
                    name=t["name"],
                    start=t["start"],
                    end=t["end"],
                    resource=t["resource"],
                    priority=t["priority"],
                    color=t["color"],
                    quantity=t["quantity"],
                    duration_minutes=t["duration_minutes"],
                )
                for t in gantt_data.get("tasks", [])
            ],
            resources=gantt_data.get("resources", []),
            start=gantt_data.get("start", ""),
            end=gantt_data.get("end", ""),
        )

        # Solver info
        solver_info = SolverInfoSchema(
            type=result.solver_info.get("type", "unknown"),
            name=result.solver_info.get("name", "Unknown"),
            version=result.solver_info.get("version", ""),
            description=result.solver_info.get("description", ""),
            best_for=result.solver_info.get("best_for", ""),
            characteristics=result.solver_info.get("characteristics", {}),
            default_params=result.solver_info.get("default_params", {}),
            error=result.solver_info.get("error", None),
        )

        # Setup intervals and infeasible WOs (from advanced OR-Tools solver)
        setup_intervals = [
            SetupIntervalSchema(
                machine_id=s.machine_id,
                wo_id=s.wo_id,
                start_time=s.start_time,
                end_time=s.end_time,
                duration_sec=s.end_time - s.start_time,
            )
            for s in getattr(result, "setup_intervals", [])
        ]

        return ScheduleResponse(
            status=result.status,
            scheduled_tasks=scheduled_tasks,
            statistics=statistics,
            quality_metrics=quality,
            gantt_data=gantt,
            solver_info=solver_info,
            setup_intervals=setup_intervals,
            infeasible_wos=getattr(result, "infeasible_wos", []),
            machine_name_map=machine_name_map,
        )

    def _get_solver_description(self, solver_type: SolverType) -> str:
        """Get description for solver type"""
        descriptions = {
            SolverType.OR_TOOLS: "Google OR-Tools Constraint Programming solver with SAT backend",
            SolverType.GENETIC_ALGORITHM: "Evolutionary algorithm using genetic operators for optimization",
            SolverType.SIMULATED_ANNEALING: "Probabilistic metaheuristic inspired by annealing in metallurgy",
            SolverType.TABU_SEARCH: "Memory-based metaheuristic that avoids cycling through tabu list",
            SolverType.ALNS: "Adaptive Large Neighborhood Search with destroy/repair operators and adaptive selection",
        }
        return descriptions.get(solver_type, "")

    def _get_solver_best_for(self, solver_type: SolverType) -> str:
        """Get best use case for solver type"""
        best_for = {
            SolverType.OR_TOOLS: "Small-medium problems (<30 jobs), optimal solutions required",
            SolverType.GENETIC_ALGORITHM: "Large problems, good balance of quality and speed",
            SolverType.SIMULATED_ANNEALING: "Fast approximate solutions, escaping local optima",
            SolverType.TABU_SEARCH: "Complex constraints, avoiding local optima",
            SolverType.ALNS: "Large-scale problems with complex constraints, quality-focused optimization",
        }
        return best_for.get(solver_type, "")

    def _get_solver_characteristics(self, solver_type: SolverType) -> Dict[str, Any]:
        """Get characteristics for solver type"""
        characteristics = {
            SolverType.OR_TOOLS: {"optimal": True, "deterministic": True, "parallelizable": True},
            SolverType.GENETIC_ALGORITHM: {
                "optimal": False,
                "deterministic": False,
                "parallelizable": True,
            },
            SolverType.SIMULATED_ANNEALING: {
                "optimal": False,
                "deterministic": False,
                "parallelizable": False,
            },
            SolverType.TABU_SEARCH: {
                "optimal": False,
                "deterministic": False,
                "parallelizable": False,
            },
            SolverType.ALNS: {
                "optimal": False,
                "deterministic": False,
                "parallelizable": False,
                "adaptive": True,
            },
        }
        return characteristics.get(solver_type, {})
