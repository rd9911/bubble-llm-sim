from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ReplicationTarget:
    """Canonical Bubble Game empirical benchmarks from the paper."""

    # Buy-rate curves keyed by (cap_type, price_index)
    buy_rate_by_state: dict[tuple[str, int], float] = field(default_factory=dict)
    # Snowball-effect slope (higher = stronger snowball)
    snowball_slope: float = 0.0
    # Capped vs uncapped treatment gap in mean buy rate
    treatment_gap: float = 0.0
    # Mean bubble depth (avg chain length before decline)
    mean_bubble_depth: float = 0.0
    # Terminal-holder frequency
    terminal_holder_freq: float = 0.0


def default_bubble_game_targets() -> ReplicationTarget:
    """Returns placeholder targets from the Bubble Game paper."""
    return ReplicationTarget(
        buy_rate_by_state={
            ("uncapped", 0): 0.90,
            ("uncapped", 1): 0.70,
            ("uncapped", 2): 0.45,
            ("uncapped", 3): 0.25,
            ("capped", 0): 0.75,
            ("capped", 1): 0.50,
            ("capped", 2): 0.25,
            ("capped", 3): 0.10,
        },
        snowball_slope=0.20,
        treatment_gap=0.15,
        mean_bubble_depth=2.5,
        terminal_holder_freq=0.30,
    )


def compute_replication_score(
    agent_metrics: dict[str, Any],
    targets: ReplicationTarget,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Weighted composite replication score. Lower is better."""
    if weights is None:
        weights = {
            "micro_js": 1.0,
            "mabg": 1.0,
            "bubble_depth_gap": 1.0,
            "snowball_slope_error": 1.0,
            "treatment_gap_error": 1.0,
        }

    micro_js = agent_metrics.get("weighted_js_divergence", 0.0)
    mabg = agent_metrics.get("mean_absolute_buy_rate_gap", 0.0)

    bubble_depth_gap = abs(agent_metrics.get("mean_bubble_depth", 0.0) - targets.mean_bubble_depth)
    snowball_err = abs(agent_metrics.get("snowball_slope", 0.0) - targets.snowball_slope)
    treatment_err = abs(agent_metrics.get("treatment_gap", 0.0) - targets.treatment_gap)

    components = {
        "micro_js": micro_js,
        "mabg": mabg,
        "bubble_depth_gap": bubble_depth_gap,
        "snowball_slope_error": snowball_err,
        "treatment_gap_error": treatment_err,
    }

    score = sum(weights.get(k, 0.0) * v for k, v in components.items())

    return {
        "replication_score": score,
        "components": components,
        "weights": weights,
    }
