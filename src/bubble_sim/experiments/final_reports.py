from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def build_final_comparison_table(
    results: list[dict[str, Any]],
) -> pd.DataFrame:
    """Main results table — 5 systems × key metrics."""
    rows = []
    for r in results:
        rows.append(
            {
                "system": r.get("name", ""),
                "role": r.get("role", ""),
                "clean_completion_rate": r.get("clean_completion_rate", 0.0),
                "weighted_js": r.get("weighted_js_divergence", 0.0),
                "mabg": r.get("mean_absolute_buy_rate_gap", 0.0),
                "bubble_depth_gap": r.get("bubble_depth_gap", 0.0),
                "bubble_incidence_gap": r.get("bubble_incidence_gap", 0.0),
                "snowball_slope_error": r.get("snowball_slope_error", 0.0),
                "terminal_holder_gap": r.get("terminal_holder_gap", 0.0),
                "parse_failure_rate": r.get("parse_failure_rate", 0.0),
                "fallback_use_rate": r.get("fallback_use_rate", 0.0),
            }
        )
    return pd.DataFrame(rows)


def build_final_report_bundle(
    comparison_df: pd.DataFrame,
    robustness_df: pd.DataFrame,
    output_dir: str | Path,
    winner_name: str = "",
) -> None:
    """Writes the final results bundle to disk."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    comparison_df.to_csv(path / "final_comparison_table.csv", index=False)
    robustness_df.to_csv(path / "seed_robustness_table.csv", index=False)

    md_lines = [
        "# Final Results Report",
        "",
    ]
    if winner_name:
        md_lines.append(f"**Selected winner**: {winner_name}")
        md_lines.append("")

    md_lines.append("## Comparison Table")
    md_lines.append("")
    md_lines.append(_df_to_md(comparison_df))
    md_lines.append("")
    md_lines.append("## Seed Robustness")
    md_lines.append("")
    md_lines.append(_df_to_md(robustness_df))
    md_lines.append("")

    (path / "final_report.md").write_text("\n".join(md_lines))


def _df_to_md(df: pd.DataFrame) -> str:
    """Manual Markdown table renderer."""
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join([header, sep] + rows)
