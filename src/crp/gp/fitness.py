"""Fitness of a GP formula: total relocations over a set of instances (lower is better).

Mirrors the fitness in cpp_reference/gp/CrpEvalOp.cpp. CachedFitness skips formulas
that were already scored.
"""
from __future__ import annotations

from typing import Callable

from crp.gp.expression import canonical, compile_formula
from crp.instance import Instance
from crp.schemes import solve_unrestricted_fast
from crp.yard import Yard


def total_relocations(text: str, instances: list[Instance], alpha: float, hidden: str) -> int:
    """Run one formula on every instance, in this process."""
    f = compile_formula(text)
    return sum(solve_unrestricted_fast(Yard(inst, alpha, hidden), f) for inst in instances)


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
