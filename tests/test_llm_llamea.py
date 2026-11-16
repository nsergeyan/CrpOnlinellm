"""LLaMEA end to end with a FAKE LLM server.

Canned answers, no API key, no cost. LLaMEA is untouched: it talks to the fake server through
our launcher. Skipped until frameworks/setup_llamea.sh has run.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

from crp.llm.evaluate import compile_rule, evaluate_rule
from crp.paths import ROOT
from fake_llm import fake_llm

LLAMEA = Path(os.environ.get("LLAMEA_DIR", ROOT / "frameworks" / "llamea")).resolve()
pytestmark = pytest.mark.skipif(not (LLAMEA / ".venv" / "bin" / "python").exists(),
                                reason="LLaMEA not set up (bash frameworks/setup_llamea.sh)")

SIGNATURE = "def priority(SH: float, EMP: float, AVG: float, CUR: float, RI: float, DIFF: float) -> float:"
# LLaMEA's answer format: a description line, then the code block
ANSWERS = [f"# Description: {idea}\n# Code:\n```python\n{SIGNATURE}\n{body}\n```" for idea, body in [
    ("Fewest blocked containers.", "    priority = RI\n    return priority"),
    ("Height plus blocked containers.", "    priority = SH + 10 * RI\n    return priority"),
    ("Always NaN.", "    priority = float('nan')\n    return priority"),       # invalid: scored, fails
    ("Never ends.", "    while True:\n        pass"),                          # invalid: stopped by the time limit
]] + ["I could not think of a better function."]                               # no code: never scored


def test_llamea_run_counts_scored_rules(training_set, tmp_path):
    with fake_llm(ANSWERS) as url:
        done = subprocess.run(
            [str(LLAMEA / ".venv" / "bin" / "python"), str(ROOT / "experiments" / "run_llamea.py"), "run",
             "--alpha", "0.5", "--seed", "1", "--budget", "10", "--model", "fake", "--base-url", url,
             "--out", str(tmp_path), "--time-limit", "2"],
            capture_output=True, text=True, timeout=600,
        )
    assert done.returncode == 0, (done.stdout + done.stderr)[-3000:]
    rules = [json.loads(line) for line in (tmp_path / "llamea_a0.5_s1.jsonl").read_text().splitlines()]
    row = json.loads((tmp_path / "llamea_a0.5_s1.row.json").read_text())

    assert row["llm_calls"] == 15                 # budget 10 + 10% = 11: the start 5, then 5 + 5
    assert len(rules) == 12                       # 3 of the 15 answers had no code
    assert all("def priority" in r["code"] for r in rules)
    assert row["evaluations"] == 10               # only the first 10 scored rules count
    counted = rules[:10]
    assert {r["total"] for r in counted if r["total"] is not None} == {26_452, 27_049}
    assert row["valid_rate"] == sum(r["total"] is not None for r in counted) / 10 < 1
    assert any("TimeoutError" in r["error"] for r in rules if r["error"])
    assert row["train_fitness"] == 26_452 == evaluate_rule(compile_rule(row["code"], "priority"), training_set, 0.5)
