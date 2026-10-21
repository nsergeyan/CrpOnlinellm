"""LLM experiments: run EoH or ReEvo once, test the best rule once, record a CSV row.

Both methods are started through ReEvo's main.py (algorithm=eoh or reevo), so they share
the LLM client, our eval.py and the prompt files. eval.py appends every scored rule to a
JSONL file in evaluation order; the run's result is the best of the first `budget` rules,
so both methods get exactly the same number of evaluations (both frameworks overshoot).
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from crp.instance import Instance
from crp.llm.evaluate import compile_rule, evaluate_rule
from crp.paths import ROOT

REEVO = ROOT / "frameworks" / "reevo"
FIELDS = [
    "date", "method", "model", "alpha", "seed", "evaluations", "train_fitness", "test_total",
    "valid_rate", "llm_calls", "seconds", "code",
]


def run_framework(method: str, alpha: float, budget: int, model: str, base_url: str,
                  pop_size: int, init_pop_size: int, rule_log: Path, work_dir: Path,
                  echo: bool = True) -> int:
    """Run ReEvo's main.py, keep a copy of its output (and show it live if echo); return the LLM calls."""
    venv_bin = REEVO / ".venv" / "bin"
    # copy our current eval.py, settings and prompt files in, so a stale copy can never be used
    subprocess.run([str(venv_bin / "python"), str(ROOT / "frameworks" / "install_reevo_files.py"),
                    str(REEVO)], check=True, capture_output=True)
    command = [
        str(venv_bin / "python"), "main.py", "problem=crp_online", f"problem.problem_size={alpha}",
        f"algorithm={method}", "llm_client=openai", f"llm_client.model={model}",
        "llm_client.api_key=local", f"+llm_client.base_url={base_url}", f"max_fe={budget}",
        f"pop_size={pop_size}", f"init_pop_size={init_pop_size}", "timeout=60",
        f"hydra.run.dir={work_dir}",
    ]
    env = {**os.environ, "PATH": f"{venv_bin}:{os.environ['PATH']}",  # eval.py runs with ReEvo's python
           "CRP_RULE_LOG": str(rule_log)}
    work_dir.mkdir(parents=True, exist_ok=True)
    llm_calls = 0
    with subprocess.Popen(command, cwd=REEVO, env=env, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT) as process, (work_dir / "output.txt").open("w") as copy:
        for line in process.stdout:
            if echo:
                print(line, end="", flush=True)
            copy.write(line)
            llm_calls += "HTTP Request: POST" in line  # one line per LLM call, for both methods
    if process.returncode != 0:
        raise RuntimeError(f"{method} stopped with an error, see {work_dir / 'output.txt'}")
    return llm_calls


def run_experiment(method: str, alpha: float, seed: int, budget: int, model: str, base_url: str,
                   test_instances: list[Instance], rule_log: Path, work_dir: Path,
                   pop_size: int = 10, init_pop_size: int = 30, echo: bool = True) -> dict:
    """One run. seed is only a run number: neither framework takes a random seed."""
    start = time.perf_counter()
    rule_log.parent.mkdir(parents=True, exist_ok=True)
    rule_log.unlink(missing_ok=True)  # a crashed earlier attempt must not mix in
    llm_calls = run_framework(method, alpha, budget, model, base_url, pop_size, init_pop_size,
                              rule_log, work_dir, echo)

    rules = [json.loads(line) for line in rule_log.read_text().splitlines()][:budget]
    valid = [r for r in rules if r["total"] is not None]
    if not valid:
        raise RuntimeError(f"no valid rule in {rule_log}")
    best = min(valid, key=lambda r: r["total"])  # first of the best on ties
    test_total = evaluate_rule(compile_rule(best["code"], "priority_v2"), test_instances, alpha)
    return {
        "date": datetime.now().isoformat(timespec="seconds"),
        "method": method,
        "model": model,
        "alpha": alpha,
        "seed": seed,
        "evaluations": len(rules),
        "train_fitness": best["total"],
        "test_total": test_total,
        "valid_rate": round(len(valid) / len(rules), 3),
        "llm_calls": llm_calls,
        "seconds": round(time.perf_counter() - start, 1),
        "code": best["code"],
    }


def append_row(path: str | Path, row: dict) -> None:
    """Add one result row; writes the header only when the file is new."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        if new:
            writer.writeheader()
        writer.writerow(row)


def _key(method, alpha, seed, model, evaluations) -> tuple[str, ...]:
    """What makes two runs 'the same run' (CSV values are strings)."""
    return method, str(float(alpha)), str(seed), model, str(evaluations)


def finished_runs(out: str | Path) -> set[tuple[str, ...]]:
    if not Path(out).exists():
        return set()
    with Path(out).open(newline="") as f:
        return {_key(r["method"], r["alpha"], r["seed"], r["model"], r["evaluations"]) for r in csv.DictReader(f)}


def run_many(methods: list[str], alphas: list[float], seeds: list[int], budget: int, model: str,
             base_url: str, test_instances: list[Instance], out: str | Path, rule_dir: Path,
             work_dir: Path, progress: Callable[[str], None] = print, **settings) -> list[dict]:
    """Run every (seed, alpha, method) not yet in the CSV, one at a time; rows are written as runs finish.

    Seed is the outer loop, so a stopped batch still has the same number of runs per method
    and alpha. A failed run is reported and skipped; starting the batch again retries it.
    """
    done = finished_runs(out)
    jobs = [(s, a, m) for s in seeds for a in alphas for m in methods
            if _key(m, a, s, model, budget) not in done]
    progress(f"{len(jobs)} runs to do, {len(methods) * len(alphas) * len(seeds) - len(jobs)} already in {out}")
    rows: list[dict] = []
    start = time.perf_counter()
    for i, (seed, alpha, method) in enumerate(jobs, 1):
        name = f"{method}_a{alpha}_s{seed}"
        try:
            row = run_experiment(method, alpha, seed, budget, model, base_url, test_instances,
                                 rule_dir / f"{name}.jsonl", work_dir / name, echo=False, **settings)
        except Exception as e:
            progress(f"[{i}/{len(jobs)}] {method} alpha {alpha} seed {seed} | FAILED: {e}")
            continue
        append_row(out, row)
        rows.append(row)
        hours, rest = divmod(int(time.perf_counter() - start), 3600)
        progress(f"[{i}/{len(jobs)}] {method} alpha {alpha} seed {seed} | train {row['train_fitness']:,} | "
                 f"test {row['test_total']:,} | {row['valid_rate']:.0%} valid | {hours}h {rest // 60:02d}m")
    return rows
