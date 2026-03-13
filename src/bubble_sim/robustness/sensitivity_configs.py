from __future__ import annotations

from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class SweepConfig:
    """One config point in a sensitivity sweep."""

    name: str
    sweep_type: str  # decoding | prompt | seed
    system_name: str = ""
    prompt_template_id: str = ""
    temperature: float = 0.2
    top_p: float = 1.0
    seed: int = 42
    episodes: int = 300


def build_decoding_sweep(
    system_name: str,
    prompt_template_id: str,
    temperatures: list[float] | None = None,
    top_ps: list[float] | None = None,
    episodes: int = 300,
) -> list[SweepConfig]:
    """6.1.1: temperature × top_p grid."""
    if temperatures is None:
        temperatures = [0.0, 0.1, 0.2, 0.4, 0.7]
    if top_ps is None:
        top_ps = [0.8, 0.9, 1.0]

    return [
        SweepConfig(
            name=f"dec_{system_name}_t{t}_p{p}",
            sweep_type="decoding",
            system_name=system_name,
            prompt_template_id=prompt_template_id,
            temperature=t,
            top_p=p,
            episodes=episodes,
        )
        for t, p in product(temperatures, top_ps)
    ]


def build_prompt_variant_sweep(
    system_name: str,
    temperature: float,
    top_p: float,
    extra_variants: list[str] | None = None,
    episodes: int = 300,
) -> list[SweepConfig]:
    """6.1.2: canonical families + winner perturbations."""
    templates = [
        "bubble_prompt_v1_minimal",
        "bubble_prompt_v2_archetype",
        "bubble_prompt_v3_strict_json",
        "bubble_prompt_v4_ablation_neutral",
    ]
    if extra_variants:
        templates.extend(extra_variants)

    return [
        SweepConfig(
            name=f"prompt_{system_name}_{t}",
            sweep_type="prompt",
            system_name=system_name,
            prompt_template_id=t,
            temperature=temperature,
            top_p=top_p,
            episodes=episodes,
        )
        for t in templates
    ]


def build_seed_sweep(
    system_name: str,
    prompt_template_id: str,
    temperature: float,
    top_p: float,
    seeds: list[int] | None = None,
    episodes: int = 300,
) -> list[SweepConfig]:
    """6.1.3: multiple seeds for variance estimation."""
    if seeds is None:
        seeds = list(range(42, 52))  # 42–51

    return [
        SweepConfig(
            name=f"seed_{system_name}_s{s}",
            sweep_type="seed",
            system_name=system_name,
            prompt_template_id=prompt_template_id,
            temperature=temperature,
            top_p=top_p,
            seed=s,
            episodes=episodes,
        )
        for s in seeds
    ]
