"""How much faster the LLM answers when several requests are sent at once (batching in Ollama),
and whether the rules it writes are as good.

Sends the same prompt (the framework's refine prompt for the Min-Max seed) with 1, 2, 4 and 8
requests at a time to one Ollama server started with OLLAMA_NUM_PARALLEL=8. For each level it
prints the answers per minute and scores every answer on the 84 quick-test yards; each level is
compared with "1 at a time" by an exact two-sided Mann-Whitney test and A12 (a rule that crashes
or has no code counts as worst). Used to decide whether the framework should write several rules
at once (README, design notes).

    python experiments/bench_parallel.py --base-url http://127.0.0.1:11434/v1
"""
import argparse
import math
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

from compare_methods import a12, mann_whitney_p
from crp.framework import prompts
from crp.framework.knowledge import SEEDS
from crp.framework.llm import LLM, read_rule
from crp.framework.population import Archive, Rule
from crp.framework.scoring import Scorer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://localhost:11434/v1")
    parser.add_argument("--model", default="qwen3:14b-nothink")
    parser.add_argument("--requests", type=int, default=48, help="answers per level")
    parser.add_argument("--levels", type=int, nargs="+", default=[1, 2, 4, 8], help="requests at a time")
    args = parser.parse_args()

    scorer = Scorer(alpha=0.5, timeout=60)
    idea, code = SEEDS["minmax"]
    per_yard, _ = scorer.score(code, list(range(len(scorer.yards))))
    seed = Rule(0, code, idea, per_yard, scorer.type_totals(per_yard))
    archive = Archive(10, scorer.types)
    archive.add(seed)
    system, prompt = prompts.system_prompt(knowledge=True), prompts.refine(seed, archive, rich=True)
    print(f"seed on the 84 quick-test yards: {seed.subtotal(scorer.quick_ids)}", flush=True)

    llm = LLM(args.model, args.base_url, temperature=1.0)
    llm.ask(system, prompt)  # loads the model; not timed
    scores: dict[int, list[float]] = {}
    for workers in args.levels:
        start = time.perf_counter()
        with ThreadPoolExecutor(workers) as pool:
            answers = list(pool.map(lambda _: llm.ask(system, prompt), range(args.requests)))
        seconds = time.perf_counter() - start
        scores[workers] = []
        for answer in answers:
            rule_code = read_rule(answer)[0]
            results, error = scorer.score(rule_code, scorer.quick_ids) if rule_code else (None, "no code")
            scores[workers].append(math.inf if error else sum(results.values()))
        valid = [s for s in scores[workers] if s != math.inf]
        line = (f"{workers} at a time: {args.requests} answers in {seconds:.0f} s, "
                f"{60 * args.requests / seconds:.1f} per minute, {len(valid)} valid rules, "
                f"84-yard total median {statistics.median(scores[workers]):.0f}, best {min(scores[workers]):.0f}")
        if workers != args.levels[0]:
            base = scores[args.levels[0]]
            line += (f"; vs {args.levels[0]} at a time: p = {mann_whitney_p(scores[workers], base):.3f}, "
                     f"A12 = {a12(scores[workers], base):.2f}")
        print(line, flush=True)
    scorer.close()


if __name__ == "__main__":
    main()
