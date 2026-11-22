"""Prompt texts: the system prompt, the three operators, the repair request and the feedback.

The problem and input descriptions are the ones EoH, ReEvo and CALM got (crp.llm.prompts); the
knowledge text is added only with the `knowledge` switch.
"""
from __future__ import annotations

import difflib

from crp.framework.knowledge import KNOWLEDGE_TEXTS
from crp.framework.lessons import Lesson
from crp.framework.population import Archive, Rule
from crp.framework.scoring import YardType
from crp.llm.prompts import FUNCTION_DESCRIPTION, PROBLEM_DESCRIPTION

ANSWER_FORMAT = (
    "The function only gets the six inputs of one candidate stack; it cannot see the yard's size, "
    "the other stacks or anything else. "
    "Answer with one line that starts with 'Idea:' and describes the rule's idea in one sentence, "
    "then the complete function in one ```python code block. The function must be named priority, "
    "take exactly the six inputs SH, EMP, AVG, CUR, RI, DIFF, and return a finite number; math and "
    "np (numpy) are available. Keep it deterministic and fast."
)
LESSON_FORMAT = (
    "A rule only gets the six inputs of one candidate stack; it cannot see the yard's size, the other "
    "stacks or anything else. This time, do not write a function: answer only with the lessons, one "
    "per line, each line starting with 'Lesson:' and holding one sentence."
)


def system_prompt(knowledge: bool, text: str = "full", answer: str = ANSWER_FORMAT) -> str:
    parts = ["You design priority functions for a container relocation heuristic.",
             PROBLEM_DESCRIPTION, FUNCTION_DESCRIPTION]
    if knowledge:
        parts.append(KNOWLEDGE_TEXTS[text])
    return "\n\n".join(parts + [answer])


def type_name(t: YardType) -> str:
    return f"{t[1]} stacks x {t[0]} tiers"


def feedback(rule: Rule, archive: Archive, rich: bool) -> str:
    """How a rule performs: only its total, or (rich) also where it is strong or weak."""
    lines = [f"Total relocations on the 840 training yards: {rule.total:,} (lower is better; "
             f"best rule so far: {archive.best().total:,})."]
    if not rich:
        return lines[0]
    best = archive.type_best()
    gap = {t: (rule.type_totals[t] - best[t]) / best[t] for t in archive.types}
    ranked = sorted(archive.types, key=lambda t: (gap[t], t))
    describe = lambda t: (f"{type_name(t)} ({'the best of all rules' if gap[t] == 0 else f'{gap[t]:+.1%} vs the best rule there'})")
    lines.append("Strongest yard types: " + "; ".join(describe(t) for t in ranked[:3]) + ".")
    lines.append("Weakest yard types: " + "; ".join(describe(t) for t in reversed(ranked[-3:])) + ".")
    largest = archive.types[-2:]
    share = sum(rule.type_totals[t] for t in largest) / rule.total
    lines.append(f"The two largest yard types ({', '.join(type_name(t) for t in largest)}) cause {share:.0%} of "
                 f"its relocations; there it is " + " and ".join(f"{gap[t]:+.1%}" for t in largest) +
                 " vs the best rule.")
    if rule.repaired:
        lines.append("This rule needed a repair after a crash.")
    return "\n".join(lines)


def show(rule: Rule, archive: Archive, rich: bool) -> str:
    return f"Idea: {rule.idea}\n```python\n{rule.code.strip()}\n```\n{feedback(rule, archive, rich)}"


def refine(rule: Rule, archive: Archive, rich: bool) -> str:
    return (f"Here is a rule and how it performs:\n\n{show(rule, archive, rich)}\n\n"
            "Improve this rule: change or add one idea that targets its weak points, and keep what "
            "makes it strong.")


def merge(a: Rule, b: Rule, archive: Archive, rich: bool) -> str:
    return (f"Here are two rules that are strong in different ways.\n\nRule A:\n{show(a, archive, rich)}\n\n"
            f"Rule B:\n{show(b, archive, rich)}\n\nWrite one new rule that combines the strengths of both.")


def explore(archive: Archive) -> str:
    ideas = "\n".join(f"- {r.idea} (total {r.total:,})" for r in archive.population())
    return (f"The best rules so far follow these ideas:\n{ideas}\n\nWrite a rule based on a clearly "
            "different idea that could beat them.")


def repair(code: str, error: str) -> str:
    return (f"This rule crashed during scoring:\n```python\n{code.strip()}\n```\nError: {error}\n\n"
            "Fix the error and keep the idea of the rule.")


def with_lessons(prompt: str, lessons: list[str]) -> str:
    if not lessons:
        return prompt
    return prompt + "\n\nLessons learned so far in this run:\n" + "\n".join(f"- {text}" for text in lessons)


def counts(lesson: Lesson) -> str:
    return (f"with it {lesson.shown_wins} of {lesson.shown} rules beat their parent, "
            f"without it {lesson.hidden_wins} of {lesson.hidden}")


def example(rule: dict) -> str:
    if rule["total"] is None:
        result = "Stopped at the quick test: worse than the 10 best rules on 84 yards."
    else:
        result = (f"Total relocations on the 840 training yards: {rule['total']:,}; "
                  f"its parent: {rule['parent_total']:,}.")
    changes = "\n".join(list(difflib.unified_diff(rule["parent_code"].strip().splitlines(),
                                                  rule["code"].strip().splitlines(), lineterm="", n=1))[2:])
    return (f"Parent's idea: {rule['parent_idea']}\nIdea: {rule['idea']}\n"
            f"Changes to the parent's code (+ added, - removed):\n```diff\n{changes}\n```\n{result}")


def update_lessons(kept: list[Lesson], rewrite: list[Lesson], deleted: list[Lesson],
                   winners: list[dict], losers: list[dict], room: int) -> str:
    listed = lambda lessons: "\n".join(f"- {lesson.text} ({counts(lesson)})" for lesson in lessons) or "- none"
    parts = ["Lessons are added at random to the prompts that ask for new rules. A rule wins if it has "
             "fewer relocations than the rule it was made from (its parent).",
             f"Current lessons:\n{listed(kept)}"]
    if rewrite:
        parts.append(f"Removed now, because rules did no better with them:\n{listed(rewrite)}")
    if deleted:
        parts.append("Removed earlier, because rules did clearly worse with them; do not write them "
                     f"again:\n{listed(deleted)}")
    parts.append("Recent rules that beat their parent:\n\n" + ("\n\n".join(map(example, winners)) or "none yet"))
    parts.append("Recent rules that did not:\n\n" + ("\n\n".join(map(example, losers)) or "none yet"))
    parts.append(f"Write {room} new {'lesson' if room == 1 else 'lessons'} that would help to write rules "
                 "that beat their parent. Base them on the changes above that won or lost, and do not "
                 "repeat a current or removed lesson. Each lesson is one sentence that names the inputs "
                 "it is about (SH, EMP, AVG, CUR, RI, DIFF), the situation it applies to (for example "
                 "safe stacks, unsafe stacks, empty stacks or ties) and what to change in the score, in "
                 "which direction.")
    return "\n\n".join(parts)
