import csv
from pathlib import Path

from crp.gp.experiment import FIELDS, append_row, medians, run_experiment, run_many
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


def test_run_many_writes_rows_and_resumes(tmp_path):
    for name, source in (("train", "training"), ("test", "caserta_840")):
        (tmp_path / name).mkdir()
        for f in sorted((ROOT / "data" / source).glob("data3-3-*.dat"))[:3]:
            (tmp_path / name / f.name).write_text(f.read_text())
    out = tmp_path / "runs.csv"
    settings = dict(alphas=[0.5], seeds=[1, 2], hidden="max", population=6, generations=1,
                    training_dir=tmp_path / "train", test_dir=tmp_path / "test", out=out, workers=2,
                    progress=lambda line: None)

    first = run_many(**settings)
    assert sorted(r["seed"] for r in first) == [1, 2]
    assert len(list(csv.DictReader(out.open()))) == 2

    again = run_many(**settings)  # both already in the CSV: nothing is rerun
    assert again == [] and len(list(csv.DictReader(out.open()))) == 2

    assert medians(out, "max", 6, 1, "train")[0.5][1] == 2
