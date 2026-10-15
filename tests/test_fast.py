"""The fast scheme must give exactly the same results as the reference scheme."""
import pytest

from crp.gp.expression import compile_formula, make_priority
from crp.schemes import solve_unrestricted, solve_unrestricted_fast
from crp.yard import Yard
from golden import ALPHAS, FORMULAS, GOLDEN


def test_fast_scheme_matches_golden(training_set):
    def total(text, alpha):
        f = compile_formula(text)
        return sum(solve_unrestricted_fast(Yard(inst, alpha, "max"), f) for inst in training_set)

    assert [tuple(total(text, a) for a in ALPHAS) for text in FORMULAS] == GOLDEN


@pytest.mark.parametrize("hidden", ["max", "ignore"])
def test_fast_and_reference_make_same_decisions(training_set, hidden):
    def outcome(solve, yard, priority):
        try:
            return solve(yard, priority), yard.stacks
        except NotImplementedError:
            return "undefined C++ case"

    for text in FORMULAS:
        slow, fast = make_priority(text), compile_formula(text)
        for alpha in ALPHAS:
            for inst in training_set[::20]:
                assert outcome(solve_unrestricted, Yard(inst, alpha, hidden), slow) == \
                       outcome(solve_unrestricted_fast, Yard(inst, alpha, hidden), fast)
