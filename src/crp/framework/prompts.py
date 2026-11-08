"""Prompt texts: the system prompt, the three operators, the repair request and the feedback.

The problem and input descriptions are the ones EoH, ReEvo and CALM got (crp.llm.prompts); the
knowledge text is added only with the `knowledge` switch.
"""
from __future__ import annotations

from crp.framework.knowledge import KNOWLEDGE
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


def system_prompt(knowledge: bool) -> str:
    parts = ["You design priority functions for a container relocation heuristic.",
             PROBLEM_DESCRIPTION, FUNCTION_DESCRIPTION]
    if knowledge:
        parts.append(KNOWLEDGE)
    return "\n\n".join(parts + [ANSWER_FORMAT])


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
