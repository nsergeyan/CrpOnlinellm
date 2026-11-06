"""Our framework (src/crp/framework) with a fake LLM: budget counting, gates, selection, a full run."""
import json
import random

import pytest

from crp.framework.knowledge import SEEDS
from crp.framework.llm import LLM, read_rule
from crp.framework.loop import run
from crp.framework.population import Archive, Rule, plain_code
from crp.framework.scoring import Scorer
from crp.framework.settings import Settings
from fake_llm import fake_llm

pytest.importorskip("numpy")  # rules may use np


def answer(idea: str, body: str) -> str:
    return (f"Idea: {idea}\n```python\ndef priority(SH, EMP, AVG, CUR, RI, DIFF):\n"
            f"    priority = {body}\n    return priority\n```")


LOW_RI = answer("few blocked containers first", "RI * 100 + SH")
LOW_RI_AGAIN = answer("the same, other numbers", "RI * 1000 + SH")  # same choices: SH is at most 12
CRASH = answer("divide", "SH / 0")
EMPTY_FIRST = answer("empty stacks first", "-EMP")
SEED_AGAIN = "Idea: Min-Max\n```python\n" + SEEDS["minmax"][1].replace("# Min-Max", "#  closest") + "```"  # other comments
ANSWERS = [LOW_RI, SEED_AGAIN, LOW_RI_AGAIN, CRASH, EMPTY_FIRST, "Sorry, no code.", answer("high", "-SH")]


def run_with(answers: list[str], tmp_path, **settings):
    with fake_llm(answers) as url:
        llm = LLM("fake", url, temperature=1.0)
        best, summary = run(Settings(alpha=0.5, **settings), llm, tmp_path / "log.jsonl")
    log = [json.loads(line) for line in (tmp_path / "log.jsonl").read_text().splitlines()]
    return best, summary, log, llm


def test_settings_label():
    assert Settings(alpha=0.5).label() == "ours"
    assert Settings(alpha=0.5, seed_rule="lowest").label() == "ours-lowest"
    assert Settings(alpha=0.5, pareto=False, feedback=False).label() == "ours-no_pareto-no_feedback"


def test_read_rule():
    code, idea = read_rule(LOW_RI)
    assert idea == "few blocked containers first" and code.startswith("def priority") and "RI * 100" in code
    assert read_rule("**Idea:** x\ndef priority(SH, EMP, AVG, CUR, RI, DIFF):\n    return 1")[0].startswith("def priority")
    assert read_rule("Sorry, no code.") == (None, "")


def test_plain_code_ignores_comments_docstrings_and_spacing():
    assert plain_code(SEEDS["minmax"][1]) == plain_code(read_rule(SEED_AGAIN)[0])
    assert plain_code(SEEDS["minmax"][1]) != plain_code(SEEDS["lowest"][1])


def test_scorer_reuses_the_same_yards():
    scorer = Scorer(alpha=0.5, timeout=60)
    try:
        assert len(scorer.types) == 21 and len(scorer.quick_ids) == 84
        assert set(scorer.crash_ids) <= set(scorer.quick_ids)  # so the quick test reuses them
        assert [scorer.type_of[i] for i in scorer.crash_ids] == [(3, 3), (3, 4), (10, 6), (10, 10)]
        full, error = scorer.score(SEEDS["minmax"][1], list(range(840)))
        assert error is None and sum(full.values()) == 24_433  # the seed's training total at alpha 0.5
        assert sum(scorer.score(SEEDS["lowest"][1], list(range(840)))[0].values()) == 29_695
        part, _ = scorer.score(SEEDS["minmax"][1], scorer.quick_ids)
        assert part == {i: full[i] for i in scorer.quick_ids}  # a yard's result never depends on the others
        assert scorer.score(read_rule(CRASH)[0], scorer.crash_ids) == \
            (None, "ZeroDivisionError: division by zero (line 2: priority = SH / 0)")
    finally:
        scorer.close()


def test_scorer_stops_an_endless_loop():
    scorer = Scorer(alpha=0.5, timeout=1)
    try:
        code = "def priority(SH, EMP, AVG, CUR, RI, DIFF):\n    while True:\n        pass\n"
        assert scorer.score(code, [0])[1].startswith("TimeoutError")
        assert scorer.score(SEEDS["minmax"][1], [0])[1] is None  # the restarted worker still scores
    finally:
        scorer.close()


