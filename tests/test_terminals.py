import pytest

from crp.instance import Instance
from crp.terminals import INT_MAX, compute_terminals
from crp.yard import Yard

SMALL = Instance("small", ((3, 7, 1), (2, 6, 5), (8, 9, 4)), n_containers=9, max_height=4)


def test_terminals_with_hidden_maximum():
    yard = Yard(SMALL, alpha=0.3, hidden="max")  # last visible = 3, hidden show as 4
    # move container 1 onto stack 1 = [2, 6, 5], seen as [2, 4, 4]
    assert compute_terminals(yard, 0, 1) == {
        "SH": 3, "EMP": 1, "AVG": 3, "CUR": 1, "RI": 0, "DIFF": 1,
    }


def test_ri_counts_smaller_values():
    yard = Yard(SMALL, alpha=1.0, hidden="max")  # everything visible
    # move container 4 onto stack 1 = [2, 6, 5]: only 2 is smaller than 4
    t = compute_terminals(yard, 2, 1)
    assert t["CUR"] == 4
    assert t["RI"] == 1
    assert t["DIFF"] == 2 - 4
    assert t["AVG"] == 4  # int(13 / 3) = int(4.33)


def test_empty_destination():
    inst = Instance("e", ((2, 1), ()), n_containers=2, max_height=4)
    t = compute_terminals(Yard(inst, alpha=1.0, hidden="max"), 0, 1)
    assert t["SH"] == 0 and t["EMP"] == 4 and t["AVG"] == 0
    assert t["DIFF"] == INT_MAX - 1


def test_undefined_cpp_cases_raise_under_ignore():
    # alpha = 0: only the target (1) is visible, everything else is -1
    all_hidden = Instance("h", ((1, 3), (2,)), n_containers=3, max_height=4)
    with pytest.raises(NotImplementedError):
        compute_terminals(Yard(all_hidden, alpha=0.0, hidden="ignore"), 0, 1)  # AVG of [-1]

    hidden_cur = Instance("c", ((1, 3), ()), n_containers=3, max_height=4)
    with pytest.raises(NotImplementedError):
        compute_terminals(Yard(hidden_cur, alpha=0.0, hidden="ignore"), 0, 1)  # CUR -1, empty dst
