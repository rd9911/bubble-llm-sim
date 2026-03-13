from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from bubble_sim.eval.buckets import assign_micro_buckets
from bubble_sim.eval.calibration import compute_resale_calibration
from bubble_sim.eval.micro_metrics import compute_bucket_buy_metrics, compute_micro_fidelity_summary


def generate_micro_fidelity_report(
    human_df: pd.DataFrame,
    agent_df: pd.DataFrame,
    output_dir: str | Path,
    bucket_scheme: str = "tier2",
    min_bucket_n: int = 10,
) -> None:
    """Computes comprehensive Phase 4.1 Micro Evaluation artifacts directly."""

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    h_df = assign_micro_buckets(human_df, bucket_scheme)
    a_df = assign_micro_buckets(agent_df, bucket_scheme)

    # Process Buckets safely computing JS/KL cleanly avoiding arrays
    metrics_df = compute_bucket_buy_metrics(h_df, a_df, min_bucket_n)

    if not metrics_df.empty:
        # Serialize DataFrames natively dropping tuple boundaries
        metrics_df["micro_bucket_str"] = metrics_df["micro_bucket"].astype(str)
        save_df = metrics_df.drop(columns=["micro_bucket"])
        save_df.to_parquet(path / "micro_bucket_metrics.parquet", index=False)

    summary = compute_micro_fidelity_summary(metrics_df)
    with open(path / "micro_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    calib = compute_resale_calibration(a_df)
    if calib:
        with open(path / "calibration_metrics.json", "w") as f:
            json.dump(calib, f, indent=2)
