from pathlib import Path

import pytest

from crp.gp.fitness import ParallelFitness, total_relocations
from crp.instance import load_dataset
from test_fast import FORMULAS, GOLDEN

TRAINING = Path(__file__).resolve().parent.parent / "data" / "training"


@pytest.fixture(scope="module")
def training():
    return load_dataset(TRAINING)


def test_total_relocations_matches_golden(training):
    assert total_relocations(FORMULAS[3], training, 0.3, "max") == GOLDEN[3][2]


def test_parallel_total_equals_serial():
    with ParallelFitness(TRAINING, workers=3) as fitness:
        assert fitness(FORMULAS[3], 0.3, "max") == GOLDEN[3][2]
        assert fitness(FORMULAS[0], 0.1, "max") == GOLDEN[0][3]
