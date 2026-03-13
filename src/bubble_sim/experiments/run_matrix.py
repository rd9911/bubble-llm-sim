from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bubble_sim.experiments.baseline_configs import BaselineConfig


@dataclass
class BaselineRun:
    """One scheduled run in the experiment matrix."""

    run_name: str
    config: BaselineConfig
    stage: str  # "A_sanity" | "B_dev" | "C_heldout"
    split_name: str


def build_run_matrix(
    configs: list[BaselineConfig],
) -> list[BaselineRun]:
    """Builds the full ordered run matrix (Stage A → B → C)."""
    runs: list[BaselineRun] = []

    for cfg in configs:
        if cfg.family == "sanity":
            runs.append(
                BaselineRun(
                    run_name=f"{cfg.name}_random_episode_v1",
                    config=cfg,
                    stage="A_sanity",
                    split_name="random_episode_v1",
                )
            )
        elif cfg.family == "llm":
            # Stage B — development split
            runs.append(
                BaselineRun(
                    run_name=f"{cfg.name}_random_episode_v1",
                    config=cfg,
                    stage="B_dev",
                    split_name="random_episode_v1",
                )
            )
            # Stage C — held-out treatment
            runs.append(
                BaselineRun(
                    run_name=f"{cfg.name}_heldout_treatment_v1",
                    config=cfg,
                    stage="C_heldout",
                    split_name="heldout_treatment_v1",
                )
            )

    # Sort by stage order
    order = {"A_sanity": 0, "B_dev": 1, "C_heldout": 2}
    runs.sort(key=lambda r: order.get(r.stage, 99))
    return runs


def filter_promoted_runs(
    run_results: list[dict[str, Any]],
    min_clean_completion: float = 0.95,
    max_fallback_rate: float = 0.02,
) -> list[str]:
    """Returns names of runs that pass operational + behavioral gates."""
    promoted = []
    for r in run_results:
        ccr = r.get("clean_completion_rate", 0.0)
        fur = r.get("fallback_use_rate", 1.0)
        if ccr >= min_clean_completion and fur <= max_fallback_rate:
            promoted.append(r["run_name"])
    return promoted
