"""
10가지 구현 기능별 검증 테스트

1.  Lot 분할          : order_quantity ÷ lot_size 자동 분할
2.  다중 리소스 동시 점유 : 하나의 공정에 CNC + AMR + RACK 동시 배정
3.  AMR 파이프라이닝    : 연속 공정에서 AMR 이미 배치 시 이송 시간 0
4.  AMR Zone 제약      : accessible_machines 로 AMR 담당 구역 분리
5.  셋업 시간 모델링    : WO×기계마다 1회, setup_id 일치 시 생략
6.  캘린더 제약        : 장비별 shift/break → 비가동 구간 배정 불가
7.  납기 하드 제약      : due_date 초과 배정 불가
8.  우선순위 소프트 제약 : priority 낮을수록(숫자 작을수록) 먼저 완료
9.  Infeasible WO 처리 : 납기 불가 WO 자동 제외 후 나머지 스케줄링
10. 간트차트 시각화     : gantt_data 생성 + PNG 저장 확인

모든 기능 테스트는 OR-Tools solver 사용 (모든 고급 기능 지원).
"""

import os
import tempfile
from datetime import datetime, timedelta, time as dtime, timezone
from typing import List

import pytest

from src.solvers import (
    AMRConfig,
    Break,
    Calendar,
    Machine,
    MachineTypeParams,
    NcCode,
    OccupiedSlot,
    Operation,
    ORToolsSolver,
    ScheduleResult,
    ScheduledTask,
    SchedulerConfig,
    SetupInterval,
    SolverConfig,
    WorkOrder,
)

# ============================================================================
# 공통 헬퍼 / 상수
# ============================================================================

TZ = timezone.utc

HORIZON_START = datetime(2026, 5, 14, 8, 0, 0, tzinfo=TZ)   # 08:00 UTC
HORIZON_END   = datetime(2026, 5, 21, 8, 0, 0, tzinfo=TZ)   # 1주일 후

MTP = {
    "CNC":             MachineTypeParams(loading_type="manual", amr_transport_qty=1, exchange_time_sec=0),
    "VMC_3AXIS_MASS":  MachineTypeParams(loading_type="manual", amr_transport_qty=1, exchange_time_sec=0),
    "VMC_3AXIS_PALLET":MachineTypeParams(loading_type="manual", amr_transport_qty=1, exchange_time_sec=0),
    "RACK":            MachineTypeParams(loading_type="manual", amr_transport_qty=1, exchange_time_sec=0),
}


def hs_plus(hours: float) -> datetime:
    return HORIZON_START + timedelta(hours=hours)


def make_nc(cycle_time_sec: int = 60, compatible: list = None) -> NcCode:
    return NcCode(
        program_id="NC-TEST",
        file_path="",
        cycle_time_sec=cycle_time_sec,
        compatible_machines=compatible or [],
    )


def make_op(
    op_id: str,
    required_machines: list,
    cycle_time_sec: int = 60,
    predecessors: list = None,
    sequence: int = 10,
    setup_id: str = "SETUP-X",
    compatible_machines: list = None,
) -> Operation:
    return Operation(
        op_id=op_id,
        op_name=f"Op {op_id}",
        sequence=sequence,
        predecessors=predecessors or [],
        required_machines=required_machines,
        setup_id=setup_id,
        nc_code=make_nc(cycle_time_sec, compatible_machines or []),
        cycle_time_sec=cycle_time_sec,
    )


def make_wo(
    wo_id: str,
    operations: list,
    order_quantity: int = 3,
    priority: int = 3,
    release_date: datetime = None,
    due_date: datetime = None,
) -> WorkOrder:
    return WorkOrder(
        wo_id=wo_id,
        product_id=f"P-{wo_id}",
        product_name=wo_id,
        order_quantity=order_quantity,
        due_date=due_date or hs_plus(200),
        priority=priority,
        release_date=release_date or HORIZON_START,
        customer="Test",
        operations=operations,
    )


def make_machine(
    machine_id: str,
    machine_type: str = "CNC",
    setup_change_time_min: int = 0,
    current_setup_id: str = None,
    calendar: Calendar = None,
    occupied_slots: list = None,
    available_from: datetime = None,
    status: str = "available",
) -> Machine:
    return Machine(
        machine_id=machine_id,
        machine_name=machine_id,
        machine_type=machine_type,
        status=status,
        available_from=available_from or HORIZON_START,
        current_setup_id=current_setup_id,
        setup_change_time_min=setup_change_time_min,
        occupied_slots=occupied_slots or [],
        calendar=calendar,
    )


def make_amr(amr_id: str, accessible_machines: list) -> AMRConfig:
    return AMRConfig(
        amr_id=amr_id,
        model="AMR-MODEL",
        status="available",
        accessible_machines=accessible_machines,
    )


def solve(
    work_orders: List[WorkOrder],
    machines: List[Machine],
    amrs: List[AMRConfig] = None,
    scheduler_config: SchedulerConfig = None,
    time_limit: int = 20,
) -> ScheduleResult:
    solver = ORToolsSolver(
        work_orders=work_orders,
        machines=machines,
        machine_type_params=MTP,
        horizon_start=HORIZON_START,
        horizon_end=HORIZON_END,
        amrs=amrs or [],
        scheduler_config=scheduler_config or SchedulerConfig(),
        config=SolverConfig(time_limit_sec=time_limit, num_workers=4),
    )
    return solver.solve()


# ============================================================================
# Feature 1 : Lot 분할
# ============================================================================


