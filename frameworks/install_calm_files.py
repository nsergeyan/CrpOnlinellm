"""Put our CRP files into a CALM folder (run by frameworks/setup_calm.sh).

Copies the problem file, the settings and the launcher, and writes the seed rule and the
function template from src/crp/llm/prompts.py, so CALM starts from the same rule and
function shape as EoH and ReEvo. CALM's own files are not touched.

    python frameworks/install_calm_files.py frameworks/calm
"""
import shutil
import sys
from pathlib import Path

from crp.llm.prompts import TEMPLATE_PROGRAM

OURS = Path(__file__).resolve().parent / "calm_crp"
# CALM reads a rule's idea from the first line of the seed file
SEED_IDEA = "# The idea of the algorithm is to place the container on the lowest stack."


def install(calm: Path) -> None:
    configs = calm / "configs" / "crp_online"
    configs.mkdir(parents=True, exist_ok=True)
    shutil.copy(OURS / "crp_online.py", calm / "problems" / "crp_online.py")
    shutil.copy(OURS / "crp_online.yaml", configs / "crp_online.yaml")
    shutil.copy(OURS / "run.py", calm / "run_crp.py")  # next to CALM's main.py, which it imports

    (configs / "seed.py").write_text(f"{SEED_IDEA}\n{TEMPLATE_PROGRAM}")
    # like CALM's own templates: the function's shape without a body
    signature, docstring = TEMPLATE_PROGRAM.splitlines()[:2]
    (configs / "template.py").write_text(f"{signature}\n{docstring}\n    pass\n    return priority\n")


if __name__ == "__main__":
    install(Path(sys.argv[1]))
    print(f"CRP files installed in {sys.argv[1]}")
