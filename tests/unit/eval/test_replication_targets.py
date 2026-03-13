from bubble_sim.eval.replication_targets import (
    ReplicationTarget,
    compute_replication_score,
    default_bubble_game_targets,
)


def test_default_targets_exist():
    t = default_bubble_game_targets()
    assert t.snowball_slope > 0
    assert len(t.buy_rate_by_state) > 0


def test_perfect_match_score_is_zero():
    targets = ReplicationTarget(
        snowball_slope=0.2,
        treatment_gap=0.15,
        mean_bubble_depth=2.5,
        terminal_holder_freq=0.3,
    )
    agent_metrics = {
        "weighted_js_divergence": 0.0,
        "mean_absolute_buy_rate_gap": 0.0,
        "mean_bubble_depth": 2.5,
        "snowball_slope": 0.2,
        "treatment_gap": 0.15,
    }
    result = compute_replication_score(agent_metrics, targets)
    assert result["replication_score"] == 0.0


def test_nonzero_gap_produces_positive_score():
    targets = default_bubble_game_targets()
    agent_metrics = {
        "weighted_js_divergence": 0.1,
        "mean_absolute_buy_rate_gap": 0.05,
        "mean_bubble_depth": 3.0,
        "snowball_slope": 0.1,
        "treatment_gap": 0.25,
    }
    result = compute_replication_score(agent_metrics, targets)
    assert result["replication_score"] > 0.0
    assert "components" in result
