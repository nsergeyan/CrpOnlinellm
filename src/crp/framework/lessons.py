"""Lessons learned during a run (README decision 57).

Every `lessons_every` batches the LLM writes short lessons from the rules so far (at most
`max_lessons`). Each prompt shows each lesson with probability 0.5, so the rules written with and
without a lesson can be compared: a rule wins if its 840-yard total is lower than its parent's
(the better parent for a merge); a rule that stops at a gate does not win, and explore rules,
which have no parent, are not counted. At each check a lesson is deleted when rules clearly win
less often with it, rewritten when it was shown often and rules did no better with it, and kept
otherwise; the LLM then fills the free places.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from statistics import NormalDist

LESSON_LINE = re.compile(r"^[\s*\-\d.)]*Lesson[^:\n]*:\**\s*(.+)$", re.MULTILINE | re.IGNORECASE)


@dataclass
class Lesson:
    id: int
    text: str
    batch: int              # the batch after which it was written
    shown: int = 0          # counted rules whose prompt showed it
    shown_wins: int = 0
    hidden: int = 0         # counted rules whose prompt left it out
    hidden_wins: int = 0

    def p_worse(self) -> float:
        """One-sided p-value that rules win less often when it is shown (two-proportion z-test)."""
        if not self.shown or not self.hidden:
            return 1.0
        rate = (self.shown_wins + self.hidden_wins) / (self.shown + self.hidden)
        spread = (rate * (1 - rate) * (1 / self.shown + 1 / self.hidden)) ** 0.5
        if spread == 0:  # no wins at all, or only wins
            return 1.0
        return NormalDist().cdf((self.shown_wins / self.shown - self.hidden_wins / self.hidden) / spread)


def decide(lesson: Lesson, delete_after: int, judge_after: int) -> str:
    """'delete', 'rewrite' or 'keep'."""
    if lesson.shown >= delete_after and lesson.p_worse() < 0.05:
        return "delete"
    if lesson.shown >= judge_after and lesson.hidden and \
            lesson.shown_wins / lesson.shown <= lesson.hidden_wins / lesson.hidden:
        return "rewrite"
    return "keep"


class Notebook:
    def __init__(self, run_seed: int):
        self.rng = random.Random(f"lessons {run_seed}")  # its own coin: the operator and parent draws stay the same
        self.lessons: list[Lesson] = []
        self.deleted: list[Lesson] = []    # harmful lessons, shown to the LLM so it does not write them again
        self.examples: list[dict] = []     # every counted rule, oldest first, for the update prompt
        self.written: set[str] = set()     # every lesson text so far, so none comes back unchanged
        self.checks = 0

    def flip(self) -> dict[str, list[int]]:
        """Which lessons one prompt shows: each with probability 0.5."""
        shown = [lesson.id for lesson in self.lessons if self.rng.random() < 0.5]
        return {"shown": shown, "hidden": [lesson.id for lesson in self.lessons if lesson.id not in shown]}

    def texts(self, ids: list[int]) -> list[str]:
        return [lesson.text for lesson in self.lessons if lesson.id in ids]

    def record(self, lessons: dict[str, list[int]], won: bool, example: dict) -> None:
        for lesson in self.lessons:
            if lesson.id in lessons["shown"]:
                lesson.shown, lesson.shown_wins = lesson.shown + 1, lesson.shown_wins + won
            elif lesson.id in lessons["hidden"]:
                lesson.hidden, lesson.hidden_wins = lesson.hidden + 1, lesson.hidden_wins + won
        self.examples.append(example)

    def recent(self, won: bool, n: int = 3) -> list[dict]:
        """The n latest rules that beat their parent, or that did not but were scored."""
        return [e for e in self.examples if e["won"] == won and e["status"] in ("evaluated", "screened_out")][-n:]

    def check(self, delete_after: int, judge_after: int) -> list[tuple[Lesson, str]]:
        self.checks += 1
        decisions = [(lesson, decide(lesson, delete_after, judge_after)) for lesson in self.lessons]
        self.lessons = [lesson for lesson, decision in decisions if decision == "keep"]
        self.deleted += [lesson for lesson, decision in decisions if decision == "delete"]
        return decisions

    def add(self, answer: str, room: int, batch: int) -> list[Lesson]:
        """The new lessons in the LLM's answer, at most `room`; repeats of earlier lessons are skipped."""
        new = []
        for text in LESSON_LINE.findall(answer):
            text = text.strip().strip("*").strip()[:300]
            if text and text.lower() not in self.written and len(new) < room:
                self.written.add(text.lower())
                new.append(Lesson(len(self.written), text, batch))
        self.lessons += new
        return new
