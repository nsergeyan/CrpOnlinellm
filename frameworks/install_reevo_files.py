"""Put our CRP files into a ReEvo folder (run by frameworks/setup_reevo.sh).

Writes the three ReEvo prompt files from src/crp/llm/prompts.py, so ReEvo and EoH always
get the same texts, and copies our settings file and eval.py. ReEvo's own files are not touched.

    python frameworks/install_reevo_files.py frameworks/reevo
"""
import json
import shutil
import sys
from pathlib import Path

from crp.llm.prompts import FUNCTION_DESCRIPTION, PROBLEM_DESCRIPTION, TEMPLATE_PROGRAM

OURS = Path(__file__).resolve().parent / "reevo_crp"


def install(reevo: Path) -> None:
    prompts = reevo / "prompts" / "crp_online"
    problem = reevo / "problems" / "crp_online"
    prompts.mkdir(parents=True, exist_ok=True)
    problem.mkdir(parents=True, exist_ok=True)

    # ReEvo numbers its versions: the seed is priority_v1, the LLM writes priority_v2
    signature = TEMPLATE_PROGRAM.splitlines()[0]
    (prompts / "func_signature.txt").write_text(signature.replace("def priority(", "def priority_v{version}("))
    (prompts / "seed_func.txt").write_text(TEMPLATE_PROGRAM.replace("def priority(", "def priority_v1("))
    (prompts / "func_desc.txt").write_text(FUNCTION_DESCRIPTION)

    # a JSON string is also a valid YAML string, so quotes and colons in the text are safe
    settings = (OURS / "crp_online.yaml").read_text()
    settings += f"description: {json.dumps(PROBLEM_DESCRIPTION)}\n"
    (reevo / "cfg" / "problem" / "crp_online.yaml").write_text(settings)
    shutil.copy(OURS / "eval.py", problem / "eval.py")


if __name__ == "__main__":
    install(Path(sys.argv[1]))
    print(f"CRP files installed in {sys.argv[1]}")
