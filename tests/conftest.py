"""Shared test fixtures: each data set is loaded once per test session."""
import pytest

from crp.instance import load_dataset
from crp.paths import TEST_SET, TRAINING_SET


@pytest.fixture(scope="session")
def test_set():
    return load_dataset(TEST_SET)


@pytest.fixture(scope="session")
def training_set():
    return load_dataset(TRAINING_SET)