def make_rule(rule_id: int, type_totals: dict) -> Rule:
    return Rule(rule_id, "", "", {rule_id: sum(type_totals.values())}, type_totals)


def test_pareto_keeps_specialists_and_drops_dominated_rules():
    types = [(3, 3), (3, 4), (4, 4)]
    archive = Archive(size=10, types=types)
    archive.add(make_rule(0, {(3, 3): 10, (3, 4): 10, (4, 4): 10}))  # best total, best on (4, 4)
    archive.add(make_rule(1, {(3, 3): 5, (3, 4): 20, (4, 4): 20}))   # best on (3, 3) only
    archive.add(make_rule(2, {(3, 3): 11, (3, 4): 10, (4, 4): 11}))  # ties on (3, 4), but rule 0 is better
    archive.add(make_rule(3, {(3, 3): 50, (3, 4): 50, (4, 4): 50}))  # best nowhere
    assert archive.specialists() == {0: [(3, 4), (4, 4)], 1: [(3, 3)]}
    rng = random.Random(1)
    picks = [archive.select_parents(False, True, rng)[0].id for _ in range(300)]
    assert set(picks) == {0, 1} and picks.count(0) > picks.count(1)  # 2 types won vs 1
    assert {r.id for r in archive.select_parents(True, True, rng)} == {0, 1}
    assert archive.select_parents(False, False, rng)[0].id in {0, 1, 2, 3}  # selection by total


def test_full_run_counts_every_yard_simulation(tmp_path):
    best, summary, log, llm = run_with(ANSWERS, tmp_path, budget=8_000)
    statuses = {e["status"] for e in log}
    assert {"evaluated", "duplicate_code", "duplicate_behaviour", "no_code"} <= statuses
    assert log[-1]["status"] == "stalled"  # the fake LLM's answers all repeat after one round
    assert all(e["answer"] == "Sorry, no code." for e in log if e["status"] == "no_code")
    assert "crash" in statuses or any(e["repairs"] for e in log)
    assert sum(e["cost"] for e in log) == summary["budget_used"] == log[-1]["used"] <= 8_000
    for e in log:
        failed_crash_tests = 4 * len([x for x in e["errors"] if x])
        if e["status"] in ("duplicate_code", "no_code"):
            assert e["cost"] == 0
        if e["status"] == "evaluated":
            assert e["cost"] == 840 + 4 * e["repairs"]  # every yard once, plus failed crash tests
        if e["status"] in ("screened_out", "duplicate_behaviour"):
            assert e["cost"] == 84 + 4 * e["repairs"]
        if e["status"] == "crash":
            assert e["cost"] == failed_crash_tests
    assert log[0]["operator"] == "seed" and log[0]["cost"] == 840 and log[0]["total"] == 24_433
    assert llm.calls == summary["llm_calls"] == sum(1 + e["repairs"] for e in log[1:] if e["operator"] != "none")
    evaluated = [e for e in log if e["status"] == "evaluated"]
    assert best.total == min(e["total"] for e in evaluated) == 24_433  # nothing in ANSWERS beats Min-Max
    assert summary["full_evaluations"] == len(evaluated)


def test_all_switches_off_is_a_plain_loop(tmp_path):
    off = dict(knowledge=False, crash_check=False, dedup=False, quick_test=False, pareto=False, feedback=False)
    _, summary, log, _ = run_with(ANSWERS, tmp_path, budget=6_000, seed_rule="lowest", **off)
    assert log[0]["total"] == 29_695
    for e in log[:-1]:
        assert e["cost"] == (0 if e["status"] == "no_code" else 840)  # crashes and repeats cost a full evaluation
    assert {"duplicate_code", "duplicate_behaviour", "screened_out"}.isdisjoint(e["status"] for e in log)
    assert log[-1]["status"] == "budget_end"
    assert summary["budget_used"] == 840 * 7


def test_run_stops_when_the_llm_only_repeats(tmp_path):
    _, summary, log, _ = run_with([SEED_AGAIN], tmp_path, budget=420_000, max_free_in_a_row=5)
    assert log[-1]["status"] == "stalled" and summary["budget_used"] == 840
