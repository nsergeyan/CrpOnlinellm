from pathlib import Path

from crp.instance import load_dataset, load_instance

DATA = Path(__file__).resolve().parent.parent / "data" / "caserta_840"


def test_load_small_instance():
    inst = load_instance(DATA / "data3-3-1.dat")
    assert inst.name == "data3-3-1"
    assert inst.stacks == ((3, 7, 1), (2, 6, 5), (8, 9, 4))
    assert inst.n_containers == 9
    assert inst.max_height == 5


def test_load_all_test_instances():
    instances = load_dataset(DATA)
    assert len(instances) == 840
    assert all(len(s) <= inst.max_height for inst in instances for s in inst.stacks)
