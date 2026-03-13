import pandas as pd

from bubble_sim.robustness.alignment_reports import (
    build_alignment_report_bundle,
    build_fidelity_comparison,
)


def test_fidelity_comparison():
    results = [
        {"regime": "aligned", "weighted_js_divergence": 0.05, "bubble_depth_gap": 0.3},
        {"regime": "base", "weighted_js_divergence": 0.10, "bubble_depth_gap": 0.5},
    ]
    df = build_fidelity_comparison(results)
    assert len(df) == 2
    assert "weighted_js" in df.columns


def test_report_bundle(tmp_path):
    cap = pd.DataFrame([{"regime": "aligned", "completion_rate": 0.99}])
    viol = pd.DataFrame([{"regime": "aligned", "event_type": "refusal"}])
    fid = pd.DataFrame(
        [
            {"regime": "aligned", "completion_rate": 0.99, "weighted_js": 0.05},
            {"regime": "base", "completion_rate": 0.90, "weighted_js": 0.10},
        ]
    )
    build_alignment_report_bundle(cap, viol, fid, tmp_path)
    assert (tmp_path / "capacity_benchmark.csv").exists()
    assert (tmp_path / "refusal_violation_table.csv").exists()
    assert (tmp_path / "fidelity_comparison.csv").exists()
    assert (tmp_path / "regime_scorecard.json").exists()
    md = (tmp_path / "alignment_tradeoff_report.md").read_text()
    assert "aligned" in md
