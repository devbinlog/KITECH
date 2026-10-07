"""
ALNS (Adaptive Large Neighborhood Search) Solver

WO 인덱스 순열 chromosome + BaseSolver 공유 decoder.
random/worst destroy + greedy/regret repair, 적응형 가중치 갱신.
"""

import logging
import math
import random
import time as time_module
from typing import Any, Dict, List, Tuple

from .base_solver import (
    AMRConfig,
    BaseSolver,
    Machine,
    MachineTypeParams,
    ScheduleResult,
    SchedulerConfig,
    SolverConfig,
    WorkOrder,
)

logger = logging.getLogger(__name__)


class ALNSSolver(BaseSolver):
    """ALNS — destroy/repair on WO permutation, adaptive weights, shared decoder."""

    def __init__(
        self,
        work_orders: List[WorkOrder],
        machines: List[Machine],
        machine_type_params: Dict[str, MachineTypeParams],
        horizon_start,
        horizon_end,
        constraints: Dict = None,
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
        self.destroy_rate = self.config.alns_destroy_rate
        self.segment_size = self.config.alns_segment_size
        self.w_best       = 9.0
        self.w_improve    = 5.0
        self.w_accept     = 1.0
        self.decay        = 0.8
        # SA-style acceptance (Ropke & Pisinger 2006)
        self.initial_temp = self.config.initial_temp
        self.cooling_rate = self.config.cooling_rate
        self.min_temp     = self.config.final_temp

    def get_solver_info(self) -> Dict[str, Any]:
        return {
            "solver": "ALNS",
            "type": "metaheuristic",
            "destroy_rate": self.destroy_rate,
            "segment_size": self.segment_size,
        }

    def _k(self, n: int) -> int:
        return max(1, min(int(round(n * self.destroy_rate)), n - 1))

    # ── Destroy ───────────────────────────────────────────────────────────────

    def _random_destroy(self, chrom: List[int]) -> Tuple[List[int], List[int]]:
        removed = random.sample(chrom, self._k(len(chrom)))
        remain  = [x for x in chrom if x not in removed]
        return remain, removed

    def _worst_destroy(self, chrom: List[int]) -> Tuple[List[int], List[int]]:
        """현재 objective(_fitness)에 가장 큰 악영향을 주는 WO부터 제거."""
        base  = self._fitness(chrom)
        gains = []
        for idx, wo_idx in enumerate(chrom):
            cand = chrom[:idx] + chrom[idx + 1:]
            score = self._fitness(cand) if cand else 0
            gains.append((base - score, wo_idx))
        gains.sort(key=lambda x: -x[0])
        removed = [g[1] for g in gains[:self._k(len(chrom))]]
        remain  = [x for x in chrom if x not in removed]
        return remain, removed

    # ── Repair ────────────────────────────────────────────────────────────────

    def _greedy_insert(self, remain: List[int], removed: List[int]) -> List[int]:
        chrom = remain[:]
        for wo_idx in removed:
            best_pos = 0
            best_fit = float("inf")
            for pos in range(len(chrom) + 1):
                cand = chrom[:pos] + [wo_idx] + chrom[pos:]
                fit  = self._fitness(cand)
                if fit < best_fit:
                    best_fit = fit
                    best_pos = pos
            chrom.insert(best_pos, wo_idx)
        return chrom

    def _regret_insert(self, remain: List[int], removed: List[int]) -> List[int]:
        chrom   = remain[:]
        pending = list(removed)
        while pending:
            best_regret = -float("inf")
            best_wo     = None
            best_pos    = 0
            for wo_idx in pending:
                fits = sorted(
                    (self._fitness(chrom[:p] + [wo_idx] + chrom[p:]), p)
                    for p in range(len(chrom) + 1)
                )
                regret = (fits[1][0] - fits[0][0]) if len(fits) > 1 else 0
                if regret > best_regret:
                    best_regret = regret
                    best_wo     = wo_idx
                    best_pos    = fits[0][1]
            chrom.insert(best_pos, best_wo)
            pending.remove(best_wo)
        return chrom

    # ── solve ─────────────────────────────────────────────────────────────────

    def solve(self, time_limit_sec: int = None) -> ScheduleResult:
        limit = time_limit_sec if time_limit_sec is not None else self.config.time_limit_sec
        t0 = time_module.time()

        if not self.work_orders:
            return self._build_result([], 0.0, "no_solution")

        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)

        destroy_ops = [self._random_destroy, self._worst_destroy]
        repair_ops  = [self._greedy_insert,  self._regret_insert]
        d_w = [1.0] * len(destroy_ops)
        r_w = [1.0] * len(repair_ops)
        d_s = [0.0] * len(destroy_ops)
        r_s = [0.0] * len(repair_ops)
        d_c = [0]   * len(destroy_ops)
        r_c = [0]   * len(repair_ops)

        def _pick(ops, weights):
            total = sum(weights)
            acc, r = 0.0, random.random() * total
            for i, w in enumerate(weights):
                acc += w
                if r <= acc:
                    return i, ops[i]
            return len(ops) - 1, ops[-1]

        current     = self._initial_solution()
        current_fit = self._fitness(current)  # H: 우선순위 가중 완료시간
        best        = current[:]
        best_fit    = current_fit
        iters       = 0

        # SA 수락 기준용 초기온도 — current_fit의 일정 비율로 자동 스케일
        # (Ropke & Pisinger 2006: T_0 = w * f(x_0), 보통 w=0.05)
        temp = max(self.initial_temp, current_fit * 0.05) if current_fit > 0 else self.initial_temp
        adjusted_min_temp = max(self.min_temp, temp * 1e-3)
        max_iters = self.config.alns_iterations if self.config.alns_iterations > 0 else float("inf")

        while time_module.time() - t0 < limit and iters < max_iters:
            d_idx, d_op = _pick(destroy_ops, d_w)
            r_idx, r_op = _pick(repair_ops,  r_w)

            remain, removed = d_op(current)
            neighbor        = r_op(remain, removed)
            neighbor_fit    = self._fitness(neighbor)
            delta           = neighbor_fit - current_fit

            score = 0.0
            if neighbor_fit < best_fit:
                best     = neighbor[:]
                best_fit = neighbor_fit
                score    = self.w_best
            elif neighbor_fit < current_fit:
                score = self.w_improve

            # SA-style acceptance: 개선이면 무조건, 악화는 exp(-Δ/T) 확률
            accept = (delta < 0) or (
                temp > adjusted_min_temp
                and random.random() < math.exp(-delta / temp)
            )
            if accept:
                current     = neighbor
                current_fit = neighbor_fit
                if score == 0.0:
                    score = self.w_accept

            temp = max(temp * self.cooling_rate, adjusted_min_temp)

            d_s[d_idx] += score;  d_c[d_idx] += 1
            r_s[r_idx] += score;  r_c[r_idx] += 1
            iters += 1

            if iters % self.segment_size == 0:
                for i in range(len(destroy_ops)):
                    avg    = d_s[i] / d_c[i] if d_c[i] else 0
                    d_w[i] = max(self.decay * d_w[i] + (1 - self.decay) * avg, 0.01)
                    d_s[i] = d_c[i] = 0
                for i in range(len(repair_ops)):
                    avg    = r_s[i] / r_c[i] if r_c[i] else 0
                    r_w[i] = max(self.decay * r_w[i] + (1 - self.decay) * avg, 0.01)
                    r_s[i] = r_c[i] = 0

        solve_time = time_module.time() - t0
        _, _, ms = self._decode(best)
        logger.info("ALNS: %d회 | makespan=%.1fmin | %.2fs", iters, ms / 60, solve_time)
        return self._build_result(best, solve_time)
