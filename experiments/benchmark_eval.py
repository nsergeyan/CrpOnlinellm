"""Time one GP evaluation (one formula on all 840 training yards), serial and parallel.

Run from PyCharm (green button), or: PYTHONPATH=src python experiments/benchmark_eval.py
"""
import os
import random
import time
from pathlib import Path

from crp.gp.fitness import ParallelFitness, total_relocations
from crp.instance import load_dataset

TRAINING = Path(__file__).resolve().parent.parent / "data" / "training"
TERMINALS = ["SH", "EMP", "AVG", "CUR", "RI", "DIFF"]


def random_formula(depth: int, rng: random.Random) -> str:
    """A full random tree, like an early GP individual."""
    if depth == 1:
        return rng.choice(TERMINALS)
    return f"{rng.choice('+-*/')} {random_formula(depth - 1, rng)} {random_formula(depth - 1, rng)}"


def best_of_3(run) -> float:
    times = []
    for _ in range(3):
        start = time.perf_counter()
        run()
        times.append(time.perf_counter() - start)
    return min(times)


if __name__ == "__main__":
    rng = random.Random(1)
    formulas = {"tiny": "+ SH * RI EMP", "random depth-5": random_formula(5, rng)}
    instances = load_dataset(TRAINING)
    workers = os.cpu_count() or 1
    with ParallelFitness(TRAINING, workers) as fitness:
        fitness("+ SH RI", 0.5, "max")  # start the workers before timing
        for name, text in formulas.items():
            for alpha in (0.5, 0.3, 0.1):
                serial = best_of_3(lambda: total_relocations(text, instances, alpha, "max"))
                parallel = best_of_3(lambda: fitness(text, alpha, "max"))
                print(f"{name:15s} alpha {alpha}: serial {serial:.3f}s | {workers} workers {parallel:.3f}s")
