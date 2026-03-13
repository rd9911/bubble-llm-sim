from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd


def build_leaderboard_row(
    candidate_id: str,
    config: dict[str, Any],
    run_health: dict[str, Any],
    micro: dict[str, Any],
    macro: dict[str, Any],
    calibration: dict[str, Any],
) -> dict[str, Any]:
    """Builds one comparable leaderboard row."""
    return {
        "candidate_id": candidate_id,
        "model_id": config.get("model_id", ""),
        "prompt_template_id": config.get("prompt_template", ""),
        "temperature": config.get("temperature", 0.0),
        "top_p": config.get("top_p", 1.0),
        "archetype_mixture_id": config.get("archetype_mixture_id", ""),
        "retrieval_mode": config.get("retrieval_mode", "none"),
        "clean_completion_rate": run_health.get("clean_completion_rate", 0.0),
        "weighted_js": micro.get("weighted_js_divergence", 0.0),
        "mean_abs_buy_rate_gap": micro.get("mean_absolute_buy_rate_gap", 0.0),
        "bubble_depth_gap": macro.get("bubble_depth_gap", 0.0),
        "bubble_incidence_gap": macro.get("bubble_incidence_gap", 0.0),
        "snowball_slope_error": macro.get("snowball_slope_error", 0.0),
        "terminal_holder_gap": macro.get("terminal_holder_gap", 0.0),
        "calibration_score": calibration.get("replication_score", 0.0),
        "passed_gate": calibration.get("passed_gate", False),
    }


def append_leaderboard_row(
    leaderboard_path: str | Path,
    row: dict[str, Any],
) -> None:
    """Appends a row to the leaderboard CSV."""
    path = Path(leaderboard_path)
    file_exists = path.exists()
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def load_leaderboard(leaderboard_path: str | Path) -> pd.DataFrame:
    """Loads leaderboard CSV sorted by calibration_score."""
    path = Path(leaderboard_path)
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "calibration_score" in df.columns:
        df = df.sort_values("calibration_score").reset_index(drop=True)
    return df
