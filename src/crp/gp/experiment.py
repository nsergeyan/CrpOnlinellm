"""One GP experiment: evolve on the training set, test the best rule once, record a CSV row."""
from __future__ import annotations

import csv
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from crp.gp.algorithm import run_gp
from crp.gp.fitness import CachedFitness, total_relocations
from crp.instance import Instance

FIELDS = [
    "date", "alpha", "hidden", "seed", "population", "generations", "evaluations",
    "train_fitness", "best_generation", "test_total", "formula", "training_set",
    "cache_hits", "seconds",
]


def run_experiment(
    score: Callable[[str], int],
    test_instances: list[Instance],
    alpha: float,
    hidden: str,
    seed: int,
    population: int,
    generations: int,
    training_set: str,
    log: Optional[Callable[[int, int, float], None]] = None,
) -> dict:
    """score must use the same alpha and hidden strategy on the training set."""
    start = time.perf_counter()
    fitness = CachedFitness(score)  # a new cache per run: one training set and scenario
    result = run_gp(fitness, random.Random(seed), population, generations, log=log)
    test_total = total_relocations(result.best.text(), test_instances, alpha, hidden)
    return {
        "date": datetime.now().isoformat(timespec="seconds"),
        "alpha": alpha,
        "hidden": hidden,
        "seed": seed,
        "population": population,
        "generations": generations,
        "evaluations": result.evaluations,
        "train_fitness": int(result.best_fitness),
        "best_generation": result.best_generation,
        "test_total": test_total,
        "formula": result.best.text(),
        "training_set": training_set,
        "cache_hits": fitness.hits,
        "seconds": round(time.perf_counter() - start, 1),
    }


def append_row(path: str | Path, row: dict) -> None:
    """Add one result row; writes the header only when the file is new."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            writer.writeheader()
        writer.writerow(row)
