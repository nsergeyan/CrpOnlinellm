import random

import pytest

from crp.gp.expression import canonical
from crp.gp.tree import GPTree, full_tree, grow_tree, initial_population
from golden import reference_formulas


def test_depths_and_sizes():
    tree = GPTree.from_text("+ SH * RI EMP")
    assert tree.depths == (0, 1, 1, 2, 2)
    assert tree.sizes == (5, 1, 3, 1, 1)
    assert tree.depth() == 2
    assert tree.subtree(2) == ("*", "RI", "EMP")


def test_full_depth_five_tree_has_63_nodes():
    def full(depth):
        return ["SH"] if depth == 0 else ["+", *full(depth - 1), *full(depth - 1)]

    tree = GPTree(full(5))
    assert len(tree) == 63 and tree.depth() == 5


def test_round_trip_on_reference_formulas():
    for name in ("expressions_res.txt", "expressions_unres.txt"):
        for line in reference_formulas(name):
            assert GPTree.from_text(line).text() == canonical(line)


@pytest.mark.parametrize("bad", ["+ SH", "SH RI", "+ SH FOO", ""])
def test_malformed_trees_raise(bad):
    with pytest.raises(ValueError):
        GPTree.from_text(bad)


def test_full_trees_are_complete():
    rng = random.Random(0)
    for _ in range(20):
        tree = full_tree(rng)
        assert len(tree) == 63 and tree.depth() == 5
        assert all(tree.is_function(i) == (d < 5) for i, d in enumerate(tree.depths))


def test_grow_trees_respect_depth_and_root():
    rng = random.Random(0)
    trees = [grow_tree(rng) for _ in range(200)]
    assert all(t.depth() <= 5 and t.is_function(0) for t in trees)  # root always a function
    assert len({len(t) for t in trees}) > 10  # sizes vary


def test_population_is_half_full_and_reproducible():
    pop = initial_population(1000, random.Random(42))
    full = sum(1 for t in pop if len(t) == 63)
    assert 400 < full < 600
    assert pop == initial_population(1000, random.Random(42))
