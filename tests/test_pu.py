import pytest

from crp.pu import solve_pu
from crp.paper import PU_TOTALS
from crp.yard import Yard


@pytest.mark.parametrize("variant, alpha", list(PU_TOTALS))
def test_pu_matches_paper(test_set, variant, alpha):
    total = sum(solve_pu(Yard(inst, alpha=alpha), variant) for inst in test_set)
    assert total == PU_TOTALS[variant, alpha]
