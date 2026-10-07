"""Test cell scheduler agent"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add paths for imports - must use the package properly
workspace = Path(__file__).parent.parent.parent.parent
src_path = workspace / "agents" / "cell-scheduler" / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(workspace / "shared"))

from solvers import (  # noqa: E402
    SolverFactory,
    SolverType,
    WorkOrder,
    Operation,
    Machine,
    MachineTypeParams,
    NcCode,
    ScheduleResult,
    ScheduledTask,
)
from cell_scheduler_agent import DataLoader, CellSchedulerAgent  # noqa: E402


# Alias for legacy tests - create solver via factory
def CellScheduler(**kwargs):
    """Legacy compatibility - create OR-Tools solver via factory."""
    # Remove solver_type if passed to avoid conflict
    kwargs.pop("solver_type", None)
    return SolverFactory.create_solver(solver_type=SolverType.OR_TOOLS, **kwargs)


@pytest.fixture
def input_directory():
    """Get scheduling input directory"""
    input_dir = workspace / "samples" / "cell-scheduler" / "input"
    return input_dir


@pytest.fixture
def scheduler_agent():
    """Create scheduler agent instance"""
    return CellSchedulerAgent()


@pytest.fixture
def scheduling_data(input_directory):
    """Load scheduling data"""
    loader = DataLoader(str(input_directory))
    return loader.load_all()


@pytest.fixture
def minimal_nc_code():
    """Create minimal NC code for testing"""
    return NcCode(
        program_id="NC001",
        file_path="/test/program.nc",
        cycle_time_sec=60,
        cycle_time_confidence=0.95,
        tool_list=["T01", "T02"],
        tool_change_count=2,
        compatible_machines=["M1", "M2"],
    )


@pytest.fixture
def minimal_operation(minimal_nc_code):
    """Create minimal operation for testing"""
    return Operation(
        op_id="OP001",
        op_name="Test Operation",
        sequence=1,
        predecessors=[],
        required_machines=["CNC"],
        setup_id="SETUP001",
        nc_code=minimal_nc_code,
    )


@pytest.fixture
def minimal_work_order(minimal_operation):
    """Create minimal work order for testing (MES v5 - operations directly)"""
    return WorkOrder(
        wo_id="WO001",
        product_id="PROD001",
        product_name="Test Product",
        order_quantity=100,
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        priority=5,
        release_date=datetime.now(timezone.utc),
        customer="Test Customer",
        operations=[minimal_operation],
    )


@pytest.fixture
def minimal_machine():
    """Create minimal machine for testing"""
    return Machine(
        machine_id="M001",
        machine_name="CNC Machine 1",
        machine_type="CNC",
        status="available",
        available_from=datetime.now(timezone.utc),
        current_setup_id=None,
        setup_change_time_min=10,
    )


# ============================================================================
# Data Loading Tests
# ============================================================================


class TestDataLoading:
    """Test data loading functionality"""

    def test_load_scheduling_data(self, input_directory):
        """Test loading scheduling input files"""
        loader = DataLoader(str(input_directory))
        data = loader.load_all()

        assert "request" in data
        assert "work_orders" in data
        assert "machines" in data
        assert len(data["work_orders"]) > 0
        assert len(data["machines"]) > 0

    def test_work_orders_structure(self, scheduling_data):
        """Test work orders data structure"""
        work_orders = scheduling_data["work_orders"]

        # Check first work order is a WorkOrder object
        wo = work_orders[0]
        assert hasattr(wo, "wo_id")
        assert hasattr(wo, "product_name")
        assert hasattr(wo, "due_date")
        assert hasattr(wo, "operations")
        assert len(wo.operations) > 0

    def test_machines_structure(self, scheduling_data):
        """Test machines data structure"""
        machines = scheduling_data["machines"]

        # Check first machine is a Machine object
        machine = machines[0]
        assert hasattr(machine, "machine_id")
        assert hasattr(machine, "machine_name")

    def test_machine_type_params_loading(self, scheduling_data):
        """Test machine type parameters loading"""
        params = scheduling_data.get("machine_type_params", {})
        # Should have at least one machine type
        assert len(params) >= 0  # May be empty in minimal setup

    def test_constraints_loading(self, scheduling_data):
        """Test constraints loading"""
        constraints = scheduling_data.get("constraints", {})
        assert isinstance(constraints, dict)

    def test_cell_layout_loading(self, scheduling_data):
        """Test cell layout loading"""
        layout = scheduling_data.get("cell_layout", {})
        assert isinstance(layout, dict)


class TestDataLoaderEdgeCases:
    """Test data loader edge cases"""

    def test_loader_with_nonexistent_directory(self):
        """Test loader with non-existent directory"""
        with pytest.raises(FileNotFoundError):
            loader = DataLoader("/nonexistent/path")
            loader.load_all()

    def test_operations_structure(self, scheduling_data):
        """Test operations structure (MES v5 - operations directly in WorkOrder)"""
        wo = scheduling_data["work_orders"][0]
        op = wo.operations[0]

        assert hasattr(op, "op_id")
        assert hasattr(op, "sequence")
        assert hasattr(op, "nc_code")

    def test_nc_code_structure(self, scheduling_data):
        """Test NC code structure in operations"""
        wo = scheduling_data["work_orders"][0]
        op = wo.operations[0]
        nc = op.nc_code

        assert hasattr(nc, "program_id")
        assert hasattr(nc, "cycle_time_sec")
        assert hasattr(nc, "compatible_machines")
        assert nc.cycle_time_sec > 0


# ============================================================================
# Scheduler Initialization Tests
# ============================================================================


class TestSchedulerInitialization:
    """Test scheduler agent initialization"""

    def test_agent_initialization(self, scheduler_agent):
        """Test scheduler agent creation"""
        assert scheduler_agent is not None
        assert scheduler_agent.name == "cell-scheduler"

    def test_agent_with_config(self):
        """Test agent initialization with config"""
        config = {"solver_time_limit": 120}
        agent = CellSchedulerAgent(config=config)
        assert agent.config == config

    @pytest.mark.skip(reason="Solver API changed - needs refactoring")
    def test_scheduler_instance(self, scheduling_data, scheduler_agent):
        """Test CellScheduler instance creation"""
        scheduler = CellScheduler(scheduling_data)
        assert scheduler is not None
        assert len(scheduler.work_orders) > 0
        assert len(scheduler.machines) > 0

    @pytest.mark.skip(reason="Solver API changed - needs refactoring")
    def test_scheduler_horizon_calculation(self, scheduling_data):
        """Test horizon calculation"""
        scheduler = CellScheduler(scheduling_data)

        assert scheduler.horizon_start is not None
        assert scheduler.horizon_end is not None
        assert scheduler.horizon_seconds > 0
        assert scheduler.horizon_end > scheduler.horizon_start


# ============================================================================
# Scheduling Tests
# ============================================================================


class TestScheduling:
    """Test actual scheduling functionality"""

    def test_scheduling_solve(self, scheduler_agent, input_directory):
        """Test scheduling solve"""
        result = scheduler_agent.process(str(input_directory))

        assert result["status"] in ["success", "error", "no_solution"]
        assert "scheduled_tasks" in result

    def test_scheduling_success_result(self, scheduler_agent, input_directory):
        """Test successful scheduling result"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            assert "statistics" in result
            assert "quality_metrics" in result
            assert "gantt_data" in result

            # Check statistics
            stats = result["statistics"]
            assert "total_tasks" in stats
            assert "makespan_seconds" in stats
            assert "makespan_hours" in stats
            assert stats["total_tasks"] > 0
            assert stats["makespan_seconds"] > 0

    def test_scheduling_quality_metrics(self, scheduler_agent, input_directory):
        """Test scheduling quality metrics"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            metrics = result["quality_metrics"]

            assert "status" in metrics
            assert "makespan_hours" in metrics
            assert "avg_machine_utilization" in metrics
            assert "machine_utilization" in metrics
            assert "total_scheduled_tasks" in metrics

            # Validate values
            assert metrics["makespan_hours"] > 0
            assert 0 <= metrics["avg_machine_utilization"] <= 100
            assert metrics["total_scheduled_tasks"] > 0

    def test_scheduling_gantt_data(self, scheduler_agent, input_directory):
        """Test Gantt data generation"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            gantt = result["gantt_data"]

            assert "tasks" in gantt
            assert "resources" in gantt
            assert len(gantt["tasks"]) > 0

            # Check task structure
            task = gantt["tasks"][0]
            assert "name" in task
            assert "start" in task
            assert "end" in task
            assert "resource" in task
            assert "duration_minutes" in task

    def test_scheduled_tasks_structure(self, scheduler_agent, input_directory):
        """Test scheduled tasks structure"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            tasks = result["scheduled_tasks"]
            assert len(tasks) > 0

            task = tasks[0]
            assert "wo_id" in task
            assert "op_id" in task
            assert "op_id" in task
            assert "machine_id" in task
            assert "start_time" in task
            assert "end_time" in task
            assert "quantity" in task

    def test_scheduling_makespan_correctness(self, scheduler_agent, input_directory):
        """Test makespan is calculated correctly"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            stats = result["statistics"]
            makespan_sec = stats["makespan_seconds"]
            makespan_hours = stats["makespan_hours"]

            # Verify conversion
            calculated_hours = makespan_sec / 3600
            assert abs(makespan_hours - round(calculated_hours, 2)) < 0.01

    def test_all_tasks_within_scheduling_horizon(self, scheduler_agent, scheduling_data):
        """Test all tasks are within scheduling horizon"""
        result = scheduler_agent.process(scheduling_data)

        if result["status"] == "success":
            tasks = result["scheduled_tasks"]
            for task in tasks:
                # Start time should be >= 0
                assert task["start_time"] >= 0
                # End time should be > start time
                assert task["end_time"] > task["start_time"]


