"""Run many LLM experiments, one after another, and append each to results/llm_full.csv.

Runs already in the CSV are skipped, so a stopped batch continues where it stopped. Order:
seed 1 of every method and alpha first, then seed 2, ... so a partial batch stays balanced.
One batch at a time per ReEvo folder: parallel runs would overwrite each other's gpt.py.
Keep the machine awake, e.g. on a Mac:
    caffeinate -i python experiments/run_llm_many.py
Examples:
    python experiments/run_llm_many.py                      # all 60: eoh+reevo x alphas 0.5 0.3 0.1 x seeds 1..10
    python experiments/run_llm_many.py --runs 1 --quick     # pipeline test: 6 quick runs
"""
import argparse

from crp.instance import load_dataset
from crp.llm.experiment import run_many
from crp.paths import RESULTS, ROOT, TEST_SET


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--methods", nargs="+", choices=["eoh", "reevo"], default=["eoh", "reevo"])
    parser.add_argument("--alphas", type=float, nargs="+", default=[0.5, 0.3, 0.1])
    parser.add_argument("--runs", type=int, default=10, help="seeds 1..runs")
    parser.add_argument("--budget", type=int, default=500, help="evaluations counted per run")
    parser.add_argument("--model", default="qwen3:14b-nothink")
    parser.add_argument("--base-url", default="http://localhost:11434/v1", help="Ollama address")
    parser.add_argument("--quick", action="store_true", help="30 evaluations, results/llm_quick.csv")
    args = parser.parse_args()
    if args.quick:
        args.budget = 30
    kind = "quick" if args.quick else "full"  # quick test rows never land in the real results

    print(f"methods {args.methods}, alphas {args.alphas}, seeds 1..{args.runs}, "
          f"{args.budget} evaluations, model {args.model}", flush=True)
    run_many(
        methods=args.methods, alphas=args.alphas, seeds=list(range(1, args.runs + 1)),
        budget=args.budget, model=args.model, base_url=args.base_url,
        test_instances=load_dataset(TEST_SET), out=RESULTS / f"llm_{kind}.csv",
        rule_dir=RESULTS / f"llm_runs_{kind}", work_dir=ROOT / "runs" / kind,
        progress=lambda line: print(line, flush=True),
    )


if __name__ == "__main__":
    main()
