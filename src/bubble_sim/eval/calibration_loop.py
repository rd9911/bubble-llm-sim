from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Any

import pandas as pd

from bubble_sim.eval.replication_targets import (
    ReplicationTarget,
    compute_replication_score,
)


@dataclass
class CalibrationConfig:
    """One point in the Option-A lever space."""

    prompt_template: str = "bubble_prompt_v1_minimal"
    temperature: float = 0.7
    top_p: float = 1.0
    archetype_mixture: dict[str, float] = field(default_factory=lambda: {"qre": 0.5, "abee": 0.5})
    label: str = ""

    def __post_init__(self) -> None:
        if not self.label:
            mix = "_".join(f"{k}{v}" for k, v in self.archetype_mixture.items())
            self.label = (
                f"{self.prompt_template}" f"_t{self.temperature}" f"_p{self.top_p}" f"_{mix}"
            )


def build_config_grid(
    prompt_templates: list[str] | None = None,
    temperatures: list[float] | None = None,
    top_ps: list[float] | None = None,
    archetype_mixtures: list[dict[str, float]] | None = None,
) -> list[CalibrationConfig]:
    """Generates CalibrationConfig list from provided ranges."""
    if prompt_templates is None:
        prompt_templates = ["bubble_prompt_v1_minimal"]
    if temperatures is None:
        temperatures = [0.7]
    if top_ps is None:
        top_ps = [1.0]
    if archetype_mixtures is None:
        archetype_mixtures = [{"qre": 0.5, "abee": 0.5}]

    configs = []
    for pt, temp, tp, mix in product(prompt_templates, temperatures, top_ps, archetype_mixtures):
        configs.append(
            CalibrationConfig(
                prompt_template=pt,
                temperature=temp,
                top_p=tp,
                archetype_mixture=mix,
            )
        )
    return configs


def run_replication_calibration(
    config_grid: list[CalibrationConfig],
    agent_metrics_per_config: list[dict[str, Any]],
    targets: ReplicationTarget,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Scores each config against replication targets, returns leaderboard."""
    rows = []
    for cfg, metrics in zip(config_grid, agent_metrics_per_config):
        result = compute_replication_score(metrics, targets, weights)
        row = {
            "label": cfg.label,
            "prompt_template": cfg.prompt_template,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "replication_score": result["replication_score"],
        }
        row.update(result["components"])
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sort_values("replication_score").reset_index(drop=True)
    return df


def select_best_replication_config(
    leaderboard: pd.DataFrame,
) -> str:
    """Returns the label of the best (lowest score) config."""
    if leaderboard.empty:
        return ""
    return str(leaderboard.iloc[0]["label"])
