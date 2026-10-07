"""
OR-Tools CP-SAT Solver (Advanced)

scheduler_advanced에서 이식한 고급 솔버.

설계 원칙:
- required_machines 항목이 machine_id → 직접 고정 배정
- required_machines 항목이 machine_type → 해당 타입 장비 중 솔버가 선택
- required_machines 항목이 "AMR" → AMR 풀에서 솔버가 선택 (accessible_machines 제약)
- machine_binding: 같은 lot 내 같은 required entry → 동일 장비 고정
- 연속 점유: 연속 op이 동일 장비 공유 시 end[i] == start[i+1]
- AMR 이동 시간: 직전 op에 없던 AMR이 등장할 때 상수 추가
- calendar: 장비별 shift/break → blocked interval
- occupied_slots: 이미 점유된 슬롯 → fixed interval (기존 RUNNING/SCHEDULED WO)
- due_date: 하드 제약
- priority 기반 가중 완료 시간 최소화
- infeasible WO: 자동 제외 후 나머지 계속
- lot_size=1 (기본값) 시 lot 분할 없이 기존 동작과 동일
"""

import logging
import time as time_module
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from ortools.sat.python import cp_model

from .base_solver import (
    AMRConfig,
    BaseSolver,
    Break,
    Calendar,
    Machine,
    MachineTypeParams,
    OccupiedSlot,
    Operation,
    ScheduleResult,
    ScheduledTask,
    SchedulerConfig,
    SetupInterval,
    SolverConfig,
    SolverType,
    WorkOrder,
)

logger = logging.getLogger(__name__)

# (wo_id, op_id, sublot_no)
TaskKey = Tuple[str, str, int]
# (wo_id, op_id, sublot_no, entry_idx)
AssignKey = Tuple[str, str, int, int]


