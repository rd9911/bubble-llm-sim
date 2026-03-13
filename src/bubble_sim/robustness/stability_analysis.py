from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

METRIC_KEYS = [
    "weighted_js_divergence",
    "mean_absolute_buy_rate_gap",
    "bubble_depth_gap",
    "snowball_slope_error",
    "terminal_holder_gap",
    "fallback_use_rate",
]


def compute_metric_range(
    results: list[dict[str, Any]],
    metric_keys: list[str] | None = None,
) -> dict[str, dict[str, float]]:
    """Min/max/range across sweep configs per metric."""
    if metric_keys is None:
        metric_keys = METRIC_KEYS

    ranges: dict[str, dict[str, float]] = {}
    for key in metric_keys:
        vals = [r.get(key, 0.0) for r in results]
        arr = np.array(vals, dtype=float)
        ranges[key] = {
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "range": float(np.max(arr) - np.min(arr)),
        }
    return ranges


def compute_seed_variance(
    seed_results: list[dict[str, Any]],
    metric_keys: list[str] | None = None,
) -> dict[str, dict[str, float]]:
    """Mean/SD/CV/min/max across seeds per metric."""
    if metric_keys is None:
        metric_keys = METRIC_KEYS

    stats: dict[str, dict[str, float]] = {}
    for key in metric_keys:
        vals = [r.get(key, 0.0) for r in seed_results]
        arr = np.array(vals, dtype=float)
        mean = float(np.mean(arr))
        sd = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        cv = sd / mean if mean != 0 else 0.0
        stats[key] = {
            "mean": mean,
            "sd": sd,
            "cv": cv,
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
        }
    return stats


def _classify_range(metric_range: float, green: float, yellow: float) -> str:
    if metric_range <= green:
        return "green"
    if metric_range <= yellow:
        return "yellow"
    return "red"


def build_stability_scorecard(
    decoding_ranges: dict[str, dict[str, float]],
    prompt_ranges: dict[str, dict[str, float]],
    seed_stats: dict[str, dict[str, float]],
    thresholds: dict[str, dict[str, float]] | None = None,
) -> dict[str, dict[str, str]]:
    """Traffic-light stability scorecard per dimension."""
    if thresholds is None:
        thresholds = {
            "decoding": {"green": 0.05, "yellow": 0.15},
            "prompt": {"green": 0.05, "yellow": 0.15},
            "seed": {"green": 0.03, "yellow": 0.10},
        }

    card: dict[str, dict[str, str]] = {
        "decoding": {},
        "prompt": {},
        "seed": {},
    }

    dt = thresholds["decoding"]
    for key, vals in decoding_ranges.items():
        card["decoding"][key] = _classify_range(vals["range"], dt["green"], dt["yellow"])

    pt = thresholds["prompt"]
    for key, vals in prompt_ranges.items():
        card["prompt"][key] = _classify_range(vals["range"], pt["green"], pt["yellow"])

    st = thresholds["seed"]
    for key, vals in seed_stats.items():
        card["seed"][key] = _classify_range(vals["sd"], st["green"], st["yellow"])

    return card


def build_robustness_report(
    decoding_results: list[dict[str, Any]],
    prompt_results: list[dict[str, Any]],
    seed_results: list[dict[str, Any]],
    output_dir: str | Path,
) -> None:
    """Writes the full 6.1 robustness report bundle."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(decoding_results).to_csv(path / "decoding_sweep.csv", index=False)
    pd.DataFrame(prompt_results).to_csv(path / "prompt_sweep.csv", index=False)
    pd.DataFrame(seed_results).to_csv(path / "seed_variance.csv", index=False)

    dec_ranges = compute_metric_range(decoding_results)
    prompt_ranges = compute_metric_range(prompt_results)
    seed_stats = compute_seed_variance(seed_results)
    scorecard = build_stability_scorecard(dec_ranges, prompt_ranges, seed_stats)

    with open(path / "stability_scorecard.json", "w") as f:
        json.dump(scorecard, f, indent=2)

    md = _render_robustness_md(dec_ranges, prompt_ranges, seed_stats, scorecard)
    (path / "robustness_report.md").write_text(md)


def _render_robustness_md(
    dec_ranges: dict[str, dict[str, float]],
    prompt_ranges: dict[str, dict[str, float]],
    seed_stats: dict[str, dict[str, float]],
    scorecard: dict[str, dict[str, str]],
) -> str:
    lines = ["# Robustness Report", ""]

    for dim, label in [
        ("decoding", "Decoding Sweep"),
        ("prompt", "Prompt Variants"),
        ("seed", "Seed Variance"),
    ]:
        lines.append(f"## {label}")
        data = dec_ranges if dim == "decoding" else prompt_ranges if dim == "prompt" else seed_stats
        for key, vals in data.items():
            color = scorecard.get(dim, {}).get(key, "")
            emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(color, "⚪")
            if "sd" in vals:
                lines.append(f"- {key}: mean={vals['mean']:.4f} " f"sd={vals['sd']:.4f} {emoji}")
            else:
                lines.append(
                    f"- {key}: range={vals['range']:.4f} "
                    f"[{vals['min']:.4f}, {vals['max']:.4f}] {emoji}"
                )
        lines.append("")

    lines.append("")
    return "\n".join(lines)
