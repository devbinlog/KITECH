"""
Genetic Algorithm Solver

WO 인덱스 순열 chromosome + BaseSolver 공유 decoder.
PMX 교차 + swap/insert 변이 + 토너먼트 선택 + elitism.
"""

import logging
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


class GeneticAlgorithmSolver(BaseSolver):
    """GA solver — WO-permutation chromosome, shared greedy decoder."""

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
        self.population_size = self.config.population_size
        self.crossover_rate  = self.config.crossover_rate
        self.mutation_rate   = self.config.mutation_rate
        self.elitism_ratio   = self.config.elitism_ratio

    def get_solver_info(self) -> Dict[str, Any]:
        return {
            "solver": "GeneticAlgorithm",
            "type": "metaheuristic",
            "population_size": self.population_size,
            "crossover_rate": self.crossover_rate,
            "mutation_rate": self.mutation_rate,
        }

    # ── GA 연산자 ─────────────────────────────────────────────────────────────

    def _init_population(self) -> List[List[int]]:
        n = len(self.work_orders)
        base = list(range(n))
        pop = [base[:], self._initial_solution()]
        while len(pop) < self.population_size:
            c = base[:]
            random.shuffle(c)
            pop.append(c)
        return pop[:self.population_size]

    # _fitness는 base_solver.BaseSolver._fitness를 그대로 상속한다 (H 통일).

    def _tournament(self, pop: List[List[int]], fits: List[float], k: int = 3) -> List[int]:
        idx = random.sample(range(len(pop)), min(k, len(pop)))
        return pop[min(idx, key=lambda i: fits[i])][:]

    def _pmx(self, p1: List[int], p2: List[int]) -> Tuple[List[int], List[int]]:
        n = len(p1)
        if n < 2:
            return p1[:], p2[:]
        a, b = sorted(random.sample(range(n), 2))

        def _make(pa, pb):
            child = [-1] * n
            child[a:b + 1] = pa[a:b + 1]
            for i in range(a, b + 1):
                val = pb[i]
                if val not in child[a:b + 1]:
                    pos = i
                    while a <= pos <= b:
                        pos = pb.index(pa[pos])
                    child[pos] = val
            for i in range(n):
                if child[i] == -1:
                    child[i] = pb[i]
            return child

        return _make(p1, p2), _make(p2, p1)

    def _mutate(self, chrom: List[int]) -> List[int]:
        c = chrom[:]
        n = len(c)
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

    # ── solve ─────────────────────────────────────────────────────────────────

    def solve(self, time_limit_sec: int = None) -> ScheduleResult:
        limit = time_limit_sec if time_limit_sec is not None else self.config.time_limit_sec
        t0 = time_module.time()

        if not self.work_orders:
            return self._build_result([], 0.0, "no_solution")

        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)
        pop  = self._init_population()
        fits = [self._fitness(c) for c in pop]

        best_idx   = min(range(len(pop)), key=lambda i: fits[i])
        best_chrom = pop[best_idx][:]
        best_fit   = fits[best_idx]
        generation = 0
        n_elite = max(1, int(self.population_size * self.elitism_ratio))
        max_gens = self.config.generations if self.config.generations > 0 else float("inf")

        while time_module.time() - t0 < limit and generation < max_gens:
            # 상위 n_elite 보존
            ranked = sorted(range(len(pop)), key=lambda i: fits[i])[:n_elite]
            new_pop = [pop[i][:] for i in ranked]
            while len(new_pop) < self.population_size:
                p1 = self._tournament(pop, fits)
                p2 = self._tournament(pop, fits)
                c1, c2 = (self._pmx(p1, p2) if random.random() < self.crossover_rate
                          else (p1[:], p2[:]))
                if random.random() < self.mutation_rate:
                    c1 = self._mutate(c1)
                if random.random() < self.mutation_rate:
                    c2 = self._mutate(c2)
                new_pop.extend([c1, c2])
            pop  = new_pop[:self.population_size]
            fits = [self._fitness(c) for c in pop]
            gen_best = min(range(len(pop)), key=lambda i: fits[i])
            if fits[gen_best] < best_fit:
                best_fit   = fits[gen_best]
                best_chrom = pop[gen_best][:]
            generation += 1

        solve_time = time_module.time() - t0
        _, _, ms = self._decode(best_chrom)
        logger.info("GA: %d세대 | makespan=%.1fmin | %.2fs", generation, ms / 60, solve_time)
        return self._build_result(best_chrom, solve_time)
