"""Fitness of a GP formula: total relocations over a set of instances (lower is better).

Mirrors the fitness in cpp_reference/gp/CrpEvalOp.cpp. ParallelFitness splits the
instances over worker processes; the total is the same, it just finishes sooner.
CachedFitness skips formulas that were already scored.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Callable

from crp.gp.expression import canonical, compile_formula
from crp.instance import Instance, load_dataset
from crp.schemes import solve_unrestricted_fast
from crp.yard import Yard


def total_relocations(text: str, instances: list[Instance], alpha: float, hidden: str) -> int:
    """Run one formula on every instance, in this process."""
    f = compile_formula(text)
    return sum(solve_unrestricted_fast(Yard(inst, alpha, hidden), f) for inst in instances)


_worker_instances: list[Instance] = []  # each worker process loads its own copy once


def _init_worker(directory: str) -> None:
    global _worker_instances
    _worker_instances = load_dataset(directory)


def _worker_total(job: tuple[str, float, str, int, int]) -> int:
    text, alpha, hidden, k, n = job
    return total_relocations(text, _worker_instances[k::n], alpha, hidden)  # every n-th instance


class ParallelFitness:
    """Keeps worker processes alive; each call splits the instances over them."""

    def __init__(self, directory: str | Path, workers: int) -> None:
        self.workers = workers
        self.pool = ProcessPoolExecutor(workers, initializer=_init_worker, initargs=(str(directory),))

    def __call__(self, text: str, alpha: float, hidden: str) -> int:
        jobs = [(text, alpha, hidden, k, self.workers) for k in range(self.workers)]
        return sum(self.pool.map(_worker_total, jobs))

    def close(self) -> None:
        self.pool.shutdown()

    def __enter__(self) -> ParallelFitness:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class CachedFitness:
    """Remembers scores, so a formula seen before is not run again.

    One cache belongs to ONE score function, i.e. one training set, alpha and hidden
    strategy. Make a new cache for every scenario.
    """

    def __init__(self, score: Callable[[str], int]) -> None:
        self._score = score
        self._results: dict[str, int] = {}
        self.hits = 0  # how often a stored result was reused

    def __call__(self, text: str) -> int:
        key = canonical(text)
        if key in self._results:
            self.hits += 1
        else:
            self._results[key] = self._score(key)
        return self._results[key]
