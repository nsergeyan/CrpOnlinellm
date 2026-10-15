from crp.instance import Instance
from crp.schemes import _best_destination, _safe_stack, solve_unrestricted
from crp.yard import Yard


def _yard(*stacks: tuple[int, ...]) -> Yard:
    n = sum(len(s) for s in stacks)
    return Yard(Instance("t", stacks, n_containers=n, max_height=4), alpha=1.0, hidden="max")


def test_preventive_move_example():
    # target 1 is under 3; priority picks stack 1 (leftmost lowest), but 2 < 3 would be
    # blocked, so 2 first moves to the safe stack 2, then 3 goes onto the emptied stack 1
    yard = _yard((1, 3), (2,), (4,))
    assert solve_unrestricted(yard, lambda t: t["SH"]) == 2
    assert yard.is_done()


def test_ties_go_to_leftmost_stack():
    yard = _yard((1, 2), (), ())
    assert _best_destination(yard, 0, lambda t: 0) == 1


def test_safe_stack_prefers_last_empty():
    yard = _yard((1, 4), (2,), (), (), (3,))
    assert _safe_stack(yard, 0, 1) == 3


def test_safe_stack_smallest_minimum_when_no_empty():
    yard = _yard((1, 5), (2,), (4,), (3,))
    assert _safe_stack(yard, 0, 1) == 3  # min 3 beats min 4, both are > 2


def test_runs_on_all_instances_without_errors(test_set):
    for inst in test_set:
        yard = Yard(inst, alpha=0.3, hidden="max")
        solve_unrestricted(yard, lambda t: t["SH"])
        assert yard.is_done()
