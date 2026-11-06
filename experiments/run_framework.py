"""Our framework: one run, and merging the runs' results into results/llm_full.csv.

    python experiments/run_framework.py run --alpha 0.5 --seed 1 [--seed-rule lowest] [--off pareto,feedback]
        one run with Ollama at --base-url; writes runs/ours/<name>.jsonl (every proposed rule),
        <name>.summary.json (budget used, LLM calls, outcomes) and <name>.row.json (the CSV row:
        the best fully evaluated rule, scored once on the test set)
    python experiments/run_framework.py collect
        appends every new row to results/llm_full.csv and copies the run's log and summary to
        results/llm_runs_full/, next to the EoH, ReEvo and CALM runs

<name> is <method>_a<alpha>_s<seed>; method is "ours", plus what differs from the full framework
(e.g. "ours-lowest", "ours-no_pareto"). The evaluations column holds the budget in full
evaluations (420,000 yard simulations = 500), as for the baselines.
"""
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from crp.framework.llm import LLM
from crp.framework.loop import run
from crp.framework.settings import SWITCHES, Settings
from crp.instance import load_dataset
from crp.llm.evaluate import compile_rule, evaluate_rule
from crp.llm.experiment import _key, append_row, finished_runs
from crp.paths import RESULTS, ROOT, TEST_SET

RUNS = ROOT / "runs" / "ours"
YARDS = 840


def run_one(settings: Settings, model: str, base_url: str, out: Path = RUNS) -> dict:
    name = f"{settings.label()}_a{settings.alpha}_s{settings.run_seed}"
    llm = LLM(model, base_url, settings.temperature)
    best, summary = run(settings, llm, out / f"{name}.jsonl")
    (out / f"{name}.summary.json").write_text(json.dumps(summary, indent=1))
    outcomes = summary["outcomes"]
    scored = sum(outcomes.get(s, 0) for s in ("crash", "screened_out", "duplicate_behaviour", "evaluated"))
    row = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "method": settings.label(),
        "model": model,
        "alpha": settings.alpha,
        "seed": settings.run_seed,
        "evaluations": settings.budget // YARDS,
        "train_fitness": best.total,
        "test_total": evaluate_rule(compile_rule(best.code, "priority"), load_dataset(TEST_SET), settings.alpha),
        "valid_rate": round(1 - outcomes.get("crash", 0) / scored, 3),
        "llm_calls": summary["llm_calls"],
        "seconds": summary["seconds"],
        "code": best.code,
    }
    (out / f"{name}.row.json").write_text(json.dumps(row))
    return row


def collect(out: Path) -> None:
    done = finished_runs(out)
    for path in sorted(RUNS.glob("ours*.row.json")):
        result = json.loads(path.read_text())
        if _key(result["method"], result["alpha"], result["seed"], result["model"], result["evaluations"]) in done:
            continue
        append_row(out, result)
        name = path.name.removesuffix(".row.json")
        for suffix in (".jsonl", ".summary.json"):
            shutil.copy(RUNS / f"{name}{suffix}", RESULTS / "llm_runs_full" / f"{name}{suffix}")
        print(f"added {name}: test {result['test_total']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("run", help="one framework run")
    one.add_argument("--alpha", type=float, required=True)
    one.add_argument("--seed", type=int, required=True, help="run number")
    one.add_argument("--seed-rule", choices=["minmax", "lowest"], default="minmax")
    one.add_argument("--off", default="", help=f"components to switch off, comma-separated: {', '.join(SWITCHES)}")
    one.add_argument("--model", default="qwen3:14b-nothink")
    one.add_argument("--base-url", default="http://localhost:11434/v1")
    one.add_argument("--budget", type=int, default=420_000, help="yard simulations")
    merge = commands.add_parser("collect", help="add all new rows to the results CSV")
    merge.add_argument("--out", type=Path, default=RESULTS / "llm_full.csv")
    args = parser.parse_args()
    if args.command == "collect":
        collect(args.out)
        return
    off = [s for s in args.off.split(",") if s]
    if unknown := set(off) - set(SWITCHES):
        parser.error(f"unknown components: {', '.join(sorted(unknown))}")
    settings = Settings(alpha=args.alpha, run_seed=args.seed, seed_rule=args.seed_rule, budget=args.budget,
                        **{name: False for name in off})
    row = run_one(settings, args.model, args.base_url)
    print(f"{settings.label()} alpha {args.alpha} seed {args.seed}: train {row['train_fitness']:,}, "
          f"test {row['test_total']:,}, {row['llm_calls']} LLM calls, {row['seconds']} s")


if __name__ == "__main__":
    main()
