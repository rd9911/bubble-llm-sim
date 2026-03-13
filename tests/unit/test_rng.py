import random

import numpy as np

from bubble_sim.utils.rng import make_seed_bundle, seed_python_and_numpy


def test_seed_bundle_determinism():
    bundle1 = make_seed_bundle(42)
    bundle2 = make_seed_bundle(42)
    assert bundle1 == bundle2
    bundle3 = make_seed_bundle(43)
    assert bundle1 != bundle3


def test_seed_bundle_namespacing():
    bundle = make_seed_bundle(42)
    assert bundle.env_seed != bundle.policy_seed
    assert bundle.env_seed != bundle.global_seed


def test_seed_python_and_numpy():
    seed_python_and_numpy(42)
    val1 = random.random()
    np_val1 = np.random.random()

    seed_python_and_numpy(42)
    val2 = random.random()
    np_val2 = np.random.random()

    assert val1 == val2
    assert np_val1 == np_val2
