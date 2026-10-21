"""ReEvo runs this once per rule: python -u eval.py <alpha> <root_dir> train|val

ReEvo has just written the LLM's code to gpt.py next to this file. We score it with our
shared evaluator (crp.llm.evaluate), the same one EoH uses. ReEvo reads the LAST printed
line: the total relocations on the training set, or a FAILED line (= invalid rule).
When experiments/run_llm.py sets CRP_RULE_LOG, every scored rule is also appended there,
in evaluation order, for both methods.
"""
import os
import sys
from pathlib import Path

from crp.llm.evaluate import main

if __name__ == "__main__":
    alpha, mood = sys.argv[1], sys.argv[3]
    if mood == "train":
        log = ["--log", os.environ["CRP_RULE_LOG"]] if os.environ.get("CRP_RULE_LOG") else []
        main(["--code", str(Path(__file__).with_name("gpt.py")), "--func", "priority_v2",
              "--alpha", alpha, "--set", "training", *log])
    else:
        # ReEvo's main.py ends with a 'val' run (alpha -1); the test set is scored once by our own scripts
        print("val skipped: the test set is scored by our own scripts")
