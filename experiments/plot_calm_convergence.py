"""Plot how CALM's population improved over the rounds and write results/calm_convergence.png.

Run from PyCharm (green button), or: python experiments/plot_calm_convergence.py
Needs matplotlib: pip install -e ".[plot]"

Same layout as plot_eoh_convergence.py. CALM's population cannot be rebuilt from the rule log,
because a collapse empties it, so it comes from CALM's own log: results/llm_runs_full/
calm_a<alpha>_s<seed>.pool.jsonl holds the 10 best totals after every round (the rules CALM
picks parents from) and marks the rounds that follow a collapse (experiments/calm_result.py
pools). One round scores up to 4 rules, so round r is drawn at 4*r evaluations.
"""
import json
import statistics

import matplotlib.pyplot as plt

from crp.paths import RESULTS

ALPHAS = (0.5, 0.3, 0.1)
SEEDS = range(1, 11)
ANSWERS_PER_ROUND = 4
ROUNDS = 125   # every run has at least 125 rounds; 125 x 4 = 500 evaluations, the budget
BLOCK = 20     # validity is measured per 20 scored rules


def read_jsonl(name: str) -> list[dict]:
    with (RESULTS / "llm_runs_full" / name).open() as f:
        return [json.loads(line) for line in f]


def pool_curves(rounds: list[dict]) -> tuple[list[float], list[float], list[int]]:
    """Best and mean total of the population per round, and the rounds right after a collapse."""
    rounds = rounds[:ROUNDS]
    best = [r["best10"][0] for r in rounds]
    mean = [statistics.mean(r["best10"]) for r in rounds]
    collapses = [r["round"] for r in rounds if r["collapse"]]
    return best, mean, collapses


def valid_curve(rules: list[dict]) -> list[float]:
    """% of the scored rules that ran without error, per block of 20 rules."""
    return [100 * sum(r["error"] is None for r in rules[i:i + BLOCK]) / BLOCK for i in range(0, 500, BLOCK)]


def draw(ax, xs: list[int], curves: list[list[float]], label: str, color: str) -> None:
    """Median over the runs, with a band from the first to the third quartile."""
    q1, median, q3 = zip(*(statistics.quantiles(values, n=4) for values in zip(*curves)))
    ax.plot(xs, median, label=label, color=color)
    ax.fill_between(xs, q1, q3, color=color, alpha=0.2)


def main() -> None:
    fig, axes = plt.subplots(2, len(ALPHAS), figsize=(13, 7), sharex=True)
    evaluations = [ANSWERS_PER_ROUND * r for r in range(1, ROUNDS + 1)]
    blocks = [i + BLOCK for i in range(0, 500, BLOCK)]
    for col, alpha in enumerate(ALPHAS):
        bests, means, valids, collapses = [], [], [], []
        for seed in SEEDS:
            best, mean, collapse_rounds = pool_curves(read_jsonl(f"calm_a{alpha}_s{seed}.pool.jsonl"))
            bests.append(best)
            means.append(mean)
            collapses += collapse_rounds
            valids.append(valid_curve(read_jsonl(f"calm_a{alpha}_s{seed}.jsonl")[:500]))
        top, bottom = axes[0, col], axes[1, col]
        draw(top, evaluations, bests, "best", "tab:blue")
        draw(top, evaluations, means, "mean of population", "tab:orange")
        draw(bottom, blocks, valids, "scored rules that ran without error", "tab:green")
        low = top.get_ylim()[0]
        top.plot([ANSWERS_PER_ROUND * r for r in collapses], [low] * len(collapses), "|", color="grey",
                 markersize=10, label="collapse (any run)")
        top.set_title(f"alpha {alpha}")
        bottom.set_xlabel("evaluations (4 per round)")
        bottom.set_ylim(0, 100)
        for ax in (top, bottom):
            ax.grid(alpha=0.3)
    axes[0, 0].set_ylabel("training total relocations")
    axes[1, 0].set_ylabel("% of scored rules that ran without error")
    axes[0, 0].legend()
    axes[1, 0].legend(loc="lower left")
    fig.suptitle("CALM convergence: median over 10 runs, band = IQR, population = the 10 best rules")
    fig.tight_layout()
    path = RESULTS / "calm_convergence.png"
    fig.savefig(path, dpi=150)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
