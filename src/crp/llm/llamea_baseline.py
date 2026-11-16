"""LLaMEA (van Stein & Bäck, 2025) as a baseline: its settings, prompt texts and evaluation function.

LLaMEA's own code is untouched (pip package, version pinned in frameworks/setup_llamea.sh). It gets
the same problem text, start rule (as its example program), LLM and temperature as EoH and ReEvo.
Settings: the package's defaults, 5 parents and 5 offspring with elitism and the one "refine"
mutation prompt, no hyper-parameter optimisation (agreed with Wei, README decision 53).

Only importable in LLaMEA's environment (frameworks/llamea/.venv), so nothing else imports it.
"""
from __future__ import annotations

import math
import os
import signal
from pathlib import Path

import openai
from llamea import LLaMEA, OpenAI_LLM, Solution

from crp.instance import Instance, load_dataset
from crp.llm.evaluate import compile_rule, total_or_raise
from crp.llm.prompts import FUNCTION_DESCRIPTION, PROBLEM_DESCRIPTION, TEMPLATE_PROGRAM
from crp.paths import TRAINING_SET

N_PARENTS, N_OFFSPRING = 5, 5
TEMPERATURE = 1.0  # as EoH and ReEvo
TIME_LIMIT = 60    # seconds for one rule on the training set, as ReEvo's timeout for EoH and ReEvo

# The last sentence is LLaMEA's own closing sentence, with "heuristic algorithm" replaced.
TASK_PROMPT = f"""
{PROBLEM_DESCRIPTION}
Your task is to write a priority function in Python code, named `priority`. {FUNCTION_DESCRIPTION}

Give an excellent and novel priority function to solve this task.
"""
EXAMPLE_PROMPT = f"""
An example of such code (the lowest stack receives the container), is as follows:
```python
{TEMPLATE_PROGRAM}```
"""


class LocalLLM(OpenAI_LLM):
    """LLaMEA's OpenAI client, sent to our own server (as LLaMEA's DeepSeek_LLM does for its server)."""

    def __init__(self, model: str, base_url: str) -> None:
        super().__init__("local", model=model, temperature=TEMPERATURE)
        self.base_url = base_url
        self._client_kwargs["base_url"] = base_url
        self.client = openai.OpenAI(**self._client_kwargs)


class TooSlow(BaseException):
    """Not an Exception, so a rule's own `except Exception` cannot swallow the time limit."""


def _stop(signum, frame):
    raise TooSlow


_training: list[Instance] = []  # each of LLaMEA's worker processes loads its own copy once


class Evaluator:
    """What LLaMEA calls for every rule: the total relocations on the training set, and one
    sentence of feedback for the next prompt. A rule that fails or is too slow gets the worst
    fitness; LLaMEA puts the error message into the next prompt itself.

    The time limit is kept here, by an alarm signal: LLaMEA's own eval_timeout would stop the
    whole run, not the rule.
    """

    def __init__(self, alpha: float, time_limit: int = TIME_LIMIT) -> None:
        self.alpha, self.time_limit = alpha, time_limit

    def __call__(self, solution: Solution, logger=None) -> Solution:
        global _training
        if not _training:
            _training = load_dataset(TRAINING_SET)
        signal.signal(signal.SIGALRM, _stop)
        signal.alarm(self.time_limit)
        try:
            total = total_or_raise(compile_rule(solution.code, "priority"), _training, self.alpha)
            solution.set_scores(total, f"The priority function needed {total} relocations in total on the "
                                       f"training yards (lower is better).")
        except TooSlow:
            solution.set_scores(math.inf, "The priority function failed.",
                                TimeoutError(f"no result after {self.time_limit} seconds"))
        except Exception as e:  # anything the LLM's code raises, plus RuleFailed from the guard
            solution.set_scores(math.inf, "The priority function failed.", e)
        finally:
            signal.alarm(0)
        return solution


def run_llamea(alpha: float, budget: int, model: str, base_url: str, work_dir: Path,
               time_limit: int = TIME_LIMIT) -> list[Solution]:
    """One LLaMEA run; returns every solution in the order LLaMEA got it (one LLM answer each).

    LLaMEA's budget counts every LLM answer, also one without code, which is never scored. As for
    EoH and ReEvo it therefore gets 10% more than the `budget` scored rules we count.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(work_dir)  # LLaMEA writes its own log folder (prompts, answers) into the current folder
    optimizer = LLaMEA(Evaluator(alpha, time_limit), LocalLLM(model, base_url), n_parents=N_PARENTS, n_offspring=N_OFFSPRING,
                       elitism=True, task_prompt=TASK_PROMPT, example_prompt=EXAMPLE_PROMPT,
                       budget=budget + budget // 10, minimization=True, experiment_name="crp_online")
    optimizer.run()
    return optimizer.run_history
