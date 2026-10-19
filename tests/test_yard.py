import pytest

from crp.instance import Instance
from crp.paper import TLP_TOTAL
from crp.yard import Yard

SMALL = Instance("small", ((3, 7, 1), (2, 6, 5), (8, 9, 4)), n_containers=9, max_height=4)


def test_relocate_moves_top_and_counts():
    yard = Yard(SMALL, alpha=1.0)
    yard.relocate(0, 1)
    assert yard.stacks == [[3, 7], [2, 6, 5, 1], [8, 9, 4]]
    assert yard.relocations == 1
    assert yard.target_stack() == 1  # container 1 is now in stack 1


def test_retrieve_is_not_counted():
    yard = Yard(SMALL, alpha=1.0)
    yard.retrieve()  # 1 is on top of stack 0
    assert yard.stacks[0] == [3, 7]
    assert yard.next_target == 2
    assert yard.relocations == 0


def test_instance_is_not_changed():
    yard = Yard(SMALL, alpha=1.0)
    yard.relocate(0, 1)
    assert SMALL.stacks == ((3, 7, 1), (2, 6, 5), (8, 9, 4))


def test_invalid_moves_raise():
    yard = Yard(SMALL, alpha=1.0)
    yard.relocate(0, 1)  # stack 1 now has 4 = max height
    with pytest.raises(ValueError, match="full"):
        yard.relocate(2, 1)
    with pytest.raises(ValueError, match="onto itself"):
        yard.relocate(0, 0)

    empty_source = Yard(Instance("e", ((), (1,)), n_containers=1, max_height=4), alpha=1.0)
    with pytest.raises(ValueError, match="empty"):
        empty_source.relocate(0, 1)

    target_buried = Yard(Instance("b", ((1, 2), ()), n_containers=2, max_height=4), alpha=1.0)
    with pytest.raises(ValueError, match="not on top"):
        target_buried.retrieve()


def _tlp(yard: Yard) -> int:
    """TLP (lowest stack, leftmost on ties) using only Yard methods."""
    while not yard.is_done():
        src = yard.target_stack()
        while yard.stacks[src][-1] != yard.next_target:
            candidates = [i for i in range(len(yard.stacks)) if i != src and not yard.is_full(i)]
            dst = min(candidates, key=lambda i: len(yard.stacks[i]))  # min keeps the first on ties
            yard.relocate(src, dst)
        yard.retrieve()
    return yard.relocations


def test_tlp_through_yard_matches_paper(test_set):
    assert sum(_tlp(Yard(inst, alpha=1.0)) for inst in test_set) == TLP_TOTAL


def test_window_moves_after_retrieval():
    yard = Yard(SMALL, alpha=0.3)  # N = 9, so alpha * N = 2.7
    assert yard.last_visible() == 3  # int(1 + 2.7)
    yard.retrieve()
    assert yard.last_visible() == 4  # int(2 + 2.7)


def test_hidden_values():
    yard = Yard(SMALL, alpha=0.3)
    assert yard.value(3) == 3  # visible: real ID
    assert yard.value(4) == 4  # hidden: last visible + 1
    assert yard.value(9) == 4  # all hidden containers look the same


def test_alpha_one_sees_everything():
    yard = Yard(SMALL, alpha=1.0)
    assert all(yard.value(c) == c for c in range(1, 10))