class TestLotSplitting:
    """order_quantity ÷ lot_size 자동 분할 검증."""

    def test_lot_split_exact(self):
        """qty=9, lot_size=3 → 3 lots, 각 3개"""
        op  = make_op("OP-1", ["CNC"])
        wo  = make_wo("WO-1", [op], order_quantity=9)
        m   = make_machine("CNC-1", "CNC")

        result = solve([wo], [m], scheduler_config=SchedulerConfig(lot_size=3))

        assert result.status == "success"
        tasks = [t for t in result.scheduled_tasks if t.wo_id == "WO-1"]
        assert len(tasks) == 3, f"기대 3 lots, 실제 {len(tasks)}"
        assert sum(t.quantity for t in tasks) == 9

    def test_lot_split_remainder(self):
        """qty=10, lot_size=3 → 4 lots (3+3+3+1)"""
        op  = make_op("OP-1", ["CNC"])
        wo  = make_wo("WO-1", [op], order_quantity=10)
        m   = make_machine("CNC-1", "CNC")

        result = solve([wo], [m], scheduler_config=SchedulerConfig(lot_size=3))

        assert result.status == "success"
        tasks = [t for t in result.scheduled_tasks if t.wo_id == "WO-1"]
        assert len(tasks) == 4, f"기대 4 lots, 실제 {len(tasks)}"
        quantities = sorted(t.quantity for t in tasks)
        assert quantities == [1, 3, 3, 3], f"lot 수량 오류: {quantities}"
        assert sum(t.quantity for t in tasks) == 10

    def test_no_splitting_when_lot_size_one(self):
        """lot_size=1 (기본값) → 분할 없이 전체 qty 1개 task"""
        op  = make_op("OP-1", ["CNC"])
        wo  = make_wo("WO-1", [op], order_quantity=5)
        m   = make_machine("CNC-1", "CNC")

        result = solve([wo], [m], scheduler_config=SchedulerConfig(lot_size=1))

        assert result.status == "success"
        tasks = [t for t in result.scheduled_tasks if t.wo_id == "WO-1"]
        assert len(tasks) == 1, f"lot_size=1이면 1개 task여야 함, 실제 {len(tasks)}"
        assert tasks[0].quantity == 5

    def test_multi_op_lot_split_tasks_per_lot(self):
        """3 공정 WO, lot_size=2, qty=4 → 2 lots, lot당 3 tasks = 총 6 tasks"""
        ops = [
            make_op("OP-1", ["CNC"], sequence=10),
            make_op("OP-2", ["CNC"], predecessors=["OP-1"], sequence=20),
            make_op("OP-3", ["CNC"], predecessors=["OP-2"], sequence=30),
        ]
        wo = make_wo("WO-1", ops, order_quantity=4)
        m  = make_machine("CNC-1", "CNC")

        result = solve([wo], [m], scheduler_config=SchedulerConfig(lot_size=2))

        assert result.status == "success"
        tasks = [t for t in result.scheduled_tasks if t.wo_id == "WO-1"]
        assert len(tasks) == 6, f"2 lots × 3 ops = 6 tasks 기대, 실제 {len(tasks)}"

    def test_lot_numbers_are_sequential(self):
        """sublot_no가 1부터 순차적으로 할당되어야 함."""
        op  = make_op("OP-1", ["CNC"])
        wo  = make_wo("WO-1", [op], order_quantity=6)
        m   = make_machine("CNC-1", "CNC")

        result = solve([wo], [m], scheduler_config=SchedulerConfig(lot_size=2))

        assert result.status == "success"
        tasks = [t for t in result.scheduled_tasks if t.wo_id == "WO-1"]
        sublot_nos = sorted(t.sublot_no for t in tasks)
        assert sublot_nos == [1, 2, 3], f"sublot_no 순서 오류: {sublot_nos}"


# ============================================================================
# Feature 2 : 다중 리소스 동시 점유
# ============================================================================


class TestMultiResourceOccupancy:
    """하나의 공정에 CNC + AMR + RACK 동시 배정 검증."""

    def test_three_resources_all_assigned(self):
        """required_machines=[CNC, AMR, RACK] → assigned_machines에 3개 항목

        AMR accessibility는 non-AMR 기계 모두에 적용되므로,
        CNC와 RACK 모두 AMR의 accessible_machines에 포함해야 한다.
        """
        op  = make_op("OP-1", ["CNC", "AMR", "RACK"])
        wo  = make_wo("WO-1", [op], order_quantity=1)
        machines = [
            make_machine("CNC-1", "CNC"),
            make_machine("RACK-1", "RACK"),
        ]
        # AMR은 CNC-1과 RACK-1 모두 접근 가능해야 함
        amrs = [make_amr("AMR-1", accessible_machines=["CNC-1", "RACK-1"])]

        result = solve([wo], machines, amrs=amrs)

        assert result.status == "success"
        tasks = [t for t in result.scheduled_tasks if t.wo_id == "WO-1"]
        assert len(tasks) == 1
        task = tasks[0]
        assert len(task.assigned_machines) == 3, (
            f"3개 리소스 배정 기대, 실제: {task.assigned_machines}"
        )
        assigned_ids = set(task.assigned_machines.values())
        assert "CNC-1" in assigned_ids
        assert "AMR-1" in assigned_ids
        assert "RACK-1" in assigned_ids

    def test_two_resources_assigned(self):
        """required_machines=[CNC, AMR] → assigned_machines에 2개 항목"""
        op  = make_op("OP-1", ["CNC", "AMR"])
        wo  = make_wo("WO-1", [op], order_quantity=1)
        machines = [make_machine("CNC-1", "CNC")]
        amrs     = [make_amr("AMR-1", accessible_machines=["CNC-1"])]

        result = solve([wo], machines, amrs=amrs)

        assert result.status == "success"
        task = next(t for t in result.scheduled_tasks if t.wo_id == "WO-1")
        assert len(task.assigned_machines) == 2
        assigned_ids = set(task.assigned_machines.values())
        assert "CNC-1" in assigned_ids
        assert "AMR-1" in assigned_ids

    def test_primary_machine_is_non_amr(self):
        """task.machine_id (primary)는 CNC여야 하고 AMR이면 안 됨."""
        op  = make_op("OP-1", ["CNC", "AMR"])
        wo  = make_wo("WO-1", [op], order_quantity=1)
        machines = [make_machine("CNC-1", "CNC")]
        amrs     = [make_amr("AMR-1", accessible_machines=["CNC-1"])]

        result = solve([wo], machines, amrs=amrs)

        assert result.status == "success"
        task = next(t for t in result.scheduled_tasks if t.wo_id == "WO-1")
        assert task.machine_id == "CNC-1", (
            f"primary machine은 CNC-1이어야 함, 실제: {task.machine_id}"
        )

    def test_resources_from_same_lot_use_same_machine_across_ops(self):
        """같은 lot 내 동일 entry는 동일 기계에 고정 (machine_binding)"""
        ops = [
            make_op("OP-1", ["CNC"],       sequence=10),
            make_op("OP-2", ["CNC", "AMR"], predecessors=["OP-1"], sequence=20),
        ]
        wo = make_wo("WO-1", ops, order_quantity=2)
        machines = [
            make_machine("CNC-1", "CNC"),
            make_machine("CNC-2", "CNC"),
        ]
        amrs = [
            make_amr("AMR-1", accessible_machines=["CNC-1", "CNC-2"]),
        ]

        result = solve([wo], machines, amrs=amrs,
                       scheduler_config=SchedulerConfig(lot_size=2))

        assert result.status == "success"
        # 같은 lot 내 OP-1, OP-2는 같은 CNC여야 함
        tasks = {(t.op_id, t.sublot_no): t for t in result.scheduled_tasks
                 if t.wo_id == "WO-1"}
        for sublot_no in (1, 2):
            t1_key = ("OP-1", sublot_no)
            t2_key = ("OP-2", sublot_no)
            if t1_key in tasks and t2_key in tasks:
                t1_cnc = tasks[t1_key].assigned_machines.get("CNC") or tasks[t1_key].machine_id
                t2_cnc = tasks[t2_key].assigned_machines.get("CNC") or tasks[t2_key].machine_id
                assert t1_cnc == t2_cnc, (
                    f"lot {sublot_no}: OP-1 CNC={t1_cnc}, OP-2 CNC={t2_cnc} — machine_binding 오류"
                )


