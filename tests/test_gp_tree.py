from pathlib import Path

import pytest

from crp.gp.expression import canonical
from crp.gp.tree import GPTree

REFERENCE = Path(__file__).resolve().parent.parent / "cpp_reference" / "reference_data"


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
        for line in (REFERENCE / name).read_text().splitlines():
            if line.strip():
                assert GPTree.from_text(line).text() == canonical(line)


@pytest.mark.parametrize("bad", ["+ SH", "SH RI", "+ SH FOO", ""])
def test_malformed_trees_raise(bad):
    with pytest.raises(ValueError):
        GPTree.from_text(bad)