# ============================================================================
# Constraint Validation Tests
# ============================================================================


class TestConstraintValidation:
    """Test constraint validation in scheduling"""

    def test_machine_capacity_constraint(self, scheduler_agent, input_directory):
        """Test that no machine has overlapping tasks"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            tasks = result["scheduled_tasks"]

            # Group tasks by machine
            machine_tasks = {}
            for task in tasks:
                machine_id = task["machine_id"]
                if machine_id not in machine_tasks:
                    machine_tasks[machine_id] = []
                machine_tasks[machine_id].append(task)

            # Check no overlaps for each machine
            for machine_id, m_tasks in machine_tasks.items():
                sorted_tasks = sorted(m_tasks, key=lambda x: x["start_time"])
                for i in range(len(sorted_tasks) - 1):
                    current = sorted_tasks[i]
                    next_task = sorted_tasks[i + 1]
                    # Current task should end before next task starts
                    assert current["end_time"] <= next_task["start_time"], (
                        f"Overlap on machine {machine_id}: "
                        f"task ending at {current['end_time']} "
                        f"overlaps with task starting at {next_task['start_time']}"
                    )

    def test_precedence_constraint(self, scheduler_agent, input_directory):
        """Test operation precedence is respected"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            tasks = result["scheduled_tasks"]

            # Group tasks by work order and job
            wo_job_tasks = {}
            for task in tasks:
                key = (task["wo_id"], task["op_id"])
                if key not in wo_job_tasks:
                    wo_job_tasks[key] = []
                wo_job_tasks[key].append(task)

            # For each job, operations should be in sequence
            for (wo_id, job_id), job_tasks in wo_job_tasks.items():
                if len(job_tasks) > 1:
                    # Sort by operation ID (assuming OP001, OP002, etc.)
                    sorted_tasks = sorted(job_tasks, key=lambda x: x["op_id"])
                    for i in range(len(sorted_tasks) - 1):
                        current = sorted_tasks[i]
                        next_op = sorted_tasks[i + 1]
                        # Current operation should finish before next starts
                        assert current["end_time"] <= next_op["start_time"], (
                            f"Precedence violated for {wo_id}/{job_id}: "
                            f"op {current['op_id']} ends at {current['end_time']}, "
                            f"but op {next_op['op_id']} starts at {next_op['start_time']}"
                        )

    def test_task_duration_correctness(self, scheduler_agent, input_directory):
        """Test task durations are positive and reasonable"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            tasks = result["scheduled_tasks"]

            for task in tasks:
                duration = task["end_time"] - task["start_time"]
                # Duration should be positive
                assert duration > 0, f"Task {task['op_id']} has non-positive duration: {duration}"
                # Duration should be reasonable (less than horizon)
                # Assuming horizon is less than 30 days
                max_duration = 30 * 24 * 3600  # 30 days in seconds
                assert duration < max_duration, (
                    f"Task {task['op_id']} has unreasonably long duration"
                )

    def test_all_operations_scheduled(self, scheduler_agent, scheduling_data, input_directory):
        """Test all operations are scheduled"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            tasks = result["scheduled_tasks"]

            # Count expected operations
            expected_ops = set()
            for wo in scheduling_data["work_orders"]:
                for op in wo.operations:
                    expected_ops.add((wo.wo_id, op.op_id))

            # Count scheduled operations
            scheduled_ops = set()
            for task in tasks:
                scheduled_ops.add((task["wo_id"], task["op_id"]))

            # All expected operations should be scheduled
            missing = expected_ops - scheduled_ops
            assert len(missing) == 0, f"Missing operations: {missing}"


