"""Plot how the best rule of our framework improved over the budget, next to EoH (also with our knowledge), ReEvo, CALM and LLaMEA.

Run from PyCharm (green button), or: python experiments/plot_framework_convergence.py
Needs matplotlib: pip install -e ".[plot]"

Writes results/framework_convergence.png (ours from both start rules and without knowledge, vs
EoH, ReEvo, CALM and LLaMEA) and results/framework_ablation_convergence.png (the full framework vs one
module switched off). The curve of a run is the best training total among the rules fully
evaluated so far; for our framework, k evaluations are the first k x 840 yard simulations of its
budget, for the others the first k logged rules (as in compare_methods.py). Line = median over the
10 runs, band = the middle 50% of the runs. GP-500's median best training total is marked at 500.
"""
import math
import statistics

import matplotlib.pyplot as plt

from compare_framework import FULL, LOWEST, NO_KNOWLEDGE, NO_PARETO, NO_SCREENING, NO_TEXT, OURS, best_after, our_log
from compare_methods import ALPHAS, read_csv, rule_logs
from crp.paths import RESULTS

STEPS = range(1, 501)
BASELINES = {"eoh": "EoH", "eoh-knowledge": "EoH with our knowledge", "reevo": "ReEvo", "calm": "CALM", "llamea": "LLaMEA"}
COLORS = {FULL: "tab:blue", LOWEST: "tab:cyan", NO_KNOWLEDGE: "tab:purple", NO_TEXT: "tab:orange",
          NO_SCREENING: "tab:red", NO_PARETO: "tab:olive", "eoh": "tab:green", "reevo": "tab:brown",
          "calm": "tab:pink", "llamea": "tab:gray", "eoh-knowledge": "darkgreen"}


def ours(method: str, alpha: str) -> list[list[float]]:
    logs = [our_log(method, alpha, str(seed)) for seed in range(1, 11)]
    return [[best_after(log, k * 840) for k in STEPS] for log in logs]


def baseline(method: str, alpha: str) -> list[list[float]]:
    curves = []
    for log in rule_logs(method, alpha):
        best, curve = math.inf, []
        for rule in log:
            if rule["total"] is not None:
                best = min(best, rule["total"])
            curve.append(best)
        curves.append(curve)
    return curves


def draw(ax, curves: list[list[float]], label: str, color: str) -> None:
    q1, median, q3 = zip(*(statistics.quantiles(values, n=4) for values in zip(*curves)))
    ax.plot(STEPS, median, label=label, color=color)
    ax.fill_between(STEPS, q1, q3, color=color, alpha=0.15)


def figure(groups: dict[str, list[str]], path, title: str) -> None:
    """groups: alpha -> the methods drawn in that panel."""
    gp500 = {}
    for row in read_csv("gp_500.csv"):
        if row["population"] == "50":
            gp500.setdefault(row["alpha"], []).append(float(row["train_fitness"]))
    fig, axes = plt.subplots(1, len(groups), figsize=(5 * len(groups), 4.5))
    for ax, (alpha, methods) in zip(axes, groups.items()):
        drawn = []
        for m in methods:
            curves = ours(m, alpha) if m in OURS else baseline(m, alpha)
            draw(ax, curves, OURS.get(m) or BASELINES[m], COLORS[m])
            drawn += [value for curve in curves for value in curve[49:]]  # from 50 evaluations on: a readable y range
        drawn.append(statistics.median(gp500[alpha]))  # keep GP-500's marker inside the y range
        ax.scatter([500], [statistics.median(gp500[alpha])], color="black", marker="x", zorder=3,
                   label="GP-500 (pop 50), median at the end")
        ax.set_ylim(min(drawn) - 50, max(drawn) + 50)
        ax.set_title(f"alpha {alpha}")
        ax.set_xlabel("evaluations")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("best training total relocations")
    axes[0].legend(fontsize=8)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f"wrote {path}")


def main() -> None:
    main_methods = [FULL, LOWEST, NO_KNOWLEDGE, "eoh", "eoh-knowledge", "reevo", "calm", "llamea"]
    figure({a: [m for m in main_methods if m != NO_KNOWLEDGE or a != "0.3"] for a in ALPHAS},
           RESULTS / "framework_convergence.png",
           "Our framework vs the LLM methods: median over 10 runs, band = middle 50%")
    figure({a: [FULL, NO_TEXT, NO_SCREENING, NO_PARETO] for a in ("0.5", "0.1")},
           RESULTS / "framework_ablation_convergence.png",
           "Ablations (Min-Max start): median over 10 runs, band = middle 50%")


if __name__ == "__main__":
    main()
