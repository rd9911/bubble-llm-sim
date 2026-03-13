from __future__ import annotations

from typing import Any

from bubble_sim.eval.replication_targets import (
    ReplicationTarget,
    compute_replication_score,
)


def compute_divergence_profile(
    agent_metrics: dict[str, Any],
    reference_metrics: dict[str, Any],
) -> dict[str, float]:
    """Structured deviation vector between two metric sets."""
    keys = [
        "mean_bubble_depth",
        "snowball_slope",
        "treatment_gap",
        "weighted_js_divergence",
        "mean_absolute_buy_rate_gap",
    ]
    profile: dict[str, float] = {}
    for k in keys:
        a = agent_metrics.get(k, 0.0)
        r = reference_metrics.get(k, 0.0)
        profile[f"{k}_shift"] = a - r
    return profile


def run_sample_divergence_study(
    baseline_metrics: dict[str, Any],
    alternative_metrics: dict[str, Any],
    targets: ReplicationTarget,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Compares alternative-sample metrics against the replication baseline and human targets."""
    # Score baseline against targets
    baseline_score = compute_replication_score(baseline_metrics, targets, weights)
    # Score alternative against targets
    alt_score = compute_replication_score(alternative_metrics, targets, weights)
    # Compute structured divergence from baseline
    divergence_from_baseline = compute_divergence_profile(alternative_metrics, baseline_metrics)

    return {
        "baseline_replication_score": baseline_score["replication_score"],
        "alternative_replication_score": alt_score["replication_score"],
        "divergence_from_baseline": divergence_from_baseline,
        "baseline_components": baseline_score["components"],
        "alternative_components": alt_score["components"],
    }
