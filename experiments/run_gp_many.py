"""Run many GP experiments in parallel (one whole run per core) and print the medians.

Runs already in the CSV are skipped, so an interrupted batch continues where it stopped.
Keep the Mac awake overnight with caffeinate, e.g.:
    caffeinate -i python experiments/run_gp_many.py --alphas 0.5
Examples:
    python experiments/run_gp_many.py                      # all 90: alphas 0.5 0.3 0.1 x seeds 1..30
    python experiments/run_gp_many.py --runs 2 --quick     # pipeline test, separate settings
"""
import argparse
import os
from pathlib import Path

from crp.gp.experiment import PAPER_MEDIANS, medians, run_many

ROOT = Path(__file__).resolve().parent.parent
TRAINING = ROOT / "data" / "training"
TEST = ROOT / "data" / "caserta_840"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--alphas", type=float, nargs="+", default=[0.5, 0.3, 0.1])
    parser.add_argument("--runs", type=int, default=30, help="seeds 1..runs")
    parser.add_argument("--hidden", choices=["max", "ignore"], default="max")
    parser.add_argument("--population", type=int, default=1000)
    parser.add_argument("--generations", type=int, default=50)
    parser.add_argument("--quick", action="store_true", help="population 100, 19 generations = 2,000 evaluations")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--out", help="default: results/gp_full.csv, or results/gp_quick.csv with --quick")
    args = parser.parse_args()
    if args.quick:
        args.population, args.generations = 100, 19
    if args.out is None:  # quick test rows never land in the real results file
        args.out = str(ROOT / "results" / ("gp_quick.csv" if args.quick else "gp_full.csv"))

    print(f"alphas {args.alphas}, seeds 1..{args.runs}, {args.hidden}, population {args.population}, "
          f"{args.generations} generations, {args.workers} workers", flush=True)
    run_many(args.alphas, list(range(1, args.runs + 1)), args.hidden, args.population, args.generations,
             TRAINING, TEST, args.out, args.workers, progress=lambda line: print(line, flush=True))

    print("\nmedian test total per alpha (these settings):")
    for alpha, (median, n) in medians(args.out, args.hidden, args.population, args.generations,
                                      TRAINING.name).items():
        paper = PAPER_MEDIANS.get(alpha)
        print(f"  alpha {alpha}: {median:,.0f} over {n} runs" + (f" | paper {paper:,}" if paper else ""))


if __name__ == "__main__":
    main()
