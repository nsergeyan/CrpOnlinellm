"""Try EoH on the online CRP with a local Ollama model (testing only, not for thesis results).

EoH's own client only speaks HTTPS; Ollama on this Mac is plain HTTP. So this script swaps
only the part of EoH that SENDS the prompt (same message: model + prompt, same retries).
EoH's prompts, parent choice and selection are untouched.

Examples (Ollama must be running, see `ollama list`):
    python experiments/try_eoh_ollama.py --alpha 0.5 --budget 20
    python experiments/try_eoh_ollama.py --alpha 0.5 --budget 20 --think   # slow: ~2.5 min per reply
"""
import argparse
import http.client
import json
import logging
import time
from datetime import datetime

from eoh import EoH, LLMConfig
from eoh.llm.api_general import InterfaceAPI

from crp.instance import load_dataset
from crp.llm.eoh_problem import CRPProblem
from crp.llm.evaluate import compile_rule, evaluate_rule
from crp.paper import GP_MEDIANS, PU_TOTALS
from crp.paths import ROOT, TEST_SET

OLLAMA_HOST, OLLAMA_PORT = "localhost", 11434
THINK = False  # set from --think in main()
logger = logging.getLogger("eoh")


def ollama_get_response(self, prompt_content: str, max_retries: int = 5) -> str | None:
    """EoH's InterfaceAPI.get_response, but over HTTP to Ollama's OpenAI-style endpoint."""
    message = {"model": self.model_LLM, "messages": [{"role": "user", "content": prompt_content}]}
    if not THINK:
        message["reasoning_effort"] = "none"  # qwen3 would otherwise think ~6,000 tokens first
    for attempt in range(max_retries):
        conn = None
        try:
            conn = http.client.HTTPConnection(OLLAMA_HOST, OLLAMA_PORT, timeout=self.timeout)
            conn.request("POST", "/v1/chat/completions", json.dumps(message),
                         {"Content-Type": "application/json"})
            parsed = json.loads(conn.getresponse().read())
            choices = parsed.get("choices")
            if not choices:
                raise ValueError(f"Ollama returned no choices: {parsed}")
            return choices[0]["message"]["content"]
        except Exception as e:
            logger.debug("Ollama error (attempt %d/%d): %s", attempt + 1, max_retries, e)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        finally:
            if conn is not None:
                conn.close()
    logger.warning("Ollama call failed after %d attempts.", max_retries)
    return None


def main() -> None:
    global THINK
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--alpha", type=float, choices=[0.5, 0.3, 0.1], required=True)
    parser.add_argument("--budget", type=int, default=20, help="samples after the first population")
    parser.add_argument("--pop-size", type=int, default=4, help="EoH first asks for 2 x this many rules")
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--think", action="store_true", help="let the model think first (slow)")
    args = parser.parse_args()
    THINK = args.think

    InterfaceAPI.get_response = ollama_get_response  # only the phone line changes
    out = ROOT / "runs" / f"eoh_try_{datetime.now():%Y%m%d-%H%M%S}"
    llm = LLMConfig(api_endpoint=f"{OLLAMA_HOST}:{OLLAMA_PORT}", api_key="ollama",
                    model=args.model, timeout=600)
    EoH(llm=llm, problem=CRPProblem(alpha=args.alpha), pop_size=args.pop_size,
        max_sample_nums=args.budget, output_dir=str(out)).run()

    best_path = out / "results" / "samples" / "samples_best.json"
    if not best_path.exists():
        print("No valid rule was found.")
        return
    best = json.loads(best_path.read_text())
    test = evaluate_rule(compile_rule(best["code"], "priority"), load_dataset(TEST_SET), args.alpha)
    print(f"\nIdea: {best['algorithm']}\n\n{best['code']}\n")
    print(f"train {int(best['objective']):,}   test {test:,}   (840 test yards, alpha {args.alpha})")
    print(f"PU1 {PU_TOTALS[(1, args.alpha)]:,}   PU2 {PU_TOTALS[(2, args.alpha)]:,}   "
          f"GP median {GP_MEDIANS[args.alpha]:,}")
    print(f"All samples and the log: {out}")


if __name__ == "__main__":
    main()
