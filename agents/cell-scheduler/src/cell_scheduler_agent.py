"""
Manufacturing Cell Scheduling Agent

Comprehensive scheduling solution for multi-machine manufacturing cells with:
- Multiple solver support (OR-Tools, GA, SA, Tabu Search)
- Multi-job scheduling with precedence constraints
- Machine compatibility checking
- Setup time optimization
- AMR (Automated Mobile Robot) integration for transport
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

# Add shared library and local solvers to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent))  # Add src directory for solvers

from core import BaseAgent
from utils import setup_logger

# Use try/except to support both relative (package) and absolute (direct) imports
try:
    from .solvers import (
        SolverFactory,
        SolverType,
        WorkOrder,
        Operation,
        NcCode,
        Machine,
        MachineTypeParams,
    )
except ImportError:
    from solvers import (
        SolverFactory,
        SolverType,
        WorkOrder,
        Operation,
        NcCode,
        Machine,
        MachineTypeParams,
    )

logger = setup_logger(__name__)


# ============================================================================
# Data Loader
# ============================================================================


class DataLoader:
    """JSON 입력 파일 로드"""

    def __init__(self, input_dir: str):
        self.input_dir = input_dir
        self.horizon_start: datetime = None

    def load_all(self) -> Dict:
        """모든 입력 데이터 로드"""
        data = {}

        # 요청 메타데이터
        with open(f"{self.input_dir}/00_scheduling_request.json", "r", encoding="utf-8") as f:
            request = json.load(f)
            self.horizon_start = datetime.fromisoformat(
                request["scheduling_request"]["scheduling_horizon"]["start"]
            )
            data["request"] = request

        # 작업지시서
        with open(f"{self.input_dir}/01_work_orders.json", "r", encoding="utf-8") as f:
            data["work_orders"] = self._parse_work_orders(json.load(f))

        # 장비
        with open(f"{self.input_dir}/02_machines.json", "r", encoding="utf-8") as f:
            data["machines"] = self._parse_machines(json.load(f))

        # 장비 유형 파라미터
        with open(f"{self.input_dir}/03_machine_type_params.json", "r", encoding="utf-8") as f:
            data["machine_type_params"] = self._parse_machine_type_params(json.load(f))

        # 셀 레이아웃
        with open(f"{self.input_dir}/05_cell_layout.json", "r", encoding="utf-8") as f:
            data["cell_layout"] = json.load(f).get("cell_layout", {})

        # 제약조건
        with open(f"{self.input_dir}/06_constraints.json", "r", encoding="utf-8") as f:
            data["constraints"] = json.load(f).get("constraints", {})

        return data

    def _parse_work_orders(self, raw: Dict) -> List[WorkOrder]:
        """작업지시서 파싱 (MES v5 - Job 계층 제거, operations 직접 포함)"""
        work_orders = []
        for wo_raw in raw["work_orders"]:
            operations = []

            # MES v5: operations directly in work order
            if "operations" in wo_raw:
                for op_raw in wo_raw["operations"]:
                    nc = op_raw["nc_code"]
                    nc_code = NcCode(
                        program_id=nc["program_id"],
                        file_path=nc["file_path"],
                        cycle_time_sec=nc["cycle_time_sec"],
                        cycle_time_confidence=nc.get("cycle_time_confidence", 1.0),
                        tool_list=nc.get("tool_list", []),
                        tool_change_count=nc.get("tool_change_count", 0),
                        compatible_machines=nc.get("compatible_machines", []),
                    )
                    operations.append(
                        Operation(
                            op_id=op_raw["op_id"],
                            op_name=op_raw["op_name"],
                            sequence=op_raw["sequence"],
                            predecessors=op_raw.get("predecessors", []),
                            required_machines=[op_raw["required_machine_type"]],
                            setup_id=op_raw["setup_id"],
                            nc_code=nc_code,
                        )
                    )
            # Legacy support: jobs array (flatten to operations)
            elif "jobs" in wo_raw:
                for job_raw in wo_raw["jobs"]:
                    for op_raw in job_raw["operations"]:
                        nc = op_raw["nc_code"]
                        nc_code = NcCode(
                            program_id=nc["program_id"],
                            file_path=nc["file_path"],
                            cycle_time_sec=nc["cycle_time_sec"],
                            cycle_time_confidence=nc.get("cycle_time_confidence", 1.0),
                            tool_list=nc.get("tool_list", []),
                            tool_change_count=nc.get("tool_change_count", 0),
                            compatible_machines=nc.get("compatible_machines", []),
                        )
                        operations.append(
                            Operation(
                                op_id=op_raw["op_id"],
                                op_name=op_raw["op_name"],
                                sequence=op_raw["sequence"],
                                predecessors=op_raw.get("predecessors", []),
                                required_machines=[op_raw["required_machine_type"]],
                                setup_id=op_raw["setup_id"],
                                nc_code=nc_code,
                            )
                        )

            work_orders.append(
                WorkOrder(
                    wo_id=wo_raw["wo_id"],
                    product_id=wo_raw["product_id"],
                    product_name=wo_raw["product_name"],
                    order_quantity=wo_raw["order_quantity"],
                    due_date=datetime.fromisoformat(wo_raw["due_date"]),
                    priority=wo_raw["priority"],
                    release_date=datetime.fromisoformat(wo_raw["release_date"]),
                    customer=wo_raw["customer"],
                    operations=operations,
                )
            )
        return work_orders

    def _parse_machines(self, raw: Dict) -> List[Machine]:
        """장비 정보 파싱"""
        machines = []
        for m in raw["machines"]:
            machines.append(
                Machine(
                    machine_id=m["machine_id"],
                    machine_name=m["machine_name"],
                    machine_type=m["machine_type"],
                    status=m["status"],
                    available_from=datetime.fromisoformat(m["available_from"]),
                    current_setup_id=m.get("current_setup_id"),
                    setup_change_time_min=m["setup_change_time_min"],
                )
            )
        return machines

    def _parse_machine_type_params(self, raw: Dict) -> Dict[str, MachineTypeParams]:
        """장비 유형별 파라미터 파싱"""
        params = {}
        for machine_type, param in raw.get("machine_types", {}).items():
            params[machine_type] = MachineTypeParams(
                loading_type=param["loading_type"],
                amr_transport_qty=param.get("amr_transport_qty", 1),
                exchange_time_sec=param.get("exchange_time_sec", 0),
                load_unload_time_sec=param.get("load_unload_time_sec", 0),
            )
        return params


# ============================================================================
# Agent
# ============================================================================


class CellSchedulerAgent(BaseAgent):
    """
    Manufacturing Cell Scheduling Agent

    Schedules work orders across multiple machines with:
    - Multiple solver options (OR-Tools, GA, SA, Tabu Search)
    - Constraint satisfaction (precedence, machine type, setup time)
    - Makespan optimization
    - Machine utilization balancing
    - Feasibility analysis
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the cell scheduler agent

        Args:
            config: Configuration dictionary
        """
        super().__init__(name="cell-scheduler", config=config or {})
        self.solver = None

    def _parse_dict_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse dictionary input to internal format.

        Converts raw dictionary work_orders and machines to domain objects.

        Args:
            input_data: Raw dictionary input

        Returns:
            Parsed data dictionary with WorkOrder and Machine objects
        """
        data = {}

        # Copy request and other metadata
        data["request"] = input_data.get("request", {})
        data["machine_type_params"] = input_data.get("machine_type_params", {})
        data["constraints"] = input_data.get("constraints", {})

        # Parse work orders
        raw_work_orders = input_data.get("work_orders", [])
        if raw_work_orders:
            # Check if already parsed (WorkOrder objects)
            if hasattr(raw_work_orders[0], "wo_id"):
                data["work_orders"] = raw_work_orders
            else:
                # Parse from dictionary
                data["work_orders"] = self._parse_work_orders_from_dict(raw_work_orders)
        else:
            data["work_orders"] = []

        # Parse machines
        raw_machines = input_data.get("machines", [])
        if raw_machines:
            if hasattr(raw_machines[0], "machine_id"):
                data["machines"] = raw_machines
            else:
                data["machines"] = self._parse_machines_from_dict(raw_machines)
        else:
            data["machines"] = []

        return data

    def _parse_work_orders_from_dict(self, work_orders: List[Dict]) -> List["WorkOrder"]:
        """Parse work orders from dictionary list (MES v5 - Job 계층 제거)."""
        parsed = []
        for wo_raw in work_orders:
            operations = []

            # MES v5: operations directly in work order
            if "operations" in wo_raw:
                for op_raw in wo_raw.get("operations", []):
                    nc = op_raw.get("nc_code", {})
                    nc_code = NcCode(
                        program_id=nc.get("program_id", "UNKNOWN"),
                        file_path=nc.get("file_path", ""),
                        cycle_time_sec=nc.get("cycle_time_sec", 60),
                        cycle_time_confidence=nc.get("cycle_time_confidence", 1.0),
                        tool_list=nc.get("tool_list", []),
                        tool_change_count=nc.get("tool_change_count", 0),
                        compatible_machines=nc.get("compatible_machines", []),
                    )
                    operations.append(
                        Operation(
                            op_id=op_raw.get("op_id", f"OP-{len(operations) + 1}"),
                            op_name=op_raw.get("op_name", "Operation"),
                            sequence=op_raw.get("sequence", len(operations) + 1),
                            predecessors=op_raw.get("predecessors", []),
                            required_machines=[op_raw.get("required_machine_type", "CNC")],
                            setup_id=op_raw.get("setup_id", "DEFAULT"),
                            nc_code=nc_code,
                            cycle_time_sec=op_raw.get("cycle_time_sec"),
                        )
                    )
            # Legacy support: jobs array (flatten to operations)
            elif "jobs" in wo_raw:
                for job_raw in wo_raw.get("jobs", []):
                    for op_raw in job_raw.get("operations", []):
                        nc = op_raw.get("nc_code", {})
                        nc_code = NcCode(
                            program_id=nc.get("program_id", "UNKNOWN"),
                            file_path=nc.get("file_path", ""),
                            cycle_time_sec=nc.get("cycle_time_sec", 60),
                            cycle_time_confidence=nc.get("cycle_time_confidence", 1.0),
                            tool_list=nc.get("tool_list", []),
                            tool_change_count=nc.get("tool_change_count", 0),
                            compatible_machines=nc.get("compatible_machines", []),
                        )
                        operations.append(
                            Operation(
                                op_id=op_raw.get("op_id", f"OP-{len(operations) + 1}"),
                                op_name=op_raw.get("op_name", "Operation"),
                                sequence=op_raw.get("sequence", len(operations) + 1),
                                predecessors=op_raw.get("predecessors", []),
                                required_machines=[op_raw.get("required_machine_type", "CNC")],
                                setup_id=op_raw.get("setup_id", "DEFAULT"),
                                nc_code=nc_code,
                                cycle_time_sec=op_raw.get("cycle_time_sec"),
                            )
                        )

            parsed.append(
                WorkOrder(
                    wo_id=wo_raw.get("wo_id", f"WO-{len(parsed) + 1}"),
                    product_id=wo_raw.get("product_id", "PROD"),
                    product_name=wo_raw.get("product_name", "Product"),
                    order_quantity=wo_raw.get("order_quantity", 1),
                    release_date=datetime.fromisoformat(
                        wo_raw.get("release_date", datetime.now(timezone.utc).isoformat()).replace("Z", "")
                    ),
                    due_date=datetime.fromisoformat(
                        wo_raw.get("due_date", (datetime.now(timezone.utc)).isoformat()).replace("Z", "")
                    ),
                    priority=wo_raw.get("priority", 1),
                    customer=wo_raw.get("customer", "Unknown"),
                    operations=operations,
                )
            )
        return parsed

    def _parse_machines_from_dict(self, machines: List[Dict]) -> List["Machine"]:
        """Parse machines from dictionary list."""
        parsed = []
        for m in machines:
            available_from_str = m.get("available_from", datetime.now(timezone.utc).isoformat())
            if isinstance(available_from_str, str):
                available_from = datetime.fromisoformat(available_from_str.replace("Z", ""))
            else:
                available_from = available_from_str

            parsed.append(
                Machine(
                    machine_id=m.get("machine_id", f"M-{len(parsed) + 1}"),
                    machine_name=m.get("machine_name", "Machine"),
                    machine_type=m.get("machine_type", "CNC"),
                    status=m.get("status", "available"),
                    available_from=available_from,
                    current_setup_id=m.get("current_setup_id"),
                    setup_change_time_min=m.get("setup_change_time_min", 5),
                )
            )
        return parsed

    def process(
        self,
        input_data: Any,
        solver_type: str = "OR_TOOLS",
    ) -> Dict[str, Any]:
        """
        Process scheduling request

        Args:
            input_data: Can be either:
                - Path to scheduling_input directory
                - Dictionary with loaded data
            solver_type: Solver to use (OR_TOOLS, GA, SA, TABU)

        Returns:
            Dictionary with scheduling results
        """
        try:
            logger.info(f"Cell Scheduler Agent processing with {solver_type}...")

            # Load data if path provided
            if isinstance(input_data, str):
                loader = DataLoader(input_data)
                data = loader.load_all()
            else:
                # Dictionary input - need to parse work_orders and machines
                data = self._parse_dict_input(input_data)

            # Get solver type
            try:
                stype = SolverFactory.get_solver_type(solver_type)
            except ValueError:
                logger.warning(f"Unknown solver type {solver_type}, using OR_TOOLS")
                stype = SolverType.OR_TOOLS

            # Get solver config
            config = SolverFactory.get_default_config(stype)
            time_limit = (
                data.get("request", {})
                .get("scheduling_request", {})
                .get("options", {})
                .get("solver_time_limit_sec", config.time_limit_sec)
            )
            config.time_limit_sec = time_limit

            # Extract horizon
            request = data.get("request", {})
            horizon = request.get("scheduling_request", {}).get("scheduling_horizon", {})
            horizon_start = datetime.fromisoformat(horizon["start"])
            horizon_end = datetime.fromisoformat(horizon["end"])

            # Create solver
            self.solver = SolverFactory.create_solver(
                solver_type=stype,
                work_orders=data.get("work_orders", []),
                machines=data.get("machines", []),
                machine_type_params=data.get("machine_type_params", {}),
                horizon_start=horizon_start,
                horizon_end=horizon_end,
                constraints=data.get("constraints", {}),
                config=config,
            )

            # Solve
            result = self.solver.solve(time_limit_sec=time_limit)

            # Generate visualizations and analysis
            gantt_data = self.solver.generate_gantt_data()
            quality_metrics = self.solver.estimate_schedule_quality()

            output = {
                "status": result.status,
                "scheduled_tasks": [t.to_dict() for t in result.scheduled_tasks],
                "statistics": {
                    "total_tasks": len(result.scheduled_tasks),
                    "makespan_seconds": result.total_makespan,
                    "makespan_hours": round(result.total_makespan / 3600, 2),
                    "machine_utilization": result.machine_utilization,
                    "bottleneck_machines": result.bottleneck_machines,
                    "solve_time_sec": round(result.solve_time_sec, 3),
                    "objective_value": result.objective_value,
                },
                "quality_metrics": quality_metrics,
                "gantt_data": gantt_data,
                "solver_info": result.solver_info,
            }

            logger.info(f"Scheduling complete: {len(result.scheduled_tasks)} tasks scheduled")
            logger.info(f"   Solver: {stype.value}")
            logger.info(f"   Makespan: {round(result.total_makespan / 3600, 2)} hours")
            if result.machine_utilization:
                avg_util = sum(result.machine_utilization.values()) / len(
                    result.machine_utilization
                )
                logger.info(f"   Avg Utilization: {round(avg_util, 2)}%")

            return output

        except Exception as e:
            logger.error(f"Scheduling error: {e}", exc_info=True)
            return {"status": "error", "error": str(e), "scheduled_tasks": []}

    def get_available_solvers(self) -> List[Dict[str, Any]]:
        """Get list of available solvers"""
        return SolverFactory.get_available_solvers()

    def recommend_solver(
        self,
        num_operations: int,
        num_machines: int,
        time_available_sec: int = 60,
        need_optimal: bool = False,
    ) -> str:
        """
        Recommend a solver based on problem characteristics

        Args:
            num_operations: Number of operations to schedule
            num_machines: Number of machines available
            time_available_sec: Time available for solving
            need_optimal: Whether optimal solution is required

        Returns:
            Recommended solver type string
        """
        solver_type = SolverFactory.recommend_solver(
            num_operations=num_operations,
            num_machines=num_machines,
            time_available_sec=time_available_sec,
            need_optimal=need_optimal,
        )
        return solver_type.value
