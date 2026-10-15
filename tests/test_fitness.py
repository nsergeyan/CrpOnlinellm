import pytest

from crp.gp.expression import canonical
from crp.gp.fitness import CachedFitness, ParallelFitness, total_relocations
from crp.paths import TRAINING_SET
from golden import FORMULAS, GOLDEN


def test_total_relocations_matches_golden(training_set):
    assert total_relocations(FORMULAS[3], training_set, 0.3, "max") == GOLDEN[3][2]


def test_parallel_total_equals_serial():
    with ParallelFitness(TRAINING_SET, workers=3) as fitness:
        assert fitness(FORMULAS[3], 0.3, "max") == GOLDEN[3][2]
        assert fitness(FORMULAS[0], 0.1, "max") == GOLDEN[0][3]


def test_canonical_spelling():
    assert canonical("  +   SH\t* RI EMP ") == "+ SH * RI EMP"
    with pytest.raises(ValueError):
        canonical("+ SH")


def test_cached_equals_uncached(training_set):
    calls = []

    def score(text):
        calls.append(text)
        return total_relocations(text, training_set, 0.3, "max")

    cached = CachedFitness(score)
    for text, golden in zip(FORMULAS, GOLDEN):
        assert cached(text) == golden[2]  # first time: really computed
    assert len(calls) == len(FORMULAS) and cached.hits == 0

    for text, golden in zip(FORMULAS, GOLDEN):
        assert cached("  " + text.replace(" ", "   ")) == golden[2]  # same formula, other spacing
    assert len(calls) == len(FORMULAS)  # nothing was recomputed
    assert cached.hits == len(FORMULAS)
