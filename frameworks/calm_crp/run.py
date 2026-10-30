"""Start CALM on the CRP and log every scored rule (installed as run_crp.py next to CALM's main.py).

CALM has no hook like ReEvo's eval.py for logging each rule, so this launcher swaps CALM's
evaluate_code (scores one rule) for a version that does the same and also appends the rule
to a JSONL log, in evaluation order. It also gives the LLM's code math and np, as our
compile_rule does for EoH and ReEvo. The seed rule is scored by CALM before the search and
is not logged, as in EoH. Once `budget` rules are logged, the launcher stops CALM: the run's
result is the best of the first `budget` logged rules, as for EoH and ReEvo.
CALM's own files are not edited. Run it from CALM's folder:

    python run_crp.py --alpha 0.5 --model /path/to/qwen3-14b-nothink --rule-log rules.jsonl --log-name crp_a0.5_s1
"""
import argparse
import json
import math
import os
from pathlib import Path

import numpy as np


def extract_function_with_math(code):
    """CALM's utils.extract_function_from_string, but the code sees math and np, as in our
    compile_rule (crp.llm.evaluate), so the same rule is valid or invalid in all three methods."""
    namespace = {"math": math, "np": np}
    try:
        exec(code, namespace)
    except BaseException:  # like CALM's bare except
        return None
    functions = [v for v in namespace.values() if callable(v) and hasattr(v, "__code__")]
    return functions[0] if len(functions) == 1 else None


class LoggedEvaluation:
    """Stands in for CALM's evaluate_code: the same scoring, plus one log line per rule."""

    def __init__(self, evaluate_code, rule_log: Path, budget: int):
        self.evaluate_code, self.rule_log, self.budget = evaluate_code, rule_log, budget
        self.logged = 0

    def remote(self, algo, instances):
        import ray
        if self.logged >= self.budget:
            print(f"Budget of {self.budget} scored rules reached, stopping CALM.", flush=True)
            os._exit(0)  # CALM's main loop catches every exception, so only a hard exit stops it
        # one rule at a time; its yards are still scored in parallel by the Ray workers
        result = ray.get(self.evaluate_code.remote(algo, instances))
        total, error = None, None
        if isinstance(result, str):  # CALM's evaluate_code returns 'code_bug' when the rule crashed
            error = result
        elif "random" in algo.code:  # CALM rejects these after scoring (calm_trainer.reward_func)
            error = "uses random: rejected by CALM"
        else:
            total = -round(sum(result["performance"]))  # performance is minus the relocations per yard
        with self.rule_log.open("a") as f:
            f.write(json.dumps({"total": total, "error": error, "code": algo.code}) + "\n")
        self.logged += 1
        return ray.put(result)  # calm_trainer calls ray.get on whatever this returns


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--alpha", type=float, required=True)
    parser.add_argument("--model", required=True, help="model folder, or online/<name> for an OpenAI-style server")
    parser.add_argument("--rule-log", type=Path, required=True, help="JSONL file, one line per scored rule")
    parser.add_argument("--log-name", required=True, help="CALM's output folder: calm_saved/crp_online/<log-name>")
    parser.add_argument("--budget", type=int, default=500)
    parser.add_argument("--base-url", default="", help="only for online/<name>")
    parser.add_argument("--api-key", default="local", help="only for online/<name>")
    args = parser.parse_args()
    os.environ["CRP_ALPHA"] = str(args.alpha)  # read by problems/crp_online.py
    args.rule_log.unlink(missing_ok=True)  # a crashed earlier attempt must not mix in

    # Import order matters: CALM's main.py picks the GPU when imported, before anything starts
    # CUDA; unsloth must come before trl, because importing it patches TRL's GRPO trainer.
    import main as calm_main
    if not args.model.startswith("online"):
        import unsloth  # noqa: F401
    import calm_trainer
    from args import Args

    calm_trainer.evaluate_code = LoggedEvaluation(calm_trainer.evaluate_code, args.rule_log, args.budget)
    calm_trainer.extract_function_from_string = extract_function_with_math
    calm_args = Args.from_yaml("configs/crp_online/crp_online.yaml")
    calm_args.model_name, calm_args.log_name = args.model, args.log_name
    calm_args.base_url, calm_args.api_key = args.base_url, args.api_key
    calm_main.run(calm_args)


if __name__ == "__main__":
    main()
