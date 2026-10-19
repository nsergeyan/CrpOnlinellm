"""PU1 and PU2: hand-made rules for the unrestricted CRP (paper baselines).

Mirrors cpp_reference/heuristics/PU1.cpp and PU2.cpp. PU2 = PU1 plus one extra
condition in the fallback step, switched on with variant=2.
"""
from __future__ import annotations

from crp.yard import INT_MAX, Yard

INT_MIN = -2_147_483_648


def solve_pu(yard: Yard, variant: int) -> int:
    """Retrieve every container with PU1 (variant=1) or PU2 (variant=2)."""
    if variant not in (1, 2):
        raise ValueError(f"variant must be 1 or 2, got {variant}")
    while not yard.is_done():
        src = yard.target_stack()
        while yard.stacks[src][-1] != yard.next_target:
            _move_blocking(yard, src, variant)
        yard.retrieve()
    return yard.relocations


def _move_blocking(yard: Yard, src: int, variant: int) -> None:
    """Relocate the top of src (one blocking container), in 1 or 2 moves."""
    top = yard.top_value(src)
    good, lowest = None, INT_MAX       # step 1: stack where every value > top
    fallback, highest = None, INT_MIN  # step 3: stack with the largest minimum
    for s in range(len(yard.stacks)):
        if s == src or yard.is_full(s):
            continue
        smallest = yard.min_value(s)
        if smallest > top:
            if lowest > smallest:
                good, lowest = s, smallest
            elif smallest == INT_MAX:  # empty stack: always taken, last one wins
                good, lowest = s, 0
        elif variant == 2 and _pu2_skips(yard, src, s, highest):
            continue
        elif highest < smallest:
            fallback, highest = s, smallest

    if good is not None:
        yard.relocate(src, good)
        return

    # step 2: free up a stack holding exactly one container
    # (C++ `secondSmallest=!INT_MAX || height==1` assigns instead of comparing,
    # so the condition reduces to "height == 1")
    single, single_value = None, -1
    for s in range(len(yard.stacks)):
        if s != src and len(yard.stacks[s]) == 1 and yard.min_value(s) > single_value:
            single, single_value = s, yard.min_value(s)
    if single is not None:
        home, home_lowest = None, INT_MAX
        for s in range(len(yard.stacks)):
            if s in (src, single) or yard.is_full(s):
                continue
            smallest = yard.min_value(s)
            if smallest > single_value:
                if home_lowest > smallest:
                    home, home_lowest = s, smallest
                elif smallest == INT_MAX:
                    home, home_lowest = s, 0
        if home is not None:
            yard.relocate(single, home)
            yard.relocate(src, single)
            return

    if fallback is None:
        raise RuntimeError("PU found no stack to move to (C++ would use stack -1)")
    yard.relocate(src, fallback)


def _pu2_skips(yard: Yard, src: int, s: int, highest: int) -> bool:
    """PU2 only: skip a stack with one free slot if src has 2+ values below highest."""
    smaller = sum(1 for c in yard.stacks[src] if yard.value(c) < highest)
    return smaller > 1 and yard.max_height - len(yard.stacks[s]) == 1
