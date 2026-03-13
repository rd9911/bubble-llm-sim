from bubble_sim.robustness.alignment_configs import (
    build_capacity_benchmark,
    build_refusal_violation_table,
)


def test_capacity_benchmark():
    results = [
        {"regime": "aligned", "completion_rate": 0.99, "refusal_rate": 0.01},
        {"regime": "base", "completion_rate": 0.90, "refusal_rate": 0.05},
    ]
    df = build_capacity_benchmark(results)
    assert len(df) == 2
    assert "completion_rate" in df.columns


def test_refusal_violation_table():
    events = [
        {"regime": "aligned", "episode_id": "ep1", "event_type": "refusal"},
        {"regime": "base", "episode_id": "ep2", "event_type": "schema_violation"},
    ]
    df = build_refusal_violation_table(events)
    assert len(df) == 2
    assert "event_type" in df.columns
