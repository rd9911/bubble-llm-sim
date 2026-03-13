from __future__ import annotations

from typing import Any


def _classify(value: float, green: float, yellow: float, lower_better: bool = True) -> str:
    """Assign green/yellow/red based on thresholds."""
    if lower_better:
        if value <= green:
            return "green"
        if value <= yellow:
            return "yellow"
        return "red"
    else:
        if value >= green:
            return "green"
        if value >= yellow:
            return "yellow"
        return "red"


def build_scorecard(
    run_health: dict[str, Any],
    micro: dict[str, Any],
    macro: dict[str, Any],
    thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Traffic-light scorecard: green/yellow/red per category."""
    if thresholds is None:
        thresholds = {
            "run_health": {
                "clean_completion_rate": {"green": 0.98, "yellow": 0.95},
                "fallback_use_rate": {"green": 0.01, "yellow": 0.02},
            },
            "micro": {
                "weighted_js": {"green": 0.05, "yellow": 0.15},
                "mabg": {"green": 0.05, "yellow": 0.15},
            },
            "macro": {
                "bubble_depth_gap": {"green": 0.5, "yellow": 1.5},
                "snowball_slope_error": {"green": 0.05, "yellow": 0.15},
            },
        }

    card: dict[str, Any] = {}

    # Run health
    rh = thresholds["run_health"]
    card["run_health"] = {
        "clean_completion_rate": _classify(
            run_health.get("clean_completion_rate", 0.0),
            rh["clean_completion_rate"]["green"],
            rh["clean_completion_rate"]["yellow"],
            lower_better=False,
        ),
        "fallback_use_rate": _classify(
            run_health.get("fallback_use_rate", 1.0),
            rh["fallback_use_rate"]["green"],
            rh["fallback_use_rate"]["yellow"],
        ),
    }

    # Micro fidelity
    mt = thresholds["micro"]
    card["micro"] = {
        "weighted_js": _classify(
            micro.get("weighted_js_divergence", 1.0),
            mt["weighted_js"]["green"],
            mt["weighted_js"]["yellow"],
        ),
        "mabg": _classify(
            micro.get("mean_absolute_buy_rate_gap", 1.0),
            mt["mabg"]["green"],
            mt["mabg"]["yellow"],
        ),
    }

    # Macro fidelity
    ma = thresholds["macro"]
    card["macro"] = {
        "bubble_depth_gap": _classify(
            abs(macro.get("bubble_depth_gap", 99.0)),
            ma["bubble_depth_gap"]["green"],
            ma["bubble_depth_gap"]["yellow"],
        ),
        "snowball_slope_error": _classify(
            abs(macro.get("snowball_slope_error", 99.0)),
            ma["snowball_slope_error"]["green"],
            ma["snowball_slope_error"]["yellow"],
        ),
    }

    return card
