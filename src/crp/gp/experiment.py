"""GP experiments: evolve on the training set, test the best rule once, record a CSV row.

run_many runs many seeds in parallel, one whole GP run per worker process.
"""
from __future__ import annotations

import csv
import random
import statistics
import time
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path
from typing import Callable, Optional

from crp.gp.algorithm import run_gp
from crp.gp.fitness import CachedFitness, total_relocations
from crp.instance import Instance, load_dataset

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
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        if new:
            writer.writeheader()
        writer.writerow(row)


# --- many runs in parallel: one whole GP run per worker process ---

_training: list[Instance] = []  # each worker process loads its own copy once
_test: list[Instance] = []


def _init_worker(training_dir: str, test_dir: str) -> None:
    global _training, _test
    _training, _test = load_dataset(training_dir), load_dataset(test_dir)


def _run_job(job: tuple) -> dict:
    alpha, hidden, seed, population, generations, training_set = job
    return run_experiment(
        score=lambda text: total_relocations(text, _training, alpha, hidden),
        test_instances=_test, alpha=alpha, hidden=hidden, seed=seed,
        population=population, generations=generations, training_set=training_set,
    )


def _key(alpha, hidden, seed, population, generations, training_set) -> tuple[str, ...]:
    """What makes two runs 'the same run' (CSV values are strings)."""
    return tuple(str(v) for v in (float(alpha), hidden, seed, population, generations, training_set))


def finished_runs(out: str | Path) -> set[tuple[str, ...]]:
    if not Path(out).exists():
        return set()
    with Path(out).open(newline="") as f:
        return {
            _key(r["alpha"], r["hidden"], r["seed"], r["population"], r["generations"], r["training_set"])
            for r in csv.DictReader(f)
        }


def run_many(
    alphas: list[float],
    seeds: list[int],
    hidden: str,
    population: int,
    generations: int,
    training_dir: str | Path,
    test_dir: str | Path,
    out: str | Path,
    workers: int,
    progress: Callable[[str], None] = print,
) -> list[dict]:
    """Run every (alpha, seed) not yet in the CSV, one run per worker; rows are written as runs finish."""
    training_set = Path(training_dir).name
    done = finished_runs(out)
    jobs = [(a, hidden, s, population, generations, training_set) for a in alphas for s in seeds
            if _key(a, hidden, s, population, generations, training_set) not in done]
    progress(f"{len(jobs)} runs to do, {len(alphas) * len(seeds) - len(jobs)} already in {out}")
    rows: list[dict] = []
    if not jobs:
        return rows
    start = time.perf_counter()
    with Pool(workers, initializer=_init_worker, initargs=(str(training_dir), str(test_dir))) as pool:
        for row in pool.imap_unordered(_run_job, jobs):
            append_row(out, row)  # only this (main) process writes the file
            rows.append(row)
            hours, rest = divmod(int(time.perf_counter() - start), 3600)
            progress(f"[{len(rows)}/{len(jobs)}] alpha {row['alpha']} seed {row['seed']} | "
                     f"train {row['train_fitness']:,} | test {row['test_total']:,} | "
                     f"{hours}h {rest // 60:02d}m")
    return rows


def medians(out: str | Path, hidden: str, population: int, generations: int, training_set: str) -> dict:
    """Median test total and number of runs per alpha, for runs with these settings."""
    by_alpha: dict[float, list[int]] = {}
    with Path(out).open(newline="") as f:
        for r in csv.DictReader(f):
            if (r["hidden"], r["population"], r["generations"], r["training_set"]) == \
                    (hidden, str(population), str(generations), training_set):
                by_alpha.setdefault(float(r["alpha"]), []).append(int(r["test_total"]))
    return {a: (statistics.median(v), len(v)) for a, v in sorted(by_alpha.items(), reverse=True)}
