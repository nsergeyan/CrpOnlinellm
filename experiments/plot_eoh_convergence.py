"""Plot how EoH's population improved over the generations and write results/eoh_convergence.png.

Run from PyCharm (green button), or: python experiments/plot_eoh_convergence.py
Needs matplotlib: pip install -e ".[plot]"

EoH keeps the 10 best distinct objective values seen so far, so the population after generation g
is the 10 best distinct valid totals among the first 20 + 40*g rules of a run's rule log
(20 initial rules, then 4 operators x 10 offspring per generation). This matches EoH's own
population_generation_<g>.json files for all 30 runs.
"""
import json
import statistics

import matplotlib.pyplot as plt

from crp.paths import RESULTS

ALPHAS = (0.5, 0.3, 0.1)
SEEDS = range(1, 11)
POP_SIZE = 10
INIT_RULES = 20
RULES_PER_GENERATION = 40
GENERATIONS = 15  # 0..14; generation 12 ends at evaluation 500, 13 and 14 are the 10% margin
BUDGET_GENERATION = 12


def run_curves(rules: list[dict]) -> tuple[list[float], list[float], list[float]]:
    """Best and mean total of the population, and % valid new rules, per generation."""
    best, mean, valid = [], [], []
    start = 0
    for g in range(GENERATIONS):
        end = INIT_RULES + RULES_PER_GENERATION * g
        population = sorted({r["total"] for r in rules[:end] if r["error"] is None})[:POP_SIZE]
        best.append(population[0])
        mean.append(statistics.mean(population))
        new = rules[start:end]
        valid.append(100 * sum(r["error"] is None for r in new) / len(new))
        start = end
    return best, mean, valid


def median_and_iqr(curves: list[list[float]]) -> tuple[list[float], list[float], list[float]]:
    """Per generation: median, first quartile and third quartile over the runs."""
    medians, q1s, q3s = [], [], []
    for values in zip(*curves):
        q1, median, q3 = statistics.quantiles(values, n=4)
        medians.append(median)
        q1s.append(q1)
        q3s.append(q3)
    return medians, q1s, q3s


def draw(ax, curves: list[list[float]], label: str, color: str) -> None:
    median, q1, q3 = median_and_iqr(curves)
    ax.plot(range(GENERATIONS), median, label=label, color=color)
    ax.fill_between(range(GENERATIONS), q1, q3, color=color, alpha=0.2)


def main() -> None:
    fig, axes = plt.subplots(2, len(ALPHAS), figsize=(13, 7), sharex=True)
    for col, alpha in enumerate(ALPHAS):
        runs = []
        for seed in SEEDS:
            with (RESULTS / "llm_runs_full" / f"eoh_a{alpha}_s{seed}.jsonl").open() as f:
                runs.append(run_curves([json.loads(line) for line in f]))
        top, bottom = axes[0, col], axes[1, col]
        draw(top, [best for best, _, _ in runs], "best", "tab:blue")
        draw(top, [mean for _, mean, _ in runs], "mean of population", "tab:orange")
        draw(bottom, [valid for _, _, valid in runs], "new rules that ran without error", "tab:green")
        top.set_title(f"alpha {alpha}")
        bottom.set_xlabel("generation")
        bottom.set_ylim(0, 100)
        for ax in (top, bottom):
            ax.axvline(BUDGET_GENERATION, color="grey", linestyle="--", linewidth=1)
            ax.grid(alpha=0.3)
    axes[0, 0].set_ylabel("training total relocations")
    axes[1, 0].set_ylabel("% of new rules that ran without error")
    axes[0, 0].legend()
    axes[1, 0].legend(loc="lower left")
    fig.suptitle("EoH convergence: median over 10 runs, band = IQR, dashed line = 500 evaluations")
    fig.tight_layout()
    path = RESULTS / "eoh_convergence.png"
    fig.savefig(path, dpi=150)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
