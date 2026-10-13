import csv
from pathlib import Path

from crp.gp.experiment import FIELDS, append_row, run_experiment
from crp.gp.fitness import total_relocations
from crp.instance import load_dataset

ROOT = Path(__file__).resolve().parent.parent


def test_experiment_row_and_csv(tmp_path):
    training = load_dataset(ROOT / "data" / "training")[::40]
    test = load_dataset(ROOT / "data" / "caserta_840")[::40]
    row = run_experiment(
        score=lambda text: total_relocations(text, training, 0.5, "max"),
        test_instances=test, alpha=0.5, hidden="max", seed=1,
        population=10, generations=2, training_set="training",
    )
    assert row["evaluations"] == 30
    assert row["test_total"] == total_relocations(row["formula"], test, 0.5, "max")
    assert row["train_fitness"] == total_relocations(row["formula"], training, 0.5, "max")

    out = tmp_path / "runs.csv"
    append_row(out, row)
    append_row(out, row)
    rows = list(csv.DictReader(out.open()))
    assert len(rows) == 2 and list(rows[0]) == FIELDS  # header written once