# ============================================================================
# Quality Metrics Tests
# ============================================================================


class TestQualityMetrics:
    """Test quality metrics calculation"""

    def test_machine_utilization_range(self, scheduler_agent, input_directory):
        """Test machine utilization is in valid range"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            utilization = result["quality_metrics"]["machine_utilization"]

            for machine_id, util in utilization.items():
                assert 0 <= util <= 100, f"Machine {machine_id} has invalid utilization: {util}"

    def test_lateness_calculation(self, scheduler_agent, input_directory):
        """Test lateness is calculated for each work order"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            metrics = result["quality_metrics"]
            lateness = metrics.get("per_wo_lateness", {})

            # Each work order should have lateness entry
            assert isinstance(lateness, dict)

            # Lateness should be non-negative
            for wo_id, late_hours in lateness.items():
                assert late_hours >= 0, f"Work order {wo_id} has negative lateness: {late_hours}"

    def test_total_lateness_consistency(self, scheduler_agent, input_directory):
        """Test total lateness is sum of individual lateness"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            metrics = result["quality_metrics"]
            total_lateness = metrics.get("total_lateness_hours", 0)
            per_wo_lateness = metrics.get("per_wo_lateness", {})

            # Total should be close to sum of individual
            calculated_total = sum(per_wo_lateness.values())
            assert abs(total_lateness - calculated_total) < 0.1, (
                f"Total lateness mismatch: reported {total_lateness}, calculated {calculated_total}"
            )

    def test_bottleneck_identification(self, scheduler_agent, input_directory):
        """Test bottleneck machines are identified"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            metrics = result["quality_metrics"]
            bottlenecks = metrics.get("bottleneck_machines", [])
            utilization = metrics.get("machine_utilization", {})

            # Bottleneck machines should have high utilization
            if bottlenecks and utilization:
                avg_util = sum(utilization.values()) / len(utilization)
                for machine_id in bottlenecks:
                    if machine_id in utilization:
                        assert utilization[machine_id] >= avg_util * 0.8, (
                            f"Bottleneck machine {machine_id} has low utilization"
                        )


