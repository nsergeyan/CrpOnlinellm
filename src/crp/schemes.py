"""Relocation schemes: the fixed loop that asks a priority function where to move.

Mirrors cpp_reference/schemes/UnrestrictedAutomaticHeuristic.cpp (Algorithm 2).
"""
from __future__ import annotations

from typing import Callable

from crp.terminals import compute_terminals
from crp.yard import INT_MAX, Yard

PriorityFunction = Callable[[dict[str, int]], float]  # terminals -> score, lowest wins


def solve_unrestricted(yard: Yard, priority: PriorityFunction) -> int:
    """Retrieve every container; return the number of relocations."""
    while not yard.is_done():
        src = yard.target_stack()
        while yard.stacks[src][-1] != yard.next_target:
            dst = _best_destination(yard, src, priority)
            # preventive moves: don't let the moved container block dst's top
            while yard.stacks[dst] and yard.top_value(dst) < yard.top_value(src):
                safe = _safe_stack(yard, src, dst)
                if safe is None:
                    break
                yard.relocate(dst, safe)
            yard.relocate(src, dst)
        yard.retrieve()
    return yard.relocations


def _best_destination(yard: Yard, src: int, priority: PriorityFunction) -> int:
    """Lowest score among non-full stacks other than src; leftmost wins ties."""
    best, best_score = -1, float("inf")
    for dst in range(len(yard.stacks)):
        if dst != src and not yard.is_full(dst):
            score = priority(compute_terminals(yard, src, dst))
            if score < best_score:  # strict <, so the leftmost tie stays
                best, best_score = dst, score
    return best


def _safe_stack(yard: Yard, src: int, dst: int) -> int | None:
    """Where to put dst's top so it isn't blocked: copy of the C++ search."""
    top = yard.top_value(dst)
    chosen, lowest = None, INT_MAX
    for s in range(len(yard.stacks)):
        if s in (src, dst) or yard.is_full(s):
            continue
        smallest = yard.min_value(s)
        if smallest > top:
            if lowest > smallest:
                chosen, lowest = s, smallest
            elif smallest == INT_MAX:  # empty stack: always taken, last one wins
                chosen, lowest = s, 0
    return chosen
