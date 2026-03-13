from __future__ import annotations

from itertools import product
from typing import Any

from bubble_sim.experiments.calibration_configs import (
    ARCHETYPE_BUNDLES,
    MIXTURE_PRESETS,
    CalibrationRunConfig,
)


def build_sampling_sweep(
    parent_baseline: str,
    prompt_template_id: str,
    temperatures: list[float] | None = None,
    top_ps: list[float] | None = None,
) -> list[CalibrationRunConfig]:
    """Stage 1: temperature × top_p grid."""
    if temperatures is None:
        temperatures = [0.0, 0.1, 0.2, 0.4, 0.7]
    if top_ps is None:
        top_ps = [0.8, 0.9, 1.0]

    configs = []
    for temp, tp in product(temperatures, top_ps):
        configs.append(
            CalibrationRunConfig(
                name=f"C1_t{temp}_p{tp}_{prompt_template_id}",
                stage="S1_sampling",
                parent_baseline=parent_baseline,
                prompt_template_id=prompt_template_id,
                temperature=temp,
                top_p=tp,
            )
        )
    return configs


def build_prompt_sweep(
    parent_baseline: str,
    temperature: float,
    top_p: float,
    templates: list[str] | None = None,
) -> list[CalibrationRunConfig]:
    """Stage 2: prompt templates at best sampling."""
    if templates is None:
        templates = [
            "bubble_prompt_v1_minimal",
            "bubble_prompt_v2_archetype",
            "bubble_prompt_v3_strict_json",
            "bubble_prompt_v4_ablation_neutral",
        ]
    return [
        CalibrationRunConfig(
            name=f"C2_{t}",
            stage="S2_prompt",
            parent_baseline=parent_baseline,
            prompt_template_id=t,
            temperature=temperature,
            top_p=top_p,
        )
        for t in templates
    ]


def build_archetype_sweep(
    parent_baseline: str,
    prompt_template_id: str,
    temperature: float,
    top_p: float,
    bundle_ids: list[str] | None = None,
) -> list[CalibrationRunConfig]:
    """Stage 3: archetype bundles."""
    if bundle_ids is None:
        bundle_ids = list(ARCHETYPE_BUNDLES.keys())
    return [
        CalibrationRunConfig(
            name=f"C3_{bid}",
            stage="S3_archetype",
            parent_baseline=parent_baseline,
            prompt_template_id=prompt_template_id,
            temperature=temperature,
            top_p=top_p,
            archetype_bundle_id=bid,
        )
        for bid in bundle_ids
    ]


def build_mixture_sweep(
    parent_baseline: str,
    prompt_template_id: str,
    temperature: float,
    top_p: float,
    archetype_bundle_id: str,
    mixture_ids: list[str] | None = None,
) -> list[CalibrationRunConfig]:
    """Stage 4: mixture presets."""
    if mixture_ids is None:
        mixture_ids = list(MIXTURE_PRESETS.keys())
    return [
        CalibrationRunConfig(
            name=f"C4_{mid}",
            stage="S4_mixture",
            parent_baseline=parent_baseline,
            prompt_template_id=prompt_template_id,
            temperature=temperature,
            top_p=top_p,
            archetype_bundle_id=archetype_bundle_id,
            mixture_id=mid,
        )
        for mid in mixture_ids
    ]


def build_retrieval_sweep(
    parent_baseline: str,
    prompt_template_id: str,
    temperature: float,
    top_p: float,
    archetype_bundle_id: str,
    mixture_id: str,
) -> list[CalibrationRunConfig]:
    """Stage 5: retrieval variants (small first pass)."""
    variants = [
        ("R0_none", 0),
        ("R2_state_history", 3),
        ("R2_state_history", 5),
    ]
    return [
        CalibrationRunConfig(
            name=f"C5_{rid}_k{k}",
            stage="S5_retrieval",
            parent_baseline=parent_baseline,
            prompt_template_id=prompt_template_id,
            temperature=temperature,
            top_p=top_p,
            archetype_bundle_id=archetype_bundle_id,
            mixture_id=mixture_id,
            retrieval_id=rid,
            retrieval_k=k,
        )
        for rid, k in variants
    ]


def promote_from_stage(
    results: list[dict[str, Any]],
    top_n: int = 3,
    score_key: str = "calibration_score",
) -> list[dict[str, Any]]:
    """Keeps top-N candidates by ascending calibration score."""
    sorted_results = sorted(results, key=lambda r: r.get(score_key, float("inf")))
    return sorted_results[:top_n]


def check_stopping_criteria(
    prev_best_score: float,
    current_best_score: float,
    min_improvement: float = 0.03,
) -> bool:
    """Returns True if calibration should stop (no meaningful improvement)."""
    if prev_best_score == 0.0:
        return False
    improvement = (prev_best_score - current_best_score) / prev_best_score
    return improvement < min_improvement