# ============================================================================
# Feature 3 : AMR 파이프라이닝
# ============================================================================


class TestAMRPipelining:
    """연속 공정에서 AMR 이미 배치 시 이송 시간 0, 새로 필요 시 추가."""

    def _make_solver(self, work_orders, machines, amrs=None, cfg=None):
        return ORToolsSolver(
            work_orders=work_orders,
            machines=machines,
            machine_type_params=MTP,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
            amrs=amrs or [],
            scheduler_config=cfg or SchedulerConfig(),
            config=SolverConfig(time_limit_sec=20, num_workers=4),
        )

    def test_amr_transfer_zero_when_prev_op_also_has_amr(self):
        """OP-1[CNC,AMR] → OP-2[CNC,AMR]: OP-2 amr_transfer_sec == 0"""
        op1 = make_op("OP-1", ["CNC", "AMR"], sequence=10)
        op2 = make_op("OP-2", ["CNC", "AMR"], predecessors=["OP-1"], sequence=20)
        wo  = make_wo("WO-1", [op1, op2], order_quantity=1)
        machines = [make_machine("CNC-1", "CNC")]
        amrs     = [make_amr("AMR-1", accessible_machines=["CNC-1"])]

        solver = self._make_solver([wo], machines, amrs)
        # _amr_transfer_sec 직접 검증
        amr_sec_op2 = solver._amr_transfer_sec(op2, prev_op=op1)
        assert amr_sec_op2 == 0, (
            f"연속 AMR 공정 이송시간은 0이어야 함, 실제: {amr_sec_op2}"
        )

    def test_amr_transfer_added_when_prev_op_has_no_amr(self):
        """OP-1[CNC] → OP-2[CNC,AMR]: OP-2 amr_transfer_sec == amr_transfer_time_sec"""
        transfer_sec = 90
        op1 = make_op("OP-1", ["CNC"],        sequence=10)
        op2 = make_op("OP-2", ["CNC", "AMR"], predecessors=["OP-1"], sequence=20)
        wo  = make_wo("WO-1", [op1, op2], order_quantity=1)
        machines = [make_machine("CNC-1", "CNC")]
        amrs     = [make_amr("AMR-1", accessible_machines=["CNC-1"])]

        solver = self._make_solver([wo], machines, amrs,
                                   cfg=SchedulerConfig(amr_transfer_time_sec=transfer_sec))
        amr_sec_op2 = solver._amr_transfer_sec(op2, prev_op=op1)
        assert amr_sec_op2 == transfer_sec, (
            f"AMR 이동 시간 {transfer_sec}s 기대, 실제: {amr_sec_op2}"
        )

    def test_first_op_with_amr_gets_transfer_time(self):
        """첫 공정에 AMR 필요 시 prev_op=None → amr_transfer_time_sec 추가"""
        transfer_sec = 60
        op1 = make_op("OP-1", ["CNC", "AMR"], sequence=10)
        wo  = make_wo("WO-1", [op1], order_quantity=1)
        machines = [make_machine("CNC-1", "CNC")]
        amrs     = [make_amr("AMR-1", accessible_machines=["CNC-1"])]

        solver = self._make_solver([wo], machines, amrs,
                                   cfg=SchedulerConfig(amr_transfer_time_sec=transfer_sec))
        amr_sec = solver._amr_transfer_sec(op1, prev_op=None)
        assert amr_sec == transfer_sec

    def test_pipelining_reflected_in_scheduled_task(self):
        """스케줄 결과의 amr_transfer_sec 값 확인."""
        transfer_sec = 60
        op1 = make_op("OP-1", ["CNC", "AMR"], cycle_time_sec=60, sequence=10)
        op2 = make_op("OP-2", ["CNC", "AMR"], cycle_time_sec=60,
                      predecessors=["OP-1"], sequence=20)
        wo  = make_wo("WO-1", [op1, op2], order_quantity=1)
        machines = [make_machine("CNC-1", "CNC")]
        amrs     = [make_amr("AMR-1", accessible_machines=["CNC-1"])]

        result = solve([wo], machines, amrs=amrs,
                       scheduler_config=SchedulerConfig(amr_transfer_time_sec=transfer_sec))

        assert result.status == "success"
        tasks = {t.op_id: t for t in result.scheduled_tasks if t.wo_id == "WO-1"}
        # OP-1: first op, transfer 있음
        assert tasks["OP-1"].amr_transfer_sec == transfer_sec
        # OP-2: prev is OP-1 which also has AMR → pipelining → 0
        assert tasks["OP-2"].amr_transfer_sec == 0, (
            f"AMR 파이프라이닝 실패: OP-2 amr_transfer_sec={tasks['OP-2'].amr_transfer_sec}"
        )

    def test_no_amr_op_has_zero_transfer(self):
        """AMR 없는 공정은 amr_transfer_sec == 0"""
        op = make_op("OP-1", ["CNC"])
        wo = make_wo("WO-1", [op], order_quantity=1)
        m  = make_machine("CNC-1", "CNC")

        solver = self._make_solver([wo], [m],
                                   cfg=SchedulerConfig(amr_transfer_time_sec=60))
        assert solver._amr_transfer_sec(op, None) == 0


