from bubble_sim.robustness.sensitivity_configs import (
    build_decoding_sweep,
    build_prompt_variant_sweep,
    build_seed_sweep,
)


def test_decoding_sweep_size():
    cfgs = build_decoding_sweep("sys1", "v2")
    assert len(cfgs) == 15
    assert all(c.sweep_type == "decoding" for c in cfgs)


def test_prompt_sweep_default():
    cfgs = build_prompt_variant_sweep("sys1", 0.2, 1.0)
    assert len(cfgs) == 4


def test_prompt_sweep_with_extras():
    cfgs = build_prompt_variant_sweep("sys1", 0.2, 1.0, extra_variants=["winner_compact"])
    assert len(cfgs) == 5


def test_seed_sweep_default():
    cfgs = build_seed_sweep("sys1", "v2", 0.2, 1.0)
    assert len(cfgs) == 10
    seeds = {c.seed for c in cfgs}
    assert seeds == set(range(42, 52))
