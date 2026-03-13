from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_resale_calibration(decisions_df: pd.DataFrame, n_bins: int = 10) -> dict[str, Any]:
    """Computes calibration scoring metrics avoiding invalid states."""

    df = decisions_df.copy()
    if (
        "action" not in df.columns
        or "belief_resell" not in df.columns
        or "resale_success" not in df.columns
    ):
        return {}

    # Strictly evaluate conditional expectations for buy decisions
    condition = (
        (df["action"] == "buy") & (df["belief_resell"].notna()) & (df["resale_success"].notna())
    )
    valid_df = df[condition]

    if valid_df.empty:
        return {}

    y_true = valid_df["resale_success"].astype(float).to_numpy()
    y_prob = valid_df["belief_resell"].astype(float).to_numpy()

    if len(y_prob) == 0:
        return {}

    brier = float(np.mean((y_prob - y_true) ** 2))

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    binids = np.digitize(y_prob, bins) - 1

    # Edge case clamping safely avoiding array indices
    binids = np.clip(binids, 0, n_bins - 1)

    bin_sums = np.bincount(binids, weights=y_prob, minlength=n_bins)
    bin_true = np.bincount(binids, weights=y_true, minlength=n_bins)
    bin_total = np.bincount(binids, minlength=n_bins)

    nonzero = bin_total > 0
    prob_pred = bin_sums[nonzero] / bin_total[nonzero]
    prob_true = bin_true[nonzero] / bin_total[nonzero]

    # Calculate Expected Calibration Error weighting empirically natively
    ece = float(np.sum(np.abs(prob_pred - prob_true) * (bin_total[nonzero] / len(y_prob))))

    # Output curve references evaluating bin reliability visually
    reliability_bins = {
        "predicted_probs": prob_pred.tolist(),
        "empirical_probs": prob_true.tolist(),
        "bin_counts": bin_total[nonzero].tolist(),
    }

    return {
        "brier_score": brier,
        "ece": ece,
        "n_samples": len(y_prob),
        "reliability": reliability_bins,
    }
