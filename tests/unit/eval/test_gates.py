from bubble_sim.eval.gates import evaluate_promotion_gates


def test_strong_candidate_passes():
    rh = {"clean_completion_rate": 0.99, "fallback_use_rate": 0.005}
    mi = {"weighted_js_divergence": 0.02, "mean_absolute_buy_rate_gap": 0.03}
    ma = {"bubble_depth_gap": 0.3, "snowball_slope_error": 0.05}
    result = evaluate_promotion_gates(rh, mi, ma)
    assert result["passed_gate"] is True
    assert result["gate1_operational"] is True


def test_weak_operational_fails():
    rh = {"clean_completion_rate": 0.80, "fallback_use_rate": 0.10}
    mi = {"weighted_js_divergence": 0.02, "mean_absolute_buy_rate_gap": 0.03}
    ma = {"bubble_depth_gap": 0.3, "snowball_slope_error": 0.05}
    result = evaluate_promotion_gates(rh, mi, ma)
    assert result["passed_gate"] is False
    assert result["gate1_operational"] is False


def test_weak_macro_fails():
    rh = {"clean_completion_rate": 0.99, "fallback_use_rate": 0.005}
    mi = {"weighted_js_divergence": 0.02, "mean_absolute_buy_rate_gap": 0.03}
    ma = {"bubble_depth_gap": 5.0, "snowball_slope_error": 1.0}
    result = evaluate_promotion_gates(rh, mi, ma)
    assert result["passed_gate"] is False
    assert result["gate3_macro"] is False
