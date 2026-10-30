"""CALM results: one run's CSV row (end of experiments/calm_job.sh), and merging the rows.

    python experiments/calm_result.py row --alpha 0.5 --seed 1 --seconds 5400
        reads runs/calm/calm_a0.5_s1.jsonl (the launcher's rule log) and CALM's own log, and
        writes runs/calm/calm_a0.5_s1.row.json: the best of the first 500 rules, test-scored
    python experiments/calm_result.py collect
        appends every new row to results/llm_full.csv and copies its rule log to
        results/llm_runs_full/, next to the EoH and ReEvo runs

Each job writes its own row file, so parallel jobs never write to the same file.
"""
import argparse
import json
import shutil
from pathlib import Path

from crp.instance import load_dataset
from crp.llm.experiment import _key, append_row, finished_runs, result_row
from crp.paths import RESULTS, ROOT, TEST_SET

RUNS = ROOT / "runs" / "calm"
CALM_LOGS = ROOT / "frameworks" / "calm" / "calm_saved" / "crp_online"
MODEL = "qwen3-14b-nothink"   # unsloth/Qwen3-14B-unsloth-bnb-4bit, thinking off
ANSWERS_PER_ROUND = 4         # CALM's default n_generations


def name(alpha: float, seed: int) -> str:
    return f"calm_a{alpha}_s{seed}"


def row(alpha: float, seed: int, seconds: float, budget: int) -> None:
    rounds = (CALM_LOGS / name(alpha, seed) / "output.log").read_text().count("=== Step ")
    result = result_row("calm", MODEL, alpha, seed, budget, RUNS / f"{name(alpha, seed)}.jsonl",
                        load_dataset(TEST_SET), None, rounds * ANSWERS_PER_ROUND, seconds)
    (RUNS / f"{name(alpha, seed)}.row.json").write_text(json.dumps(result))


def collect(out: Path) -> None:
    done = finished_runs(out)
    for path in sorted(RUNS.glob("calm_a*_s*.row.json")):
        result = json.loads(path.read_text())
        if _key(result["method"], result["alpha"], result["seed"], result["model"],
                result["evaluations"]) in done:
            continue
        append_row(out, result)
        rule_log = path.with_name(path.name.replace(".row.json", ".jsonl"))
        shutil.copy(rule_log, RESULTS / "llm_runs_full" / rule_log.name)
        print(f"added {path.name.removesuffix('.row.json')}: test {result['test_total']:,}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("row", help="write one run's row file")
    one.add_argument("--alpha", type=float, required=True)
    one.add_argument("--seed", type=int, required=True)
    one.add_argument("--seconds", type=float, required=True, help="the run's wall-clock time")
    one.add_argument("--budget", type=int, default=500)
    merge = commands.add_parser("collect", help="add all new rows to the results CSV")
    merge.add_argument("--out", type=Path, default=RESULTS / "llm_full.csv")
    args = parser.parse_args()
    if args.command == "row":
        row(args.alpha, args.seed, args.seconds, args.budget)
    else:
        collect(args.out)


if __name__ == "__main__":
    main()
