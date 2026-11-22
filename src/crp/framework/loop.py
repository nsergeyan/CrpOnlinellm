"""The main loop of our framework (docs/framework_design.md).

Budget: yard simulations, the same 420,000 per run as the baselines (500 full evaluations of 840
yards). Each scoring call costs the number of yards it simulates; an exact duplicate costs
nothing. Each yard is simulated at most once per rule: the quick test reuses the crash test's 4
yards and the full evaluation the quick test's 84 (a yard's result does not depend on the other
yards scored with it), so a full evaluation costs exactly 840. The seed's evaluation is counted. The run ends when the next step would not fit in the budget; the result is the best
fully evaluated rule. Answers the LLM wrote for a batch but the run no longer uses are dropped
(they count as LLM calls, not as budget).

The LLM writes `batch_size` rules at the same time, all from the archive as it is when the batch
starts; they are then checked and scored one after another, so each rule still sees the newest
population at the quick test. With batch_size 1 every rule is written from the newest archive.

Every proposed rule gets one line in the JSONL log: operator, parents, idea, code, the gate where
it stopped (status), its cost, repairs, and its quick and full results; the raw answer when it
has no code.

With lessons (`lessons_every` > 0, README decision 57) each prompt shows each lesson with
probability 0.5, and every rule with a parent counts as a win or not for the lessons its prompt
showed and hid; every `lessons_every` batches the lessons are checked and the free places filled
(one more LLM call). The rule's log line says which lessons it saw; the checks go to
<log>.lessons.jsonl.
"""
from __future__ import annotations

import json
import random
import time
from dataclasses import asdict
from pathlib import Path

from crp.framework import prompts
from crp.framework.knowledge import SEEDS
from crp.framework.lessons import Notebook
from crp.framework.llm import LLM, read_rule
from crp.framework.population import Archive, Rule, plain_code
from crp.framework.scoring import Scorer
from crp.framework.settings import Settings


class BudgetEnd(Exception):
    """The next scoring step does not fit in the budget."""


