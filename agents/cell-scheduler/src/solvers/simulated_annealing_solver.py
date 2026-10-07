"""
Simulated Annealing Solver

WO 인덱스 순열 chromosome + BaseSolver 공유 decoder.
swap/insert 이웃 탐색, 지수 냉각, reheat 메커니즘.
"""

import logging
import math
import random
import time as time_module
from typing import Any, Dict, List

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


class SimulatedAnnealingSolver(BaseSolver):
    """SA solver — WO-permutation chromosome, reheat, shared greedy decoder."""

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
        self.initial_temp  = self.config.initial_temp
        self.cooling_rate  = self.config.cooling_rate
        self.min_temp      = self.config.final_temp
        self.reheat_every  = 500
        self.reheat_factor = 2.0

    def get_solver_info(self) -> Dict[str, Any]:
        return {
            "solver": "SimulatedAnnealing",
            "type": "metaheuristic",
            "initial_temp": self.initial_temp,
            "cooling_rate": self.cooling_rate,
        }

    def _calibrate_initial_temp(self, chrom: List[int], n_samples: int = 30,
                                 target_accept: float = 0.8) -> float:
        """초기 샘플링으로 평균 악화 delta를 측정해 초기온도를 보정.
        T = -avg_delta / ln(target_accept) → 초기 수락률이 target_accept에 근접.

        솔버 간 objective 일관성을 위해 _fitness(우선순위 가중 완료시간) 기준.
        """
        if len(chrom) < 2:
            return self.initial_temp
        base = self._fitness(chrom)
        deltas = []
        for _ in range(n_samples):
            neighbor = self._neighbor(chrom)
            delta = self._fitness(neighbor) - base
            if delta > 0:
                deltas.append(delta)
        if not deltas:
            return self.initial_temp
        avg_delta = sum(deltas) / len(deltas)
        calibrated = -avg_delta / math.log(target_accept)
        return max(calibrated, self.initial_temp)  # 설정값보다 낮아지지는 않도록

    def _neighbor(self, chrom: List[int]) -> List[int]:
        n = len(chrom)
        c = chrom[:]
        if n < 2:
            return c
        if random.random() < 0.5 or n < 3:
            i, j = random.sample(range(n), 2)
            c[i], c[j] = c[j], c[i]
        else:
            i = random.randrange(n)
            j = random.randrange(n - 1)
            if j >= i:
                j += 1
            val = c.pop(i)
            c.insert(j, val)
        return c

    def solve(self, time_limit_sec: int = None) -> ScheduleResult:
        limit = time_limit_sec if time_limit_sec is not None else self.config.time_limit_sec
        t0 = time_module.time()

        if not self.work_orders:
            return self._build_result([], 0.0, "no_solution")

        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)
        current     = self._initial_solution()
        current_fit = self._fitness(current)  # H: 우선순위 가중 완료시간
        best        = current[:]
        best_fit    = current_fit

        temp       = self._calibrate_initial_temp(current)
        # 보정된 초기온도 기준으로 min_temp도 비례 조정 (1/1000 수준)
        adjusted_min_temp = max(self.min_temp, temp * 1e-3)
        no_improve = 0
        iters      = 0
        max_iters  = self.config.sa_iterations if self.config.sa_iterations > 0 else float("inf")

        # 보정된 초기온도(이후 reheat 상한)
        temp_ceiling = temp

        while time_module.time() - t0 < limit and iters < max_iters:
            neighbor     = self._neighbor(current)
            neighbor_fit = self._fitness(neighbor)
            delta        = neighbor_fit - current_fit

            if delta < 0 or (temp > adjusted_min_temp
                             and random.random() < math.exp(-delta / temp)):
                current     = neighbor
                current_fit = neighbor_fit

            if current_fit < best_fit:
                best       = current[:]
                best_fit   = current_fit
                no_improve = 0
            else:
                no_improve += 1

            if no_improve >= self.reheat_every:
                temp       = min(temp * self.reheat_factor, temp_ceiling)
                no_improve = 0

            temp  = max(temp * self.cooling_rate, adjusted_min_temp)
            iters += 1

        solve_time = time_module.time() - t0
        _, _, ms = self._decode(best)
        logger.info("SA: %d회 | makespan=%.1fmin | %.2fs", iters, ms / 60, solve_time)
        return self._build_result(best, solve_time)
