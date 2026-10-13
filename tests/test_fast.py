"""The fast scheme must give exactly the same results as the reference scheme."""
from pathlib import Path

import pytest

from crp.gp.expression import compile_formula, make_priority
from crp.instance import load_dataset
from crp.schemes import solve_unrestricted, solve_unrestricted_fast
from crp.yard import Yard

ROOT = Path(__file__).resolve().parent.parent
TRAINING = ROOT / "data" / "training"
REFERENCE = ROOT / "cpp_reference" / "reference_data"

_unres = [l for l in (REFERENCE / "expressions_unres.txt").read_text().splitlines() if l.strip()]
_res = [l for l in (REFERENCE / "expressions_res.txt").read_text().splitlines() if l.strip()]
FORMULAS = ["+ SH * RI EMP", "- AVG CUR", "/ DIFF EMP", _unres[0], _unres[1], _res[0], _res[1]]
ALPHAS = (1.0, 0.5, 0.3, 0.1)

# Totals on data/training (Maximum) from the reference path (solve_unrestricted + evaluate),
# recorded before any optimisation. One row per formula, columns = ALPHAS.
GOLDEN = [
    (28949, 28115, 27629, 29654),
    (51539, 53931, 59680, 63774),
    (67167, 67963, 71170, 74364),
    (23631, 23731, 24582, 28561),
    (23577, 23773, 25169, 34281),
    (24116, 24100, 25096, 33966),
    (24716, 24380, 25325, 34338),
]


@pytest.fixture(scope="module")
def training():
    return load_dataset(TRAINING)


def test_fast_scheme_matches_golden(training):
    def total(text, alpha):
        f = compile_formula(text)
        return sum(solve_unrestricted_fast(Yard(inst, alpha, "max"), f) for inst in training)

    assert [tuple(total(text, a) for a in ALPHAS) for text in FORMULAS] == GOLDEN


@pytest.mark.parametrize("hidden", ["max", "ignore"])
def test_fast_and_reference_make_same_decisions(training, hidden):
    def outcome(solve, yard, priority):
        try:
            return solve(yard, priority), yard.stacks
        except NotImplementedError:
            return "undefined C++ case"

    for text in FORMULAS:
        slow, fast = make_priority(text), compile_formula(text)
        for alpha in ALPHAS:
            for inst in training[::20]:
                assert outcome(solve_unrestricted, Yard(inst, alpha, hidden), slow) == \
                       outcome(solve_unrestricted_fast, Yard(inst, alpha, hidden), fast)
