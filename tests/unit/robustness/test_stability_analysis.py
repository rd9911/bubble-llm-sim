from bubble_sim.robustness.stability_analysis import (
    build_robustness_report,
    build_stability_scorecard,
    compute_metric_range,
    compute_seed_variance,
)


def test_metric_range():
    results = [
        {"weighted_js_divergence": 0.1},
        {"weighted_js_divergence": 0.3},
    ]
    ranges = compute_metric_range(results, ["weighted_js_divergence"])
    assert ranges["weighted_js_divergence"]["min"] == 0.1
    assert ranges["weighted_js_divergence"]["max"] == 0.3
    assert abs(ranges["weighted_js_divergence"]["range"] - 0.2) < 1e-9


def test_seed_variance():
    results = [
        {"weighted_js_divergence": 0.10},
        {"weighted_js_divergence": 0.20},
        {"weighted_js_divergence": 0.15},
    ]
    stats = compute_seed_variance(results, ["weighted_js_divergence"])
    assert abs(stats["weighted_js_divergence"]["mean"] - 0.15) < 1e-9
    assert stats["weighted_js_divergence"]["sd"] > 0
    assert stats["weighted_js_divergence"]["cv"] > 0


def test_stability_scorecard_green():
    dec = {"weighted_js_divergence": {"min": 0.1, "max": 0.12, "range": 0.02}}
    prompt = {"weighted_js_divergence": {"min": 0.1, "max": 0.13, "range": 0.03}}
    seed = {
        "weighted_js_divergence": {"mean": 0.1, "sd": 0.01, "cv": 0.1, "min": 0.09, "max": 0.11}
    }
    card = build_stability_scorecard(dec, prompt, seed)
    assert card["decoding"]["weighted_js_divergence"] == "green"
    assert card["seed"]["weighted_js_divergence"] == "green"


def test_robustness_report_files(tmp_path):
    data = [{"weighted_js_divergence": 0.1, "fallback_use_rate": 0.01}]
    build_robustness_report(data, data, data, tmp_path)
    assert (tmp_path / "decoding_sweep.csv").exists()
    assert (tmp_path / "prompt_sweep.csv").exists()
    assert (tmp_path / "seed_variance.csv").exists()
    assert (tmp_path / "stability_scorecard.json").exists()
    assert (tmp_path / "robustness_report.md").exists()
