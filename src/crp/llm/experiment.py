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

from crp.instance import Instance
from crp.llm.evaluate import compile_rule, evaluate_rule
from crp.paths import ROOT

REEVO = ROOT / "frameworks" / "reevo"
FIELDS = [
    "date", "method", "model", "alpha", "seed", "evaluations", "train_fitness", "test_total",
    "valid_rate", "llm_calls", "seconds", "code",
]


def run_framework(method: str, alpha: float, budget: int, model: str, base_url: str,
                  pop_size: int, init_pop_size: int, rule_log: Path, work_dir: Path) -> int:
    """Run ReEvo's main.py, echo its output live, keep a copy; return the number of LLM calls."""
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
            print(line, end="", flush=True)
            copy.write(line)
            llm_calls += "HTTP Request: POST" in line  # one line per LLM call, for both methods
    if process.returncode != 0:
        raise RuntimeError(f"{method} stopped with an error, see {work_dir / 'output.txt'}")
    return llm_calls


def run_experiment(method: str, alpha: float, seed: int, budget: int, model: str, base_url: str,
                   test_instances: list[Instance], rule_log: Path, work_dir: Path,
                   pop_size: int = 10, init_pop_size: int = 30) -> dict:
    """One run. seed is only a run number: neither framework takes a random seed."""
    start = time.perf_counter()
    rule_log.parent.mkdir(parents=True, exist_ok=True)
    rule_log.unlink(missing_ok=True)  # a crashed earlier attempt must not mix in
    llm_calls = run_framework(method, alpha, budget, model, base_url, pop_size, init_pop_size,
                              rule_log, work_dir)

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
