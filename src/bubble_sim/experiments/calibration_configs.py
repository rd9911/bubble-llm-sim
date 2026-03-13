from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CalibrationRunConfig:
    """One point in the calibration sweep space."""

    name: str
    stage: str  # S1_sampling | S2_prompt | S3_archetype | S4_mixture | S5_retrieval | S6_heldout
    parent_baseline: str = ""
    prompt_template_id: str = "bubble_prompt_v2_archetype"
    temperature: float = 0.2
    top_p: float = 1.0
    max_output_tokens: int = 120
    archetype_bundle_id: str = ""
    mixture_id: str = ""
    retrieval_id: str = "R0_none"
    retrieval_k: int = 0
    episodes_per_treatment: int = 100
    split_name: str = "val"
    treatments: tuple[str, ...] = ("capped", "uncapped")
    price_path: tuple[int, ...] = (1, 10, 100, 1000, 10000)


# --- Archetype bundle presets ---

ARCHETYPE_BUNDLES: dict[str, dict[str, Any]] = {
    "archset_v1_conservative": {
        "qre_like": {"noise_level": 0.1, "risk_attitude": "low"},
        "bounded_step": {"depth_of_reasoning": 3, "risk_attitude": "low"},
        "abee_like": {"analogy_class_tendency": "low", "risk_attitude": "low"},
        "mixed": {"noise_level": 0.3, "depth_of_reasoning": 2},
    },
    "archset_v2_balanced": {
        "qre_like": {"noise_level": 0.3, "risk_attitude": "medium"},
        "bounded_step": {"depth_of_reasoning": 2, "risk_attitude": "medium"},
        "abee_like": {"analogy_class_tendency": "medium", "risk_attitude": "medium"},
        "mixed": {"noise_level": 0.5, "depth_of_reasoning": 1},
    },
    "archset_v3_speculative": {
        "qre_like": {"noise_level": 0.5, "risk_attitude": "high"},
        "bounded_step": {"depth_of_reasoning": 1, "risk_attitude": "high"},
        "abee_like": {"analogy_class_tendency": "high", "risk_attitude": "high"},
        "mixed": {"noise_level": 0.7, "depth_of_reasoning": 0},
    },
    "archset_v4_high_noise": {
        "qre_like": {"noise_level": 0.7, "risk_attitude": "medium"},
        "bounded_step": {"depth_of_reasoning": 1, "risk_attitude": "medium"},
        "abee_like": {"analogy_class_tendency": "medium", "risk_attitude": "high"},
        "mixed": {"noise_level": 0.7, "depth_of_reasoning": 1},
    },
}

# --- Mixture presets ---

MIXTURE_PRESETS: dict[str, dict[str, float]] = {
    "M1_equal": {
        "qre_like": 0.25,
        "bounded_step": 0.25,
        "abee_like": 0.25,
        "mixed": 0.25,
    },
    "M2_noisy_heavy": {
        "qre_like": 0.40,
        "bounded_step": 0.20,
        "abee_like": 0.20,
        "mixed": 0.20,
    },
    "M3_bounded_heavy": {
        "qre_like": 0.20,
        "bounded_step": 0.40,
        "abee_like": 0.20,
        "mixed": 0.20,
    },
    "M4_analogy_heavy": {
        "qre_like": 0.20,
        "bounded_step": 0.20,
        "abee_like": 0.40,
        "mixed": 0.20,
    },
    "M5_mixed_heavy": {
        "qre_like": 0.20,
        "bounded_step": 0.20,
        "abee_like": 0.20,
        "mixed": 0.40,
    },
}
