import numpy as np
import pandas as pd

from bubble_sim.eval.micro_metrics import compute_bucket_buy_metrics, compute_micro_fidelity_summary


def test_identical_distributions_have_zero_js():
    # 15 rows smoothly clear sparse thresholds mathematically
    df = pd.DataFrame(
        [
            {"micro_bucket": ("cap", 1), "action": "buy"},
            {"micro_bucket": ("cap", 1), "action": "buy"},
            {"micro_bucket": ("cap", 1), "action": "no_buy"},
        ]
        * 5
    )

    metrics = compute_bucket_buy_metrics(df, df, min_bucket_n=10)
    assert len(metrics) == 1
    assert abs(metrics["js_divergence"].iloc[0]) < 1e-5
    assert metrics["buy_rate_gap"].iloc[0] == 0.0


def test_sparse_buckets_filtered():
    df_h = pd.DataFrame([{"micro_bucket": ("cap", 1), "action": "buy"}] * 5)
    df_a = pd.DataFrame([{"micro_bucket": ("cap", 1), "action": "buy"}] * 5)

    metrics = compute_bucket_buy_metrics(df_h, df_a, min_bucket_n=10)
    assert bool(metrics["is_sparse"].iloc[0]) is True
    assert np.isnan(metrics["js_divergence"].iloc[0])


def test_summary_weights_correctly():
    m_df = pd.DataFrame(
        [
            {
                "human_n": 100,
                "is_sparse": False,
                "js_divergence": 0.1,
                "buy_rate_gap": 0.2,
                "kl_divergence": 0.2,
            },
            {
                "human_n": 50,
                "is_sparse": False,
                "js_divergence": 0.4,
                "buy_rate_gap": -0.4,
                "kl_divergence": 0.5,
            },
        ]
    )

    res = compute_micro_fidelity_summary(m_df)

    # Weights dynamically represent strict mapping limits
    expected_js = (2 / 3) * 0.1 + (1 / 3) * 0.4
    expected_gap = (2 / 3) * 0.2 + (1 / 3) * 0.4

    assert abs(res["weighted_js_divergence"] - expected_js) < 1e-6
    assert abs(res["mean_absolute_buy_rate_gap"] - expected_gap) < 1e-6
