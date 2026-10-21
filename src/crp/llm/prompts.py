"""Prompt texts shared by EoH and ReEvo (single source, so the two can never differ).

Additions to the plain problem text:
- AVG also counts the unknown containers (as last known ID + 1) under the Maximum strategy,
  see _stack_numbers in schemes.py.
- "Store the score in a variable named priority ... return priority": the original EoH cuts
  the code at the last 'return' and appends 'return priority', so 'return SH' would fail.
  Both methods get the same sentence, so the comparison stays fair.
"""

PROBLEM_DESCRIPTION = (
    "Solving the online container relocation problem (CRP) with a limited look-ahead. "
    "A yard has stacks of containers with a maximum height. Each container's ID is its "
    "retrieval order: container 1 leaves first. Only the top container of a stack can be "
    "moved, so every container above the current target must be relocated to another stack "
    "before the target can leave. Only IDs inside a look-ahead window are known; unknown "
    "containers are treated as one more than the last known ID. The goal is to minimise the "
    "total number of relocations."
)

FUNCTION_DESCRIPTION = (
    "The priority function is called each time a blocking container must be relocated, once "
    "for every candidate destination stack (not full, not the source stack). It returns a "
    "score; the stack with the LOWEST score receives the container, and ties go to the "
    "leftmost stack. Inputs: SH = number of containers in the candidate stack; EMP = free "
    "slots left in it; AVG = average ID in it, counting unknown containers as one more than "
    "the last known ID, rounded down (0 if empty); CUR = ID of the container being moved; "
    "RI = number of containers in the stack with a smaller ID than CUR (they will be blocked "
    "by it); DIFF = smallest ID in the stack minus CUR (about 2.1e9 for an empty stack). The "
    "relocation scheme may also make preventive moves; the function only chooses the "
    "destination. Store the score in a variable named priority and end the function with "
    "return priority."
)

# The seed rule both frameworks start from: lowest stack wins (like TLP).
TEMPLATE_PROGRAM = '''def priority(SH: float, EMP: float, AVG: float, CUR: float, RI: float, DIFF: float) -> float:
    """Score one candidate stack for the container being relocated. Lowest score wins."""
    priority = SH
    return priority
'''