def run(settings: Settings, llm: LLM, log_path: Path) -> tuple[Rule, dict]:
    """One run; returns the best rule and a summary (budget used, LLM calls, outcomes)."""
    start = time.perf_counter()
    rng = random.Random(settings.run_seed)
    scorer = Scorer(settings.alpha, settings.timeout, settings.crash_yards, settings.quick_per_type)
    archive = Archive(settings.population_size, scorer.types)
    system = prompts.system_prompt(settings.knowledge, settings.knowledge_text)
    lesson_system = prompts.system_prompt(settings.knowledge, settings.knowledge_text, prompts.LESSON_FORMAT)
    notebook = Notebook(settings.run_seed) if settings.lessons_every else None
    all_ids = list(range(len(scorer.yards)))
    state = {"used": 0, "seen_code": set(), "seen_quick": set(), "outcomes": {}}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = log_path.open("w")
    lessons_log = log_path.with_suffix(".lessons.jsonl").open("w") if notebook is not None else None

    def score(code: str, ids: list[int], results: dict[int, int], entry: dict) -> str | None:
        """Simulates the yards of `ids` not in `results` yet and adds them; the error, if any."""
        missing = [i for i in ids if i not in results]
        if settings.budget - state["used"] < len(missing):
            raise BudgetEnd
        state["used"] += len(missing)
        entry["cost"] += len(missing)
        new, error = scorer.score(code, missing)
        if error is None:
            results.update(new)
        return error

    def promising(quick: dict[int, int]) -> bool:
        """Could enter the population: better than its worst rule on the same 84 yards."""
        population = archive.population()
        return (len(population) < settings.population_size
                or sum(quick.values()) < max(r.subtotal(scorer.quick_ids) for r in population))

    def try_rule(code: str | None, idea: str, entry: dict) -> Rule | None:
        """Gates, quick test and full evaluation; sets entry['status']."""
        if code is None:
            entry["status"] = "no_code"
            return None
        if settings.dedup and plain_code(code) in state["seen_code"]:
            entry["status"] = "duplicate_code"
            return None
        state["seen_code"].add(plain_code(code))
        results: dict[int, int] = {}  # this rule's relocations per yard, filled step by step
        if settings.crash_check:  # crash test on 4 yards, with repair from the error message
            while (error := score(code, scorer.crash_ids, results, entry)) is not None:
                entry["errors"].append(error)
                if entry["repairs"] == settings.max_repairs:
                    entry["status"] = "crash"
                    return None
                entry["repairs"] += 1
                answer = llm.ask(system, prompts.repair(code, error))
                new_code, new_idea = read_rule(answer)
                if new_code is None:
                    entry["answer"] = answer  # to see why it has no code
                if new_code is None or (settings.dedup and plain_code(new_code) in state["seen_code"]):
                    entry["status"] = "crash"
                    return None
                code, idea = new_code, new_idea or idea
                state["seen_code"].add(plain_code(code))
                entry["code"], entry["idea"] = code, idea
        if settings.quick_test:
            if (error := score(code, scorer.quick_ids, results, entry)) is not None:
                entry["status"], entry["errors"] = "crash", entry["errors"] + [error]
                return None
            quick = {i: results[i] for i in scorer.quick_ids}
            entry["quick_total"] = sum(quick.values())
            fingerprint = tuple(quick.values())
            if settings.dedup and fingerprint in state["seen_quick"]:
                entry["status"] = "duplicate_behaviour"
                return None
            state["seen_quick"].add(fingerprint)
            if not promising(quick):
                entry["status"] = "screened_out"
                return None
        if (error := score(code, all_ids, results, entry)) is not None:
            entry["status"], entry["errors"] = "crash", entry["errors"] + [error]
            return None
        rule = Rule(len(archive.rules), code, idea, results, {}, entry["repairs"] > 0)
        rule.type_totals = scorer.type_totals(rule.per_yard)
        archive.add(rule)
        entry.update(status="evaluated", rule_id=rule.id, total=rule.total,
                     type_totals={f"{t[0]}-{t[1]}": v for t, v in rule.type_totals.items()})
        return rule

    def propose() -> tuple[str, list[Rule], str, dict | None]:
        """An operator, its parents, the prompt, and which lessons the prompt shows and hides."""
        operator = rng.choices(("refine", "merge", "explore"), weights=settings.operator_weights)[0]
        if operator == "merge" and len(archive.rules) < 2:
            operator = "refine"
        if operator == "explore":
            parents, prompt = [], prompts.explore(archive)
        else:
            parents = archive.select_parents(operator == "merge", settings.pareto, rng)
            if operator == "merge" and len(parents) == 2:
                prompt = prompts.merge(*parents, archive, settings.feedback)
            else:
                operator, parents = "refine", parents[:1]
                prompt = prompts.refine(parents[0], archive, settings.feedback)
        if notebook is None:
            return operator, parents, prompt, None
        lessons = notebook.flip()
        return operator, parents, prompts.with_lessons(prompt, notebook.texts(lessons["shown"])), lessons

    def check_lessons(batch_number: int) -> None:
        """Every `lessons_every` batches: delete, rewrite or keep each lesson, then fill the free places."""
        decisions = notebook.check(settings.lesson_delete_after, settings.lesson_judge_after)
        record = {"batch": batch_number, "step": step, "used": state["used"],
                  "lessons": [{**asdict(lesson), "decision": decision} for lesson, decision in decisions]}
        room = settings.max_lessons - len(notebook.lessons)
        if room:
            prompt = prompts.update_lessons(notebook.lessons, [l for l, d in decisions if d == "rewrite"],
                                            notebook.deleted, notebook.recent(True), notebook.recent(False), room)
            answer = llm.ask(lesson_system, prompt)
            record.update(prompt=prompt, answer=answer,
                          new=[asdict(l) for l in notebook.add(answer, room, batch_number)])
        lessons_log.write(json.dumps(record) + "\n")
        lessons_log.flush()

    def new_entry(step: int, operator: str, parents: list[Rule], code: str | None, idea: str) -> dict:
        return {"step": step, "operator": operator, "parents": [p.id for p in parents], "idea": idea,
                "code": code, "status": None, "cost": 0, "repairs": 0, "errors": []}

    try:
        seed_idea, seed_code = SEEDS[settings.seed_rule]
        entry = new_entry(0, "seed", [], seed_code, seed_idea)
        if try_rule(seed_code, seed_idea, entry) is None:
            raise RuntimeError(f"the seed rule was not evaluated: {entry}")
        cheapest = len(scorer.crash_ids if settings.crash_check else
                       scorer.quick_ids if settings.quick_test else all_ids)
        step = free_in_a_row = batches = 0
        batch: list[tuple[str, list[Rule], str, dict | None]] = []  # proposals whose answers are not used yet
        answers: list[str] = []
        while True:
            log.write(json.dumps({**entry, "used": state["used"], "llm_calls": llm.calls}) + "\n")
            log.flush()
            state["outcomes"][entry["status"]] = state["outcomes"].get(entry["status"], 0) + 1
            free_in_a_row = free_in_a_row + 1 if entry["cost"] == 0 else 0
            if settings.budget - state["used"] < cheapest or free_in_a_row >= settings.max_free_in_a_row:
                entry = new_entry(step + 1, "none", [], None, "")  # a last line that says why it ended
                entry["status"] = "budget_end" if free_in_a_row < settings.max_free_in_a_row else "stalled"
                raise BudgetEnd
            if not batch:  # the next rules, all written from the archive as it is now
                if notebook is not None and batches and batches % settings.lessons_every == 0:
                    check_lessons(batches)
                batch = [propose() for _ in range(settings.batch_size)]
                answers = llm.ask_many(system, [prompt for _, _, prompt, _ in batch])
                batches += 1
            (operator, parents, _, lessons), answer = batch.pop(0), answers.pop(0)
            step += 1
            code, idea = read_rule(answer)
            entry = new_entry(step, operator, parents, code, idea)
            if code is None:
                entry["answer"] = answer  # to see why it has no code
            rule = try_rule(code, idea, entry)
            if notebook is not None:
                entry["lessons"] = lessons
                if parents:  # explore rules have no parent and are not counted
                    parent = min(parents, key=lambda p: p.total)  # for a merge, the better parent
                    entry["beat_parent"] = rule is not None and rule.total < parent.total
                    notebook.record(lessons, entry["beat_parent"], {
                        "won": entry["beat_parent"], "status": entry["status"], "parent_idea": parent.idea,
                        "idea": entry["idea"], "code": entry["code"], "total": entry.get("total"),
                        "parent_total": parent.total})
    except BudgetEnd:
        entry["status"] = entry["status"] or "budget_end"  # None: the budget ended inside a proposal
        log.write(json.dumps({**entry, "used": state["used"], "llm_calls": llm.calls}) + "\n")
    finally:
        log.close()
        if lessons_log is not None:
            lessons_log.close()
        scorer.close()
    summary = {"settings": settings.as_dict(), "budget_used": state["used"], "llm_calls": llm.calls,
               "full_evaluations": len(archive.rules), "outcomes": state["outcomes"],
               "seconds": round(time.perf_counter() - start, 1)}
    if notebook is not None:
        summary["lesson_checks"] = notebook.checks
    return archive.best(), summary
