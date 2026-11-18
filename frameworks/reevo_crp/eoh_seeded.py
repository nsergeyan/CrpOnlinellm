"""Start ReEvo's main.py with EoH's own seed option switched on (README decision 54).

ReEvo's EoH launcher fixes EoH's settings and leaves exp_use_seed off, so EoH writes its first
rules itself. This script switches it on before main.py runs, with the seed file named by
CRP_EOH_SEEDS (written by install_reevo_files.py). It also passes the iteration number that
ReEvo's EoH leaves out on its seed path (it is only used in log lines; without it the call
fails). ReEvo's own files are not touched.

    cd frameworks/reevo && CRP_EOH_SEEDS=... .venv/bin/python ../reevo_crp/eoh_seeded.py <main.py arguments>
"""
import os
import runpy
import sys
from pathlib import Path

REEVO = Path.cwd()
sys.path.insert(0, str(REEVO))  # ReEvo's modules, as when main.py is started directly

from baselines.eoh import problem_adapter  # noqa: E402
from baselines.eoh.original import getParas  # noqa: E402

SEEDS = str(Path(os.environ["CRP_EOH_SEEDS"]).resolve())  # absolute: Hydra changes the folder
default_paras = getParas.Paras.__init__


def seeded_paras(self) -> None:
    default_paras(self)
    self.exp_use_seed, self.exp_seed_path = True, SEEDS


evaluate = problem_adapter.Problem.batch_evaluate
getParas.Paras.__init__ = seeded_paras
problem_adapter.Problem.batch_evaluate = lambda self, codes, iteration=0: evaluate(self, codes, iteration)

sys.argv = [str(REEVO / "main.py"), *sys.argv[1:]]
runpy.run_path(str(REEVO / "main.py"), run_name="__main__")
