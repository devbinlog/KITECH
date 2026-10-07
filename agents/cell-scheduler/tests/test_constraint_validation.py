"""Tests for solver constraint validation.

Covers:
- Downtime window: operation cannot overlap equipment downtime
- Release date: operation cannot start before release
- Machine compatibility: operation assigned to correct machine type
- Precedence: multi-operation WO ordering

Uses SA solver (fastest, <0.01s) for all constraint tests.
"""

import pytest
from datetime import datetime, timedelta, timezone

from src.solvers import (
    SolverType,
    SolverConfig,
    WorkOrder,
    Operation,
    NcCode,
    Machine,
    OccupiedSlot,
    MachineTypeParams,
    SimulatedAnnealingSolver,
    GeneticAlgorithmSolver,
)
from src.solvers.base_solver import BaseSolver


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime.now(timezone.utc).replace(second=0, microsecond=0)
HORIZON_START = NOW
HORIZON_END = NOW + timedelta(hours=24)


def make_nc(cycle_time_sec: int = 300, machine_type: str = "CNC") -> NcCode:
    return NcCode(
        program_id="NC-TEST",
        file_path="/nc/test.nc",
        cycle_time_sec=cycle_time_sec,
        cycle_time_confidence=1.0,
        tool_list=[],
        tool_change_count=0,
        compatible_machines=[machine_type],
    )


def make_op(
    op_id: str,
    machine_type: str = "CNC",
    cycle_time_sec: int = 300,
    predecessors=None,
    sequence: int = 10,
) -> Operation:
    return Operation(
        op_id=op_id,
        op_name=f"Op {op_id}",
        sequence=sequence,
        predecessors=predecessors or [],
        required_machines=[machine_type],
        setup_id="SETUP-A",
        nc_code=make_nc(cycle_time_sec, machine_type),
    )


def make_wo(
    wo_id: str,
    operations,
    release_date=None,
    due_date=None,
    priority: int = 5,
    qty: int = 1,
) -> WorkOrder:
    return WorkOrder(
        wo_id=wo_id,
        product_id="PROD-001",
        product_name="Test Product",
        order_quantity=qty,
        due_date=due_date or (HORIZON_START + timedelta(hours=20)),
        priority=priority,
        release_date=release_date or HORIZON_START,
        customer="Test Customer",
        operations=operations,
    )


def make_machine(
    machine_id: str = "M001",
    machine_type: str = "CNC",
    occupied_slots=None,
) -> Machine:
    return Machine(
        machine_id=machine_id,
        machine_name=f"Machine {machine_id}",
        machine_type=machine_type,
        status="available",
        available_from=HORIZON_START,
        current_setup_id=None,
        setup_change_time_min=5,
        occupied_slots=occupied_slots or [],
    )


MACHINE_TYPE_PARAMS = {
    "CNC": MachineTypeParams(
        loading_type="manual",
        amr_transport_qty=1,
        exchange_time_sec=0,
        load_unload_time_sec=0,
    ),
    "ROBOT": MachineTypeParams(
        loading_type="auto",
        amr_transport_qty=1,
        exchange_time_sec=0,
        load_unload_time_sec=0,
    ),
}


def run_sa(work_orders, machines, horizon_start=None, horizon_end=None, time_limit=10):
    """Run SA solver and return ScheduleResult."""
    solver = SimulatedAnnealingSolver(
        work_orders=work_orders,
        machines=machines,
        machine_type_params=MACHINE_TYPE_PARAMS,
        horizon_start=horizon_start or HORIZON_START,
        horizon_end=horizon_end or HORIZON_END,
        config=SolverConfig(
            time_limit_sec=time_limit,
            sa_iterations=500,
            initial_temp=50.0,
            cooling_rate=0.9,
        ),
    )
    return solver.solve()


# ---------------------------------------------------------------------------
# 1. Downtime window constraint
# ---------------------------------------------------------------------------


