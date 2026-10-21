"""Run one LLM experiment (EoH or ReEvo) and append the result to results/llm_full.csv.

Needs Ollama running with the no-thinking model (frameworks/make_nothink_model.py) and
ReEvo set up (frameworks/setup_reevo.sh). Every scored rule goes to results/llm_runs/,
the frameworks' own output (prompts, answers) to runs/.

Examples (from the project folder):
    python experiments/run_llm.py --method eoh --alpha 0.5 --seed 1 --quick   # pipeline test, 30 evaluations
    python experiments/run_llm.py --method reevo --alpha 0.5 --seed 1         # full run, 500 evaluations
"""
import argparse

from crp.instance import load_dataset
from crp.llm.experiment import append_row, run_experiment
from crp.paths import RESULTS, ROOT, TEST_SET


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--method", choices=["eoh", "reevo"], required=True)
    parser.add_argument("--alpha", type=float, required=True)
    parser.add_argument("--seed", type=int, required=True, help="run number")
    parser.add_argument("--budget", type=int, default=500, help="evaluations counted per run")
    parser.add_argument("--model", default="qwen3:14b-nothink")
    parser.add_argument("--base-url", default="http://localhost:11434/v1", help="Ollama address")
    parser.add_argument("--quick", action="store_true", help="30 evaluations, results/llm_quick.csv")
    args = parser.parse_args()
    if args.quick:
        args.budget = 30
    kind = "quick" if args.quick else "full"  # quick test rows never land in the real results
    name = f"{args.method}_a{args.alpha}_s{args.seed}"

    row = run_experiment(
        method=args.method, alpha=args.alpha, seed=args.seed, budget=args.budget,
        model=args.model, base_url=args.base_url, test_instances=load_dataset(TEST_SET),
        rule_log=RESULTS / f"llm_runs_{kind}" / f"{name}.jsonl", work_dir=ROOT / "runs" / kind / name,
    )
    append_row(RESULTS / f"llm_{kind}.csv", row)
    print(f"\nbest on training: {row['train_fitness']:,} ({row['evaluations']} rules, "
          f"{row['valid_rate']:.0%} valid, {row['llm_calls']} LLM calls)")
    print(f"test total:       {row['test_total']:,}")
    print(f"saved to {RESULTS / f'llm_{kind}.csv'}")


if __name__ == "__main__":
    main()
