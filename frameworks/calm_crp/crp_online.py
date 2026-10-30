"""CRP problem file for CALM (copied to CALM's problems/crp_online.py by install_calm_files.py).

CALM reads name, description and unit for its prompts, and calls Environment to score a rule.
Scoring reuses our shared evaluator (crp.llm.evaluate), so a rule gets the same total as
in EoH and ReEvo. CALM wants higher = better, so each yard's score is minus its relocations.
CALM scores each yard as a separate Ray task, so run_async usually gets a single yard.
The alpha comes from the CRP_ALPHA environment variable, read when CALM creates the
Environment in its main process; Ray copies the object, alpha included, to its workers.
"""
import os

from crp.instance import load_dataset
from crp.llm.evaluate import total_or_raise
from crp.llm.prompts import FUNCTION_DESCRIPTION, PROBLEM_DESCRIPTION
from crp.paths import TEST_SET, TRAINING_SET

name = "online container relocation"
description = f"{PROBLEM_DESCRIPTION} {FUNCTION_DESCRIPTION}"
unit = "relocations per yard on average (lower is better)"


class Environment:
    def __init__(self):
        self.alpha = float(os.environ["CRP_ALPHA"])

    def training_dataset(self):
        return load_dataset(TRAINING_SET)

    def testing_dataset(self):
        # only used by CALM's own heuristic.py tool; our scripts score the test set themselves
        return {"caserta_840": {"instances": load_dataset(TEST_SET)}}

    def run_async(self, policy, instances):
        # total_or_raise checks every score (number, finite), so a bad rule raises and
        # CALM counts it as a bug; it scores the rule exactly as for EoH and ReEvo
        return {"performance": [-total_or_raise(policy, [inst], self.alpha) for inst in instances]}
