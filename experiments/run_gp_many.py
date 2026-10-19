"""Run many GP experiments in parallel (one whole run per core).

Runs already in the CSV are skipped, so an interrupted batch continues where it stopped.
Keep the Mac awake overnight with caffeinate, e.g.:
    caffeinate -i python experiments/run_gp_many.py --alphas 0.5
Examples:
    python experiments/run_gp_many.py                      # all 90: alphas 0.5 0.3 0.1 x seeds 1..30
    python experiments/run_gp_many.py --runs 2 --quick     # pipeline test, separate settings
"""
import argparse
import os

from crp.gp.experiment import run_many
from crp.paths import RESULTS, TEST_SET, TRAINING_SET


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--alphas", type=float, nargs="+", default=[0.5, 0.3, 0.1])
    parser.add_argument("--runs", type=int, default=30, help="seeds 1..runs")
    parser.add_argument("--population", type=int, default=1000)
    parser.add_argument("--generations", type=int, default=50)
    parser.add_argument("--quick", action="store_true",
                        help="population 100, 19 generations = 2,000 evaluations")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--out", help="default: results/gp_full.csv, or results/gp_quick.csv with --quick")
    args = parser.parse_args()
    if args.quick:
        args.population, args.generations = 100, 19
    if args.out is None:  # quick test rows never land in the real results file
        args.out = str(RESULTS / ("gp_quick.csv" if args.quick else "gp_full.csv"))

    print(f"alphas {args.alphas}, seeds 1..{args.runs}, population {args.population}, "
          f"{args.generations} generations, {args.workers} workers", flush=True)
    seeds = list(range(1, args.runs + 1))
    run_many(args.alphas, seeds, args.population, args.generations, TRAINING_SET, TEST_SET,
             args.out, args.workers, progress=lambda line: print(line, flush=True))
    print("\ndone; medians vs the paper: python experiments/summarize_results.py")


if __name__ == "__main__":
    main()