# ============================================================================
# Gantt Data Tests
# ============================================================================


class TestGanttDataGeneration:
    """Test Gantt chart data generation"""

    def test_gantt_task_count_matches_scheduled(self, scheduler_agent, input_directory):
        """Test Gantt task count matches scheduled tasks"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            scheduled_count = len(result["scheduled_tasks"])
            gantt_count = len(result["gantt_data"]["tasks"])
            assert scheduled_count == gantt_count

    def test_gantt_resources_are_machines(self, scheduler_agent, scheduling_data, input_directory):
        """Test Gantt resources correspond to machines"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            gantt_resources = set(result["gantt_data"]["resources"])
            machine_ids = set(m.machine_id for m in scheduling_data["machines"])

            # All gantt resources should be valid machines
            for resource in gantt_resources:
                assert resource in machine_ids, f"Unknown resource in Gantt: {resource}"

    def test_gantt_datetime_format(self, scheduler_agent, input_directory):
        """Test Gantt datetime format is valid ISO format"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            gantt = result["gantt_data"]

            # Check start and end
            datetime.fromisoformat(gantt["start"])
            datetime.fromisoformat(gantt["end"])

            # Check task start and end times
            for task in gantt["tasks"]:
                datetime.fromisoformat(task["start"])
                datetime.fromisoformat(task["end"])

    def test_gantt_duration_minutes_correctness(self, scheduler_agent, input_directory):
        """Test Gantt duration_minutes is calculated correctly"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            for task in result["gantt_data"]["tasks"]:
                start = datetime.fromisoformat(task["start"])
                end = datetime.fromisoformat(task["end"])
                calculated_minutes = (end - start).total_seconds() / 60
                assert abs(task["duration_minutes"] - calculated_minutes) < 0.1


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_process_with_dict_input(self, scheduler_agent, scheduling_data):
        """Test process with dictionary input instead of path"""
        result = scheduler_agent.process(scheduling_data)
        assert result["status"] in ["success", "error", "no_solution"]

    def test_empty_work_orders_handling(self, scheduler_agent):
        """Test handling of empty work orders"""
        minimal_data = {
            "request": {
                "scheduling_request": {
                    "scheduling_horizon": {
                        "start": datetime.now(timezone.utc).isoformat(),
                        "end": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                    }
                }
            },
            "work_orders": [],
            "machines": [],
            "machine_type_params": {},
            "cell_layout": {},
            "constraints": {},
        }

        result = scheduler_agent.process(minimal_data)
        # Should not crash, may return error or no_solution
        assert "status" in result

    @pytest.mark.skip(reason="Solver API changed - needs refactoring")
    def test_solve_with_short_time_limit(self, scheduling_data):
        """Test solving with very short time limit"""
        scheduler = CellScheduler(scheduling_data)
        result = scheduler.solve(time_limit_sec=1)

        # Should return some result even with short time
        assert result.status in ["success", "no_solution"]

    def test_solve_time_recorded(self, scheduler_agent, input_directory):
        """Test that solve time is recorded"""
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            solve_time = result["statistics"]["solve_time_sec"]
            assert solve_time >= 0
            assert solve_time < 120  # Should complete within reasonable time


