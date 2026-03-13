from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """Computes KL(P || Q) cleanly clipping pure zeros avoiding NaNs."""
    p_safe = np.clip(p, 1e-10, 1.0)
    q_safe = np.clip(q, 1e-10, 1.0)
    return float(np.sum(p_safe * np.log(p_safe / q_safe)))


def js_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """Computes symmetric JS(P, Q) measuring distributional gap bounds."""
    m = 0.5 * (p + q)
    return 0.5 * kl_divergence(p, m) + 0.5 * kl_divergence(q, m)


def compute_bucket_buy_metrics(
    human_df: pd.DataFrame, agent_df: pd.DataFrame, min_bucket_n: int = 10
) -> pd.DataFrame:
    """Computes JS/KL divergence and MABG filtering sparse buckets natively."""

    if "micro_bucket" not in human_df.columns or "micro_bucket" not in agent_df.columns:
        raise ValueError("DataFrames must have 'micro_bucket' column assigned.")

    # Compute human aggregations mapping decision bounds strictly
    h_agg = human_df.groupby("micro_bucket").agg(
        human_n=("action", "count"), human_buys=("action", lambda x: (x == "buy").sum())
    )
    h_agg["human_buy_rate"] = h_agg["human_buys"] / h_agg["human_n"]

    # Compute agent aggregations
    a_agg = agent_df.groupby("micro_bucket").agg(
        agent_n=("action", "count"), agent_buys=("action", lambda x: (x == "buy").sum())
    )
    a_agg["agent_buy_rate"] = a_agg["agent_buys"] / a_agg["agent_n"]

    # Join tracking natively dropping un-matched structures dynamically
    merged = h_agg.join(a_agg, how="inner").reset_index()

    # Filter sparse threshold buckets directly
    merged["is_sparse"] = (merged["human_n"] < min_bucket_n) | (merged["agent_n"] < min_bucket_n)

    # Compute alignment metric differentials
    merged["buy_rate_gap"] = merged["agent_buy_rate"] - merged["human_buy_rate"]

    js_scores = []
    kl_scores = []

    for _, row in merged.iterrows():
        if row["is_sparse"]:
            js_scores.append(np.nan)
            kl_scores.append(np.nan)
            continue

        ph = np.array([1 - row["human_buy_rate"], row["human_buy_rate"]])
        pa = np.array([1 - row["agent_buy_rate"], row["agent_buy_rate"]])

        js_scores.append(js_divergence(ph, pa))
        kl_scores.append(kl_divergence(ph, pa))

    merged["js_divergence"] = js_scores
    merged["kl_divergence"] = kl_scores

    return merged


def compute_micro_fidelity_summary(bucket_metrics_df: pd.DataFrame) -> dict[str, Any]:
    """Generates weighted summary statistics aggregating Phase 4.1 metrics cleanly."""
    total_buckets = len(bucket_metrics_df)
    if total_buckets == 0:
        return {}

    sparse_buckets = bucket_metrics_df["is_sparse"].sum()
    valid_df = bucket_metrics_df[~bucket_metrics_df["is_sparse"]].copy()

    res = {
        "total_buckets": total_buckets,
        "sparse_bucket_fraction": float(sparse_buckets / total_buckets),
    }

    if valid_df.empty:
        return res

    # Weights normalized across human empirical distribution limits
    total_valid_human = valid_df["human_n"].sum()
    valid_df["weight"] = valid_df["human_n"] / total_valid_human

    # Calculate MABG manually
    valid_df["abs_gap"] = valid_df["buy_rate_gap"].abs()

    res["weighted_js_divergence"] = float((valid_df["js_divergence"] * valid_df["weight"]).sum())
    res["weighted_kl_divergence"] = float((valid_df["kl_divergence"] * valid_df["weight"]).sum())
    res["mean_absolute_buy_rate_gap"] = float((valid_df["abs_gap"] * valid_df["weight"]).sum())

    return res
