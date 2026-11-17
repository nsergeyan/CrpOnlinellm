"""Compare our framework with GP, EoH, ReEvo, CALM, LLaMEA and Min-Max, and write results/framework_comparison.md.

Run from PyCharm (green button), or: python experiments/compare_framework.py   (about 2 minutes)

Same yards, scorer and statistics as experiments/compare_methods.py: two-sided exact Mann-Whitney U
test, Holm correction over the rows of one table, A12 = the chance that a run of the first method
beats a run of the second. Every method except the two GP-800 settings and GP-51,000 has a budget
of 500 evaluations (420,000 yard simulations for our framework). GP from Min-Max: one individual
of the initial population is the Min-Max formula (README decision 51); "Min-Max also a terminal":
random trees and mutations can pick the Min-Max score too (decision 52). GP counts an evaluation also when the
formula repeats an earlier one and is not simulated again, while our framework rejects repeats
for free; GP-800 is the check for that: with 800 evaluations GP simulates about 500 different
formulas (section 8). Section 5 scores the best rule of every run again,
yard by yard, and stops if a total differs from the one in the results files. The three check
runs with one rule at a time ("ours-batch1", README decision 43) are not part of the comparison.
"""
import gzip
import json
import statistics
from collections import Counter, defaultdict

from compare_methods import ALPHAS, CHECKPOINTS, a12, fmt, holm, mann_whitney_p, read_csv, rule_logs, total
from crp.framework.knowledge import SEEDS
from crp.framework.scoring import yard_type
from crp.gp.expression import MINMAX, compile_formula
from crp.instance import load_dataset
from crp.llm.evaluate import compile_rule, guarded
from crp.paths import RESULTS, TEST_SET, TRAINING_SET
from crp.schemes import solve_unrestricted_fast
from crp.yard import Yard

FULL, LOWEST, NO_KNOWLEDGE = "ours", "ours-lowest", "ours-lowest-no_knowledge"
NO_TEXT, NO_SCREENING, NO_PARETO = "ours-no_knowledge", "ours-no_crash_check-no_dedup-no_quick_test", "ours-no_pareto-no_feedback"
OURS = {FULL: "Ours (Min-Max start)", LOWEST: "Ours (lowest-stack start)", NO_TEXT: "Ours, no knowledge text",
        NO_SCREENING: "Ours, screening and repair off", NO_PARETO: "Ours, Pareto and feedback off",
        NO_KNOWLEDGE: "Ours, lowest-stack start, no knowledge text"}
BASELINES = {"gp500": "GP-500 (pop 50)", "gp500_100": "GP-500 (pop 100)", "gp800": "GP-800 (pop 50)",
             "gp500_mm": "GP-500 from Min-Max", "gp800_mm": "GP-800 from Min-Max",
             "gp500_mmt": "GP-500, Min-Max also a terminal", "gp800_mmt": "GP-800, Min-Max also a terminal",
             "eoh": "EoH", "reevo": "ReEvo", "calm": "CALM", "llamea": "LLaMEA", "gp51k": "GP-51,000"}
GP_FILES = {"gp800": "gp_800.csv", "gp500_mm": "gp_500_minmax.csv", "gp800_mm": "gp_800_minmax.csv",
            "gp500_mmt": "gp_500_minmax_terminal.csv", "gp800_mmt": "gp_800_minmax_terminal.csv"}
NAMES = OURS | BASELINES
BUDGET = 420_000  # yard simulations of one run of ours
median = statistics.median


def table(header: list[str], rows: list[list[str]]) -> list[str]:
    return ["", "| " + " | ".join(header) + " |", "|---" * len(header) + "|"] + ["| " + " | ".join(r) + " |" for r in rows]


def tests(pairs: list[tuple[str, list[float], list[float]]]) -> list[str]:
    """A table of Mann-Whitney tests, Holm-corrected over all its rows. pairs: (label, first, second)."""
    p_values = [mann_whitney_p(a, b) for _, a, b in pairs]
    rows = []
    for (label, a, b), p, corrected in zip(pairs, p_values, holm(p_values)):
        diff = median(a) - median(b)
        rows.append([label, fmt(median(a)), fmt(median(b)), f"{diff:+,.0f} ({diff / median(b):+.1%})", f"{p:.4f}",
                     f"{corrected:.4f}{' *' if corrected < 0.05 else ''}", f"{a12(a, b):.2f}"])
    return table(["comparison", "median, first", "median, second", "difference", "p", "p, Holm-corrected",
                  "A12 (first wins)"], rows)


