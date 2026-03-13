from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BaselineConfig:
    """One baseline experiment configuration."""

    name: str
    family: str  # "sanity" or "llm"
    prompt_template_id: str = ""
    temperature: float = 0.2
    top_p: float = 1.0
    max_output_tokens: int = 120
    max_retries: int = 2
    fallback_action: str = "no_buy"
    archetype_mixture: dict[str, float] = field(default_factory=dict)
    treatments: tuple[str, ...] = ("capped", "uncapped")
    price_path: tuple[int, ...] = (1, 10, 100, 1000, 10000)
    episodes_per_treatment: int = 100
    split_name: str = "random_episode_v1"
    # For sanity policies only
    policy_type: str = ""  # always_buy | always_no_buy | threshold
    threshold: int | None = None


def sanity_baseline_configs() -> list[BaselineConfig]:
    """S1–S4 sanity controls."""
    return [
        BaselineConfig(
            name="S1_always_no_buy",
            family="sanity",
            policy_type="always_no_buy",
        ),
        BaselineConfig(
            name="S2_always_buy",
            family="sanity",
            policy_type="always_buy",
        ),
        BaselineConfig(
            name="S3_threshold_10",
            family="sanity",
            policy_type="threshold",
            threshold=10,
        ),
        BaselineConfig(
            name="S4_threshold_100",
            family="sanity",
            policy_type="threshold",
            threshold=100,
        ),
    ]


_DEFAULT_MIXTURE: dict[str, float] = {
    "A1_qre_low_noise": 1 / 6,
    "A2_qre_high_noise": 1 / 6,
    "A3_bounded_step_1": 1 / 6,
    "A4_bounded_step_2": 1 / 6,
    "A5_abee_like": 1 / 6,
    "A6_mixed": 1 / 6,
}


def llm_baseline_configs() -> list[BaselineConfig]:
    """B1–B3 LLM baselines."""
    return [
        BaselineConfig(
            name="B1_minimal_prompt",
            family="llm",
            prompt_template_id="bubble_prompt_v1_minimal",
        ),
        BaselineConfig(
            name="B2_archetype_prompt",
            family="llm",
            prompt_template_id="bubble_prompt_v2_archetype",
            archetype_mixture=_DEFAULT_MIXTURE,
        ),
        BaselineConfig(
            name="B3_strict_json_prompt",
            family="llm",
            prompt_template_id="bubble_prompt_v3_strict_json",
            archetype_mixture=_DEFAULT_MIXTURE,
        ),
    ]


def all_baseline_configs() -> list[BaselineConfig]:
    """All Phase 5.1 baselines in recommended order."""
    return sanity_baseline_configs() + llm_baseline_configs()
