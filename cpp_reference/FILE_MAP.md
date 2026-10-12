# C++ reference → Python file map

This folder is a **filtered copy** of the authors' C++ code (Ðurasević et al.), keeping only
what we need to reproduce the online CRP with a **limited horizon**, for the **restricted and
unrestricted** schemes. It is read-only reference material; nothing here gets compiled.

- Original: 2 projects, ~380 files (`crp` ≈ 265 source files / ~19,800 lines, plus `crpecf`).
- Kept: 56 source files / ~5,000 lines. Expected Python size: ~1,200–1,500 lines.

## Folder layout

| Folder | What it contains |
|---|---|
| `simulator/` | The yard: stacks, retrieve/relocate, hidden IDs, finding the target |
| `data_io/` | Reading Caserta files, generating new (training) instances |
| `schemes/` | Restricted and unrestricted relocation schemes (Algorithms 1 and 2) |
| `heuristics/` | The 10 hand-made baseline rules |
| `gp/` | Terminals, formula evaluation, fitness evaluation (GP itself is ECF, not ported) |
| `reference_data/` | One sample instance + 59 evolved formulas (for testing our evaluator) |

## File → Python module

| C++ file | Python module | Keep | Drop |
|---|---|---|---|
| `simulator/ContainerYard.*` | `crp/yard.py` | stacks, `Retrieve`, `Relocate`, move counter, `MaximumKnownContainer`, `GetTopContainerId`, `GetContainerId`, helpers used by terminals (`reshuffleIndex`, `calculateAverageContainerID`, `GetMinimumStack`, `GetNumberOfUknown`, …) | crane time, energy, weights, multi-bay, duplicate IDs, arrival events, groups (later) |
| `simulator/BayFloor.*` | `crp/yard.py` | stack storage (list of lists, bottom → top) | multi-bay indexing |
| `simulator/Location.*` | (not needed) | — | Python uses a plain stack index |
| `simulator/SelectFirstAvailabelContainerStrategy.*`, `ContainerSourceSelectionStrategy.*` | `crp/yard.py` | "which stack holds the target" | strategies for duplicate IDs |
| `data_io/CasertaDataSetLoader.*` | `crp/instance.py` | file format, max height = tiers + 2 from file name | container weights |
| `data_io/ProblemInstance.*`, `DataSet.*`, `DataSetLoader.h` | `crp/instance.py` | an `Instance` dataclass + list of instances | factory boilerplate |
| `data_io/CasertaProblemInstanceGenerator.*`, `CasertaProblemSetGenerator.*` | `crp/instance.py` | random shuffle of IDs 1..N into stacks; 21 classes × 40 | time-based seed → we use a **fixed seed** (reproducible) |
| `schemes/PriorityHeuristic.*` | `crp/schemes.py` | common interface: `solve(yard)` | — |
| `schemes/RestrictedAutomaticHeuristic.*` | `crp/schemes.py` | Algorithm 1 | `retrievalRate`, `GetPriorities` |
| `schemes/UnrestrictedAutomaticHeuristic.*` | `crp/schemes.py` | Algorithm 2 (preventive moves) | relocation-type counters |
| `heuristics/TLP.*` | `crp/heuristics/tlp.py` | lowest stack | — |
| `heuristics/ReshuffleIndex.*` | `crp/heuristics/ri.py` | RI rule | — |
| `heuristics/MinMax.*` | `crp/heuristics/minmax.py` | MM rule | — |
| `heuristics/PR4.*` | `crp/heuristics/pr4.py` | PR4 rule | — |
| `heuristics/RDH.*` | `crp/heuristics/rdh.py` | RDH rule | — |
| `heuristics/ExpectedReshuffleIndex.*` | `crp/heuristics/eri.py` | ERI rule | — |
| `heuristics/ExpectedMiniMax.*` | `crp/heuristics/em.py` | EM rule | — |
| `heuristics/ExpectedGroupHeuristic.*` | `crp/heuristics/egh.py` | EGH rule | — |
| `heuristics/PU1.*`, `PU2.*` | `crp/heuristics/pu1.py`, `pu2.py` | unrestricted hand-made rules | — |
| `gp/Terminals.*`, `Terminal.*` | `crp/terminals.py` | SH, EMP, AVG, CUR, RI, DIFF (+ NUNC, NPER, NRAT later) | ~25 terminals from other projects (HS, LS, ENGY, WGHT, CHAIN, …) |
| `gp/Evaluator.*` | `crp/gp/expression.py` | prefix-expression parsing, + − × and protected ÷ | sin, cos, ifpos, ifgt, min |
| `gp/CrpEvalOp.*` | `crp/gp/fitness.py` | fitness = total relocations over the training set | surrogates, sockets, energy/time criteria, multi-objective |
| `gp/HeuristicFactory.cpp` | `crp/gp/fitness.py` | which scheme class goes with "restricted"/"unrestricted" | ~15 other heuristic variants |
| `gp/parameters_NOT_PAPER_SETTINGS.txt` | — | reference only | **not** the paper's settings (pop 100, depth 4); paper: pop 1000, depth 5, 50,000 evals |

## Behaviours to copy exactly (found in the C++)

These details change the numbers, so the Python must match them:

1. **Look-ahead window:** last visible ID = `int(next_id + alpha * N)` → rounded **down**, no cap needed.
2. **Hidden IDs:** Ignore = `-1` and skipped in calculations; **Maximum = last visible ID + 1**.
   In the C++, Maximum is commented out — it must be switched in **both** `GetTopContainerId` and `GetContainerId`.
3. **Ties between stacks:** the **leftmost** stack wins (the time-based tie-break never actually switches).
4. **Retrievals are not counted**; only relocations are.
5. **Max height** = tiers + 2 (tiers read from the file name).
6. **AVG** is cut to a whole number (`int`); AVG of an empty stack = 0.
7. **MIN** of an empty stack (or one with only hidden IDs under Ignore) = 2,147,483,647 (`INT_MAX`); DIFF = MIN − CUR.
8. **Protected division:** if |divisor| < 1e-9, the result is 1.
9. **CUR** = the moved container's visible value (hidden → −1 or last visible + 1).
10. **Unrestricted preventive move:** triggered when `top(destination) < top(source)` using **visible** values;
    the safe stack S1 excludes source, destination and full stacks; an **empty** stack is preferred
    (the last empty one in left-to-right order), otherwise the stack with the **smallest minimum ID** above DC.

## Reference data

- `data3-3-1.dat` — identical to Caserta's public copy (github.com/marcocaserta/BRP).
- `expressions_res.txt` / `expressions_unres.txt` — evolved formulas in prefix notation
  (e.g. `+ SH * RI EMP`). Useful to test that our expression evaluator parses and runs them.
  Which scenario they were evolved for is unknown.

## Validation targets (from the paper)

| Check | Paper | Status |
|---|---|---|
| TLP, all 840 test yards | 36,024 | ✅ matched in Python |
| PU1 / PU2, α = 1.0 (Table 5) | 25,049 / 24,962 | to do |
| PU1 / PU2, Maximum, α = 0.5 / 0.3 / 0.1 | 25,116 / 25,027 · 25,905 / 25,826 · 31,719 / 31,763 | to do |