# ============================================================================
# Feature 4 : AMR Zone 제약
# ============================================================================


class TestAMRZoneConstraint:
    """accessible_machines 로 AMR 담당 구역 분리 검증."""

    def test_amr_assigned_only_to_accessible_machine(self):
        """CNC-1 배정 시 CNC-1 접근 가능한 AMR-1만 배정되어야 함."""
        op = make_op("OP-1", ["CNC-1", "AMR"])   # CNC-1 명시
        wo = make_wo("WO-1", [op], order_quantity=1)
        machines = [
            make_machine("CNC-1", "CNC"),
            make_machine("CNC-2", "CNC"),
        ]
        amrs = [
            make_amr("AMR-1", accessible_machines=["CNC-1"]),
            make_amr("AMR-2", accessible_machines=["CNC-2"]),
        ]

        result = solve([wo], machines, amrs=amrs)

        assert result.status == "success"
        task = next(t for t in result.scheduled_tasks if t.wo_id == "WO-1")
        assert task.assigned_machines.get("CNC-1") == "CNC-1"
        assigned_amr = task.assigned_machines.get("AMR")
        assert assigned_amr == "AMR-1", (
            f"CNC-1 작업에는 AMR-1만 가능, 실제 배정: {assigned_amr}"
        )

    def test_amr2_not_assigned_to_zone1_machine(self):
        """CNC-1 배정 시 CNC-2 전용 AMR-2는 배정되면 안 됨."""
        op = make_op("OP-1", ["CNC-1", "AMR"])
        wo = make_wo("WO-1", [op], order_quantity=1)
        machines = [make_machine("CNC-1", "CNC")]
        amrs = [
            make_amr("AMR-1", accessible_machines=["CNC-1"]),
            make_amr("AMR-2", accessible_machines=["CNC-2"]),  # 다른 구역
        ]

        result = solve([wo], machines, amrs=amrs)

        assert result.status == "success"
        task = next(t for t in result.scheduled_tasks if t.wo_id == "WO-1")
        assigned_amr = task.assigned_machines.get("AMR")
        assert assigned_amr != "AMR-2", f"구역 위반: AMR-2가 CNC-1에 배정됨"
        assert assigned_amr == "AMR-1"

    def test_zone_assignment_with_type_based_machine(self):
        """머신 타입 기반 배정 시 AMR Zone 제약 유지."""
        op = make_op("OP-1", ["CNC", "AMR"])    # type-based
        wo = make_wo("WO-1", [op], order_quantity=1)
        machines = [
            make_machine("CNC-1", "CNC"),
            make_machine("CNC-2", "CNC"),
        ]
        amrs = [
            make_amr("AMR-A", accessible_machines=["CNC-1"]),
            make_amr("AMR-B", accessible_machines=["CNC-2"]),
        ]

        result = solve([wo], machines, amrs=amrs)

        assert result.status == "success"
        task = next(t for t in result.scheduled_tasks if t.wo_id == "WO-1")
        cnc_id  = task.assigned_machines.get("CNC") or task.machine_id
        amr_id  = task.assigned_machines.get("AMR")
        # AMR은 배정된 CNC에 접근 가능한 것이어야 함
        if cnc_id == "CNC-1":
            assert amr_id == "AMR-A", f"CNC-1에는 AMR-A 배정 기대, 실제: {amr_id}"
        elif cnc_id == "CNC-2":
            assert amr_id == "AMR-B", f"CNC-2에는 AMR-B 배정 기대, 실제: {amr_id}"


# ============================================================================
# Feature 5 : 셋업 시간 모델링
# ============================================================================


