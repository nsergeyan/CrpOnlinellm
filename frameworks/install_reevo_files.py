"""Put our CRP files into a ReEvo folder (run by frameworks/setup_reevo.sh).

Writes the three ReEvo prompt files from src/crp/llm/prompts.py, so ReEvo and EoH always
get the same texts, and copies our settings file and eval.py. ReEvo's own files are not touched.
Two problems: crp_online (the plain problem text) and crp_online_knowledge for EoH with our
framework's prior knowledge (README decision 54): the problem text plus our CRP knowledge text,
and the Min-Max seed as EoH's start rule.

    python frameworks/install_reevo_files.py frameworks/reevo
"""
import json
import shutil
import sys
from pathlib import Path

from crp.framework.knowledge import KNOWLEDGE, SEEDS
from crp.llm.prompts import FUNCTION_DESCRIPTION, PROBLEM_DESCRIPTION, TEMPLATE_PROGRAM

OURS = Path(__file__).resolve().parent / "reevo_crp"


def install_problem(reevo: Path, name: str, description: str) -> Path:
    """One problem's prompt files, settings and eval.py; returns its problem folder."""
    prompts = reevo / "prompts" / name
    problem = reevo / "problems" / name
    prompts.mkdir(parents=True, exist_ok=True)
    problem.mkdir(parents=True, exist_ok=True)

    # ReEvo numbers its versions: the seed is priority_v1, the LLM writes priority_v2
    signature = TEMPLATE_PROGRAM.splitlines()[0]
    (prompts / "func_signature.txt").write_text(signature.replace("def priority(", "def priority_v{version}("))
    (prompts / "seed_func.txt").write_text(TEMPLATE_PROGRAM.replace("def priority(", "def priority_v1("))
    (prompts / "func_desc.txt").write_text(FUNCTION_DESCRIPTION)

    # a JSON string is also a valid YAML string, so quotes and colons in the text are safe
    settings = (OURS / "crp_online.yaml").read_text().replace("problem_name: crp_online", f"problem_name: {name}")
    settings += f"description: {json.dumps(description)}\n"
    (reevo / "cfg" / "problem" / f"{name}.yaml").write_text(settings)
    shutil.copy(OURS / "eval.py", problem / "eval.py")
    return problem


def install(reevo: Path) -> None:
    install_problem(reevo, "crp_online", PROBLEM_DESCRIPTION)
    problem = install_problem(reevo, "crp_online_knowledge", f"{PROBLEM_DESCRIPTION}\n\n{KNOWLEDGE}")
    # EoH's own seed file format; EoH scores this rule as priority_v2, the name eval.py loads
    idea, code = SEEDS["minmax"]
    seed = {"algorithm": idea, "code": code.replace("def priority(", "def priority_v2(")}
    (problem / "seeds.json").write_text(json.dumps([seed], indent=1))


if __name__ == "__main__":
    install(Path(sys.argv[1]))
    print(f"CRP files installed in {sys.argv[1]}")