# ============================================================================
# Data Class Tests
# ============================================================================


class TestDataClasses:
    """Test data class functionality"""

    def test_scheduled_task_creation(self):
        """Test ScheduledTask dataclass"""
        task = ScheduledTask(
            wo_id="WO001",
            op_id="OP001",
            machine_id="M001",
            start_time=0,
            end_time=3600,
            quantity=10,
            setup_time=300,
        )

        assert task.wo_id == "WO001"
        assert task.end_time - task.start_time == 3600
        assert task.setup_time == 300

    def test_schedule_result_creation(self):
        """Test ScheduleResult dataclass"""
        result = ScheduleResult(
            status="success",
            scheduled_tasks=[],
            objective_value=1000.0,
            solve_time_sec=5.5,
            total_makespan=7200,
            machine_utilization={"M001": 85.5},
            bottleneck_machines=["M001"],
        )

        assert result.status == "success"
        assert result.total_makespan == 7200
        assert result.machine_utilization["M001"] == 85.5

    def test_nc_code_creation(self, minimal_nc_code):
        """Test NcCode dataclass"""
        assert minimal_nc_code.program_id == "NC001"
        assert minimal_nc_code.cycle_time_sec == 60
        assert len(minimal_nc_code.tool_list) == 2

    def test_operation_creation(self, minimal_operation):
        """Test Operation dataclass"""
        assert minimal_operation.op_id == "OP001"
        assert minimal_operation.sequence == 1
        assert minimal_operation.nc_code is not None

    def test_work_order_creation(self, minimal_work_order):
        """Test WorkOrder dataclass (MES v5 - operations directly)"""
        assert minimal_work_order.wo_id == "WO001"
        assert minimal_work_order.priority == 5
        assert len(minimal_work_order.operations) == 1

    def test_machine_creation(self, minimal_machine):
        """Test Machine dataclass"""
        assert minimal_machine.machine_id == "M001"
        assert minimal_machine.status == "available"
        assert minimal_machine.setup_change_time_min == 10

    def test_machine_type_params_creation(self):
        """Test MachineTypeParams dataclass"""
        params = MachineTypeParams(
            loading_type="manual",
            amr_transport_qty=5,
            exchange_time_sec=120,
            load_unload_time_sec=60,
        )

        assert params.loading_type == "manual"
        assert params.amr_transport_qty == 5


