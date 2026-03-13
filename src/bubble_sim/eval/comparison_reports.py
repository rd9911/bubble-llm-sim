from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def build_replication_leaderboard(
    leaderboard_df: pd.DataFrame,
    output_dir: str | Path,
) -> None:
    """Writes a replication leaderboard to disk."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    leaderboard_df.to_parquet(path / "replication_leaderboard.parquet", index=False)
    leaderboard_df.to_csv(path / "replication_leaderboard.csv", index=False)


def build_replication_vs_divergence_report(
    replication_result: dict[str, Any],
    divergence_result: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Any]:
    """Side-by-side comparison of replication vs exploration."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    report = {
        "replication": replication_result,
        "divergence": divergence_result,
    }

    with open(path / "comparison_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return report
