from bubble_sim.eval.leaderboard import (
    append_leaderboard_row,
    build_leaderboard_row,
    load_leaderboard,
)


def test_leaderboard_row_has_required_fields():
    row = build_leaderboard_row(
        candidate_id="test_1",
        config={"prompt_template": "v1", "temperature": 0.7},
        run_health={"clean_completion_rate": 0.99},
        micro={"weighted_js_divergence": 0.05},
        macro={"bubble_depth_gap": 0.3},
        calibration={"replication_score": 0.1, "passed_gate": True},
    )
    assert row["candidate_id"] == "test_1"
    assert row["calibration_score"] == 0.1
    assert row["passed_gate"] is True


def test_append_and_load(tmp_path):
    csv_path = tmp_path / "lb.csv"
    row_a = build_leaderboard_row("a", {}, {}, {}, {}, {"replication_score": 0.5})
    row_b = build_leaderboard_row("b", {}, {}, {}, {}, {"replication_score": 0.1})
    append_leaderboard_row(csv_path, row_a)
    append_leaderboard_row(csv_path, row_b)
    df = load_leaderboard(csv_path)
    assert len(df) == 2
    # Sorted ascending by calibration_score — "b" should be first
    assert df.iloc[0]["candidate_id"] == "b"
