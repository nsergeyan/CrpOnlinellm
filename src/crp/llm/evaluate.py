"""Shared evaluator for LLM-written priority functions (used by both EoH and ReEvo via eval.py).

The LLM sends Python text. compile_rule turns it into a function, a guard checks every
score it returns, and evaluate_rule runs it with the same scheme and yards as GP.
Any bad answer (exception, non-number, NaN, inf) fails the whole rule: the result is None.

Timeouts are not handled here: an endless loop never returns, so the caller must kill it
(ReEvo's main.py runs eval.py with a timeout, for both EoH and ReEvo).

Command line (ReEvo protocol: the last printed line is the total, or a FAILED line):
    python -m crp.llm.evaluate --code gpt.py --func priority_v2 --alpha 0.5 --set training
"""
from __future__ import annotations

import argparse
import math
import numbers
from pathlib import Path
from typing import Callable, Optional

from crp.instance import Instance, load_dataset
from crp.paths import TEST_SET, TRAINING_SET
from crp.schemes import FastPriority, solve_unrestricted_fast
from crp.yard import Yard


class RuleFailed(Exception):
    """The LLM's rule did something we cannot score."""


def compile_rule(code: str, name: str) -> Callable[..., object]:
    """Run the code text in a fresh namespace and return the function called `name`."""
    namespace: dict[str, object] = {"math": math}
    try:
        import numpy  # comes with the llm extra; the core project does not need it
        namespace["np"] = numpy
    except ImportError:
        pass
    exec(code, namespace)
    func = namespace.get(name)
    if not callable(func):
        raise RuleFailed(f"no function named {name!r} in the code")
    return func


def guarded(func: Callable[..., object]) -> FastPriority:
    """Wrap func so every score is checked before the scheme compares it."""
    def checked(sh: float, emp: float, avg: float, cur: float, ri: float, diff: float) -> float:
        score = func(sh, emp, avg, cur, ri, diff)
        # bool counts as a number in Python, but True/False is not a score
        if isinstance(score, bool) or not isinstance(score, numbers.Real):
            raise RuleFailed(f"score is not a number: {score!r}")
        score = float(score)
        if not math.isfinite(score):  # NaN would silently lose every comparison
            raise RuleFailed(f"score is not finite: {score}")
        return score
    return checked


def total_or_raise(func: Callable[..., object], instances: list[Instance], alpha: float,
                   hidden: str = "max") -> int:
    """Total relocations over all instances; raises if the rule misbehaves."""
    f = guarded(func)
    return sum(solve_unrestricted_fast(Yard(inst, alpha, hidden), f) for inst in instances)


def evaluate_rule(func: Callable[..., object], instances: list[Instance], alpha: float,
                  hidden: str = "max") -> Optional[int]:
    """Total relocations (lower is better), or None if the rule failed."""
    try:
        return total_or_raise(func, instances, alpha, hidden)
    except Exception:  # anything the LLM's code raises, plus RuleFailed from the guard
        return None


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--code", type=Path, required=True, help="Python file with the rule")
    parser.add_argument("--func", default="priority", help="function name inside the file")
    parser.add_argument("--alpha", type=float, required=True)
    parser.add_argument("--hidden", choices=["max", "ignore"], default="max")
    parser.add_argument("--set", choices=["training", "test"], default="training")
    args = parser.parse_args(argv)

    instances = load_dataset(TRAINING_SET if args.set == "training" else TEST_SET)
    try:
        func = compile_rule(args.code.read_text(), args.func)
        total = total_or_raise(func, instances, args.alpha, args.hidden)
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        return
    print(total)


if __name__ == "__main__":
    main()
