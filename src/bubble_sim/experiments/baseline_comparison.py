from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def build_baseline_comparison_table(
    results: list[dict[str, Any]],
) -> pd.DataFrame:
    """Builds the central baseline comparison table."""
    rows = []
    for r in results:
        rows.append(
            {
                "baseline": r.get("name", ""),
                "clean_completion_rate": r.get("clean_completion_rate", 0.0),
                "weighted_js": r.get("weighted_js_divergence", 0.0),
                "mabg": r.get("mean_absolute_buy_rate_gap", 0.0),
                "bubble_depth_gap": r.get("bubble_depth_gap", 0.0),
                "bubble_incidence_gap": r.get("bubble_incidence_gap", 0.0),
                "snowball_slope_error": r.get("snowball_slope_error", 0.0),
                "terminal_holder_gap": r.get("terminal_holder_gap", 0.0),
                "calibration_score": r.get("calibration_score", 0.0),
            }
        )
    return pd.DataFrame(rows)


def export_comparison_table(
    df: pd.DataFrame,
    output_dir: str | Path,
) -> None:
    """Exports comparison table as CSV and Markdown."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    df.to_csv(path / "baseline_comparison.csv", index=False)

    # Manual Markdown table to avoid tabulate dependency
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    md = "\n".join([header, sep] + rows) + "\n"
    (path / "baseline_comparison.md").write_text(md)
