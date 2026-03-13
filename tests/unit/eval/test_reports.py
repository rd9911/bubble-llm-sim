import json

import pandas as pd

from bubble_sim.eval.reports import generate_micro_fidelity_report


def test_report_generation(tmp_path):
    h_df = pd.DataFrame(
        [{"cap_type": "capped", "price_index": 1, "previous_actions_len": 0, "action": "buy"}] * 15
    )

    a_df = pd.DataFrame(
        [{"cap_type": "capped", "price_index": 1, "previous_actions_len": 0, "action": "no_buy"}]
        * 15
    )

    generate_micro_fidelity_report(h_df, a_df, tmp_path, min_bucket_n=10)

    assert (tmp_path / "micro_bucket_metrics.parquet").exists()
    assert (tmp_path / "micro_summary.json").exists()

    with open(tmp_path / "micro_summary.json") as f:
        data = json.load(f)
        assert "weighted_js_divergence" in data