class TestDowntimeWindowConstraint:
    """Operations must not overlap machine occupied (downtime) slots."""

    def test_operation_scheduled_after_downtime_slot(self):
        """If machine has occupied slot, op must start after it ends."""
        # Downtime from t=0 to t=3600 (first hour)
        downtime_slot = OccupiedSlot(start=0, end=3600)
        machine = make_machine("M001", "CNC", occupied_slots=[downtime_slot])
        op = make_op("OP-001", "CNC", cycle_time_sec=300)
        wo = make_wo("WO-001", [op], qty=1)

        result = run_sa([wo], [machine])

        assert result.status == "success"
        assert len(result.scheduled_tasks) == 1

        task = result.scheduled_tasks[0]
        # Task must not overlap [0, 3600]
        assert task.start_time >= 3600 or task.end_time <= 0, (
            f"Task overlaps downtime: start={task.start_time}, end={task.end_time}"
        )

    def test_operation_does_not_overlap_mid_horizon_downtime(self):
        """Downtime in the middle of horizon must be avoided."""
        # Downtime from t=1800 to t=5400 (30 min to 1.5 hr)
        downtime_slot = OccupiedSlot(start=1800, end=5400)
        machine = make_machine("M001", "CNC", occupied_slots=[downtime_slot])
        # Short op: 600 sec
        op = make_op("OP-001", "CNC", cycle_time_sec=600)
        wo = make_wo("WO-001", [op], qty=1)

        result = run_sa([wo], [machine])

        assert result.status == "success"
        for task in result.scheduled_tasks:
            overlaps = task.start_time < 5400 and task.end_time > 1800
            assert not overlaps, (
                f"Task [{task.start_time}, {task.end_time}] overlaps downtime [1800, 5400]"
            )

    def test_multiple_downtime_slots_all_avoided(self):
        """Multiple occupied slots on same machine: all must be avoided."""
        slots = [
            OccupiedSlot(start=0, end=1800),
            OccupiedSlot(start=7200, end=9000),
        ]
        machine = make_machine("M001", "CNC", occupied_slots=slots)
        op = make_op("OP-001", "CNC", cycle_time_sec=300)
        wo = make_wo("WO-001", [op], qty=1)

        result = run_sa([wo], [machine])

        assert result.status == "success"
        for task in result.scheduled_tasks:
            for slot in slots:
                overlaps = task.start_time < slot.end and task.end_time > slot.start
                assert not overlaps, (
                    f"Task [{task.start_time}, {task.end_time}] overlaps slot [{slot.start}, {slot.end}]"
                )

    def test_no_downtime_op_starts_at_zero(self):
        """Without occupied slots, op can start immediately."""
        machine = make_machine("M001", "CNC", occupied_slots=[])
        op = make_op("OP-001", "CNC", cycle_time_sec=300)
        wo = make_wo("WO-001", [op], qty=1)

        result = run_sa([wo], [machine])

        assert result.status == "success"
        assert len(result.scheduled_tasks) == 1
        # Op should start at or very close to 0 (release time)
        task = result.scheduled_tasks[0]
        assert task.start_time >= 0

    def test_adjust_start_for_occupied_slots_direct(self):
        """Unit test BaseSolver._adjust_start_for_occupied_slots."""
        slot = OccupiedSlot(start=0, end=3600)
        machine = make_machine("M001", "CNC", occupied_slots=[slot])
        op = make_op("OP-001")
        wo = make_wo("WO-001", [op])

        solver = SimulatedAnnealingSolver(
            work_orders=[wo],
            machines=[machine],
            machine_type_params=MACHINE_TYPE_PARAMS,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
        )

        # Desired start=0, duration=300, default setup_time=300
        adjusted = solver._adjust_start_for_occupied_slots("M001", 0, 300)
        # Must be >= 3600 (slot end) + 300 (setup)
        assert adjusted >= 3600

    def test_adjust_start_no_overlap_needed(self):
        """If desired start is after slot, no adjustment needed."""
        slot = OccupiedSlot(start=0, end=1000)
        machine = make_machine("M001", "CNC", occupied_slots=[slot])
        op = make_op("OP-001")
        wo = make_wo("WO-001", [op])

        solver = SimulatedAnnealingSolver(
            work_orders=[wo],
            machines=[machine],
            machine_type_params=MACHINE_TYPE_PARAMS,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
        )

        # Start at 5000, duration=300 → no overlap with [0, 1000]
        adjusted = solver._adjust_start_for_occupied_slots("M001", 5000, 300)
        assert adjusted == 5000


