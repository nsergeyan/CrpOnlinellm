import random

from crp.instance import (
    CASERTA_CLASSES,
    generate_instance,
    load_dataset,
    load_instance,
    write_instance,
)
from crp.paths import TEST_SET


def test_load_small_instance():
    inst = load_instance(TEST_SET / "data3-3-1.dat")
    assert inst.name == "data3-3-1"
    assert inst.stacks == ((3, 7, 1), (2, 6, 5), (8, 9, 4))
    assert inst.n_containers == 9
    assert inst.max_height == 5


def test_load_all_test_instances():
    instances = load_dataset(TEST_SET)
    assert len(instances) == 840
    assert all(len(s) <= inst.max_height for inst in instances for s in inst.stacks)


def test_generated_instance_is_full_and_valid():
    inst = generate_instance("data4-5-1", n_stacks=5, tiers=4, rng=random.Random(0))
    assert len(inst.stacks) == 5 and all(len(s) == 4 for s in inst.stacks)
    assert sorted(i for s in inst.stacks for i in s) == list(range(1, 21))
    assert inst.max_height == 6


def test_same_seed_same_instance():
    a = generate_instance("x", 6, 3, random.Random(2026))
    b = generate_instance("x", 6, 3, random.Random(2026))
    assert a == b


def test_classes_match_test_set():
    names = {inst.name.rsplit("-", 1)[0] for inst in load_dataset(TEST_SET)}
    assert names == {f"data{t}-{s}" for t, ss in CASERTA_CLASSES.items() for s in ss}


def test_write_then_load_roundtrip(tmp_path):
    inst = generate_instance("data3-4-7", n_stacks=4, tiers=3, rng=random.Random(1))
    write_instance(inst, tmp_path / "data3-4-7.dat")
    assert load_instance(tmp_path / "data3-4-7.dat") == inst
