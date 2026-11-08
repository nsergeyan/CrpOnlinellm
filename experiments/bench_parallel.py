"""How much faster the LLM answers when several requests are sent at once (batching in Ollama).

Sends the same prompt (the framework's refine prompt for the Min-Max seed) with 1, 2, 4 and 8
requests at a time to one Ollama server started with OLLAMA_NUM_PARALLEL=8, and prints the
answers per minute and how many answers contain a priority function. Used to decide whether the
framework should write several rules at once (README, design notes).

    python experiments/bench_parallel.py --base-url http://127.0.0.1:11434/v1
"""
import argparse
import time
from concurrent.futures import ThreadPoolExecutor

from crp.framework import prompts
from crp.framework.knowledge import SEEDS
from crp.framework.llm import LLM, read_rule
from crp.framework.population import Archive, Rule
from crp.framework.scoring import Scorer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://localhost:11434/v1")
    parser.add_argument("--model", default="qwen3:14b-nothink")
    parser.add_argument("--requests", type=int, default=24, help="answers per level")
    parser.add_argument("--levels", type=int, nargs="+", default=[1, 2, 4, 8], help="requests at a time")
    args = parser.parse_args()

    scorer = Scorer(alpha=0.5, timeout=60)
    idea, code = SEEDS["minmax"]
    per_yard, _ = scorer.score(code, list(range(len(scorer.yards))))
    seed = Rule(0, code, idea, per_yard, scorer.type_totals(per_yard))
    archive = Archive(10, scorer.types)
    archive.add(seed)
    scorer.close()
    system, prompt = prompts.system_prompt(knowledge=True), prompts.refine(seed, archive, rich=True)

    llm = LLM(args.model, args.base_url, temperature=1.0)
    llm.ask(system, prompt)  # loads the model; not timed
    for workers in args.levels:
        start = time.perf_counter()
        with ThreadPoolExecutor(workers) as pool:
            answers = list(pool.map(lambda _: llm.ask(system, prompt), range(args.requests)))
        seconds = time.perf_counter() - start
        valid = sum(read_rule(answer)[0] is not None for answer in answers)
        print(f"{workers} at a time: {args.requests} answers in {seconds:.0f} s, "
              f"{60 * args.requests / seconds:.1f} per minute, {valid} with a rule", flush=True)


if __name__ == "__main__":
    main()
