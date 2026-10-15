"""Terminals: the numbers a priority function sees about one candidate stack.

Mirrors cpp_reference/gp/Terminals.cpp (CalculateTerminals) and the ContainerYard
helpers it calls (reshuffleIndex, GetMinimumStack, calculateAverageContainerID).
Terminal set C only: SH, EMP, AVG, CUR, RI, DIFF.
"""
from __future__ import annotations

from crp.yard import INT_MAX, Yard

UNDEFINED_IN_CPP = "C++ behaviour is undefined here (Ignore strategy only), see docs/paper_vs_code.md row 11"


def compute_terminals(yard: Yard, src: int, dst: int) -> dict[str, int]:
    """Terminal values for moving the top container of src onto dst."""
    cur = yard.top_value(src)
    values = [v for v in map(yard.value, yard.stacks[dst]) if v != -1]  # Ignore: skip hidden
    height = len(yard.stacks[dst])
    smallest = min(values, default=INT_MAX)
    if (height > 0 and not values) or (smallest == INT_MAX and cur < 0):
        raise NotImplementedError(UNDEFINED_IN_CPP)
    return {
        "SH": height,
        "EMP": yard.max_height - height,
        "AVG": int(sum(values) / len(values)) if height > 0 else 0,
        "CUR": cur,
        "RI": sum(1 for v in values if v < cur),
        "DIFF": smallest - cur,
    }
