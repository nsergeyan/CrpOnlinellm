"""Generate the fixed GP training set once: 21 Caserta classes x 40 instances.

Run from PyCharm (green button), or: python experiments/make_training_set.py
"""
import random
from pathlib import Path

from crp.instance import CASERTA_CLASSES, generate_instance, write_instance

SEED = 2026
PER_CLASS = 40
OUT = Path(__file__).resolve().parent.parent / "data" / "training"

if OUT.exists():
    raise SystemExit(f"{OUT} already exists; delete it first if you really want to regenerate")
OUT.mkdir(parents=True)
rng = random.Random(SEED)
for tiers, stack_counts in CASERTA_CLASSES.items():
    for n_stacks in stack_counts:
        for k in range(1, PER_CLASS + 1):
            name = f"data{tiers}-{n_stacks}-{k}"
            write_instance(generate_instance(name, n_stacks, tiers, rng), OUT / f"{name}.dat")
print("wrote", sum(1 for _ in OUT.glob("*.dat")), "instances to", OUT)
