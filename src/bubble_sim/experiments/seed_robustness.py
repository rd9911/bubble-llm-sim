from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_seed_robustness(
    seed_results: list[dict[str, Any]],
    metric_keys: list[str] | None = None,
) -> dict[str, dict[str, float]]:
    """Computes mean and SD across seeds per metric."""
    if metric_keys is None:
        metric_keys = [
            "weighted_js_divergence",
            "mean_absolute_buy_rate_gap",
            "bubble_depth_gap",
            "snowball_slope_error",
            "terminal_holder_gap",
        ]

    stats: dict[str, dict[str, float]] = {}
    for key in metric_keys:
        values = [r.get(key, 0.0) for r in seed_results]
        arr = np.array(values, dtype=float)
        stats[key] = {
            "mean": float(np.mean(arr)),
            "sd": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        }
    return stats


def build_robustness_table(
    system_seed_results: dict[str, list[dict[str, Any]]],
    metric_keys: list[str] | None = None,
) -> pd.DataFrame:
    """Builds mean ± SD table across systems."""
    rows = []
    for system_name, seed_results in system_seed_results.items():
        stats = compute_seed_robustness(seed_results, metric_keys)
        row: dict[str, Any] = {"system": system_name}
        for key, vals in stats.items():
            row[f"{key}_mean"] = vals["mean"]
            row[f"{key}_sd"] = vals["sd"]
        rows.append(row)
    return pd.DataFrame(rows)


def check_directional_consistency(
    baseline_seeds: list[dict[str, Any]],
    calibrated_seeds: list[dict[str, Any]],
    metric_key: str = "calibration_score",
) -> bool:
    """Returns True if calibrated beats baseline in every seed pair."""
    if len(baseline_seeds) != len(calibrated_seeds):
        return False
    for b, c in zip(
        sorted(baseline_seeds, key=lambda x: x.get("seed", 0)),
        sorted(calibrated_seeds, key=lambda x: x.get("seed", 0)),
    ):
        if c.get(metric_key, 99) >= b.get(metric_key, 99):
            return False
    return True
