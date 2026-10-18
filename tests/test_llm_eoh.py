"""EoH end to end with a FAKE LLM: canned answers, no API key, no cost."""
import itertools
import json
import threading

import pytest

pytest.importorskip("eoh")

from eoh import EoH, LLMConfig
from eoh.llm.api_general import InterfaceAPI

from crp.llm.eoh_problem import CRPProblem

GOOD = """{Prefer stacks where the moved container blocks the fewest others.}
```python
def priority(SH: float, EMP: float, AVG: float, CUR: float, RI: float, DIFF: float) -> float:
    return RI
```"""
GOOD_TRAIN = 26_452  # 'return RI' on the training set, alpha 0.5

NAN = """{Return NaN everywhere.}
```python
def priority(SH, EMP, AVG, CUR, RI, DIFF):
    return float('nan')
```"""

MATH = """{Use math without importing it (our compile_rule provides math).}
```python
def priority(SH, EMP, AVG, CUR, RI, DIFF):
    return math.sqrt(SH) + 100 * RI
```"""

GARBAGE = "Sorry, I cannot help with that."


@pytest.fixture
def fake_llm(monkeypatch):
    answers = itertools.cycle([GOOD, NAN, MATH, GARBAGE])
    lock = threading.Lock()  # EoH may call from several threads

    def get_response(self, prompt, max_retries=5):
        if prompt == "1+1=?":  # EoH's connection check at start-up
            return "2"
        with lock:
            return next(answers)

    monkeypatch.setattr(InterfaceAPI, "get_response", get_response)


def test_problem_scores_like_our_evaluator():
    problem = CRPProblem(alpha=0.5)
    assert problem.evaluate(GOOD.split("```python\n")[1].split("```")[0]) == GOOD_TRAIN
    assert problem.evaluate("def priority(SH, EMP, AVG, CUR, RI, DIFF):\n    return 'x'\n") is None


def test_eoh_runs_with_fake_llm(fake_llm, tmp_path):
    llm = LLMConfig(api_endpoint="fake.invalid", api_key="fake", model="fake")
    EoH(llm=llm, problem=CRPProblem(alpha=0.5), pop_size=2, n_pop=2,
        max_sample_nums=4, output_dir=str(tmp_path)).run()

    samples = []
    for path in (tmp_path / "results" / "samples").glob("samples_*~*.json"):
        samples += json.loads(path.read_text())
    by_code = {s["code"]: s["objective"] for s in samples if s["code"]}

    assert any("float('nan')" in code and obj is None for code, obj in by_code.items())
    assert any("math.sqrt" in code and obj is not None for code, obj in by_code.items())
    best = json.loads((tmp_path / "results" / "samples" / "samples_best.json").read_text())
    assert best["objective"] == GOOD_TRAIN
