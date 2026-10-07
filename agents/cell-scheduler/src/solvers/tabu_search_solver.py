"""
Tabu Search Solver

WO 인덱스 순열 chromosome + BaseSolver 공유 decoder.
swap 이웃 전탐색, tabu 리스트, aspiration criterion, diversification.
"""

import logging
import random
import time as time_module
from typing import Any, Dict, List, Optional, Tuple

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


class TabuSearchSolver(BaseSolver):
    """Tabu search — swap neighborhood, aspiration, diversification on stagnation."""

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
        self.tabu_tenure    = self.config.tabu_tenure
        self.max_no_improve = self.config.diversification_freq

    def get_solver_info(self) -> Dict[str, Any]:
        return {
            "solver": "TabuSearch",
            "type": "metaheuristic",
            "tabu_tenure": self.tabu_tenure,
        }

    def _all_neighbors(
        self, chrom: List[int]
    ) -> List[Tuple[List[int], Tuple[str, int, int]]]:
        """swap + insert 이웃 모두 생성. 이동 종류를 tabu key에 포함해 구분."""
        n = len(chrom)
        result: List[Tuple[List[int], Tuple[str, int, int]]] = []
        # swap
        for i in range(n):
            for j in range(i + 1, n):
                c = chrom[:]
                c[i], c[j] = c[j], c[i]
                result.append((c, ("swap", i, j)))
        # insert (i에서 빼서 j에 삽입)
        for i in range(n):
            for j in range(n):
                if i == j or j == i + 1 or (i == n - 1 and j == n):
                    continue  # no-op 케이스 제거
                if not (0 <= j <= n - 1):
                    continue
                c = chrom[:]
                val = c.pop(i)
                c.insert(j, val)
                result.append((c, ("insert", i, j)))
        return result

    def solve(self, time_limit_sec: int = None) -> ScheduleResult:
        limit = time_limit_sec if time_limit_sec is not None else self.config.time_limit_sec
        t0 = time_module.time()

        if not self.work_orders:
            return self._build_result([], 0.0, "no_solution")

        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)
        n = len(self.work_orders)

        current     = self._initial_solution()
        current_fit = self._fitness(current)  # H: 우선순위 가중 완료시간
        best        = current[:]
        best_fit    = current_fit

        tabu_list:  List[Tuple] = []
        # tabu_tenure는 list 크기 상한 (#8 통일: tabu_list_size 폐기)
        max_no_improve = self.max_no_improve
        no_improve = 0
        iters      = 0
        max_iters  = self.config.tabu_iterations if self.config.tabu_iterations > 0 else float("inf")

        while time_module.time() - t0 < limit and iters < max_iters:
            neighbors = self._all_neighbors(current)

            best_nb:     Optional[List[int]] = None
            best_nb_fit  = float("inf")
            best_move:   Optional[Tuple]     = None

            for nb, move in neighbors:
                fit      = self._fitness(nb)
                is_tabu  = move in tabu_list
                aspirate = fit < best_fit
                if (not is_tabu or aspirate) and fit < best_nb_fit:
                    best_nb     = nb
                    best_nb_fit = fit
                    best_move   = move

            if best_nb is None:
                if not neighbors:
                    break
                nb, move = random.choice(neighbors)
                best_nb, best_move, best_nb_fit = nb, move, self._fitness(nb)

            current     = best_nb
            current_fit = best_nb_fit
            tabu_list.append(best_move)
            if len(tabu_list) > self.tabu_tenure:
                tabu_list.pop(0)

            if current_fit < best_fit:
                best       = current[:]
                best_fit   = current_fit
                no_improve = 0
            else:
                no_improve += 1

            if no_improve >= self.max_no_improve:
                current = list(range(n))
                random.shuffle(current)
                current_fit = self._fitness(current)
                tabu_list.clear()
                no_improve = 0

            iters += 1

        solve_time = time_module.time() - t0
        _, _, ms = self._decode(best)
        logger.info("Tabu: %d회 | makespan=%.1fmin | %.2fs", iters, ms / 60, solve_time)
        return self._build_result(best, solve_time)
