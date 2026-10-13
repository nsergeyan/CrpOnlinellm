import random

import pytest

from crp.gp import crossover
from crp.gp.crossover import _try_points
from crp.gp.tree import GPTree, full_tree, initial_population

T = GPTree.from_text


@pytest.mark.parametrize("op", crossover.OPERATORS)
def test_children_are_valid_and_within_depth(op):
    rng = random.Random(0)
    pop = initial_population(60, rng)
    for male, female in zip(pop, reversed(pop)):
        child = op(male, female, rng)
        if child is not None:  # GPTree() already checks the structure
            assert child.depth() <= 5


def test_gives_up_after_five_tries():
    male, female = full_tree(random.Random(1)), full_tree(random.Random(2))
    calls = []

    def leaf_onto_root():  # female's whole depth-5 tree at a male leaf (depth 5): too deep
        calls.append(1)
        return 62, 0

    assert _try_points(male, female, leaf_onto_root) is None
    assert len(calls) == 5


def test_simple_swaps_one_subtree():
    rng = random.Random(3)
    male, female = T("+ SH RI"), T("* EMP CUR")
    children = {crossover.simple(male, female, rng).text() for _ in range(200)}
    # function point (prob 0.9) or a leaf in each parent
    assert children <= {"* EMP CUR", "EMP", "CUR", "+ * EMP CUR RI", "+ SH * EMP CUR",
                        "+ EMP RI", "+ CUR RI", "+ SH EMP", "+ SH CUR"}
    assert "+ SH * EMP CUR" in children


def test_context_preserved_keeps_male_shape_on_same_shapes():
    rng = random.Random(4)
    male, female = full_tree(random.Random(5)), full_tree(random.Random(6))
    for _ in range(50):
        child = crossover.context_preserved(male, female, rng)
        assert child.depths == male.depths


def test_uniform_takes_each_node_from_a_parent():
    rng = random.Random(7)
    male, female = full_tree(random.Random(8)), full_tree(random.Random(9))
    child = crossover.uniform(male, female, rng)
    assert child.depths == male.depths
    assert all(c in (m, f) for c, m, f in zip(child.nodes, male.nodes, female.nodes))


def test_size_fair_picks_similar_sizes():
    rng = random.Random(10)
    male, female = full_tree(random.Random(11)), full_tree(random.Random(12))
    for _ in range(50):
        child = crossover.size_fair(male, female, rng)
        # full trees: a female subtree only fits if it is no taller than the male one it replaces
        assert child is None or len(child) <= len(male)


def test_one_point_copies_ecf_extra_skip():
    # common region in ECF: (0,0) and (1,1); after the differing pair (SH vs *) it skips
    # the subtrees AND one more node, so the pair (RI, EMP) is never a crossover point
    rng = random.Random(13)
    male, female = T("+ SH RI"), T("+ * SH RI EMP")
    children = {crossover.one_point(male, female, rng).text() for _ in range(200)}
    assert children == {"+ * SH RI EMP", "+ * SH RI RI"}


def test_mate_uses_all_five_operators():
    seen = set()
    rng = random.Random(14)
    originals = crossover.OPERATORS

    def spy(op):
        return lambda m, f, r: (seen.add(op.__name__), op(m, f, r))[1]

    crossover.OPERATORS = tuple(spy(op) for op in originals)
    try:
        for _ in range(100):
            crossover.mate(T("+ SH RI"), T("* EMP CUR"), rng)
    finally:
        crossover.OPERATORS = originals
    assert seen == {op.__name__ for op in originals}