class ORToolsSolver(BaseSolver):
    """
    OR-Tools CP-SAT Constraint Programming Solver (Advanced)

    Features:
    - Lot splitting (lot_size from SchedulerConfig)
    - Multi-resource operations (required_machines list with AMR support)
    - Machine binding (same lot, same entry → same machine)
    - Continuous occupancy (shared machines between consecutive ops)
    - Calendar constraints (shift times and breaks)
    - Occupied slot constraints (existing RUNNING/SCHEDULED tasks)
    - Proper setup time model (per WO × machine, setup_id skip)
    - Infeasible WO auto-removal
    """

    def __init__(
        self,
        work_orders: List[WorkOrder],
        machines: List[Machine],
        machine_type_params: Dict[str, MachineTypeParams],
        horizon_start: datetime,
        horizon_end: datetime,
        constraints: Dict[str, Any] = None,
        config: SolverConfig = None,
        amrs: List[AMRConfig] = None,
        scheduler_config: SchedulerConfig = None,
    ):
        super().__init__(
            work_orders=work_orders,
            machines=machines,
            machine_type_params=machine_type_params,
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            constraints=constraints,
            config=config,
            amrs=amrs,
            scheduler_config=scheduler_config,
        )

        # Exclude maintenance machines/AMRs
        self.machines = [m for m in self.machines if m.status != "maintenance"]
        self.amrs = [a for a in self.amrs if a.status != "maintenance"]

        # Lookup maps
        self.mach_map: Dict[str, Machine] = {m.machine_id: m for m in self.machines}
        self.amr_map: Dict[str, AMRConfig] = {a.amr_id: a for a in self.amrs}
        self.type_map: Dict[str, List[str]] = {}
        for m in self.machines:
            self.type_map.setdefault(m.machine_type, []).append(m.machine_id)
        # machine_name → machine_id (for nc_code.compatible_machines which may use names)
        self.name_map: Dict[str, str] = {m.machine_name: m.machine_id for m in self.machines}

        self.model = cp_model.CpModel()
        self.task_vars: Dict[TaskKey, Tuple] = {}
        self.assign_vars: Dict[AssignKey, Dict[str, Any]] = {}
        self.setup_vars: Dict[Tuple, Tuple] = {}
        self.setup_interval_list: List[SetupInterval] = []

    # ── Public ────────────────────────────────────────────────────────────────

    def get_solver_info(self) -> Dict[str, Any]:
        return {
            "type": SolverType.OR_TOOLS.value,
            "name": "OR-Tools CP-SAT (Advanced)",
            "version": "9.7+",
            "description": "Google OR-Tools CP-SAT with lot splitting, AMR, calendar, and setup modeling",
            "best_for": "Small-medium problems with complex resource constraints",
            "characteristics": {
                "optimal": True,
                "deterministic": True,
                "parallelizable": True,
                "lot_splitting": True,
                "amr_support": True,
                "calendar_support": True,
            },
            "default_params": {
                "time_limit_sec": self.config.time_limit_sec,
                "num_workers": self.config.num_workers,
                "lot_size": self.scheduler_config.lot_size,
            },
        }

    def solve(self, time_limit_sec: int = None) -> ScheduleResult:
        time_limit = time_limit_sec or self.config.time_limit_sec
        t0 = time_module.time()
        infeasible: List[str] = []

        # Iteratively remove infeasible WOs
        active_wos = list(self.work_orders)
        while True:
            result = self._try_solve(active_wos, t0, time_limit)
            if result.status in ("success", "feasible"):
                result.infeasible_wos = infeasible
                return result
            if result.status == "no_solution" and len(active_wos) > 1:
                removed = max(active_wos, key=lambda w: w.priority)
                infeasible.append(removed.wo_id)
                active_wos.remove(removed)
                logger.warning("Removing infeasible WO and retrying: %s", removed.wo_id)
                self.model = cp_model.CpModel()
                self.task_vars.clear()
                self.assign_vars.clear()
                self.setup_vars.clear()
            else:
                result.infeasible_wos = infeasible
                return result

    # ── Core solve ────────────────────────────────────────────────────────────

    def _try_solve(self, work_orders: List[WorkOrder], t0: float, time_limit: int) -> ScheduleResult:
        self._build_model(work_orders)

        solver = cp_model.CpSolver()
        solver.parameters.num_workers = self.config.num_workers
        solver.parameters.log_search_progress = self.config.log_search_progress

        def _remaining() -> float:
            return max(1.0, time_limit - (time_module.time() - t0))

        # ── 계층적 lexicographic 최적화 ─────────────────────────────────────────
        # 1순위 tardiness → 2순위 weighted_completion(우선순위) → 3순위 makespan → 4순위 setup.
        # 상수(int) expr은 최적화 대상이 아니므로 건너뛴다(makespan은 항상 실변수).
        stages: List[Tuple[str, Any]] = []
        if not isinstance(self._tardiness_expr, int):
            stages.append(("tardiness", self._tardiness_expr))
        if not isinstance(self._completion_expr, int):
            stages.append(("completion", self._completion_expr))
        stages.append(("makespan", self._makespan_var))
        if not isinstance(self._setup_expr, int):
            stages.append(("setup", self._setup_expr))

        got = False
        last_ok_status = None
        for name, expr in stages:
            self.model.Minimize(expr)
            solver.parameters.max_time_in_seconds = _remaining()
            status = solver.Solve(self.model)
            if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                break
            # 이 단계 해를 보존하고, 해당 tier를 최적값으로 고정 후 다음 tier 진행
            self._extract_solution(solver, work_orders)
            got = True
            last_ok_status = status
            tier_val = int(round(solver.ObjectiveValue()))
            self.model.Add(expr <= tier_val)

        elapsed = time_module.time() - t0

        if got:
            makespan = self._calculate_makespan()
            ev = self.evaluate(self.scheduled_tasks)
            utilization = self.compute_utilization(self.scheduled_tasks, makespan)
            return ScheduleResult(
                status="success",  # MES convention
                scheduled_tasks=self.scheduled_tasks,
                objective_value=float(ev["weighted_tardiness"]),  # tier-1 헤드라인
                solve_time_sec=elapsed,
                total_makespan=makespan,
                machine_utilization=utilization,
                bottleneck_machines=self._find_bottlenecks(),
                solver_info={
                    **self.get_solver_info(),
                    "solution_status": "optimal" if last_ok_status == cp_model.OPTIMAL else "feasible",
                    "iterations": solver.NumBranches(),
                    "conflicts": solver.NumConflicts(),
                },
                setup_intervals=self.setup_interval_list,
                weighted_tardiness_sec=ev["weighted_tardiness"],
                weighted_completion_sec=ev["weighted_completion"],
                total_setup_sec=ev["total_setup"],
            )

        logger.warning("No feasible solution found")
        return ScheduleResult(
            status="no_solution",
            scheduled_tasks=[],
            objective_value=float("inf"),
            solve_time_sec=elapsed,
            total_makespan=0,
            machine_utilization={},
            bottleneck_machines=[],
            solver_info={**self.get_solver_info(), "solution_status": "infeasible"},
        )

    # ── Model building ────────────────────────────────────────────────────────

    def _build_model(self, work_orders: List[WorkOrder]):
        self._create_setup_vars(work_orders)
        self._create_task_and_assign_vars(work_orders)
        self._add_assign_sum_constraints(work_orders)
        self._add_machine_binding(work_orders)
        self._add_amr_accessibility(work_orders)
        self._add_setup_constraints(work_orders)
        self._add_no_overlap()
        self._add_occupied_slot_constraints()
        self._add_intra_lot_precedence(work_orders)
        self._add_inter_lot_precedence(work_orders)
        self._add_due_date_constraints(work_orders)
        self._build_objective_exprs(work_orders)

        total_ops = sum(len(wo.operations) for wo in work_orders)
        logger.info(
            "Model built: %d WOs, %d ops, %d task vars, %d assign vars",
            len(work_orders), total_ops, len(self.task_vars), len(self.assign_vars),
        )

    # ── Candidate resolution ──────────────────────────────────────────────────

    def _is_amr_entry(self, entry: str) -> bool:
        return entry.upper() == "AMR" or entry in self.amr_map

    def _resolve_machine_candidates(self, entry: str, compatible: List[str]) -> List[str]:
        """Return candidate machine_ids for a non-AMR required_machines entry."""
        if entry in self.mach_map:
            return [entry]
        candidates = self.type_map.get(entry, [])
        if compatible:
            # compatible_machines may contain machine names (e.g. "DH400") or IDs (e.g. "EQ-10")
            compatible_ids: set = set()
            for c in compatible:
                if c in self.mach_map:
                    compatible_ids.add(c)
                elif c in self.name_map:
                    compatible_ids.add(self.name_map[c])
            candidates = [c for c in candidates if c in compatible_ids]
        return candidates

    def _resolve_amr_candidates(self, entry: str) -> List[str]:
        if entry in self.amr_map:
            return [entry]
        return list(self.amr_map.keys())

    def _compatible_for_op(self, op: Operation) -> List[str]:
        if op.nc_code:
            return op.nc_code.compatible_machines
        return []

    # ── Setup vars ────────────────────────────────────────────────────────────

    def _create_setup_vars(self, work_orders: List[WorkOrder]):
        """One setup interval per (wo_id, machine_id) for machines needing setup.

        seen은 setup_var를 실제로 만든 머신만 기록한다. 그래야 첫 op에서 setup이
        생략된 경우라도 이후 op에서 같은 머신에 다른 setup_id가 필요하면 var를
        생성할 수 있다. (단, 한 WO·머신당 하나의 setup_var만 모델링 — 첫 필요
        시점에 생성)
        """
        for wo in work_orders:
            seen: Set[str] = set()  # setup_var를 실제로 만든 머신
            for op in sorted(wo.operations, key=lambda o: o.sequence):
                compat = self._compatible_for_op(op)
                for entry in op.required_machines:
                    if self._is_amr_entry(entry):
                        continue
                    for m_id in self._resolve_machine_candidates(entry, compat):
                        if m_id in seen:
                            continue
                        eq = self.mach_map[m_id]
                        if eq.setup_change_time_min <= 0:
                            continue
                        # 이 op의 setup_id가 머신의 현재 설정과 일치하면 setup 불필요
                        # — seen에는 추가하지 않아 다음 op에서 다른 setup_id면 재평가
                        if eq.current_setup_id and eq.current_setup_id == op.setup_id:
                            continue
                        seen.add(m_id)
                        dur = eq.setup_change_time_min * 60
                        avail = self._avail_sec(eq)
                        ss = self.model.NewIntVar(avail, self.horizon_seconds, f"ss_{wo.wo_id}_{m_id}")
                        se = self.model.NewIntVar(avail, self.horizon_seconds, f"se_{wo.wo_id}_{m_id}")
                        self.model.Add(se == ss + dur)
                        self.setup_vars[(wo.wo_id, m_id)] = (ss, se, dur)

    # ── Task + Assignment vars ─────────────────────────────────────────────────

    def _create_task_and_assign_vars(self, work_orders: List[WorkOrder]):
        for wo in work_orders:
            ops = sorted(wo.operations, key=lambda o: o.sequence)
            lot_sizes = self._lot_sizes(wo.order_quantity)
            rel_sec = max(0, int((wo.release_date - self.horizon_start).total_seconds()))

            for sublot_no, lot_qty in enumerate(lot_sizes, start=1):
                for i, op in enumerate(ops):
                    prev_op = ops[i - 1] if i > 0 else None
                    amr_sec = self._amr_transfer_sec(op, prev_op)
                    duration = lot_qty * op.get_cycle_time() + amr_sec
                    avail = self._earliest_start(op, rel_sec)

                    s = self.model.NewIntVar(avail, self.horizon_seconds,
                                            f"s_{wo.wo_id}_{op.op_id}_l{sublot_no}")
                    e = self.model.NewIntVar(avail, self.horizon_seconds,
                                            f"e_{wo.wo_id}_{op.op_id}_l{sublot_no}")
                    self.model.Add(e == s + duration)
                    self.task_vars[(wo.wo_id, op.op_id, sublot_no)] = (s, e, duration, amr_sec)

                    compat = self._compatible_for_op(op)
                    for idx, entry in enumerate(op.required_machines):
                        key = (wo.wo_id, op.op_id, sublot_no, idx)
                        if self._is_amr_entry(entry):
                            candidates = self._resolve_amr_candidates(entry)
                        else:
                            candidates = self._resolve_machine_candidates(entry, compat)

                        if not candidates:
                            logger.warning("No candidates for entry '%s' op %s", entry, op.op_id)
                            continue

                        if len(candidates) == 1:
                            bv = self.model.NewBoolVar(
                                f"a_{wo.wo_id}_{op.op_id}_l{sublot_no}_e{idx}_{candidates[0]}")
                            self.model.Add(bv == 1)
                            self.assign_vars[key] = {candidates[0]: bv}
                        else:
                            bvs = {}
                            for c in candidates:
                                bv = self.model.NewBoolVar(
                                    f"a_{wo.wo_id}_{op.op_id}_l{sublot_no}_e{idx}_{c}")
                                bvs[c] = bv
                            self.assign_vars[key] = bvs

    # ── Assignment sum == 1 ───────────────────────────────────────────────────

    def _add_assign_sum_constraints(self, work_orders: List[WorkOrder]):
        for wo in work_orders:
            lot_sizes = self._lot_sizes(wo.order_quantity)
            for sublot_no in range(1, len(lot_sizes) + 1):
                for op in wo.operations:
                    for idx in range(len(op.required_machines)):
                        key = (wo.wo_id, op.op_id, sublot_no, idx)
                        bvs = self.assign_vars.get(key, {})
                        if len(bvs) > 1:
                            self.model.AddExactlyOne(list(bvs.values()))

    # ── Machine binding ───────────────────────────────────────────────────────

    def _add_machine_binding(self, work_orders: List[WorkOrder]):
        """Same lot, same required entry string → same machine assigned."""
        for wo in work_orders:
            ops = sorted(wo.operations, key=lambda o: o.sequence)
            lot_sizes = self._lot_sizes(wo.order_quantity)
            for sublot_no in range(1, len(lot_sizes) + 1):
                entry_to_ops: Dict[str, List[Tuple[Operation, int]]] = {}
                for op in ops:
                    for idx, entry in enumerate(op.required_machines):
                        entry_to_ops.setdefault(entry, []).append((op, idx))

                for entry, op_list in entry_to_ops.items():
                    if len(op_list) < 2:
                        continue
                    first_op, first_idx = op_list[0]
                    first_key = (wo.wo_id, first_op.op_id, sublot_no, first_idx)
                    first_bvs = self.assign_vars.get(first_key, {})

                    for op_j, idx_j in op_list[1:]:
                        key_j = (wo.wo_id, op_j.op_id, sublot_no, idx_j)
                        bvs_j = self.assign_vars.get(key_j, {})
                        all_candidates = set(first_bvs) | set(bvs_j)
                        for m in all_candidates:
                            bv_i = first_bvs.get(m)
                            bv_j = bvs_j.get(m)
                            if bv_i is not None and bv_j is not None:
                                self.model.Add(bv_i == bv_j)
                            elif bv_i is not None:
                                self.model.Add(bv_i == 0)
                            elif bv_j is not None:
                                self.model.Add(bv_j == 0)

    # ── AMR accessibility ─────────────────────────────────────────────────────

    def _add_amr_accessibility(self, work_orders: List[WorkOrder]):
        """Chosen AMR must have chosen non-AMR machine in its accessible_machines."""
        for wo in work_orders:
            lot_sizes = self._lot_sizes(wo.order_quantity)
            for sublot_no in range(1, len(lot_sizes) + 1):
                for op in wo.operations:
                    amr_indices = [i for i, e in enumerate(op.required_machines)
                                   if self._is_amr_entry(e)]
                    mch_indices = [i for i, e in enumerate(op.required_machines)
                                   if not self._is_amr_entry(e)]
                    if not amr_indices or not mch_indices:
                        continue

                    for mch_idx in mch_indices:
                        mch_key = (wo.wo_id, op.op_id, sublot_no, mch_idx)
                        mch_bvs = self.assign_vars.get(mch_key, {})
                        for amr_idx in amr_indices:
                            amr_key = (wo.wo_id, op.op_id, sublot_no, amr_idx)
                            amr_bvs = self.assign_vars.get(amr_key, {})
                            for m_id, mch_bv in mch_bvs.items():
                                accessible = [a_id for a_id, a in self.amr_map.items()
                                              if m_id in a.accessible_machines]
                                inaccessible = [a_id for a_id in amr_bvs
                                                if a_id not in accessible]
                                for a_id in inaccessible:
                                    self.model.Add(amr_bvs[a_id] == 0).OnlyEnforceIf(mch_bv)
                                accessible_bvs = [amr_bvs[a_id] for a_id in accessible
                                                  if a_id in amr_bvs]
                                if accessible_bvs:
                                    self.model.Add(sum(accessible_bvs) == 1).OnlyEnforceIf(mch_bv)

    # ── Setup constraints ─────────────────────────────────────────────────────

    def _add_setup_constraints(self, work_orders: List[WorkOrder]):
        """Setup must finish before first op of the WO on that machine."""
        for wo in work_orders:
            ops = sorted(wo.operations, key=lambda o: o.sequence)
            seen: Set[str] = set()
            for op in ops:
                compat = self._compatible_for_op(op)
                for idx, entry in enumerate(op.required_machines):
                    if self._is_amr_entry(entry):
                        continue
                    for m_id in self._resolve_machine_candidates(entry, compat):
                        if m_id in seen:
                            continue
                        seen.add(m_id)
                        key = (wo.wo_id, m_id)
                        if key not in self.setup_vars:
                            continue
                        _, se, _ = self.setup_vars[key]
                        s_op, *_ = self.task_vars[(wo.wo_id, op.op_id, 1)]
                        assign_key = (wo.wo_id, op.op_id, 1, idx)
                        bvs = self.assign_vars.get(assign_key, {})
                        bv = bvs.get(m_id)
                        if bv is not None:
                            self.model.Add(se <= s_op).OnlyEnforceIf(bv)

    # ── NoOverlap ─────────────────────────────────────────────────────────────

    def _add_no_overlap(self):
        intervals_per_resource: Dict[str, list] = {}

        # Setup intervals (optional — active only when this WO actually picks m_id)
        # 해당 (wo_id, m_id)를 실제로 사용하는 assign boolvar OR로 묶어 setup_used 결정
        self._setup_used_vars: Dict[Tuple[str, str], Any] = {}
        for (wo_id, m_id), (ss, se, sd) in self.setup_vars.items():
            assign_bvs = [
                bvs[m_id]
                for (w, _, _, _), bvs in self.assign_vars.items()
                if w == wo_id and m_id in bvs
            ]
            if not assign_bvs:
                continue
            is_used = self.model.NewBoolVar(f"setup_used_{wo_id}_{m_id}")
            # is_used == OR(assign_bvs)
            self.model.AddBoolOr(assign_bvs).OnlyEnforceIf(is_used)
            self.model.AddBoolAnd([b.Not() for b in assign_bvs]).OnlyEnforceIf(is_used.Not())
            self._setup_used_vars[(wo_id, m_id)] = is_used
            iv = self.model.NewOptionalIntervalVar(ss, sd, se, is_used, f"setup_{wo_id}_{m_id}")
            intervals_per_resource.setdefault(m_id, []).append(iv)

        # Task intervals (optional, based on assignment)
        for (wo_id, op_id, sublot_no, entry_idx), bvs in self.assign_vars.items():
            s, e, dur, _ = self.task_vars[(wo_id, op_id, sublot_no)]
            for m_id, bv in bvs.items():
                iv = self.model.NewOptionalIntervalVar(
                    s, dur, e, bv,
                    f"iv_{wo_id}_{op_id}_l{sublot_no}_e{entry_idx}_{m_id}"
                )
                intervals_per_resource.setdefault(m_id, []).append(iv)

        # Calendar blocked intervals
        for m in self.machines:
            if m.calendar:
                for i, (bs, bd) in enumerate(self._calendar_blocked(m)):
                    iv = self.model.NewFixedSizeIntervalVar(bs, bd, f"cal_{m.machine_id}_{i}")
                    intervals_per_resource.setdefault(m.machine_id, []).append(iv)

        for resource_id, ivs in intervals_per_resource.items():
            if len(ivs) > 1:
                self.model.AddNoOverlap(ivs)

    def _calendar_blocked(self, m: Machine) -> List[Tuple[int, int]]:
        """Return (start_sec, duration_sec) of blocked intervals within horizon."""
        cal = m.calendar
        blocked = []
        hs = self.horizon_start
        current = hs.replace(hour=0, minute=0, second=0, microsecond=0)
        horizon_end_dt = self.horizon_end

        while current < horizon_end_dt:
            shift_start_dt = current.replace(
                hour=cal.shift_start.hour, minute=cal.shift_start.minute)
            shift_end_dt = current.replace(
                hour=cal.shift_end.hour, minute=cal.shift_end.minute)

            # Night before shift
            if shift_start_dt.hour > 0 or shift_start_dt.minute > 0:
                night_s = int((current - hs).total_seconds())
                night_e = int((shift_start_dt - hs).total_seconds())
                if night_e > night_s and night_e > 0 and night_s < self.horizon_seconds:
                    bs = max(0, night_s)
                    be = min(self.horizon_seconds, night_e)
                    if be > bs:
                        blocked.append((bs, be - bs))

            # Breaks within shift
            for brk in cal.breaks:
                brk_s = current.replace(hour=brk.start.hour, minute=brk.start.minute)
                brk_e = current.replace(hour=brk.end.hour, minute=brk.end.minute)
                bs_sec = int((brk_s - hs).total_seconds())
                be_sec = int((brk_e - hs).total_seconds())
                if be_sec > 0 and bs_sec < self.horizon_seconds and be_sec > bs_sec:
                    bs = max(0, bs_sec)
                    be = min(self.horizon_seconds, be_sec)
                    if be > bs:
                        blocked.append((bs, be - bs))

            # Night after shift
            next_day = current + timedelta(days=1)
            night_s = int((shift_end_dt - hs).total_seconds())
            night_e = int((next_day - hs).total_seconds())
            if night_e > night_s and night_e > 0 and night_s < self.horizon_seconds:
                bs = max(0, night_s)
                be = min(self.horizon_seconds, night_e)
                if be > bs:
                    blocked.append((bs, be - bs))

            current = next_day

        return blocked

    # ── Occupied slot constraints (existing RUNNING/SCHEDULED tasks) ──────────

    def _add_occupied_slot_constraints(self):
        """Prevent new tasks from overlapping existing occupied slots on machines."""
        total_slots = 0
        for machine in self.machines:
            if not machine.occupied_slots:
                continue

            # Check assign_vars for tasks assigned to this machine
            machine_assign_keys = [
                (key, bvs) for key, bvs in self.assign_vars.items()
                if machine.machine_id in bvs
            ]

            if not machine_assign_keys:
                continue

            occupied_intervals = []
            for i, slot in enumerate(machine.occupied_slots):
                slot_start = max(0, slot.start)
                slot_end = min(self.horizon_seconds, slot.end)
                if slot_start >= slot_end:
                    continue
                dur = slot_end - slot_start
                iv = self.model.NewFixedSizeIntervalVar(
                    slot_start, dur, f"occ_{machine.machine_id}_{i}"
                )
                occupied_intervals.append(iv)
                total_slots += 1

            if not occupied_intervals:
                continue

            # Add optional intervals for tasks that might be assigned to this machine
            task_intervals_for_machine = []
            seen_task_keys: Set[Tuple] = set()
            for (wo_id, op_id, sublot_no, entry_idx), bvs in machine_assign_keys:
                task_key = (wo_id, op_id, sublot_no)
                if task_key in seen_task_keys:
                    continue
                seen_task_keys.add(task_key)
                s, e, dur, _ = self.task_vars[task_key]
                bv = bvs[machine.machine_id]
                iv = self.model.NewOptionalIntervalVar(
                    s, dur, e, bv,
                    f"occ_task_{machine.machine_id}_{wo_id}_{op_id}_l{sublot_no}"
                )
                task_intervals_for_machine.append(iv)

            if task_intervals_for_machine:
                self.model.AddNoOverlap(occupied_intervals + task_intervals_for_machine)

        if total_slots:
            logger.info("Added occupied-slot constraints for %d slots", total_slots)

    # ── Intra-lot precedence + continuous occupancy ───────────────────────────

    def _add_intra_lot_precedence(self, work_orders: List[WorkOrder]):
        for wo in work_orders:
            ops = sorted(wo.operations, key=lambda o: o.sequence)
            lot_sizes = self._lot_sizes(wo.order_quantity)
            for sublot_no in range(1, len(lot_sizes) + 1):
                for i in range(len(ops) - 1):
                    op_curr = ops[i]
                    op_next = ops[i + 1]
                    _, e_curr, *_ = self.task_vars[(wo.wo_id, op_curr.op_id, sublot_no)]
                    s_next, *_ = self.task_vars[(wo.wo_id, op_next.op_id, sublot_no)]

                    shared_entries = set(op_curr.required_machines) & set(op_next.required_machines)
                    if shared_entries:
                        self.model.Add(e_curr == s_next)  # continuous occupancy
                    else:
                        self.model.Add(e_curr <= s_next)

    # ── Inter-lot precedence (lot completion + same-op order) ────────────────

    def _add_inter_lot_precedence(self, work_orders: List[WorkOrder]):
        """Lot 순서 제약 (decoder semantics와 일치):
        1) lot N의 마지막 공정이 끝나야 lot N+1의 첫 공정 시작 가능
        2) 같은 공정의 lot N이 끝나야 lot N+1의 같은 공정 시작 가능
        """
        for wo in work_orders:
            ops = sorted(wo.operations, key=lambda o: o.sequence)
            if not ops:
                continue
            num_lots = len(self._lot_sizes(wo.order_quantity))
            last_op = ops[-1]
            first_op = ops[0]
            for sublot_no in range(1, num_lots):
                # (1) lot 완료 후 다음 lot 시작
                _, e_last_of_prev, *_ = self.task_vars[(wo.wo_id, last_op.op_id, sublot_no)]
                s_first_of_next, *_ = self.task_vars[(wo.wo_id, first_op.op_id, sublot_no + 1)]
                self.model.Add(e_last_of_prev <= s_first_of_next)
                # (2) 같은 공정 간 순서 (이미 (1)에 함의되지만 명시적으로 유지)
                for op in ops:
                    _, e_curr, *_ = self.task_vars[(wo.wo_id, op.op_id, sublot_no)]
                    s_next, *_ = self.task_vars[(wo.wo_id, op.op_id, sublot_no + 1)]
                    self.model.Add(e_curr <= s_next)

    # ── Due date soft constraint (lateness penalty) ──────────────────────────

    def _add_due_date_constraints(self, work_orders: List[WorkOrder]):
        """납기는 soft 제약 — lateness 변수만 생성하고 objective에서 패널티화한다."""
        self._lateness_vars: Dict[str, Any] = {}
        for wo in work_orders:
            ops = sorted(wo.operations, key=lambda o: o.sequence)
            num_lots = len(self._lot_sizes(wo.order_quantity))
            _, e_last, *_ = self.task_vars[(wo.wo_id, ops[-1].op_id, num_lots)]
            # due_sec < 0 (이미 지난 납기)도 정상 처리: lateness = e_last - due_sec
            due_sec = int((wo.due_date - self.horizon_start).total_seconds())
            # lateness 상한: e_last(max=horizon_seconds) - due_sec
            # due_sec이 음수면 상한이 더 커져야 하므로 그만큼 추가
            late_ub = self.horizon_seconds + max(0, -due_sec)
            lateness = self.model.NewIntVar(0, late_ub, f"late_{wo.wo_id}")
            # lateness >= e_last - due_sec, lateness >= 0
            self.model.Add(lateness >= e_last - due_sec)
            self._lateness_vars[wo.wo_id] = lateness

    # ── Objective ─────────────────────────────────────────────────────────────

    def _build_objective_exprs(self, work_orders: List[WorkOrder]):
        """Lexicographic 목적함수 컴포넌트 식을 만들어 저장한다(Minimize는 _try_solve에서 단계별).

        - _tardiness_expr:  Σ weight·lateness   (tier-1, 납기 준수)
        - _completion_expr: Σ weight·e_last     (tier-2, 우선순위 가중 완료시간)
        - _makespan_var:    max(모든 task end)   (tier-3, 처리량)
        - _setup_expr:      Σ is_used·setup_dur (tier-4, 셋업 최소)

        big-M 가중합 대신 계층적 순차 최적화를 쓰는 이유: horizon이 길면(예: 23일)
        가중합 계수가 int64를 넘쳐 CP-SAT가 깨진다. 순차 최적화는 오버플로가 없다.
        """
        # tier-3: makespan = max of all task end vars (항상 실변수)
        all_ends = [tv[1] for tv in self.task_vars.values()]
        mk = self.model.NewIntVar(0, self.horizon_seconds, "makespan")
        if all_ends:
            self.model.AddMaxEquality(mk, all_ends)
        else:
            self.model.Add(mk == 0)
        self._makespan_var = mk

        # tier-1: weighted tardiness (lateness 변수는 _add_due_date_constraints에서 생성)
        tard_terms = []
        if work_orders:
            max_pri = max(wo.priority for wo in work_orders)
            for wo in work_orders:
                weight = max_pri - wo.priority + 1
                lateness = getattr(self, "_lateness_vars", {}).get(wo.wo_id)
                if lateness is not None:
                    tard_terms.append(weight * lateness)
        self._tardiness_expr = sum(tard_terms) if tard_terms else 0

        # tier-2: weighted completion (우선순위 주문 먼저 완료)
        comp_terms = []
        if work_orders:
            max_pri = max(wo.priority for wo in work_orders)
            for wo in work_orders:
                weight = max_pri - wo.priority + 1
                ops = sorted(wo.operations, key=lambda o: o.sequence)
                if not ops:
                    continue
                num_lots = len(self._lot_sizes(wo.order_quantity))
                key = (wo.wo_id, ops[-1].op_id, num_lots)
                if key in self.task_vars:
                    _, e_last, *_ = self.task_vars[key]
                    comp_terms.append(weight * e_last)
        self._completion_expr = sum(comp_terms) if comp_terms else 0

        # tier-4: total setup (is_used 변수는 _add_no_overlap에서 생성)
        setup_terms = []
        used_vars = getattr(self, "_setup_used_vars", {})
        for (wo_id, m_id), (_ss, _se, dur) in self.setup_vars.items():
            used = used_vars.get((wo_id, m_id))
            if used is not None:
                setup_terms.append(used * dur)
        self._setup_expr = sum(setup_terms) if setup_terms else 0

    # ── Solution extraction ───────────────────────────────────────────────────

    def _extract_solution(self, solver: cp_model.CpSolver, work_orders: List[WorkOrder]):
        # 실제 사용된 (wo, machine) setup만 기록: setup_used 또는 assign 결과 확인
        used_setups: Dict[Tuple[str, str], int] = {}
        for (wo_id, m_id), (_, _, dur) in self.setup_vars.items():
            used_bv = getattr(self, "_setup_used_vars", {}).get((wo_id, m_id))
            if used_bv is not None and solver.Value(used_bv) == 1:
                used_setups[(wo_id, m_id)] = dur

        # 첫 op에 setup_sec 귀속 (해당 머신을 실제로 선택한 첫 공정에 부여)
        first_op_setup: Dict[Tuple[str, str], int] = {}
        for wo in work_orders:
            ops = sorted(wo.operations, key=lambda o: o.sequence)
            used_machines_seen: Set[str] = set()
            for op in ops:
                total = 0
                for idx, entry in enumerate(op.required_machines):
                    if self._is_amr_entry(entry):
                        continue
                    bvs = self.assign_vars.get((wo.wo_id, op.op_id, 1, idx), {})
                    for m_id, bv in bvs.items():
                        if solver.Value(bv) != 1:
                            continue
                        if m_id in used_machines_seen:
                            continue
                        used_machines_seen.add(m_id)
                        if (wo.wo_id, m_id) in used_setups:
                            total += used_setups[(wo.wo_id, m_id)]
                if total:
                    first_op_setup[(wo.wo_id, op.op_id)] = total

        self.scheduled_tasks = []
        for wo in work_orders:
            ops = sorted(wo.operations, key=lambda o: o.sequence)
            lot_sizes = self._lot_sizes(wo.order_quantity)

            for sublot_no, lot_qty in enumerate(lot_sizes, start=1):
                for i, op in enumerate(ops):
                    s, e, _, amr_sec = self.task_vars[(wo.wo_id, op.op_id, sublot_no)]
                    setup_sec = (first_op_setup.get((wo.wo_id, op.op_id), 0)
                                 if sublot_no == 1 else 0)

                    # Resolve actual assignments
                    assigned: Dict[str, str] = {}
                    primary_machine = ""
                    for idx, entry in enumerate(op.required_machines):
                        key = (wo.wo_id, op.op_id, sublot_no, idx)
                        bvs = self.assign_vars.get(key, {})
                        for m_id, bv in bvs.items():
                            if solver.Value(bv) == 1:
                                assigned[entry] = m_id
                                if not self._is_amr_entry(entry) and not primary_machine:
                                    primary_machine = m_id
                                break

                    if not primary_machine and assigned:
                        primary_machine = next(iter(assigned.values()))

                    self.scheduled_tasks.append(ScheduledTask(
                        wo_id=wo.wo_id,
                        op_id=op.op_id,
                        machine_id=primary_machine,
                        start_time=solver.Value(s),
                        end_time=solver.Value(e),
                        quantity=lot_qty,
                        setup_time=setup_sec,
                        sublot_no=sublot_no,   # 분할 조각 순번
                        lot_no=wo.lot_no,      # 작업지시 별칭
                        op_name=op.op_name,
                        assigned_machines=assigned,
                        amr_transfer_sec=amr_sec,
                    ))

        self.scheduled_tasks.sort(key=lambda t: (t.start_time, t.wo_id, t.sublot_no))

        # Extract setup intervals for visualization (실제 사용된 것만)
        self.setup_interval_list = []
        for (wo_id, m_id), (ss, se, _) in self.setup_vars.items():
            if (wo_id, m_id) not in used_setups:
                continue
            self.setup_interval_list.append(SetupInterval(
                machine_id=m_id,
                wo_id=wo_id,
                start_time=solver.Value(ss),
                end_time=solver.Value(se),
            ))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _lot_sizes(self, order_quantity: int) -> List[int]:
        if order_quantity <= 0:
            return []
        ls = self.scheduler_config.lot_size
        if ls <= 1:
            return [order_quantity]
        n = (order_quantity + ls - 1) // ls
        sizes = [ls] * (n - 1)
        sizes.append(order_quantity - ls * (n - 1))
        return sizes

    def _amr_transfer_sec(self, op: Operation, prev_op: Optional[Operation]) -> int:
        has_amr = any(self._is_amr_entry(e) for e in op.required_machines)
        if not has_amr:
            return 0
        if prev_op is None:
            return self.scheduler_config.amr_transfer_time_sec
        prev_has_amr = any(self._is_amr_entry(e) for e in prev_op.required_machines)
        return 0 if prev_has_amr else self.scheduler_config.amr_transfer_time_sec

    def _avail_sec(self, eq: Machine) -> int:
        return max(0, int((eq.available_from - self.horizon_start).total_seconds()))

    def _earliest_start(self, op: Operation, release_sec: int) -> int:
        result = release_sec
        compat = self._compatible_for_op(op)
        for entry in op.required_machines:
            if self._is_amr_entry(entry):
                continue
            for m_id in self._resolve_machine_candidates(entry, compat):
                eq = self.mach_map[m_id]
                result = max(result, self._avail_sec(eq))
        return result