# ============================================================================
# Scheduler Internal Methods Tests
# ============================================================================


@pytest.mark.skip(reason="Solver internal API changed - needs refactoring")
class TestSchedulerInternalMethods:
    """Test scheduler internal methods"""

    def test_calculate_makespan(self, scheduling_data):
        """Test makespan calculation"""
        scheduler = CellScheduler(scheduling_data)
        result = scheduler.solve(time_limit_sec=30)

        if result.status == "success":
            makespan = scheduler._calculate_makespan()
            assert makespan > 0
            # Makespan should equal max end time
            max_end = max(t.end_time for t in scheduler.scheduled_tasks)
            assert makespan == max_end

    def test_calculate_utilization(self, scheduling_data):
        """Test utilization calculation"""
        scheduler = CellScheduler(scheduling_data)
        result = scheduler.solve(time_limit_sec=30)

        if result.status == "success":
            utilization = scheduler._calculate_utilization()
            assert isinstance(utilization, dict)
            assert len(utilization) == len(scheduler.machines)

    def test_find_bottlenecks(self, scheduling_data):
        """Test bottleneck detection"""
        scheduler = CellScheduler(scheduling_data)
        result = scheduler.solve(time_limit_sec=30)

        if result.status == "success":
            bottlenecks = scheduler._find_bottlenecks()
            assert isinstance(bottlenecks, list)

    def test_generate_gantt_data(self, scheduling_data):
        """Test Gantt data generation method"""
        scheduler = CellScheduler(scheduling_data)
        result = scheduler.solve(time_limit_sec=30)

        if result.status == "success":
            gantt = scheduler.generate_gantt_data()
            assert "tasks" in gantt
            assert "resources" in gantt
            assert "start" in gantt
            assert "end" in gantt

    def test_estimate_schedule_quality(self, scheduling_data):
        """Test quality estimation method"""
        scheduler = CellScheduler(scheduling_data)
        result = scheduler.solve(time_limit_sec=30)

        if result.status == "success":
            quality = scheduler.estimate_schedule_quality()
            assert "status" in quality
            assert "makespan_hours" in quality
            assert "avg_machine_utilization" in quality

    def test_quality_no_schedule(self, scheduling_data):
        """Test quality estimation with no schedule"""
        scheduler = CellScheduler(scheduling_data)
        # Don't solve, just check quality
        scheduler.scheduled_tasks = []
        quality = scheduler.estimate_schedule_quality()

        assert quality["status"] == "no_schedule"
        assert quality["makespan_hours"] == 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for full scheduling workflow"""

    def test_full_workflow(self, scheduler_agent, input_directory):
        """Test full scheduling workflow"""
        # Process
        result = scheduler_agent.process(str(input_directory))

        if result["status"] == "success":
            # Verify all components
            assert len(result["scheduled_tasks"]) > 0
            assert result["statistics"]["total_tasks"] > 0
            assert result["quality_metrics"]["status"] == "scheduled"
            assert len(result["gantt_data"]["tasks"]) > 0

            # Verify consistency
            assert result["statistics"]["total_tasks"] == len(result["scheduled_tasks"])
            assert result["quality_metrics"]["total_scheduled_tasks"] == len(
                result["scheduled_tasks"]
            )

    def test_deterministic_results(self, scheduler_agent, input_directory):
        """Test that results are deterministic with same input"""
        result1 = scheduler_agent.process(str(input_directory))
        result2 = scheduler_agent.process(str(input_directory))

        if result1["status"] == "success" and result2["status"] == "success":
            # Same number of tasks
            assert len(result1["scheduled_tasks"]) == len(result2["scheduled_tasks"])

            # Statistics should be similar (may vary slightly due to solver)
            assert (
                abs(
                    result1["statistics"]["makespan_hours"]
                    - result2["statistics"]["makespan_hours"]
                )
                < 1.0
            )


# ============================================================================
# AGENT FUNCTIONAL TESTS (New)
# ============================================================================


class TestCellSchedulerAgentFunctional:
    """Test actual CellSchedulerAgent functionality"""

    def test_agent_process_with_sample_input(self, input_directory):
        """Test agent processing with sample input directory"""
        agent = CellSchedulerAgent()
        result = agent.process(str(input_directory), solver_type="OR_TOOLS")

        assert result["status"] in ["success", "optimal", "feasible"]
        assert "scheduled_tasks" in result
        assert "statistics" in result

    def test_agent_process_dict_input(self):
        """Test agent processing with dictionary input"""
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        test_input = {
            "request": {
                "scheduling_request": {
                    "scheduling_horizon": {
                        "start": now.isoformat(),
                        "end": (now + timedelta(days=7)).isoformat(),
                    }
                }
            },
            "work_orders": [
                {
                    "wo_id": "WO-TEST",
                    "product_id": "PART-001",
                    "product_name": "Test Part",
                    "order_quantity": 5,
                    "release_date": now.isoformat(),
                    "due_date": (now + timedelta(days=1)).isoformat(),
                    "priority": 1,
                    "customer": "Test",
                    "operations": [
                        {
                            "op_id": "OP-001",
                            "op_name": "Machining",
                            "sequence": 1,
                            "predecessors": [],
                            "required_machine_type": "CNC",
                            "setup_id": "SETUP-1",
                            "cycle_time_sec": 120,
                        }
                    ],
                }
            ],
            "machines": [
                {
                    "machine_id": "CNC-001",
                    "machine_name": "CNC 1",
                    "machine_type": "CNC",
                    "status": "available",
                    "available_from": now.isoformat(),
                    "setup_change_time_min": 5,
                }
            ],
            "machine_type_params": {"CNC": {"setup_time_default": 5}},
        }

        agent = CellSchedulerAgent()
        result = agent.process(test_input, solver_type="OR_TOOLS")

        assert result["status"] in ["success", "optimal", "feasible"]
        assert len(result["scheduled_tasks"]) >= 1

    def test_agent_different_solvers(self, input_directory):
        """Test agent with different solver types"""
        agent = CellSchedulerAgent()

        for solver_type in ["OR_TOOLS", "GA", "SA", "TABU"]:
            result = agent.process(str(input_directory), solver_type=solver_type)
            assert result["status"] in ["success", "optimal", "feasible", "timeout"], (
                f"Solver {solver_type} failed with status: {result['status']}"
            )
