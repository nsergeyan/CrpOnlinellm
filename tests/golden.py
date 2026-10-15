"""Golden numbers for the GP evaluation path, shared by test_fast.py and test_fitness.py.

Totals on data/training (Maximum) from the reference path (solve_unrestricted + evaluate),
recorded before any optimisation. One row per formula, columns = ALPHAS.
"""
from crp.paths import REFERENCE_DATA


def reference_formulas(name: str) -> list[str]:
    """The authors' formulas from expressions_res.txt or expressions_unres.txt."""
    return [line for line in (REFERENCE_DATA / name).read_text().splitlines() if line.strip()]


_unres = reference_formulas("expressions_unres.txt")
_res = reference_formulas("expressions_res.txt")
FORMULAS = ["+ SH * RI EMP", "- AVG CUR", "/ DIFF EMP", _unres[0], _unres[1], _res[0], _res[1]]
ALPHAS = (1.0, 0.5, 0.3, 0.1)
GOLDEN = [
    (28949, 28115, 27629, 29654),
    (51539, 53931, 59680, 63774),
    (67167, 67963, 71170, 74364),
    (23631, 23731, 24582, 28561),
    (23577, 23773, 25169, 34281),
    (24116, 24100, 25096, 33966),
    (24716, 24380, 25325, 34338),
]
