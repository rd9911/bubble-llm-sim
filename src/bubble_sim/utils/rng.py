from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SeedBundle:
    global_seed: int
    env_seed: int
    policy_seed: int
    split_seed: int
    bootstrap_seed: int
    archetype_seed: int


def _derive_seed(parent_seed: int, namespace: str) -> int:
    payload = f"{parent_seed}:{namespace}".encode()
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:8], 16)


def make_seed_bundle(global_seed: int) -> SeedBundle:
    return SeedBundle(
        global_seed=global_seed,
        env_seed=_derive_seed(global_seed, "env"),
        policy_seed=_derive_seed(global_seed, "policy"),
        split_seed=_derive_seed(global_seed, "split"),
        bootstrap_seed=_derive_seed(global_seed, "bootstrap"),
        archetype_seed=_derive_seed(global_seed, "archetype"),
    )


def seed_python_and_numpy(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
