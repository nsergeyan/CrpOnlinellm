"""Run one GP experiment and append the result to results/gp_runs.csv.

Examples (from PyCharm, or with PYTHONPATH=src from the project folder):
    python experiments/run_gp.py --alpha 0.5 --seed 1 --quick   # test mode: 2,000 evaluations
    python experiments/run_gp.py --alpha 0.5 --seed 1           # full run: 51,000 evaluations
"""
import argparse
import os
import time
from pathlib import Path

from crp.gp.experiment import append_row, run_experiment
from crp.gp.fitness import ParallelFitness
from crp.instance import load_dataset

ROOT = Path(__file__).resolve().parent.parent
TRAINING = ROOT / "data" / "training"
TEST = ROOT / "data" / "caserta_840"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--alpha", type=float, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--hidden", choices=["max", "ignore"], default="max")
    parser.add_argument("--population", type=int, default=1000)
    parser.add_argument("--generations", type=int, default=50)
    parser.add_argument("--quick", action="store_true", help="population 100, 19 generations = 2,000 evaluations")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--out", default=str(ROOT / "results" / "gp_runs.csv"))
    args = parser.parse_args()
    if args.quick:
        args.population, args.generations = 100, 19

    start = time.perf_counter()

    def log(generation: int, evaluations: int, best: float) -> None:
        print(f"gen {generation:3d} | evals {evaluations:6d} | best {best:9,.0f} | {time.perf_counter() - start:6.0f}s",
              flush=True)

    print(f"alpha {args.alpha}, {args.hidden}, seed {args.seed}, population {args.population}, "
          f"{args.generations} generations, {args.workers} workers")
    with ParallelFitness(TRAINING, args.workers) as parallel:
        row = run_experiment(
            score=lambda text: parallel(text, args.alpha, args.hidden),
            test_instances=load_dataset(TEST),
            alpha=args.alpha,
            hidden=args.hidden,
            seed=args.seed,
            population=args.population,
            generations=args.generations,
            training_set=TRAINING.name,
            log=log,
        )
    append_row(args.out, row)
    print(f"\nbest on training: {row['train_fitness']:,} (generation {row['best_generation']})")
    print(f"test total:       {row['test_total']:,}")
    print(f"formula:          {row['formula']}")
    print(f"cache hits:       {row['cache_hits']:,} of {row['evaluations']:,} evaluations")
    print(f"saved to {args.out}")


if __name__ == "__main__":
    main()
