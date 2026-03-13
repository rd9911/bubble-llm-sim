from bubble_sim.eval.divergence_analysis import (
    compute_divergence_profile,
    run_sample_divergence_study,
)
from bubble_sim.eval.replication_targets import ReplicationTarget


def test_divergence_profile_zero_when_identical():
    m = {
        "mean_bubble_depth": 2.5,
        "snowball_slope": 0.2,
        "treatment_gap": 0.15,
        "weighted_js_divergence": 0.05,
        "mean_absolute_buy_rate_gap": 0.02,
    }
    profile = compute_divergence_profile(m, m)
    for v in profile.values():
        assert v == 0.0


def test_divergence_study_returns_scores():
    targets = ReplicationTarget(
        snowball_slope=0.2,
        treatment_gap=0.15,
        mean_bubble_depth=2.5,
    )
    baseline = {
        "weighted_js_divergence": 0.01,
        "mean_absolute_buy_rate_gap": 0.01,
        "mean_bubble_depth": 2.5,
        "snowball_slope": 0.2,
        "treatment_gap": 0.15,
    }
    alt = {
        "weighted_js_divergence": 0.3,
        "mean_absolute_buy_rate_gap": 0.2,
        "mean_bubble_depth": 4.0,
        "snowball_slope": 0.05,
        "treatment_gap": 0.4,
    }
    result = run_sample_divergence_study(baseline, alt, targets)
    assert result["baseline_replication_score"] < result["alternative_replication_score"]
    assert "divergence_from_baseline" in result
    assert result["divergence_from_baseline"]["mean_bubble_depth_shift"] == 1.5
