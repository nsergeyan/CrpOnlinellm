"""All switches and numbers of one framework run.

Every component can be switched off for the ablations (docs/framework_design.md):
- component 1, CRP knowledge: `knowledge` (text in the prompts) and `seed_rule` (minmax or lowest)
- component 2, screening and repair: `crash_check` (with repair), `dedup`, `quick_test`
- component 3: `pareto` (parent selection) and `feedback` (where a rule is strong or weak)
"""
from __future__ import annotations

from dataclasses import dataclass, fields

SWITCHES = ("knowledge", "crash_check", "dedup", "quick_test", "pareto", "feedback")


@dataclass(frozen=True)
class Settings:
    alpha: float
    run_seed: int = 1              # run number; also seeds the framework's own random choices
    seed_rule: str = "minmax"      # "minmax" or "lowest" (the start rule of EoH, ReEvo and CALM)
    knowledge: bool = True
    crash_check: bool = True
    dedup: bool = True
    quick_test: bool = True
    pareto: bool = True
    feedback: bool = True
    budget: int = 420_000          # yard simulations: 500 full evaluations x 840 yards, as GP-500 and EoH
    population_size: int = 10      # the best rules by total: feedback reference and quick-test bar
    crash_yards: int = 4           # two of the smallest yard types, two of the largest
    quick_per_type: int = 4        # 4 x 21 yard types = 84 yards
    max_repairs: int = 2           # repair attempts per crashed rule
    timeout: float = 60.0          # seconds per scoring call, as EoH and ReEvo
    temperature: float = 1.0       # as EoH and ReEvo
    operator_weights: tuple[float, float, float] = (0.6, 0.3, 0.1)  # refine, merge, explore (pilot: explore never improved)
    max_free_in_a_row: int = 100   # stop if this many proposals in a row cost nothing (only repeats)

    def label(self) -> str:
        """Method name in the results: 'ours', plus what differs from the full framework."""
        parts = ["ours"]
        if self.seed_rule != "minmax":
            parts.append(self.seed_rule)
        parts += [f"no_{name}" for name in SWITCHES if not getattr(self, name)]
        return "-".join(parts)

    def as_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self)}