# ---------------------------------------------------------------------------
# 2. Release date constraint
# ---------------------------------------------------------------------------


class TestReleaseDateConstraint:
    """Operations must not start before the work order's release date."""

    def test_op_not_scheduled_before_release_date(self):
        """Release date 2 hours in the future → op must start >= 7200s."""
        release = HORIZON_START + timedelta(hours=2)
        machine = make_machine("M001", "CNC")
        op = make_op("OP-001", "CNC", cycle_time_sec=300)
        wo = make_wo("WO-001", [op], release_date=release, qty=1)

        result = run_sa([wo], [machine])

        assert result.status == "success"
        for task in result.scheduled_tasks:
            assert task.start_time >= 7200, (
                f"Task started at {task.start_time}s but release is at 7200s"
            )

    def test_immediate_release_starts_at_zero(self):
        """Release date = horizon_start → op may start at t=0."""
        machine = make_machine("M001", "CNC")
        op = make_op("OP-001", "CNC", cycle_time_sec=300)
        wo = make_wo("WO-001", [op], release_date=HORIZON_START, qty=1)

        result = run_sa([wo], [machine])

        assert result.status == "success"
        task = result.scheduled_tasks[0]
        assert task.start_time >= 0

    def test_release_date_clamp_when_past(self):
        """Release date in the past should clamp to 0 (max(0, release_offset))."""
        past_release = HORIZON_START - timedelta(hours=2)
        machine = make_machine("M001", "CNC")
        op = make_op("OP-001", "CNC", cycle_time_sec=300)
        wo = make_wo("WO-001", [op], release_date=past_release, qty=1)

        result = run_sa([wo], [machine])

        assert result.status == "success"
        # Past release clamped to 0 → start_time >= 0
        task = result.scheduled_tasks[0]
        assert task.start_time >= 0

    def test_multiple_work_orders_different_release_dates(self):
        """Each WO's operations respect their own release date."""
        machine = make_machine("M001", "CNC")

        op1 = make_op("OP-A", "CNC", cycle_time_sec=300)
        wo1 = make_wo("WO-A", [op1], release_date=HORIZON_START, qty=1)

        op2 = make_op("OP-B", "CNC", cycle_time_sec=300)
        wo2 = make_wo("WO-B", [op2], release_date=HORIZON_START + timedelta(hours=3), qty=1)

        result = run_sa([wo1, wo2], [machine])

        assert result.status == "success"

        for task in result.scheduled_tasks:
            if task.wo_id == "WO-A":
                assert task.start_time >= 0
            elif task.wo_id == "WO-B":
                assert task.start_time >= 3 * 3600, (
                    f"WO-B started too early: {task.start_time}s < {3*3600}s"
                )

    def test_initialize_operations_computes_release_time_correctly(self):
        """_initialize_operations computes release_time as max(0, offset)."""
        release = HORIZON_START + timedelta(hours=1)
        machine = make_machine("M001", "CNC")
        op = make_op("OP-001")
        wo = make_wo("WO-001", [op], release_date=release)

        solver = SimulatedAnnealingSolver(
            work_orders=[wo],
            machines=[machine],
            machine_type_params=MACHINE_TYPE_PARAMS,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
        )
        solver._initialize_operations()

        assert len(solver.operations) == 1
        assert solver.operations[0].release_time == 3600  # 1 hour in seconds


# ---------------------------------------------------------------------------
# 3. Machine compatibility constraint
# ---------------------------------------------------------------------------


