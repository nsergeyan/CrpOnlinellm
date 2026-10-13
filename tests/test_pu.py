from pathlib import Path

import pytest

from crp.heuristics.pu import solve_pu
from crp.instance import load_dataset
from crp.yard import Yard

DATA = Path(__file__).resolve().parent.parent / "data" / "caserta_840"

# Paper totals over the 840 Caserta instances, Maximum strategy for hidden IDs
PAPER = [
    (1, 1.0, 25_049), (2, 1.0, 24_962),
    (1, 0.5, 25_116), (2, 0.5, 25_027),
    (1, 0.3, 25_905), (2, 0.3, 25_826),
    (1, 0.1, 31_719), (2, 0.1, 31_763),
]


@pytest.mark.parametrize("variant, alpha, expected", PAPER)
def test_pu_matches_paper(variant, alpha, expected):
    total = sum(
        solve_pu(Yard(inst, alpha=alpha, hidden="max"), variant) for inst in load_dataset(DATA)
    )
    assert total == expected
