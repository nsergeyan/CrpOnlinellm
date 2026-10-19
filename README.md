# Online container relocation: a Python reproduction

Research project (Data Science and AI, Leiden University). It reproduces, in Python, the
genetic-programming experiments from:

> Đurasević, Đumić & Gil-Gala (2026). *Automated design of relocation rules with genetic
> programming for the online container relocation problem.* Expert Systems with Applications.

The same code will later evaluate heuristics designed by an LLM ([EoH](https://github.com/FeiLiu36/EoH)),
so any Python function can act as a relocation rule.

## The problem in short

A yard has stacks of containers. Each container's ID is its retrieval order, and only the top of a
stack can be moved. To retrieve a buried container, the ones above it must be **relocated** to
other stacks. The goal is to minimise relocations. In the **online** variant only the next
`alpha * N` container IDs are known; hidden containers are all treated as "last known ID + 1"
(the *Maximum* strategy).

A relocation rule = a fixed **scheme** (here the *unrestricted* scheme, which may also make
preventive moves) + a **priority function** that scores every candidate stack. GP evolves the
priority function as a formula over six terminals (SH, EMP, AVG, CUR, RI, DIFF).

## Results

Total relocations over the 840 Caserta test instances (lower is better).

**Exact reproductions** (deterministic rules, must match to the unit):

| Check | Paper | Ours |
|---|---|---|
| TLP, any alpha | 36,024 | 36,024 |
| PU1 / PU2, alpha 1.0 | 25,049 / 24,962 | 25,049 / 24,962 |
| PU1 / PU2, alpha 0.5 | 25,116 / 25,027 | 25,116 / 25,027 |
| PU1 / PU2, alpha 0.3 | 25,905 / 25,826 | 25,905 / 25,826 |
| PU1 / PU2, alpha 0.1 | 31,719 / 31,763 | 31,719 / 31,763 |

**GP** (median of 30 runs per alpha; random, so it only needs to come close):

| alpha | Ours | Paper | Our middle 50% of runs |
|---|---|---|---|
| 0.5 | 24,074 | 24,094 | 24,039 - 24,123 |
| 0.3 | 24,768 | 24,733 | 24,730 - 24,790 |
| 0.1 | 28,985 | 28,985 | 28,959 - 29,034 |

The paper's median lies inside our middle 50% for every alpha, and every one of the 90 GP rules
beats the best hand-made rule. Full table: [`results/summary.md`](results/summary.md).

## Setup

Python 3.10 or newer, no third-party packages (pytest for the tests only).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install -e ".[dev,llm]"   # only for the LLM experiments
bash scripts/setup_reevo.sh  # only for the LLM experiments: ReEvo + original EoH (Python 3.11, see frameworks/README.md)
pytest                      # 118 tests, about 40 seconds (the ReEvo test is skipped until setup)
```

## How to run

| Task | Command | Time |
|---|---|---|
| One GP run, quick test (2,000 evaluations) | `python experiments/run_gp.py --alpha 0.5 --seed 1 --quick` | ~30 s |
| One full GP run (51,000 evaluations, all cores) | `python experiments/run_gp.py --alpha 0.5 --seed 1` | ~11 min |
| The paper's 90 runs (30 seeds x 3 alphas) | `caffeinate -i python experiments/run_gp_many.py` | ~12 h |
| Results table from the CSV | `python experiments/summarize_results.py` | instant |
| Speed of one evaluation | `python experiments/benchmark_eval.py` | ~10 s |
| Regenerate the training set (already done) | `python experiments/make_training_set.py` | instant |

Full runs go to `results/gp_full.csv`, quick ones to `results/gp_quick.csv`. The batch script skips
runs that are already in the CSV, so an interrupted batch continues where it stopped.

## How it works

```
data/training (840 yards, seed 2026)
        │
        ▼
GP (port of the ECF 1.4.2 library the authors used)          src/crp/gp/
  population 1,000, steady-state tournament of 3, 51,000 evaluations
        │ fitness of a formula = total relocations on the training set
        ▼
formula ──compile──► priority function ──► unrestricted scheme ──► yard + look-ahead window
                                            src/crp/schemes.py      src/crp/yard.py
        │
        ▼ best formula, evaluated once
data/caserta_840 (840 test yards) ──► results/gp_full.csv
```

## Project layout

| Path | What it contains |
|---|---|
| `src/crp/instance.py` | `Instance` (starting layout), Caserta loader, training-set generator |
| `src/crp/yard.py` | `Yard`: stacks, `relocate`, `retrieve`, look-ahead window (`value`) |
| `src/crp/terminals.py` | the six terminals for one candidate stack |
| `src/crp/schemes.py` | unrestricted scheme: readable reference + a fast version that GP uses |
| `src/crp/heuristics/pu.py` | PU1 and PU2, the paper's hand-made baselines |
| `src/crp/gp/` | GP: `tree`, `crossover` (5), `mutation` (7), `algorithm` (the loop), `expression` (parse and compile formulas), `fitness` (cached and parallel), `experiment` (runs and CSV) |
| `src/crp/paper.py` | every paper number we reproduce |
| `src/crp/paths.py` | data and results folders |
| `experiments/` | scripts listed under "How to run" |
| `tests/` | unit tests plus "matches the paper" tests |
| `data/caserta_840/` | the 840 public Caserta test instances |
| `data/training/` | our 840 training instances (same 21 classes, seed 2026) |
| `results/` | `gp_full.csv` (90 runs), `summary.md`, overnight log |
| `docs/paper_vs_code.md` | 18 places where paper and code differ, and which we followed |
| `cpp_reference/` | filtered copy of the authors' C++ code; `FILE_MAP.md` maps it to Python |

## Design notes

- **Exactness first.** Details that change the numbers (tie-breaking, rounding, hidden values,
  even a C++ `=` that should probably be `!=`) are copied from the authors' code and listed in
  `docs/paper_vs_code.md`.
- **Reference and fast path.** `solve_unrestricted` + `evaluate` are written to be read;
  `solve_unrestricted_fast` + `compile_formula` give identical results about 4x faster. A test pins
  28 totals from the reference path and compares both paths move by move.
- **Fair comparison by design.** A priority function only receives the six terminals, never the raw
  yard, so it cannot see hidden container IDs. LLM-written functions use the same interface,
  scorer, training set and test set as GP.

### LLM phase: decisions

1. Compare EoH and ReEvo with GP and PU1/PU2, using the published frameworks rather than a
   self-written LLM loop, so the results concern established methods.
2. A rule that crashes or returns a non-number, NaN or inf fails as a whole, checked before the
   scheme uses the score; otherwise NaN would silently send the container to the last stack.
3. Both methods score code through `crp.llm.evaluate`, in exactly the same way.
4. One shared prompt file, `src/crp/llm/prompts.py`, so both methods get identical texts; the AVG
   description matches the code (unknown containers count as last known ID + 1).
5. The authors' original framework code, unchanged, at a pinned commit, installed by
   `scripts/setup_reevo.sh` in its own Python 3.11 environment.
6. EoH is the original paper version, using the copy bundled with ReEvo, so both methods share
   the LLM client, scorer and prompt files. The newer EoH v0.2 was tried and removed.
7. Qwen3-14B with thinking off; 500 evaluations x 10 runs per method per alpha.
8. Thinking is switched the same way for both methods (model default or shared prompt text).
9. The shared prompt asks for a variable `priority` and `return priority`, because the original
   EoH replaces the last line of the code with `return priority`.

## License

My code is MIT licensed, see `LICENSE`. `cpp_reference/` and `data/caserta_840/` belong to
their original authors and are not covered by it.
