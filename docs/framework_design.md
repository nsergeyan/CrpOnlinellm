# Our CRP framework: design (v1)

An LLM framework for designing priority rules for the online CRP, without RL or fine-tuning. It
uses the same rule format (a priority function over SH, EMP, AVG, CUR, RI, DIFF), the same
scorer, the same training and test yards and the same budget as GP-500, EoH, ReEvo and CALM, so
the results compare directly. Each part answers a problem measured in the earlier runs.

## Why these parts

| Measured problem | Part that addresses it | Idea from |
|---|---|---|
| The LLMs rarely find basic CRP ideas (Min-Max logic in 2 to 12% of rules, after ~300 evaluations) | CRP knowledge in the prompt, Min-Max seed | DRoC, Jin & Tanaka |
| EoH spent 17.5% of its budget on rules that crash | crash test on 4 yards + repair from the error message | DRoC |
| Repeated rules (CALM 21% exact code repeats) | duplicate filter | our analysis |
| Every rule costs a full evaluation | quick test on 84 yards (ranks rules like the full 840: Spearman 0.998) | GEPA |
| Early convergence of the population | Pareto selection over yard types | GEPA |
| The LLM only sees one total per rule | rich feedback: where a rule is strong or weak | GEPA |

## Main loop

```
seed rule  ──►  population (10 rules, each fully evaluated)
                     │
  repeat until the 420,000 yard simulations are used:
    1. choose an operator: refine / merge / explore
    2. choose parent(s): Pareto selection
    3. LLM writes a new rule (task + knowledge + parents + rich feedback)
    4. exact duplicate?            → reject (costs 0)
    5. crash test on 4 yards       → crash? repair from the error message (max 2 tries)
    6. quick test on 84 yards      → behaves like an existing rule? → reject
                                   → not promising? → stop here
    7. full evaluation on 840 yards → update population and Pareto front
  result = the best fully evaluated rule, scored once on the test set
```

## The three components (each can be switched off for the ablations)

**1. CRP knowledge**
- `knowledge`: a short text in every prompt, written from the literature: badly-placed
  containers, stack quality (the smallest ID in a stack), forced vs additional relocations, why
  stacks with DIFF > 0 are safe, and how unknown containers work in the online setting.
- `seed`: `minmax`, Min-Max with ties broken by the lowest stack,
  `(DIFF if DIFF > 0 else 1e10 - DIFF) * 100 + SH`, chosen on the training set; or `lowest`,
  `priority = SH`, the seed of EoH, ReEvo and CALM. Both are run (option c agreed with Wei).

**2. Screening and repair**
- `crash_check`: 4 fixed yards (two small, two of the largest size); on a crash, the error
  message goes back to the LLM for a repair.
- `dedup`: identical code is rejected before any scoring; after the quick test, a rule with
  identical per-yard results to an existing rule is rejected.
- `quick_test`: 84 fixed yards (4 per yard type). A rule is fully evaluated only if its 84-yard
  total is better than the worst rule of the population on the same 84 yards, i.e. it could
  enter the population. The population's 84-yard totals are known from their full evaluations.

**3. Pareto selection and rich feedback**
- `pareto`: parents are chosen from the rules that are best on at least one of the 21 yard
  types (tied winners all count), with probability proportional to the number of types they win.
  Off: selection by total.
- `feedback`: the prompt shows a parent's total and its 3 best and 3 worst yard types compared
  with the population's best, its result on the largest yards, and any crash history. Off: only
  the total, as in EoH.
- Operators: refine (improve one rule from its feedback), merge (combine two rules that win
  different yard types), explore (a new idea, using the knowledge text).

## Budget (agreed with Wei)

The same 420,000 yard simulations per run as the baselines (500 evaluations x 840 yards).

| Step | Cost (yard simulations) |
|---|---|
| exact duplicate rejected | 0 |
| crash test | 4 |
| quick test | 84 |
| full evaluation | 840 |
| the seed's full evaluation | 840 (counted) |

The run stops when the next step would exceed the budget. The result is the best fully
evaluated rule, scored once on the test set. LLM calls, run time and repair attempts are
reported separately.

## LLM

Qwen3-14B through Ollama (`qwen3:14b-nothink`), the same model file, 4-bit format, temperature
(1.0) and thinking-off setting as EoH and ReEvo, so only the method differs from EoH.

## Safety

Each evaluation runs in a separate process with a time limit (60 s, as for EoH and ReEvo), and
with the fixed random seed of decision 14.

## Logging

One JSONL line per proposed rule: code, operator, parents, the gate where it stopped, cost,
quick and full scores, per-type totals, repair attempts. The ablation counters (budget per gate,
duplicates blocked, successful repairs, rules screened out) and the convergence plots come from
this log.

## Files

| File | Purpose |
|---|---|
| `src/crp/framework/settings.py` | all switches and numbers (population 10, 84 yards, 2 repairs, ...) |
| `src/crp/framework/knowledge.py` | the CRP knowledge text and the two seed rules |
| `src/crp/framework/scoring.py` | crash test, quick test, full evaluation with timeout, yard counting, per-type totals (reuses `crp.llm.evaluate`) |
| `src/crp/framework/population.py` | population, Pareto selection, duplicate check |
| `src/crp/framework/prompts.py` | prompt texts for the operators, feedback and repair |
| `src/crp/framework/llm.py` | small OpenAI-style client for Ollama, code extraction |
| `src/crp/framework/loop.py` | the main loop |
| `experiments/run_framework.py` | one run: rule log and result row (`method = ours`, same CSV format) |
| `tests/test_framework.py` | fake LLM: budget, gates, Pareto, a short full run |

## Experiments (agreed with Wei)

| Experiment | Alphas | Runs |
|---|---|---|
| full framework, Min-Max seed | 0.5, 0.3, 0.1 | 10 each |
| full framework, lowest-stack seed | 0.5, 0.3, 0.1 | 10 each |
| ablations, one component off at a time | 0.5, 0.1 | 10 each |

Main comparison: against GP-500 (exact Mann-Whitney, Holm correction, A12), and against EoH,
ReEvo and CALM, with the same analysis as `experiments/compare_methods.py`.