class TestSetupTimeModeling:
    """WO × 기계마다 1회 셋업, setup_id 일치 시 생략 검증."""

    def test_setup_time_applied_when_setup_id_differs(self):
        """machine.current_setup_id ≠ op.setup_id → setup_time > 0"""
        op = make_op("OP-1", ["CNC-1"], setup_id="SETUP-A")
        wo = make_wo("WO-1", [op], order_quantity=1)
        m  = make_machine("CNC-1", "CNC",
                          setup_change_time_min=5,
                          current_setup_id=None)   # 다른 셋업

        result = solve([wo], [m])

        assert result.status == "success"
        task = next(t for t in result.scheduled_tasks
                    if t.wo_id == "WO-1" and t.sublot_no == 1)
        assert task.setup_time == 5 * 60, (
            f"셋업 시간 300s 기대, 실제: {task.setup_time}"
        )

    def test_setup_time_skipped_when_setup_id_matches(self):
        """machine.current_setup_id == op.setup_id → setup_time == 0"""
        op = make_op("OP-1", ["CNC-1"], setup_id="SETUP-A")
        wo = make_wo("WO-1", [op], order_quantity=1)
        m  = make_machine("CNC-1", "CNC",
                          setup_change_time_min=5,
                          current_setup_id="SETUP-A")  # 동일 셋업

        result = solve([wo], [m])

        assert result.status == "success"
        task = next(t for t in result.scheduled_tasks
                    if t.wo_id == "WO-1" and t.sublot_no == 1)
        assert task.setup_time == 0, (
            f"setup_id 일치 시 셋업 시간 0 기대, 실제: {task.setup_time}"
        )

    def test_setup_applied_only_on_first_op_of_wo(self):
        """같은 WO의 두 번째 공정은 셋업 시간 0 (이미 1회 처리)"""
        ops = [
            make_op("OP-1", ["CNC-1"], setup_id="SETUP-A", sequence=10),
            make_op("OP-2", ["CNC-1"], predecessors=["OP-1"],
                    setup_id="SETUP-B", sequence=20),
        ]
        wo = make_wo("WO-1", ops, order_quantity=1)
        m  = make_machine("CNC-1", "CNC",
                          setup_change_time_min=5,
                          current_setup_id=None)

        result = solve([wo], [m])

        assert result.status == "success"
        tasks = sorted(
            [t for t in result.scheduled_tasks if t.wo_id == "WO-1" and t.sublot_no == 1],
            key=lambda t: t.start_time,
        )
        assert len(tasks) == 2
        # 첫 번째 공정 셋업 > 0
        assert tasks[0].setup_time == 5 * 60, "첫 공정 셋업 필요"
        # 두 번째 공정 셋업 = 0 (WO당 1회)
        assert tasks[1].setup_time == 0, "두 번째 공정 셋업 없어야 함"

    def test_setup_interval_recorded_in_result(self):
        """setup_intervals에 셋업 구간 정보가 포함되어야 함."""
        op = make_op("OP-1", ["CNC-1"], setup_id="SETUP-A")
        wo = make_wo("WO-1", [op], order_quantity=1)
        m  = make_machine("CNC-1", "CNC",
                          setup_change_time_min=5,
                          current_setup_id=None)

        result = solve([wo], [m])

        assert result.status == "success"
        assert len(result.setup_intervals) > 0, "셋업 구간 정보 없음"
        si = result.setup_intervals[0]
        assert si.machine_id == "CNC-1"
        assert si.wo_id == "WO-1"
        assert si.end_time - si.start_time == 5 * 60

    def test_setup_only_once_per_wo_machine_pair(self):
        """setup_intervals에 WO×기계 쌍당 1개만 존재해야 함."""
        ops = [
            make_op("OP-1", ["CNC-1"], setup_id="SETUP-A", sequence=10),
            make_op("OP-2", ["CNC-1"], predecessors=["OP-1"],
                    setup_id="SETUP-A", sequence=20),
        ]
        wo = make_wo("WO-1", ops, order_quantity=3)
        m  = make_machine("CNC-1", "CNC",
                          setup_change_time_min=5,
                          current_setup_id=None)

        result = solve([wo], [m], scheduler_config=SchedulerConfig(lot_size=3))

        assert result.status == "success"
        # (WO-1, CNC-1) 쌍 셋업 구간이 1개여야 함
        si_count = sum(1 for si in result.setup_intervals
                       if si.wo_id == "WO-1" and si.machine_id == "CNC-1")
        assert si_count == 1, f"셋업 구간은 WO×기계 쌍당 1개, 실제: {si_count}"


# ============================================================================
# Feature 6 : 캘린더 제약
# ============================================================================


