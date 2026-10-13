import csv
from pathlib import Path

from crp.gp.experiment import FIELDS, _key, append_row, finished_runs, medians, run_experiment, run_many
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


def test_quick_rows_never_count_as_full_runs(tmp_path):
    out = tmp_path / "mixed.csv"
    base = dict(date="x", alpha=0.5, hidden="max", seed=1, evaluations=0, train_fitness=0,
                best_generation=0, formula="SH", training_set="training", cache_hits=0, seconds=0)
    append_row(out, {**base, "population": 100, "generations": 19, "test_total": 99_999})  # quick
    append_row(out, {**base, "seed": 2, "population": 1000, "generations": 50, "test_total": 24_000})  # full

    done = finished_runs(out)
    assert _key(0.5, "max", 1, 1000, 50, "training") not in done  # quick seed 1 does not skip full seed 1
    assert _key(0.5, "max", 2, 1000, 50, "training") in done
    assert medians(out, "max", 1000, 50, "training") == {0.5: (24_000, 1)}  # quick row ignored
