from bubble_sim.eval.scorecards import build_scorecard


def test_perfect_metrics_all_green():
    rh = {"clean_completion_rate": 0.99, "fallback_use_rate": 0.005}
    mi = {"weighted_js_divergence": 0.01, "mean_absolute_buy_rate_gap": 0.01}
    ma = {"bubble_depth_gap": 0.1, "snowball_slope_error": 0.01}
    card = build_scorecard(rh, mi, ma)
    assert card["run_health"]["clean_completion_rate"] == "green"
    assert card["micro"]["weighted_js"] == "green"
    assert card["macro"]["bubble_depth_gap"] == "green"


def test_bad_metrics_all_red():
    rh = {"clean_completion_rate": 0.50, "fallback_use_rate": 0.20}
    mi = {"weighted_js_divergence": 0.90, "mean_absolute_buy_rate_gap": 0.80}
    ma = {"bubble_depth_gap": 5.0, "snowball_slope_error": 1.0}
    card = build_scorecard(rh, mi, ma)
    assert card["run_health"]["clean_completion_rate"] == "red"
    assert card["micro"]["weighted_js"] == "red"
    assert card["macro"]["snowball_slope_error"] == "red"
