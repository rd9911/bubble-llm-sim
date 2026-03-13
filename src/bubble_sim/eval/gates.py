from __future__ import annotations

from typing import Any


def evaluate_promotion_gates(
    run_health: dict[str, Any],
    micro: dict[str, Any],
    macro: dict[str, Any],
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """4-gate promotion system for candidate configurations."""
    if thresholds is None:
        thresholds = {
            "min_clean_completion_rate": 0.95,
            "max_fallback_use_rate": 0.02,
            "max_weighted_js": 0.3,
            "max_mabg": 0.25,
            "max_bubble_depth_gap": 2.0,
            "max_snowball_slope_error": 0.3,
        }

    # Gate 1 — Operational reliability
    ccr = run_health.get("clean_completion_rate", 0.0)
    fur = run_health.get("fallback_use_rate", 1.0)
    gate1 = (
        ccr >= thresholds["min_clean_completion_rate"]
        and fur <= thresholds["max_fallback_use_rate"]
    )

    # Gate 2 — Micro fidelity
    wjs = micro.get("weighted_js_divergence", 1.0)
    mabg = micro.get("mean_absolute_buy_rate_gap", 1.0)
    gate2 = wjs <= thresholds["max_weighted_js"] and mabg <= thresholds["max_mabg"]

    # Gate 3 — Macro fidelity
    bdg = abs(macro.get("bubble_depth_gap", 99.0))
    sse = abs(macro.get("snowball_slope_error", 99.0))
    gate3 = (
        bdg <= thresholds["max_bubble_depth_gap"] and sse <= thresholds["max_snowball_slope_error"]
    )

    # Gate 4 — Held-out stability (pass-through if not evaluated)
    gate4 = macro.get("held_out_stable", True)

    return {
        "gate1_operational": gate1,
        "gate2_micro": gate2,
        "gate3_macro": gate3,
        "gate4_heldout": gate4,
        "passed_gate": gate1 and gate2 and gate3 and gate4,
        "details": {
            "clean_completion_rate": ccr,
            "fallback_use_rate": fur,
            "weighted_js": wjs,
            "mabg": mabg,
            "bubble_depth_gap": bdg,
            "snowball_slope_error": sse,
        },
    }
