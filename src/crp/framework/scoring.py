"""Scoring rules on the training yards, with a time limit, one yard at a time.

A rule runs in a separate worker process, so an endless loop can be stopped (the worker is then
restarted). Each yard is scored on its own with the shared evaluator (crp.llm.evaluate), which
fixes the random seed per call, so a yard's result never depends on which other yards are scored
with it: the quick-test result of a rule is exactly part of its full evaluation.

Yard types are the 21 Caserta classes, (tiers, stacks).
"""
from __future__ import annotations

import multiprocessing
import traceback
from collections import defaultdict

from crp.instance import Instance, load_dataset
from crp.paths import TRAINING_SET

YardType = tuple[int, int]  # (tiers, stacks)


def yard_type(instance: Instance) -> YardType:
    return instance.max_height - 2, len(instance.stacks)  # max_height is tiers + 2


def short_error(error: BaseException, code: str) -> str:
    """The error and the line of the rule where it happened, for the repair prompt."""
    message = f"{type(error).__name__}: {error}"
    rule_frames = [f for f in traceback.extract_tb(error.__traceback__) if f.filename == "<string>"]
    lines = code.splitlines()
    if rule_frames and 0 < rule_frames[-1].lineno <= len(lines):
        message += f" (line {rule_frames[-1].lineno}: {lines[rule_frames[-1].lineno - 1].strip()})"
    return message  # a SyntaxError's message already names its line


def _worker(connection, alpha: float) -> None:
    from crp.llm.evaluate import compile_rule, total_or_raise

    yards = load_dataset(TRAINING_SET)
    while (task := connection.recv()) is not None:
        code, ids = task
        try:
            rule = compile_rule(code, "priority")
            connection.send(("ok", [total_or_raise(rule, [yards[i]], alpha) for i in ids]))
        except BaseException as error:  # whatever the LLM's code does, including sys.exit
            connection.send(("error", short_error(error, code)))


class Scorer:
    """Scores rule code on chosen training yards; per-yard relocations or an error message."""

    def __init__(self, alpha: float, timeout: float, crash_yards: int = 4, quick_per_type: int = 4):
        self.alpha, self.timeout = alpha, timeout
        self.yards = load_dataset(TRAINING_SET)
        by_type: dict[YardType, list[int]] = defaultdict(list)
        for i, instance in enumerate(self.yards):
            by_type[yard_type(instance)].append(i)
        self.types = sorted(by_type, key=lambda t: (t[0] * t[1], t))  # small yards first
        self.ids_of_type = {t: by_type[t] for t in self.types}
        self.type_of = [yard_type(instance) for instance in self.yards]
        # crash test: the first yard of the two smallest and of the two largest types
        ends = self.types[: crash_yards // 2] + self.types[len(self.types) - crash_yards // 2:]
        self.crash_ids = [self.ids_of_type[t][0] for t in ends]
        self.quick_ids = [i for t in self.types for i in self.ids_of_type[t][:quick_per_type]]
        self._context = multiprocessing.get_context("spawn")
        self._start()

    def _start(self) -> None:
        self._connection, worker_end = self._context.Pipe()
        self._process = self._context.Process(target=_worker, args=(worker_end, self.alpha), daemon=True)
        self._process.start()

    def _restart(self) -> None:
        self._process.kill()
        self._process.join()
        self._start()

    def score(self, code: str, ids: list[int]) -> tuple[dict[int, int] | None, str | None]:
        """({yard id: relocations}, None) or (None, error message)."""
        if not ids:
            return {}, None
        self._connection.send((code, ids))
        if not self._connection.poll(self.timeout):
            self._restart()
            return None, f"TimeoutError: scoring took longer than {self.timeout:.0f} s (an endless or very slow loop?)"
        try:
            status, payload = self._connection.recv()
        except EOFError:  # the worker died, e.g. out of memory
            self._restart()
            return None, "the rule crashed the scoring process"
        return (dict(zip(ids, payload)), None) if status == "ok" else (None, payload)

    def type_totals(self, per_yard: dict[int, int]) -> dict[YardType, int]:
        totals: dict[YardType, int] = defaultdict(int)
        for i, relocations in per_yard.items():
            totals[self.type_of[i]] += relocations
        return dict(totals)

    def close(self) -> None:
        self._connection.send(None)
        self._process.join(timeout=5)
        if self._process.is_alive():
            self._process.kill()
