"""The CRP as an EoH problem: EoH proposes rules, our evaluator scores them.

EoH sends this object to a fresh process for every evaluation, so it must live in the
installed package (a class from a script could not be found there). Needs the llm extra.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from eoh import BaseProblem

from crp.instance import load_dataset
from crp.llm.evaluate import compile_rule, evaluate_rule
from crp.llm.prompts import FUNCTION_DESCRIPTION, PROBLEM_DESCRIPTION, TEMPLATE_PROGRAM
from crp.paths import TRAINING_SET


class CRPProblem(BaseProblem):
    task_description = PROBLEM_DESCRIPTION + " " + FUNCTION_DESCRIPTION
    template_program = TEMPLATE_PROGRAM

    def __init__(self, alpha: float, hidden: str = "max", timeout: int = 60,
                 directory: str | Path = TRAINING_SET) -> None:
        super().__init__(timeout=timeout)
        self.alpha = alpha
        self.hidden = hidden
        self.instances = load_dataset(directory)  # loaded once, travels with the object

    def evaluate_program(self, program_str: str, callable_func) -> Optional[float]:
        # callable_func (EoH's own compile) is ignored: we compile with compile_rule,
        # exactly as ReEvo's path does, so both frameworks score code the same way
        try:
            func = compile_rule(program_str, "priority")
        except Exception:
            return None
        return evaluate_rule(func, self.instances, self.alpha, self.hidden)


