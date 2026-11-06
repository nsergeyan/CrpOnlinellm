"""The fully evaluated rules, parent selection (by total or Pareto over yard types), duplicates.

Every fully evaluated rule stays in the archive. The population is the `size` best by total: the
reference for the feedback and the bar for the quick test. With Pareto selection, parents come
from the rules that are best on at least one yard type (ties count for all of them, rules
dominated by another such rule on every type are dropped), with probability proportional to the
number of types they win. Without it, parents come from the population, rank-weighted (1/rank).
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass

from crp.framework.scoring import YardType


@dataclass
class Rule:
    id: int
    code: str
    idea: str
    per_yard: dict[int, int]            # training yard id -> relocations (all 840 yards)
    type_totals: dict[YardType, int]
    repaired: bool = False

    @property
    def total(self) -> int:
        return sum(self.per_yard.values())

    def subtotal(self, ids: list[int]) -> int:
        return sum(self.per_yard[i] for i in ids)


def plain_code(code: str) -> str:
    """The code without docstrings, comments and spacing, to find exact repeats."""
    code = re.sub(r'"""[\s\S]*?"""', "", code)
    return re.sub(r"\s+", " ", re.sub(r"#.*", "", code)).strip()


class Archive:
    def __init__(self, size: int, types: list[YardType]):
        self.size, self.types = size, types
        self.rules: list[Rule] = []

    def add(self, rule: Rule) -> None:
        self.rules.append(rule)

    def population(self) -> list[Rule]:
        return sorted(self.rules, key=lambda r: (r.total, r.id))[: self.size]

    def best(self) -> Rule:
        return self.population()[0]

    def type_best(self, rules: list[Rule] | None = None) -> dict[YardType, int]:
        rules = self.rules if rules is None else rules
        return {t: min(r.type_totals[t] for r in rules) for t in self.types}

    def specialists(self) -> dict[int, list[YardType]]:
        """Rule id -> the yard types it is best on, after dropping dominated rules."""
        best = self.type_best()
        wins = {r.id: [t for t in self.types if r.type_totals[t] == best[t]] for r in self.rules}
        candidates = [r for r in self.rules if wins[r.id]]

        def dominated(r: Rule) -> bool:
            return any(o is not r and all(o.type_totals[t] <= r.type_totals[t] for t in self.types)
                       and any(o.type_totals[t] < r.type_totals[t] for t in self.types) for o in candidates)

        return {r.id: wins[r.id] for r in candidates if not dominated(r)}

    def select_parents(self, two: bool, pareto: bool, rng: random.Random) -> list[Rule]:
        """One parent (refine), or two different ones (merge) when the archive has two rules."""
        if pareto:
            wins = self.specialists()
            pool = [r for r in self.rules if r.id in wins]
            weight = {r.id: len(wins[r.id]) for r in pool}
        else:
            pool = self.population()
            weight = {r.id: 1 / rank for rank, r in enumerate(pool, 1)}
        first = rng.choices(pool, weights=[weight[r.id] for r in pool])[0]
        if not two:
            return [first]
        partners = [r for r in pool if r is not first]
        if pareto:  # prefer a partner that is best on yard types the first one is not
            partners = [r for r in partners if set(wins[r.id]) - set(wins[first.id])] or partners
        if partners:
            return [first, rng.choices(partners, weights=[weight[r.id] for r in partners])[0]]
        rest = [r for r in self.population() if r is not first]  # Pareto pool of one: next best
        return [first, rest[0]] if rest else [first]
