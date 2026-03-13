from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd


def build_calibration_leaderboard_row(
    candidate_id: str,
    stage: str,
    parent_baseline: str,
    config: dict[str, Any],
    run_health: dict[str, Any],
    micro: dict[str, Any],
    macro: dict[str, Any],
    calibration_score: float,
    promoted: bool = False,
) -> dict[str, Any]:
    """Extended leaderboard row for calibration runs."""
    return {
        "candidate_id": candidate_id,
        "stage": stage,
        "parent_baseline": parent_baseline,
        "prompt_template_id": config.get("prompt_template_id", ""),
        "temperature": config.get("temperature", 0.0),
        "top_p": config.get("top_p", 1.0),
        "archetype_bundle_id": config.get("archetype_bundle_id", ""),
        "mixture_id": config.get("mixture_id", ""),
        "retrieval_id": config.get("retrieval_id", "R0_none"),
        "weighted_js": micro.get("weighted_js_divergence", 0.0),
        "mabg": micro.get("mean_absolute_buy_rate_gap", 0.0),
        "bubble_depth_gap": macro.get("bubble_depth_gap", 0.0),
        "snowball_slope_error": macro.get("snowball_slope_error", 0.0),
        "terminal_holder_gap": macro.get("terminal_holder_gap", 0.0),
        "parse_failure_rate": run_health.get("parse_failure_rate", 0.0),
        "fallback_use_rate": run_health.get("fallback_use_rate", 0.0),
        "calibration_score": calibration_score,
        "promoted": promoted,
    }


def append_calibration_row(
    leaderboard_path: str | Path,
    row: dict[str, Any],
) -> None:
    """Appends a calibration row to the CSV."""
    path = Path(leaderboard_path)
    file_exists = path.exists()
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def load_calibration_leaderboard(
    leaderboard_path: str | Path,
) -> pd.DataFrame:
    """Loads calibration leaderboard sorted by calibration_score."""
    path = Path(leaderboard_path)
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "calibration_score" in df.columns:
        df = df.sort_values("calibration_score").reset_index(drop=True)
    return df
