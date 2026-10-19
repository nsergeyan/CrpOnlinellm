# LLM frameworks

Both frameworks come from the ReEvo repository at a pinned commit, used unchanged.
Only our own files plug them into the CRP.

| Framework | Code | Run with |
|---|---|---|
| ReEvo | ReEvo repo, commit `6dce18257da5e11db2d138e417a2fffc5c72d05f` | `main.py algorithm=reevo` |
| EoH (original, ICML 2024) | `baselines/eoh/` in the same ReEvo commit: the official EoH code (commit `d7c5a69`, May 2024) as used in the ReEvo paper | `main.py algorithm=eoh` |

Both share ReEvo's LLM client (same model, same temperature), our `eval.py` (same scorer)
and the same prompt files, so only the search method differs. The EoH copy changes only
the plumbing (LLM client, evaluation, file paths) and drops one sentence from its m2 prompt
("The function should return N output(s): ..."; the other prompts keep it). The newer
EoH v0.2 (2026 rewrite) was tried first and removed; see git history up to commit 3ae9a2a.

Original EoH behaviour to know: it cuts the LLM's code at the last `return` and appends the
output name, so a rule must end with `return priority` (e.g. `priority = RI` then
`return priority`). A rule written as `return SH` becomes `return priority` and fails with
NameError. This is the paper's code, kept as is; `tests/test_llm_reevo.py` shows it.
`frameworks/setup_reevo.sh` also installs joblib, which this EoH copy needs but ReEvo's
package list leaves out.

## ReEvo

ReEvo is a program that runs from its own folder, not a library, and needs Python >= 3.11.
`frameworks/setup_reevo.sh` clones it at the commit above, creates `frameworks/reevo/.venv`
(Python 3.11), installs ReEvo's packages and our `crp` code into it, and adds our files.
It refuses to continue if ReEvo's own files were edited.

Our files (the only additions to ReEvo's folder):

| In this repo | Copied to `frameworks/reevo/` |
|---|---|
| `frameworks/reevo_crp/crp_online.yaml` + description from `src/crp/llm/prompts.py` | `cfg/problem/crp_online.yaml` |
| `frameworks/reevo_crp/eval.py` | `problems/crp_online/eval.py` |
| generated from `src/crp/llm/prompts.py` | `prompts/crp_online/{func_desc,func_signature,seed_func}.txt` |

After changing any of these, run `bash frameworks/setup_reevo.sh` again to re-copy them.

ReEvo starts `python eval.py` for every rule, using whichever `python` is first on PATH,
so run it with ReEvo's environment first on PATH:

```bash
cd frameworks/reevo
PATH="$PWD/.venv/bin:$PATH" python main.py problem=crp_online problem.problem_size=0.5 ...
```

`tests/test_llm_reevo.py` runs the real ReEvo against a fake LLM server (skipped until the setup has run).