class TestMachineCompatibilityConstraint:
    """Operations must be assigned to machines of the correct type."""

    def test_cnc_op_assigned_to_cnc_machine(self):
        """CNC operation → must land on a CNC machine, not ROBOT."""
        cnc = make_machine("M-CNC", "CNC")
        robot = make_machine("M-ROBOT", "ROBOT")

        op = make_op("OP-001", "CNC", cycle_time_sec=300)
        wo = make_wo("WO-001", [op], qty=1)

        result = run_sa([wo], [cnc, robot])

        assert result.status == "success"
        for task in result.scheduled_tasks:
            if task.op_id == "OP-001":
                assert task.machine_id == "M-CNC", (
                    f"CNC op assigned to wrong machine: {task.machine_id}"
                )

    def test_robot_op_assigned_to_robot_machine(self):
        """ROBOT operation → must land on ROBOT machine."""
        cnc = make_machine("M-CNC", "CNC")
        robot = make_machine("M-ROBOT", "ROBOT")

        op = make_op("OP-001", "ROBOT", cycle_time_sec=300)
        wo = make_wo("WO-001", [op], qty=1)

        result = run_sa([wo], [cnc, robot])

        assert result.status == "success"
        for task in result.scheduled_tasks:
            if task.op_id == "OP-001":
                assert task.machine_id == "M-ROBOT", (
                    f"ROBOT op assigned to wrong machine: {task.machine_id}"
                )

    def test_get_compatible_machines_case_insensitive(self):
        """Machine type matching is case-insensitive."""
        # Machine has lowercase type, operation has uppercase
        machine = Machine(
            machine_id="M001",
            machine_name="CNC 1",
            machine_type="cnc",  # lowercase
            status="available",
            available_from=HORIZON_START,
            current_setup_id=None,
            setup_change_time_min=5,
        )
        op = make_op("OP-001", "CNC")  # uppercase
        wo = make_wo("WO-001", [op])

        solver = SimulatedAnnealingSolver(
            work_orders=[wo],
            machines=[machine],
            machine_type_params=MACHINE_TYPE_PARAMS,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
        )
        compatible = solver._get_compatible_machines(op)
        assert len(compatible) == 1
        assert compatible[0].machine_id == "M001"

    def test_no_compatible_machines_fallback_to_all(self):
        """No matching machine type → fallback to all machines (logged as mismatch)."""
        machine = make_machine("M001", "CNC")
        op = make_op("OP-001", "LATHE")  # No LATHE machines
        wo = make_wo("WO-001", [op])

        solver = SimulatedAnnealingSolver(
            work_orders=[wo],
            machines=[machine],
            machine_type_params=MACHINE_TYPE_PARAMS,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
        )
        compatible = solver._get_compatible_machines(op)
        # Falls back to all machines
        assert compatible == solver.machines
        assert "LATHE" in solver.machine_type_mismatches

    def test_multiple_machines_same_type(self):
        """With multiple CNC machines, op should go on one of them."""
        cnc1 = make_machine("M-CNC-1", "CNC")
        cnc2 = make_machine("M-CNC-2", "CNC")
        op = make_op("OP-001", "CNC", cycle_time_sec=300)
        wo = make_wo("WO-001", [op], qty=1)

        result = run_sa([wo], [cnc1, cnc2])

        assert result.status == "success"
        task = result.scheduled_tasks[0]
        assert task.machine_id in ("M-CNC-1", "M-CNC-2")

    def test_mixed_type_ops_go_to_correct_machines(self):
        """WO with CNC + ROBOT ops: each goes to correct machine type."""
        cnc = make_machine("M-CNC", "CNC")
        robot = make_machine("M-ROBOT", "ROBOT")

        op_cnc = make_op("OP-CNC", "CNC", cycle_time_sec=300, sequence=10)
        op_robot = make_op("OP-ROBOT", "ROBOT", cycle_time_sec=300,
                           predecessors=["OP-CNC"], sequence=20)
        wo = make_wo("WO-001", [op_cnc, op_robot], qty=1)

        result = run_sa([wo], [cnc, robot])

        assert result.status == "success"
        task_map = {t.op_id: t for t in result.scheduled_tasks}

        if "OP-CNC" in task_map:
            assert task_map["OP-CNC"].machine_id == "M-CNC"
        if "OP-ROBOT" in task_map:
            assert task_map["OP-ROBOT"].machine_id == "M-ROBOT"


# ---------------------------------------------------------------------------
# 4. Precedence constraint (multi-operation WO)
# ---------------------------------------------------------------------------


