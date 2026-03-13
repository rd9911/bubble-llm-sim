from bubble_sim.eval.calibration_loop import (
    build_config_grid,
    run_replication_calibration,
    select_best_replication_config,
)
from bubble_sim.eval.replication_targets import (
    ReplicationTarget,
)


def test_grid_builder_cartesian():
    grid = build_config_grid(
        prompt_templates=["p1", "p2"],
        temperatures=[0.5, 1.0],
    )
    assert len(grid) == 4


def test_best_config_picks_lowest():
    targets = ReplicationTarget(
        snowball_slope=0.2,
        treatment_gap=0.15,
        mean_bubble_depth=2.5,
    )
    grid = build_config_grid(
        prompt_templates=["good", "bad"],
        temperatures=[0.7],
    )
    metrics_list = [
        {
            "weighted_js_divergence": 0.01,
            "mean_absolute_buy_rate_gap": 0.01,
            "mean_bubble_depth": 2.5,
            "snowball_slope": 0.2,
            "treatment_gap": 0.15,
        },
        {
            "weighted_js_divergence": 0.5,
            "mean_absolute_buy_rate_gap": 0.3,
            "mean_bubble_depth": 4.0,
            "snowball_slope": 0.0,
            "treatment_gap": 0.5,
        },
    ]
    lb = run_replication_calibration(grid, metrics_list, targets)
    best = select_best_replication_config(lb)
    assert "good" in best
