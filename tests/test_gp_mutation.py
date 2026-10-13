import random

import pytest

from crp.gp import mutation
from crp.gp.tree import GPTree, full_tree, initial_population

T = GPTree.from_text


class ScriptedRng(random.Random):
    """random.Random whose randrange answers come from a script (for exact ECF cases)."""

    def __init__(self, picks):
        super().__init__(0)
        self.picks = list(picks)

    def randrange(self, *args):
        return self.picks.pop(0)


@pytest.mark.parametrize("op", mutation.OPERATORS)
def test_mutants_are_valid_and_within_depth(op):
    rng = random.Random(0)
    for tree in initial_population(100, rng):
        new = op(tree, rng)
        if new is not None:
            assert new.depth() <= 5


def test_gauss_never_changes_anything():
    rng = random.Random(1)
    assert all(mutation.gauss(t, rng) is None for t in initial_population(50, rng))


def test_node_complement_swaps_one_operator():
    child = mutation.node_complement(T("+ SH * RI EMP"), random.Random(2))
    assert child.text() in {"- SH * RI EMP", "+ SH / RI EMP"}


def test_node_complement_fails_on_a_terminal():
    assert mutation.node_complement(T("SH"), random.Random(3)) is None


def test_permutation_swaps_children_half_the_time():
    rng = random.Random(4)
    results = [mutation.permutation(T("+ SH RI"), rng) for _ in range(1000)]
    failed = results.count(None)  # 4 tries all on a terminal: (2/3)^4 = 20%
    assert 150 < failed < 250
    done = [r.text() for r in results if r is not None]
    assert set(done) == {"+ SH RI", "+ RI SH"}
    assert 0.4 < done.count("+ RI SH") / len(done) < 0.6


def test_node_replace_keeps_arity():
    rng = random.Random(5)
    for _ in range(100):
        child = mutation.node_replace(T("+ SH RI"), rng)
        if child is not None:
            assert len(child) == 3 and child.text() != "+ SH RI"


def test_hoist_can_leave_a_single_terminal():
    rng = random.Random(6)
    results = {mutation.hoist(T("+ SH RI"), rng).text() for _ in range(100)}
    assert results == {"+ SH RI", "SH", "RI"}


def test_shrink_replaces_a_subtree_by_a_terminal():
    child = mutation.shrink(T("+ SH * RI EMP"), random.Random(7))
    assert len(child) in (1, 3)


def test_subtree_success_needs_a_good_node_within_three_tries():
    tree = full_tree(random.Random(8))  # positions 5, 6 are leaves at depth 5; 0 is the root
    assert tree.depths[5] == 5 and tree.depths[6] == 5
    assert mutation.subtree(tree, ScriptedRng([5, 6, 5, 0])) is None  # found on 4th try: ECF fails
    assert mutation.subtree(tree, ScriptedRng([5, 6, 0])) is not None  # found on 3rd try: ok


def test_mutate_respects_probability():
    tree = T("+ SH * RI EMP")
    assert mutation.mutate(tree, random.Random(9), prob=0.0) is tree
    rng = random.Random(10)
    changed = sum(mutation.mutate(tree, rng) != tree for _ in range(2000))
    assert 300 < changed < 600  # 0.3 of the time an operator runs, some of them change nothing
