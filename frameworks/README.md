# LLM frameworks

Both frameworks are used unchanged, at pinned commits. Only our own files plug them into the CRP.

| Framework | Commit | How it gets here |
|---|---|---|
| EoH v0.2 | `472545785c936dcfc863d2bc0d6109cf23c7ce62` | `pip install -e ".[llm]"` (pinned in `pyproject.toml`) |
| ReEvo | `6dce18257da5e11db2d138e417a2fffc5c72d05f` | `bash scripts/setup_reevo.sh` (clones into `frameworks/reevo/`, not in git) |

## ReEvo

ReEvo is a program that runs from its own folder, not a library, and needs Python >= 3.11.
`scripts/setup_reevo.sh` clones it at the commit above, creates `frameworks/reevo/.venv`
(Python 3.11), installs ReEvo's packages and our `crp` code into it, and adds our files.
It refuses to continue if ReEvo's own files were edited.

Our files (the only additions to ReEvo's folder):

| In this repo | Copied to `frameworks/reevo/` |
|---|---|
| `frameworks/reevo_crp/crp_online.yaml` + description from `src/crp/llm/prompts.py` | `cfg/problem/crp_online.yaml` |
| `frameworks/reevo_crp/eval.py` | `problems/crp_online/eval.py` |
| generated from `src/crp/llm/prompts.py` | `prompts/crp_online/{func_desc,func_signature,seed_func}.txt` |

After changing any of these, run `bash scripts/setup_reevo.sh` again to re-copy them.

ReEvo starts `python eval.py` for every rule, using whichever `python` is first on PATH,
so run it with ReEvo's environment first on PATH:

```bash
cd frameworks/reevo
PATH="$PWD/.venv/bin:$PATH" python main.py problem=crp_online problem.problem_size=0.5 ...
```

`tests/test_llm_reevo.py` runs the real ReEvo against a fake LLM server (skipped until the setup has run).
