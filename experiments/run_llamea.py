"""LLaMEA as a baseline: one run, and merging the runs' results into results/llm_full.csv.

Needs LLaMEA's environment (bash frameworks/setup_llamea.sh) and Ollama with the no-thinking model.

    frameworks/llamea/.venv/bin/python experiments/run_llamea.py run --alpha 0.5 --seed 1 [--budget 20]
        one run; writes runs/llamea/llamea_a0.5_s1.jsonl (every scored rule, in LLaMEA's order)
        and llamea_a0.5_s1.row.json (the CSV row: the best of the first 500 scored rules, scored
        once on the test set). LLaMEA's own log (prompts, answers) goes to runs/llamea/work/.
    python experiments/run_llamea.py collect
        appends every new row to results/llm_full.csv and copies its rule log to
        results/llm_runs_full/, next to the EoH, ReEvo and CALM runs

Budget and best rule are counted as for EoH, ReEvo and CALM (crp.llm.experiment.result_row).
"""
import argparse
import json
import shutil
import time
from pathlib import Path

from crp.instance import load_dataset
from crp.llm.experiment import _key, append_row, finished_runs, result_row
from crp.paths import RESULTS, ROOT, TEST_SET

RUNS = ROOT / "runs" / "llamea"


def run_one(alpha: float, seed: int, budget: int, model: str, base_url: str, out: Path, time_limit: int) -> dict:
    """seed is only a run number: LLaMEA takes no random seed."""
    from crp.llm.llamea_baseline import run_llamea  # needs LLaMEA's environment; `collect` does not

    name = f"llamea_a{alpha}_s{seed}"
    out = out.resolve()  # run_llamea changes the current folder
    start = time.perf_counter()
    history = run_llamea(alpha, budget, model, base_url, out / "work" / name, time_limit)
    rule_log = out / f"{name}.jsonl"
    with rule_log.open("w") as f:
        for solution in history:
            if solution.code:  # an answer without code was never scored
                total = int(solution.fitness) if solution.fitness != float("inf") else None
                f.write(json.dumps({"total": total, "error": solution.error or None, "code": solution.code}) + "\n")
    row = result_row("llamea", model, alpha, seed, budget, rule_log, load_dataset(TEST_SET), "priority",
                     len(history), time.perf_counter() - start)  # one LLM call per solution
    (out / f"{name}.row.json").write_text(json.dumps(row))
    return row


def collect(out: Path) -> None:
    done = finished_runs(out)
    for path in sorted(RUNS.glob("llamea_a*_s*.row.json")):
        result = json.loads(path.read_text())
        if result["evaluations"] != 500:  # a test run with a smaller --budget
            print(f"skipped {path.name}: budget of {result['evaluations']} evaluations, not a full run")
            continue
        if _key(result["method"], result["alpha"], result["seed"], result["model"], result["evaluations"]) in done:
            continue
        append_row(out, result)
        rule_log = path.with_name(path.name.replace(".row.json", ".jsonl"))
        shutil.copy(rule_log, RESULTS / "llm_runs_full" / rule_log.name)
        test = "failed on the test set" if result["test_total"] is None else f"{result['test_total']:,}"
        print(f"added {path.name.removesuffix('.row.json')}: test {test}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("run", help="one LLaMEA run")
    one.add_argument("--alpha", type=float, required=True)
    one.add_argument("--seed", type=int, required=True, help="run number")
    one.add_argument("--budget", type=int, default=500, help="scored rules counted per run")
    one.add_argument("--model", default="qwen3:14b-nothink")
    one.add_argument("--base-url", default="http://localhost:11434/v1", help="Ollama address")
    one.add_argument("--out", type=Path, default=RUNS, help="folder for the run's files")
    one.add_argument("--time-limit", type=int, default=60, help="seconds for one rule on the training set")
    merge = commands.add_parser("collect", help="add all new rows to the results CSV")
    merge.add_argument("--out", type=Path, default=RESULTS / "llm_full.csv")
    args = parser.parse_args()
    if args.command == "collect":
        collect(args.out)
        return
    row = run_one(args.alpha, args.seed, args.budget, args.model, args.base_url, args.out, args.time_limit)
    test = "failed on the test set" if row["test_total"] is None else f"{row['test_total']:,}"
    print(f"llamea alpha {args.alpha} seed {args.seed}: train {row['train_fitness']:,}, test {test}, "
          f"{row['valid_rate']:.0%} valid, {row['llm_calls']} LLM calls, {row['seconds']} s")


if __name__ == "__main__":
    main()
