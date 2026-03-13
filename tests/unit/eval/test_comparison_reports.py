import json

import pandas as pd

from bubble_sim.eval.comparison_reports import (
    build_replication_leaderboard,
    build_replication_vs_divergence_report,
)


def test_leaderboard_writes_files(tmp_path):
    df = pd.DataFrame(
        [
            {"label": "cfg_a", "replication_score": 0.1},
            {"label": "cfg_b", "replication_score": 0.5},
        ]
    )
    build_replication_leaderboard(df, tmp_path)
    assert (tmp_path / "replication_leaderboard.parquet").exists()
    assert (tmp_path / "replication_leaderboard.csv").exists()


def test_comparison_report_json(tmp_path):
    rep = {"replication_score": 0.1}
    div = {"replication_score": 0.5}
    result = build_replication_vs_divergence_report(rep, div, tmp_path)
    assert "replication" in result
    assert "divergence" in result
    with open(tmp_path / "comparison_report.json") as f:
        data = json.load(f)
    assert "replication" in data