def our_log(method: str, alpha: str, seed: str) -> list[dict]:
    with gzip.open(RESULTS / "llm_runs_full" / f"{method}_a{alpha}_s{seed}.jsonl.gz", "rt") as f:
        return [json.loads(line) for line in f]


def best_after(log: list[dict], simulations: int) -> int:
    """Best training total among the rules fully evaluated within the first `simulations` of the budget."""
    return min(e["total"] for e in log if e["status"] == "evaluated" and e["used"] <= simulations)


def type_totals(rule, alpha: str, yards: list) -> dict[tuple[int, int], int]:
    totals = defaultdict(int)
    for yard in yards:
        totals[yard_type(yard)] += solve_unrestricted_fast(Yard(yard, float(alpha)), rule)
    return totals


def main() -> None:
    llm, gp500, gp51k = read_csv("llm_full.csv"), read_csv("gp_500.csv"), read_csv("gp_full.csv")
    runs = defaultdict(list)  # (method, alpha) -> the rows of its runs
    for row in llm:
        runs[row["method"], row["alpha"]].append(row)
    for row in gp500:
        runs["gp500" if row["population"] == "50" else "gp500_100", row["alpha"]].append(row)
    for row in gp51k:
        runs["gp51k", row["alpha"]].append(row)
    for name, file in GP_FILES.items():
        for row in read_csv(file):
            runs[name, row["alpha"]].append(row)
    test = {key: [total(r["test_total"]) for r in rows] for key, rows in runs.items()}
    train = {key: [float(r["train_fitness"]) for r in rows] for key, rows in runs.items()}
    logs = {(m, a): [our_log(m, a, r["seed"]) for r in runs[m, a]] for m in OURS for a in ALPHAS if (m, a) in runs}
    training_yards, test_yards = load_dataset(TRAINING_SET), load_dataset(TEST_SET)
    minmax = guarded(compile_rule(SEEDS["minmax"][1], "priority"))
    minmax_types = {a: type_totals(minmax, a, test_yards) for a in ALPHAS}
    minmax_test = {a: sum(minmax_types[a].values()) for a in ALPHAS}
    minmax_train = {a: sum(type_totals(minmax, a, training_yards).values()) for a in ALPHAS}

    lines = [
        "# Our framework vs GP, the LLM methods and Min-Max",
        "",
        "Total relocations (lower is better). Test totals over the 840 Caserta yards, training totals",
        "over the 840 training yards. Ours, EoH, ReEvo, CALM and LLaMEA: 10 runs per alpha, Qwen3-14B with thinking",
        "off; GP: 30 runs per alpha. Every method except the two GP-800 settings and GP-51,000 has 500",
        "evaluations. GP-800 gives GP about 500 different formulas, since GP also counts repeats (section 8).",
        "GP from Min-Max has the Min-Max formula as one individual of its initial population; with",
        "\"Min-Max also a terminal\", GP's random trees and mutations can pick the Min-Max score too. Min-Max",
        "is our priority function for the Min-Max idea, the rule our framework starts from, without any",
        "search. Generated by",
        "`experiments/compare_framework.py`; the statistics are described in its docstring.",
        "",
        "## 1. Test totals",
    ]
    for alpha in ALPHAS:
        rows = [["Min-Max, no search", "1", fmt(minmax_test[alpha]), "", "", "", "", fmt(minmax_train[alpha]),
                 f"{minmax_test[alpha] - minmax_train[alpha]:+,.0f}"]]
        for m in NAMES:
            if (m, alpha) in runs:
                values = test[m, alpha]
                q1, mid, q3 = statistics.quantiles(values, n=4)
                gap = [te - tr for te, tr in zip(values, train[m, alpha]) if te != float("inf")]
                rows.append([NAMES[m], str(len(values)), fmt(mid), f"{fmt(q1)} - {fmt(q3)}", fmt(min(values)),
                             fmt(max(values)), f"{sum(v < minmax_test[alpha] for v in values)} of {len(values)}",
                             fmt(median(train[m, alpha])), f"{median(gap):+,.0f}"])
        lines += ["", f"**alpha {alpha}**"] + table(
            ["method", "runs", "median", "IQR", "best", "worst", "runs better than Min-Max", "training median",
             "test minus training"], rows)

    lines += ["", "## 2. Our framework against each baseline", "",
              "Test totals; Holm-corrected over the twelve baselines of one table."]
    for m in (FULL, LOWEST, NO_KNOWLEDGE):
        for alpha in ALPHAS:
            if (m, alpha) in runs:
                lines += ["", f"**{OURS[m]}, alpha {alpha}**"] + tests(
                    [(f"vs {BASELINES[b]}", test[m, alpha], test[b, alpha]) for b in BASELINES])

    ablations = [(m, a) for a in ("0.5", "0.1") for m in (NO_TEXT, NO_SCREENING, NO_PARETO)]
    lines += ["", "## 3. Ablations: the full framework against one module switched off", "",
              "All from the Min-Max start. Holm-corrected over the six rows of a table.", "", "**Test totals**"]
    lines += tests([(f"full vs {OURS[m].removeprefix('Ours, ')}, alpha {a}", test[FULL, a], test[m, a]) for m, a in ablations])
    lines += ["", "**Training totals** (what the search optimises)"]
    lines += tests([(f"full vs {OURS[m].removeprefix('Ours, ')}, alpha {a}", train[FULL, a], train[m, a]) for m, a in ablations])

    cells = {("Min-Max", "yes"): FULL, ("Min-Max", "no"): NO_TEXT, ("lowest stack", "yes"): LOWEST, ("lowest stack", "no"): NO_KNOWLEDGE}
    lines += ["", "## 4. CRP knowledge: the start rule and the knowledge text", "", "**Median test totals**"]
    lines += table(["start rule", "knowledge text"] + [f"alpha {a}" for a in ALPHAS],
                   [[start, text] + [fmt(median(test[m, a])) if (m, a) in runs else "" for a in ALPHAS]
                    for (start, text), m in cells.items()])
    pairs = [(FULL, NO_TEXT), (LOWEST, NO_KNOWLEDGE), (FULL, LOWEST), (NO_TEXT, NO_KNOWLEDGE)]
    lines += ["", "**Effect of one source of knowledge** (test totals; Holm-corrected over the rows)"]
    lines += tests([(f"alpha {a}: {OURS[x]} vs {OURS[y]}", test[x, a], test[y, a])
                    for a in ALPHAS for x, y in pairs if (x, a) in runs and (y, a) in runs])

    lines += ["", "## 5. Where the gains are: test totals per yard type", "",
              "Median over the runs of the best rules' totals on one yard type, as the difference from Min-Max",
              "(negative = fewer relocations than Min-Max). Yard types from small to large."]
    for alpha in ALPHAS:
        columns = {}
        for m in (FULL, "gp500", "gp51k"):
            per_run = []
            for row in runs[m, alpha]:
                rule = guarded(compile_rule(row["code"], "priority")) if m == FULL else compile_formula(row["formula"])
                per_run.append(type_totals(rule, alpha, test_yards))
                assert sum(per_run[-1].values()) == total(row["test_total"]), f"{m} alpha {alpha} seed {row['seed']}"
            columns[m] = {t: median(run[t] for run in per_run) for t in minmax_types[alpha]}
        rows = [[f"{t[0]} x {t[1]}", fmt(minmax_types[alpha][t])]
                + [f"{(columns[m][t] - minmax_types[alpha][t]) / minmax_types[alpha][t]:+.1%}" for m in columns]
                for t in sorted(minmax_types[alpha], key=lambda t: (t[0] * t[1], t))]
        lines += ["", f"**alpha {alpha}**"] + table(["tiers x stacks", "Min-Max"] + [NAMES[m] for m in columns], rows)

    lines += ["", "## 6. Convergence: median best training total after k evaluations", "",
              "For our framework, k evaluations are k x 840 yard simulations of the budget."]
    for alpha in ALPHAS:
        rows = [[OURS[m]] + [fmt(median(best_after(log, k * 840) for log in logs[m, alpha])) for k in CHECKPOINTS]
                for m in OURS if (m, alpha) in logs]
        for m in ("eoh", "reevo", "calm", "llamea"):
            rows.append([NAMES[m]] + [fmt(median(min(r["total"] for r in log[:k] if r["total"] is not None)
                                                 for log in rule_logs(m, alpha))) for k in CHECKPOINTS])
        lines += ["", f"**alpha {alpha}**"] + table(["method"] + [str(k) for k in CHECKPOINTS], rows)

    lines += ["", "## 7. Search behaviour of our framework", "", "**Per run** (medians over the runs)"]
    behaviour, operators = [], []
    for (m, alpha), group in logs.items():
        per_run, new_bests, proposed = defaultdict(list), Counter(), Counter()
        for log, row in zip(group, runs[m, alpha]):
            rules = [e for e in log[1:] if e["status"] not in ("budget_end", "stalled")]  # log[0] is the start rule
            status = Counter(e["status"] for e in rules)
            evaluated = [e for e in log if e["status"] == "evaluated"]
            best = min(evaluated, key=lambda e: e["total"])
            for name, value in (("rules", len(rules)), ("evaluated", status["evaluated"] / len(rules)),
                                ("screened", status["screened_out"] / len(rules)),
                                ("repeats", (status["duplicate_behaviour"] + status["duplicate_code"]) / len(rules)),
                                ("crashed", status["crash"] / len(rules)), ("calls", float(row["llm_calls"])),
                                ("hours", float(row["seconds"]) / 3600), ("found", best["used"] / BUDGET),
                                ("late", best_after(log, BUDGET * 2 // 3) - best["total"]),
                                ("lines", sum(1 for x in best["code"].splitlines() if x.strip() and not x.strip().startswith("#")))):
                per_run[name].append(value)
            so_far = log[0]["total"]
            for e in rules:
                proposed[e["operator"]] += 1
                if e["status"] == "evaluated" and e["total"] < so_far:
                    new_bests[e["operator"]], so_far = new_bests[e["operator"]] + 1, e["total"]
        mid = {name: median(values) for name, values in per_run.items()}
        behaviour.append([OURS[m], alpha, fmt(mid["rules"]), f"{mid['evaluated']:.0%}", f"{mid['screened']:.0%}",
                          f"{mid['repeats']:.0%}", f"{mid['crashed']:.1%}", fmt(mid["calls"]), f"{mid['hours']:.1f}",
                          f"{mid['found']:.0%}", fmt(mid["late"]), f"{sum(v == 0 for v in per_run['late'])} of {len(group)}",
                          fmt(mid["lines"])])
        operators.append([OURS[m], alpha] + [f"{new_bests[o]} of {proposed[o]:,}" for o in ("refine", "merge", "explore")])
    lines += table(["version", "alpha", "proposed rules", "fully evaluated", "stopped by the quick test", "repeats",
                    "crashed", "LLM calls", "hours", "best rule found at (share of budget)",
                    "gain in the last third of the budget", "runs without a gain in the last third",
                    "code lines of the best rule"], behaviour)
    lines += ["", "**Operators**: rules that were a new best of their run, of all rules the operator proposed "
              "(the runs of a version together)"]
    lines += table(["version", "alpha", "refine", "merge", "explore"], operators)
    lines += ["", "## 8. GP's repeated evaluations", "",
              "GP counts every evaluation, also of a formula it has scored before (not simulated again).",
              "Different formulas simulated per run:"]
    lines += table(["GP setting", "alpha", "evaluations", "different formulas, median", "fewest", "most"],
                   [[BASELINES[m], a, fmt(float(runs[m, a][0]["evaluations"]))]
                    + [fmt(f([float(r["evaluations"]) - float(r["cache_hits"]) for r in runs[m, a]])) for f in (median, min, max)]
                    for m in ("gp500", "gp500_100", "gp800", "gp500_mm", "gp800_mm", "gp500_mmt", "gp800_mmt", "gp51k")
                    for a in ALPHAS])
    lines += ["", "**GP started from Min-Max**: the best formula of a run against its start formula `MM`"]
    lines += table(["GP setting", "alpha", "runs", "ended with plain MM", "best formula uses MM",
                    "better than Min-Max on the training set", "better than Min-Max on the test set"],
                   [[BASELINES[m], a, str(len(runs[m, a])), str(sum(r["formula"] == MINMAX for r in runs[m, a])),
                     str(sum(MINMAX in r["formula"].split() for r in runs[m, a])),
                     str(sum(v < minmax_train[a] for v in train[m, a])),
                     str(sum(v < minmax_test[a] for v in test[m, a]))]
                    for m in ("gp500_mm", "gp800_mm", "gp500_mmt", "gp800_mmt") for a in ALPHAS])
    lines += ["", "\\* p < 0.05 after Holm correction. IQR = the middle 50% of the runs. A failed run (its best",
              "rule crashed on a test yard) counts as the worst result in the medians and tests."]
    path = RESULTS / "framework_comparison.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