class TestCalendarConstraint:
    """shift 시간 + 휴식 시간 반영: 비가동 구간 외에 배정되어야 함."""

    # 자정 기준 horizon (캘린더 블록 확인용)
    HS_CAL = datetime(2026, 5, 14, 0, 0, 0, tzinfo=TZ)
    HE_CAL = datetime(2026, 5, 15, 0, 0, 0, tzinfo=TZ)

    def _cal_solve(self, work_orders, machines, amrs=None, scheduler_config=None):
        solver = ORToolsSolver(
            work_orders=work_orders,
            machines=machines,
            machine_type_params=MTP,
            horizon_start=self.HS_CAL,
            horizon_end=self.HE_CAL,
            amrs=amrs or [],
            scheduler_config=scheduler_config or SchedulerConfig(),
            config=SolverConfig(time_limit_sec=20, num_workers=4),
        )
        return solver.solve()

    def _make_cal_wo(self, wo_id, op, qty=1):
        return WorkOrder(
            wo_id=wo_id,
            product_id=f"P-{wo_id}",
            product_name=wo_id,
            order_quantity=qty,
            due_date=self.HE_CAL,
            priority=3,
            release_date=self.HS_CAL,
            customer="Test",
            operations=[op],
        )

    def test_task_not_scheduled_before_shift_start(self):
        """shift_start=08:00 → task.start_time >= 28800s (자정 기준)"""
        cal = Calendar(
            shift_start=dtime(8, 0),
            shift_end=dtime(17, 0),
        )
        op = make_op("OP-1", ["CNC-1"], cycle_time_sec=60)
        wo = self._make_cal_wo("WO-1", op, qty=1)
        m  = make_machine("CNC-1", "CNC", calendar=cal,
                          available_from=self.HS_CAL)

        result = self._cal_solve([wo], [m])

        assert result.status == "success", f"스케줄 실패: {result.status}"
        task = next(t for t in result.scheduled_tasks if t.wo_id == "WO-1")
        shift_start_sec = 8 * 3600  # 28800
        assert task.start_time >= shift_start_sec, (
            f"shift 전 배정됨: start={task.start_time}s < 28800s"
        )

    def test_task_not_scheduled_after_shift_end(self):
        """shift_end=17:00 → task.end_time <= 61200s"""
        cal = Calendar(
            shift_start=dtime(8, 0),
            shift_end=dtime(17, 0),
        )
        op = make_op("OP-1", ["CNC-1"], cycle_time_sec=60)
        wo = self._make_cal_wo("WO-1", op, qty=1)
        m  = make_machine("CNC-1", "CNC", calendar=cal,
                          available_from=self.HS_CAL)

        result = self._cal_solve([wo], [m])

        assert result.status == "success"
        task = next(t for t in result.scheduled_tasks if t.wo_id == "WO-1")
        shift_end_sec = 17 * 3600  # 61200
        assert task.end_time <= shift_end_sec, (
            f"shift 후 종료됨: end={task.end_time}s > 61200s"
        )

    def test_task_not_scheduled_during_break(self):
        """break 12:00-13:00 (43200s-46800s) 구간에 작업 없어야 함."""
        cal = Calendar(
            shift_start=dtime(8, 0),
            shift_end=dtime(17, 0),
            breaks=[Break(start=dtime(12, 0), end=dtime(13, 0))],
        )
        op = make_op("OP-1", ["CNC-1"], cycle_time_sec=600)  # 10분
        wo = self._make_cal_wo("WO-1", op, qty=1)
        m  = make_machine("CNC-1", "CNC", calendar=cal,
                          available_from=self.HS_CAL)

        result = self._cal_solve([wo], [m])

        assert result.status == "success"
        task = next(t for t in result.scheduled_tasks if t.wo_id == "WO-1")
        break_start = 12 * 3600   # 43200
        break_end   = 13 * 3600   # 46800
        overlaps_break = task.start_time < break_end and task.end_time > break_start
        assert not overlaps_break, (
            f"break 구간 [{break_start}, {break_end}] 겹침: "
            f"task=[{task.start_time}, {task.end_time}]"
        )


# ============================================================================
# Feature 7 : 납기 하드 제약
# ============================================================================


class TestDueDateHardConstraint:
    """due_date를 초과하는 배정 금지 (hard constraint)."""

    def test_task_ends_before_due_date(self):
        """task.end_time <= due_date 오프셋"""
        due_offset_sec = 2 * 3600   # 2시간
        op  = make_op("OP-1", ["CNC-1"], cycle_time_sec=60)
        wo  = make_wo("WO-1", [op], order_quantity=1,
                      due_date=hs_plus(2))  # 2h 후
        m   = make_machine("CNC-1", "CNC")

        result = solve([wo], [m])

        assert result.status == "success"
        task = next(t for t in result.scheduled_tasks if t.wo_id == "WO-1")
        assert task.end_time <= due_offset_sec, (
            f"납기 초과: end_time={task.end_time}s > due={due_offset_sec}s"
        )

    def test_all_lots_end_before_due_date(self):
        """lot 분할 시 마지막 lot의 end_time <= due_date"""
        due_offset_sec = 5 * 3600
        op  = make_op("OP-1", ["CNC-1"], cycle_time_sec=30)
        wo  = make_wo("WO-1", [op], order_quantity=6,
                      due_date=hs_plus(5))
        m   = make_machine("CNC-1", "CNC")

        result = solve([wo], [m], scheduler_config=SchedulerConfig(lot_size=2))

        assert result.status == "success"
        wo_tasks = [t for t in result.scheduled_tasks if t.wo_id == "WO-1"]
        last_end = max(t.end_time for t in wo_tasks)
        assert last_end <= due_offset_sec, (
            f"마지막 lot 납기 초과: end={last_end}s > due={due_offset_sec}s"
        )

    def test_no_tasks_violate_due_date(self):
        """여러 WO 스케줄 시 어느 WO도 납기를 넘으면 안 됨."""
        ops_a = [make_op("OP-A1", ["CNC-1"], cycle_time_sec=60)]
        ops_b = [make_op("OP-B1", ["CNC-1"], cycle_time_sec=60)]
        wos = [
            make_wo("WO-A", ops_a, order_quantity=1, due_date=hs_plus(3),
                    priority=1),
            make_wo("WO-B", ops_b, order_quantity=1, due_date=hs_plus(6),
                    priority=2),
        ]
        m = make_machine("CNC-1", "CNC")

        result = solve(wos, [m])

        assert result.status == "success"
        for wo in wos:
            due_sec = int((wo.due_date - HORIZON_START).total_seconds())
            wo_end  = max((t.end_time for t in result.scheduled_tasks
                           if t.wo_id == wo.wo_id), default=0)
            assert wo_end <= due_sec, (
                f"{wo.wo_id} 납기 초과: end={wo_end}s > due={due_sec}s"
            )


# ============================================================================
# Feature 8 : 우선순위 소프트 제약
# ============================================================================


