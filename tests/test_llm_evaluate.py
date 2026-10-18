import os
import subprocess
import sys

import pytest

from crp.llm.evaluate import RuleFailed, compile_rule, evaluate_rule
from crp.paths import ROOT

# Best GP rule of alpha 0.5, seed 1 (results/gp_full.csv), translated once from prefix to Python
# with crp.gp.expression.parse and pasted here. pdiv is GP's protected division. GP scored it train 23,560 and test 24,081.
GP_SEED_1 = """
def pdiv(a, b):
    return 1.0 if abs(b) < 1e-9 else a / b

def priority(SH, EMP, AVG, CUR, RI, DIFF):
    return ((pdiv(pdiv((DIFF * SH), CUR), (DIFF * (CUR + DIFF)))
             - pdiv((SH * DIFF), ((SH + CUR) * (RI * EMP))))
            * (pdiv(((DIFF * EMP) + (RI + EMP)), RI)
               + (((AVG * RI) * (SH - DIFF)) + pdiv(pdiv(CUR, DIFF), (EMP + DIFF)))))
"""

# The seed rule both frameworks start from: lowest stack wins (like TLP).
# Totals at alpha 0.5, Maximum; the slow reference solve_unrestricted gives the same.
RETURN_SH = "def priority(SH, EMP, AVG, CUR, RI, DIFF):\n    return SH\n"
RETURN_SH_TRAIN, RETURN_SH_TEST = 29_695, 30_249


def rule(body: str):
    return compile_rule(f"def priority(SH, EMP, AVG, CUR, RI, DIFF):\n    {body}\n", "priority")


def test_gp_rule_gives_gp_totals(training_set, test_set):
    func = compile_rule(GP_SEED_1, "priority")
    assert evaluate_rule(func, training_set, 0.5) == 23_560
    assert evaluate_rule(func, test_set, 0.5) == 24_081


def test_seed_rule_golden(training_set, test_set):
    func = compile_rule(RETURN_SH, "priority")
    assert evaluate_rule(func, training_set, 0.5) == RETURN_SH_TRAIN
    assert evaluate_rule(func, test_set, 0.5) == RETURN_SH_TEST


def test_math_and_numpy_available(test_set):
    func = compile_rule("def priority(SH, EMP, AVG, CUR, RI, DIFF):\n"
                        "    return math.sqrt(SH) + float(np.log1p(SH))\n", "priority")
    assert evaluate_rule(func, test_set[:5], 0.5) is not None


@pytest.mark.parametrize("body", [
    "raise ValueError('boom')",       # crash
    "return 1 / 0",                   # crash inside arithmetic
    "return float('nan')",            # NaN: would silently pick the last stack
    "return float('inf')",
    "return 'low'",                   # text
    "return None",
    "return True",
    "return [SH]",
])
def test_bad_rules_fail(body, test_set):
    assert evaluate_rule(rule(body), test_set[:5], 0.5) is None


def test_bad_only_sometimes_still_fails(test_set):
    # NaN only for empty stacks: rare, but one bad score is enough to fail the rule
    assert evaluate_rule(rule("return float('nan') if SH == 0 else SH"), test_set, 0.5) is None


def test_numpy_scores_are_accepted(test_set):
    np = pytest.importorskip("numpy")
    plain = evaluate_rule(rule("return SH"), test_set[:20], 0.5)
    assert evaluate_rule(rule("return np.float32(SH)"), test_set[:20], 0.5) == plain
    assert evaluate_rule(rule("return np.int64(SH)"), test_set[:20], 0.5) == plain


def test_compile_errors():
    with pytest.raises(SyntaxError):
        compile_rule("def priority(:\n", "priority")
    with pytest.raises(RuleFailed):
        compile_rule(RETURN_SH, "priority_v2")


def run_cli(tmp_path, code: str, *args: str) -> str:
    path = tmp_path / "gpt.py"
    path.write_text(code)
    out = subprocess.run(
        [sys.executable, "-m", "crp.llm.evaluate", "--code", str(path), *args],
        capture_output=True, text=True, cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert out.returncode == 0, out.stderr
    return out.stdout.strip().splitlines()[-1]


def test_cli_last_line_is_total(tmp_path):
    code = RETURN_SH.replace("priority", "priority_v2")
    last = run_cli(tmp_path, code, "--func", "priority_v2", "--alpha", "0.5", "--set", "test")
    assert int(last) == RETURN_SH_TEST


def test_cli_failure_line(tmp_path):
    last = run_cli(tmp_path, "def priority(SH, EMP, AVG, CUR, RI, DIFF):\n    return 'x'\n",
                   "--alpha", "0.5")
    assert last.startswith("FAILED: RuleFailed")
