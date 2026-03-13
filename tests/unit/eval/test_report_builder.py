from bubble_sim.eval.report_builder import build_eval_report


def test_report_creates_all_files(tmp_path):
    eval_dir = tmp_path / "eval_001"
    build_eval_report(
        eval_dir=eval_dir,
        eval_manifest={"eval_id": "eval_001", "run_id": "run_1"},
        run_health={"clean_completion_rate": 0.99, "fallback_use_rate": 0.005},
        micro={"weighted_js_divergence": 0.02},
        macro={"bubble_depth_gap": 0.3},
        calibration={"replication_score": 0.1},
        gate_result={"passed_gate": True, "gate1_operational": True},
        scorecard={"run_health": {"clean_completion_rate": "green"}},
    )
    assert (eval_dir / "eval_manifest.json").exists()
    assert (eval_dir / "run_health.json").exists()
    assert (eval_dir / "micro_summary.json").exists()
    assert (eval_dir / "macro_summary.json").exists()
    assert (eval_dir / "calibration_summary.json").exists()
    assert (eval_dir / "leaderboard_row.json").exists()
    assert (eval_dir / "report.md").exists()

    md = (eval_dir / "report.md").read_text()
    assert "eval_001" in md
    assert "✅" in md
    assert "🟢" in md