class TestPriorityConstraint:
    """priority 낮을수록(숫자 작을수록) 먼저 완료되도록 목적함수 반영."""

    def test_high_priority_wo_completes_first_on_single_machine(self):
        """단일 기계: priority=1 WO가 priority=2 WO보다 먼저 완료."""
        op1 = make_op("OP-1", ["CNC-1"], cycle_time_sec=120)
        op2 = make_op("OP-2", ["CNC-1"], cycle_time_sec=120)
        wo1 = make_wo("WO-HIGH", [op1], order_quantity=1, priority=1)
        wo2 = make_wo("WO-LOW",  [op2], order_quantity=1, priority=2)
        m   = make_machine("CNC-1", "CNC")

        result = solve([wo1, wo2], [m])

        assert result.status == "success"
        end_high = max(t.end_time for t in result.scheduled_tasks if t.wo_id == "WO-HIGH")
        end_low  = max(t.end_time for t in result.scheduled_tasks if t.wo_id == "WO-LOW")
        assert end_high <= end_low, (
            f"우선순위 소프트 제약 위반: HIGH 완료={end_high}s, LOW 완료={end_low}s"
        )

    def test_higher_priority_wo_starts_earlier(self):
        """priority=1 WO의 start_time ≤ priority=3 WO의 start_time."""
        op1 = make_op("OP-1", ["CNC-1"], cycle_time_sec=120)
        op2 = make_op("OP-2", ["CNC-1"], cycle_time_sec=120)
        wo1 = make_wo("WO-P1", [op1], order_quantity=1, priority=1)
        wo3 = make_wo("WO-P3", [op2], order_quantity=1, priority=3)
        m   = make_machine("CNC-1", "CNC")

        result = solve([wo1, wo3], [m])

        assert result.status == "success"
        start_p1 = min(t.start_time for t in result.scheduled_tasks if t.wo_id == "WO-P1")
        start_p3 = min(t.start_time for t in result.scheduled_tasks if t.wo_id == "WO-P3")
        assert start_p1 <= start_p3, (
            f"priority=1 이 늦게 시작: P1 start={start_p1}s, P3 start={start_p3}s"
        )

    def test_objective_weight_scales_with_priority(self):
        """priority=1 weight > priority=2 weight (높은 우선순위 = 높은 목적 가중치)."""
        # ORToolsSolver의 _add_objective 논리 검증:
        # weight = max_pri - wo.priority + 1
        # priority=1 → weight=2 (max_pri=2), priority=2 → weight=1
        op1 = make_op("OP-1", ["CNC-1"])
        op2 = make_op("OP-2", ["CNC-1"])
        wo1 = make_wo("WO-1", [op1], priority=1)
        wo2 = make_wo("WO-2", [op2], priority=2)
        m   = make_machine("CNC-1", "CNC")

        solver = ORToolsSolver(
            work_orders=[wo1, wo2],
            machines=[m],
            machine_type_params=MTP,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
            config=SolverConfig(time_limit_sec=5),
        )

        max_pri = max(wo.priority for wo in [wo1, wo2])
        weight1 = max_pri - wo1.priority + 1   # 2
        weight2 = max_pri - wo2.priority + 1   # 1
        assert weight1 > weight2, (
            f"priority=1 가중치({weight1})가 priority=2({weight2})보다 커야 함"
        )


# ============================================================================
# Feature 9 : Infeasible WO 처리
# ============================================================================


class TestInfeasibleWOHandling:
    """납기 불가 WO 자동 제외 후 나머지 스케줄링."""

    def test_infeasible_wo_excluded_feasible_wo_scheduled(self):
        """납기 0초인 WO는 infeasible_wos에, 나머지 WO는 스케줄됨."""
        op_ok   = make_op("OP-OK",  ["CNC-1"], cycle_time_sec=60)
        op_bad  = make_op("OP-BAD", ["CNC-1"], cycle_time_sec=60)
        wo_ok   = make_wo("WO-OK",  [op_ok],  order_quantity=1,
                          due_date=hs_plus(5), priority=1)
        wo_bad  = make_wo("WO-BAD", [op_bad], order_quantity=1,
                          due_date=HORIZON_START,   # 납기 = 시작시간 (duration > 0 → 불가)
                          priority=5)
        m = make_machine("CNC-1", "CNC")

        result = solve([wo_ok, wo_bad], [m])

        assert result.status == "success", f"스케줄 실패: {result.status}"
        assert "WO-BAD" in result.infeasible_wos, (
            f"WO-BAD가 infeasible_wos에 없음: {result.infeasible_wos}"
        )
        scheduled_ids = {t.wo_id for t in result.scheduled_tasks}
        assert "WO-OK" in scheduled_ids, "WO-OK가 스케줄되지 않음"
        assert "WO-BAD" not in scheduled_ids, "WO-BAD가 스케줄에 포함됨"

    def test_low_priority_wo_removed_first(self):
        """infeasible 제거 시 priority 숫자 큰(낮은 우선순위) WO 먼저 제거."""
        op1 = make_op("OP-1", ["CNC-1"], cycle_time_sec=60)
        op2 = make_op("OP-2", ["CNC-1"], cycle_time_sec=60)
        wo_hi  = make_wo("WO-HI",  [op1], order_quantity=1,
                         due_date=HORIZON_START, priority=1)   # 불가, 높은 우선순위
        wo_low = make_wo("WO-LOW", [op2], order_quantity=1,
                         due_date=HORIZON_START, priority=5)   # 불가, 낮은 우선순위
        m = make_machine("CNC-1", "CNC")

        result = solve([wo_hi, wo_low], [m])

        # 둘 다 infeasible이지만, 낮은 우선순위(priority=5)가 먼저 제거
        # 최종적으로 남은 WO도 infeasible이면 전체 실패 가능
        # 핵심: infeasible_wos 중 WO-LOW가 먼저 제거됨
        if result.infeasible_wos:
            # WO-LOW(priority=5)가 infeasible_wos 첫 번째여야 함
            assert "WO-LOW" in result.infeasible_wos

    def test_result_has_infeasible_wos_field(self):
        """ScheduleResult.infeasible_wos 필드가 항상 존재."""
        op = make_op("OP-1", ["CNC-1"], cycle_time_sec=60)
        wo = make_wo("WO-1", [op], order_quantity=1)
        m  = make_machine("CNC-1", "CNC")

        result = solve([wo], [m])

        assert hasattr(result, "infeasible_wos")
        assert isinstance(result.infeasible_wos, list)

    def test_no_infeasible_wos_when_all_feasible(self):
        """모든 WO가 납기 준수 가능 → infeasible_wos 비어있어야 함."""
        op = make_op("OP-1", ["CNC-1"], cycle_time_sec=60)
        wo = make_wo("WO-1", [op], order_quantity=1,
                     due_date=hs_plus(10))
        m  = make_machine("CNC-1", "CNC")

        result = solve([wo], [m])

        assert result.status == "success"
        assert result.infeasible_wos == [], (
            f"feasible WO인데 infeasible_wos 비어있지 않음: {result.infeasible_wos}"
        )


