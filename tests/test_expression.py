import random
from pathlib import Path

import pytest

from crp.gp.expression import compile_formula, evaluate, make_priority, parse
from crp.instance import load_dataset
from crp.schemes import solve_unrestricted
from crp.yard import Yard

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "caserta_840"
REFERENCE = ROOT / "cpp_reference" / "reference_data"

T = {"SH": 3, "EMP": 2, "AVG": 5, "CUR": 4, "RI": 1, "DIFF": 0}


def test_parse_builds_tree():
    assert parse("+ SH * RI EMP") == ("+", "SH", ("*", "RI", "EMP"))


def test_evaluate_example():
    assert evaluate(parse("+ SH * RI EMP"), T) == 3 + 1 * 2


def test_minus_is_left_minus_right():
    assert evaluate(parse("- SH RI"), T) == 3 - 1


def test_protected_division():
    assert evaluate(parse("/ SH DIFF"), T) == 1.0  # DIFF = 0
    assert evaluate(parse("/ SH EMP"), T) == 1.5


@pytest.mark.parametrize("bad", ["+ SH", "SH RI", "+ SH FOO", ""])
def test_malformed_formulas_raise(bad):
    with pytest.raises(ValueError):
        parse(bad)


def test_all_reference_formulas_parse():
    lines = [
        line
        for name in ("expressions_res.txt", "expressions_unres.txt")
        for line in (REFERENCE / name).read_text().splitlines()
        if line.strip()
    ]
    assert len(lines) == 60
    for line in lines:
        parse(line)


def test_formula_solves_all_instances():
    first = (REFERENCE / "expressions_unres.txt").read_text().splitlines()[0]
    priority = make_priority(first)
    for inst in load_dataset(DATA):
        yard = Yard(inst, alpha=0.5, hidden="max")
        solve_unrestricted(yard, priority)
        assert yard.is_done()


def test_compiled_formula_equals_tree_evaluation():
    rng = random.Random(0)
    names = ("SH", "EMP", "AVG", "CUR", "RI", "DIFF")
    formulas = [
        line
        for name in ("expressions_res.txt", "expressions_unres.txt")
        for line in (REFERENCE / name).read_text().splitlines()
        if line.strip()
    ] + ["+ SH * RI EMP", "/ SH DIFF", "- AVG CUR"]
    for text in formulas:
        tree, f = parse(text), compile_formula(text)
        for _ in range(50):
            t = {k: rng.choice([0, 1, 2, 7, -1, 30, 2_147_483_646]) for k in names}
            assert f(*(float(t[k]) for k in names)) == evaluate(tree, t)