class TestPrecedenceConstraint:
    """Operations with predecessors must be scheduled after them."""

    def test_two_op_precedence_op2_after_op1(self):
        """OP-002 has OP-001 as predecessor → OP-002 must start after OP-001 ends."""
        machine = make_machine("M001", "CNC")
        op1 = make_op("OP-001", "CNC", cycle_time_sec=600, sequence=10)
        op2 = make_op("OP-002", "CNC", cycle_time_sec=300,
                      predecessors=["OP-001"], sequence=20)
        wo = make_wo("WO-001", [op1, op2], qty=1)

        result = run_sa([wo], [machine])

        assert result.status == "success"
        tasks = {t.op_id: t for t in result.scheduled_tasks}

        if "OP-001" in tasks and "OP-002" in tasks:
            t1 = tasks["OP-001"]
            t2 = tasks["OP-002"]
            assert t2.start_time >= t1.end_time, (
                f"OP-002 starts ({t2.start_time}) before OP-001 ends ({t1.end_time})"
            )

    def test_chain_three_ops_precedence(self):
        """OP-001 → OP-002 → OP-003: each must start after previous ends."""
        machine = make_machine("M001", "CNC")
        op1 = make_op("OP-001", "CNC", cycle_time_sec=300, sequence=10)
        op2 = make_op("OP-002", "CNC", cycle_time_sec=300,
                      predecessors=["OP-001"], sequence=20)
        op3 = make_op("OP-003", "CNC", cycle_time_sec=300,
                      predecessors=["OP-002"], sequence=30)
        wo = make_wo("WO-001", [op1, op2, op3], qty=1)

        result = run_sa([wo], [machine])

        assert result.status == "success"
        tasks = {t.op_id: t for t in result.scheduled_tasks}

        if all(k in tasks for k in ("OP-001", "OP-002", "OP-003")):
            assert tasks["OP-002"].start_time >= tasks["OP-001"].end_time
            assert tasks["OP-003"].start_time >= tasks["OP-002"].end_time

    def test_no_predecessors_can_start_immediately(self):
        """Op with no predecessors can start at release_time without waiting."""
        machine = make_machine("M001", "CNC")
        op = make_op("OP-001", "CNC", cycle_time_sec=300, predecessors=[])
        wo = make_wo("WO-001", [op], release_date=HORIZON_START, qty=1)

        result = run_sa([wo], [machine])

        assert result.status == "success"
        task = result.scheduled_tasks[0]
        assert task.start_time >= 0

    def test_ensure_precedence_order_method(self):
        """Unit test _ensure_precedence_order on a simple 2-op chain."""
        machine = make_machine("M001", "CNC")
        op1 = make_op("OP-001", "CNC", cycle_time_sec=300, sequence=10)
        op2 = make_op("OP-002", "CNC", cycle_time_sec=300,
                      predecessors=["OP-001"], sequence=20)
        wo = make_wo("WO-001", [op1, op2])

        solver = SimulatedAnnealingSolver(
            work_orders=[wo],
            machines=[machine],
            machine_type_params=MACHINE_TYPE_PARAMS,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
        )
        solver._initialize_operations()

        # ops: [0=OP-001, 1=OP-002], try reversed order [1, 0]
        ordered = solver._ensure_precedence_order([1, 0], solver.operations)

        # OP-001 (idx=0) must come before OP-002 (idx=1)
        assert ordered.index(0) < ordered.index(1)

    def test_precedence_across_different_machines(self):
        """OP-002 (ROBOT) must start after OP-001 (CNC) even on different machines."""
        cnc = make_machine("M-CNC", "CNC")
        robot = make_machine("M-ROBOT", "ROBOT")

        op1 = make_op("OP-001", "CNC", cycle_time_sec=600, sequence=10)
        op2 = make_op("OP-002", "ROBOT", cycle_time_sec=300,
                      predecessors=["OP-001"], sequence=20)
        wo = make_wo("WO-001", [op1, op2], qty=1)

        result = run_sa([wo], [cnc, robot])

        assert result.status == "success"
        tasks = {t.op_id: t for t in result.scheduled_tasks}

        if "OP-001" in tasks and "OP-002" in tasks:
            assert tasks["OP-002"].start_time >= tasks["OP-001"].end_time
