import pandas as pd

from bubble_sim.eval.buckets import assign_micro_buckets


def test_buckets_assigns_correctly():
    df = pd.DataFrame([{"cap_type": "capped", "price_index": 2, "previous_actions_len": 1}])
    res = assign_micro_buckets(df, "tier2")
    assert res["micro_bucket"].iloc[0] == ("capped", 2, 1)


def test_buckets_computes_previous_actions_len():
    # If len is missing it infers cleanly avoiding null crashes
    df = pd.DataFrame(
        [{"cap_type": "capped", "price_index": 2, "previous_actions": ["buy", "no_buy"]}]
    )
    res = assign_micro_buckets(df, "tier2")
    assert res["micro_bucket"].iloc[0] == ("capped", 2, 2)
