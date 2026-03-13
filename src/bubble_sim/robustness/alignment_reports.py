from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def build_fidelity_comparison(
    regime_results: list[dict[str, Any]],
) -> pd.DataFrame:
    """Side-by-side capacity + micro + macro comparison."""
    rows = []
    for r in regime_results:
        rows.append(
            {
                "regime": r.get("regime", ""),
                "completion_rate": r.get("completion_rate", 0.0),
                "refusal_rate": r.get("refusal_rate", 0.0),
                "schema_violation_rate": r.get("schema_violation_rate", 0.0),
                "weighted_js": r.get("weighted_js_divergence", 0.0),
                "mabg": r.get("mean_absolute_buy_rate_gap", 0.0),
                "bubble_depth_gap": r.get("bubble_depth_gap", 0.0),
                "snowball_slope_error": r.get("snowball_slope_error", 0.0),
                "terminal_holder_gap": r.get("terminal_holder_gap", 0.0),
            }
        )
    return pd.DataFrame(rows)


def build_alignment_report_bundle(
    capacity_df: pd.DataFrame,
    violation_df: pd.DataFrame,
    fidelity_df: pd.DataFrame,
    output_dir: str | Path,
) -> None:
    """Writes the full 6.2 alignment regime report bundle."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    capacity_df.to_csv(path / "capacity_benchmark.csv", index=False)
    violation_df.to_csv(path / "refusal_violation_table.csv", index=False)
    fidelity_df.to_csv(path / "fidelity_comparison.csv", index=False)

    scorecard = _build_regime_scorecard(fidelity_df)
    with open(path / "regime_scorecard.json", "w") as f:
        json.dump(scorecard, f, indent=2)

    md = _render_alignment_md(capacity_df, fidelity_df, scorecard)
    (path / "alignment_tradeoff_report.md").write_text(md)


def _build_regime_scorecard(
    fidelity_df: pd.DataFrame,
) -> dict[str, Any]:
    """Simple best-regime-per-metric scorecard."""
    scorecard: dict[str, Any] = {}
    for col in fidelity_df.columns:
        if col == "regime":
            continue
        if col in ("completion_rate",):
            best_idx = fidelity_df[col].idxmax()
        else:
            best_idx = fidelity_df[col].idxmin()
        if best_idx is not None:
            scorecard[col] = str(fidelity_df.loc[best_idx, "regime"])
    return scorecard


def _render_alignment_md(
    capacity_df: pd.DataFrame,
    fidelity_df: pd.DataFrame,
    scorecard: dict[str, Any],
) -> str:
    lines = [
        "# Alignment Regime Trade-off Report",
        "",
        "## Capacity Benchmark",
        "",
        _df_to_md(capacity_df),
        "",
        "## Fidelity Comparison",
        "",
        _df_to_md(fidelity_df),
        "",
        "## Best Regime per Metric",
        "",
    ]
    for metric, regime in scorecard.items():
        lines.append(f"- **{metric}**: {regime}")
    lines.append("")
    return "\n".join(lines)


def _df_to_md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join([header, sep] + rows)
