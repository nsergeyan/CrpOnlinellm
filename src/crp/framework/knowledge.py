"""Component 1: CRP knowledge for the prompts, and the two seed rules.

The knowledge text describes concepts from the CRP literature (badly-placed containers and stack
quality as in Jin & Tanaka 2023, the Min-Max idea behind PU1/PU2) in terms of the six inputs.
It contains no numbers from the test set. The Min-Max seed was chosen on the training set.
"""
from crp.llm.prompts import TEMPLATE_PROGRAM

KNOWLEDGE = """Known facts about the container relocation problem:
- A container is badly placed if some container below it in the same stack leaves earlier
  (has a smaller ID). Every badly placed container has to be relocated at least once more, so
  the main goal is to avoid creating badly placed containers.
- The smallest ID in a stack is the stack's quality. If DIFF > 0, every container in the stack
  leaves after CUR, so CUR stays well placed there (a safe stack). If DIFF < 0, CUR blocks the RI
  containers below it and will have to move again.
- Min-Max: among safe stacks, prefer the one with the smallest DIFF, so stacks whose containers
  leave much later stay free for containers that leave later too. If no stack is safe, prefer the
  largest DIFF, so the next forced relocation of CUR happens as late as possible.
- An empty stack (DIFF about 2.1e9) is always safe, but it is the most flexible place in the yard.
- SH and EMP matter too: a tall stack holds more containers that CUR could end up above, and a
  nearly full stack leaves little room for later moves.
- Online setting: only IDs inside the look-ahead window are known, and every unknown container
  counts as one more than the last known ID. With a small window many stacks have the same DIFF
  and AVG, so the other inputs (SH, EMP, RI) must tell them apart."""

MINMAX_SEED = '''def priority(SH: float, EMP: float, AVG: float, CUR: float, RI: float, DIFF: float) -> float:
    """Score one candidate stack for the container being relocated. Lowest score wins."""
    # Min-Max: the closest safe stack (DIFF > 0) first, else the stack with the largest DIFF;
    # ties (common when few IDs are known) go to the lowest stack
    priority = (DIFF if DIFF > 0 else 1e10 - DIFF) * 100 + SH
    return priority
'''

SEEDS = {
    "minmax": ("Min-Max with ties broken by the lowest stack.", MINMAX_SEED),
    "lowest": ("Put the container on the lowest stack.", TEMPLATE_PROGRAM),
}
