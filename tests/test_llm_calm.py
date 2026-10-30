"""CALM (paper version) on the CRP: our problem file, and the launcher end to end with a FAKE LLM.

The problem-file test needs only our code. The end-to-end test runs CALM's real main.py in its
API mode (no GPU, no training) through our run_crp.py; it is skipped until
frameworks/setup_calm.sh has run.
"""
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from crp.paths import ROOT
from fake_llm import fake_llm

CALM = Path(os.environ.get("CALM_DIR", ROOT / "frameworks" / "calm")).resolve()
needs_calm = pytest.mark.skipif(not (CALM / ".venv" / "bin" / "python").exists(),
                                reason="CALM not set up (bash frameworks/setup_calm.sh)")

SIGNATURE = "def priority(SH: float, EMP: float, AVG: float, CUR: float, RI: float, DIFF: float) -> float:"
# CALM's answer format: the idea in double braces, then one Python block
ANSWERS = [f"{{{{The idea of the algorithm is to {idea}.}}}}\n```python\n{SIGNATURE}\n{body}\n```" for idea, body in [
    ("choose the stack that blocks the fewest containers", "    priority = RI\n    return priority"),
    ("weigh height and blocked containers", "    priority = SH + 10 * RI\n    return priority"),
    ("return an invalid score", "    priority = float('nan')\n    return priority"),
    ("break ties randomly", "    import random\n    priority = RI + random.random()\n    return priority"),
    ("use math without importing it", "    priority = math.sqrt(SH) + 100 * RI\n    return priority"),
]]


def test_problem_file_scores_like_the_shared_evaluator(monkeypatch, training_set):
    from crp.llm.evaluate import RuleFailed, evaluate_rule

    monkeypatch.setenv("CRP_ALPHA", "0.5")
    spec = importlib.util.spec_from_file_location("crp_online", ROOT / "frameworks" / "calm_crp" / "crp_online.py")
    problem = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(problem)
    env = problem.Environment()

    def lowest_stack(SH, EMP, AVG, CUR, RI, DIFF):
        return SH
    calm_total = -sum(env.run_async(lowest_stack, training_set)["performance"])
    assert calm_total == evaluate_rule(lowest_stack, training_set, 0.5) == 29_695
    with pytest.raises(RuleFailed):                          # a NaN score fails the rule, as in EoH
        env.run_async(lambda *inputs: float("nan"), training_set[:1])


@needs_calm
def test_calm_logs_every_scored_rule_and_stops_at_the_budget(tmp_path):
    stub = tmp_path / "stub"
    stub.mkdir()
    # CALM's main.py asks NVIDIA's NVML for GPUs when imported; there are none on a laptop
    (stub / "pynvml.py").write_text("def nvmlInit(): pass\ndef nvmlDeviceGetCount(): return 0\n"
                                    "def nvmlShutdown(): pass\n")
    rule_log, log_name = tmp_path / "rules.jsonl", f"test_{tmp_path.name}"
    try:
        with fake_llm(ANSWERS) as url:
            done = subprocess.run(
                [str(CALM / ".venv" / "bin" / "python"), "run_crp.py", "--alpha", "0.5", "--model", "online/fake",
                 "--base-url", url, "--rule-log", str(rule_log), "--log-name", log_name, "--budget", "7"],
                cwd=CALM, capture_output=True, text=True, timeout=600, env={**os.environ, "PYTHONPATH": str(stub)},
            )
    finally:
        shutil.rmtree(CALM / "calm_saved" / "crp_online" / log_name, ignore_errors=True)
    assert done.returncode == 0, (done.stdout + done.stderr)[-3000:]
    assert "Budget of 7 scored rules reached" in done.stdout

    rules = [json.loads(line) for line in rule_log.read_text().splitlines()]
    # the 5 answers in order, then the first two again; the 8th rule is never scored
    assert [r["total"] for r in rules] == [26_452, 27_049, None, None, 27_047, 26_452, 27_049]
    assert rules[2]["error"] == "code_bug"                       # NaN score
    assert rules[3]["error"] == "uses random: rejected by CALM"  # scored, then rejected by CALM
