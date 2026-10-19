# C++ reference → Python file map

A filtered, read-only copy of the authors' C++ code (Ðurasević et al.): only the files this
Python reproduction was ported from. Nothing here is compiled.

| C++ file | Python | What was taken |
|---|---|---|
| `simulator/ContainerYard.*`, `BayFloor.*` | `src/crp/yard.py` | stacks, `Relocate`, `Retrieve`, move counter, look-ahead window (`MaximumKnownContainer`, `GetTopContainerId`, `GetContainerId`), `GetMinimumStack` |
| `simulator/SelectFirstAvailabelContainerStrategy.*`, `ContainerSourceSelectionStrategy.*` | `src/crp/yard.py` | which stack holds the target |
| `data_io/CasertaDataSetLoader.*`, `ProblemInstance.*`, `DataSet.*`, `DataSetLoader.h` | `src/crp/instance.py` | file format; max height = tiers + 2 from the file name |
| `data_io/CasertaProblemInstanceGenerator.*`, `CasertaProblemSetGenerator.*` | `src/crp/instance.py` | shuffle IDs 1..N into stacks; 21 classes (we use a fixed seed, not the clock) |
| `schemes/UnrestrictedAutomaticHeuristic.*`, `PriorityHeuristic.*` | `src/crp/schemes.py` | Algorithm 2 with preventive moves |
| `heuristics/PU1.*`, `PU2.*` | `src/crp/pu.py` | the two hand-made unrestricted rules |
| `heuristics/TLP.*` | `tests/test_yard.py` | lowest-stack rule, used as a loader/yard check (36,024) |
| `gp/Terminals.*`, `Terminal.*` | `src/crp/terminals.py` | SH, EMP, AVG, CUR, RI, DIFF |
| `gp/Evaluator.*` | `src/crp/gp/expression.py` | prefix formulas, + − × and protected ÷ |
| `gp/CrpEvalOp.*`, `HeuristicFactory.cpp` | `src/crp/gp/fitness.py` | fitness = total relocations over the training set |
| `gp/parameters_NOT_PAPER_SETTINGS.txt` | — | reference only; **not** the paper's settings |

The GP algorithm itself comes from the ECF 1.4.2 library (not included); see `src/crp/gp/`.

## Behaviours copied exactly (they change the numbers)

1. **Look-ahead window:** last visible ID = `int(next_id + alpha * N)`, rounded down.
2. **Hidden IDs:** Maximum = last visible ID + 1 (commented out in the C++, switched on in both
   `GetTopContainerId` and `GetContainerId`); Ignore = −1 and skipped.
3. **Ties between stacks:** the leftmost stack wins.
4. **Retrievals are not counted**, only relocations.
5. **Max height** = tiers + 2.
6. **AVG** is cut to a whole number; AVG of an empty stack = 0.
7. **MIN** of an empty stack = 2,147,483,647 (`INT_MAX`); DIFF = MIN − CUR.
8. **Protected division:** if |divisor| < 1e-9, the result is 1.
9. **CUR** = the moved container's visible value.
10. **Preventive move:** triggered when `top(destination) < top(source)` on visible values; the
    safe stack excludes source, destination and full stacks; the last empty stack wins, otherwise
    the stack with the smallest minimum above the moved container.

Where paper and code disagree, see `docs/paper_vs_code.md`.

## Reference data

- `data3-3-1.dat`: identical to Caserta's public copy.
- `expressions_res.txt`, `expressions_unres.txt`: formulas evolved by the authors, used in
  `tests/golden.py` to test the formula evaluator.