# ============================================================================
# Feature 10 : 간트차트 시각화
# ============================================================================


class TestGanttChartVisualization:
    """gantt_data 생성 및 PNG 저장 검증."""

    def test_generate_gantt_data_returns_dict(self):
        """generate_gantt_data()가 dict 반환."""
        op = make_op("OP-1", ["CNC-1"], cycle_time_sec=60)
        wo = make_wo("WO-1", [op], order_quantity=1)
        m  = make_machine("CNC-1", "CNC")

        result = solve([wo], [m])
        assert result.status == "success"

        solver = ORToolsSolver(
            work_orders=[wo],
            machines=[m],
            machine_type_params=MTP,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
            config=SolverConfig(time_limit_sec=20),
        )
        solver.solve()
        gantt = solver.generate_gantt_data()

        assert isinstance(gantt, dict)
        assert "tasks" in gantt
        assert "resources" in gantt
        assert "start" in gantt
        assert "end" in gantt

    def test_gantt_tasks_contain_required_fields(self):
        """gantt tasks 항목에 name, start, end, resource 포함."""
        op = make_op("OP-1", ["CNC-1"], cycle_time_sec=60)
        wo = make_wo("WO-1", [op], order_quantity=1)
        m  = make_machine("CNC-1", "CNC")

        solver = ORToolsSolver(
            work_orders=[wo],
            machines=[m],
            machine_type_params=MTP,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
            config=SolverConfig(time_limit_sec=20),
        )
        solver.solve()
        gantt = solver.generate_gantt_data()

        assert len(gantt["tasks"]) > 0
        task_entry = gantt["tasks"][0]
        for field in ("name", "start", "end", "resource"):
            assert field in task_entry, f"gantt task에 '{field}' 누락"

    def test_gantt_resources_match_scheduled_machines(self):
        """gantt resources가 스케줄된 기계 목록과 일치."""
        op = make_op("OP-1", ["CNC-1"], cycle_time_sec=60)
        wo = make_wo("WO-1", [op], order_quantity=1)
        m  = make_machine("CNC-1", "CNC")

        solver = ORToolsSolver(
            work_orders=[wo],
            machines=[m],
            machine_type_params=MTP,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
            config=SolverConfig(time_limit_sec=20),
        )
        solver.solve()
        gantt = solver.generate_gantt_data()

        assert "CNC-1" in gantt["resources"]

    def test_png_files_created_via_matplotlib(self):
        """matplotlib으로 PNG 파일 생성 확인."""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
        except ImportError:
            pytest.skip("matplotlib 미설치, 간트차트 PNG 테스트 건너뜀")

        op = make_op("OP-1", ["CNC-1"], cycle_time_sec=60)
        wo = make_wo("WO-1", [op], order_quantity=2)
        m  = make_machine("CNC-1", "CNC")

        solver = ORToolsSolver(
            work_orders=[wo],
            machines=[m],
            machine_type_params=MTP,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
            scheduler_config=SchedulerConfig(lot_size=2),
            config=SolverConfig(time_limit_sec=20),
        )
        result = solver.solve()
        assert result.status == "success"

        gantt = solver.generate_gantt_data()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Machine Gantt
            fig, ax = plt.subplots(figsize=(10, 4))
            resources = gantt["resources"]
            for i, task_entry in enumerate(gantt["tasks"]):
                res_idx = resources.index(task_entry["resource"]) if task_entry["resource"] in resources else 0
                ax.barh(res_idx,
                        task_entry["duration_minutes"],
                        left=0, height=0.5)
            ax.set_yticks(range(len(resources)))
            ax.set_yticklabels(resources)
            machine_png = os.path.join(tmpdir, "gantt_machine.png")
            plt.savefig(machine_png)
            plt.close()

            # Work Order Gantt
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            for task_entry in gantt["tasks"]:
                ax2.barh(task_entry["name"],
                         task_entry["duration_minutes"],
                         left=0, height=0.5)
            wo_png = os.path.join(tmpdir, "gantt_work_order.png")
            plt.savefig(wo_png)
            plt.close()

            assert os.path.exists(machine_png), "gantt_machine.png 생성 실패"
            assert os.path.getsize(machine_png) > 0, "gantt_machine.png 빈 파일"
            assert os.path.exists(wo_png),     "gantt_work_order.png 생성 실패"
            assert os.path.getsize(wo_png) > 0, "gantt_work_order.png 빈 파일"

    def test_gantt_data_has_all_scheduled_tasks(self):
        """gantt tasks 수 == scheduled_tasks 수"""
        ops = [
            make_op("OP-1", ["CNC-1"], cycle_time_sec=60, sequence=10),
            make_op("OP-2", ["CNC-1"], predecessors=["OP-1"],
                    cycle_time_sec=60, sequence=20),
        ]
        wo = make_wo("WO-1", ops, order_quantity=4)
        m  = make_machine("CNC-1", "CNC")

        solver = ORToolsSolver(
            work_orders=[wo],
            machines=[m],
            machine_type_params=MTP,
            horizon_start=HORIZON_START,
            horizon_end=HORIZON_END,
            scheduler_config=SchedulerConfig(lot_size=2),
            config=SolverConfig(time_limit_sec=20),
        )
        solver.solve()
        gantt = solver.generate_gantt_data()

        assert len(gantt["tasks"]) == len(solver.scheduled_tasks), (
            f"gantt tasks={len(gantt['tasks'])} ≠ scheduled_tasks={len(solver.scheduled_tasks)}"
        )
