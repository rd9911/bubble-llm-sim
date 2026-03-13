from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_SEEDS: tuple[int, ...] = (42, 43, 44, 45, 46)


@dataclass(frozen=True)
class FinalSystemConfig:
    """One system in the final comparison set."""

    name: str
    role: str  # control | baseline | calibrated
    config_ref: str = ""
    prompt_template_id: str = ""
    is_deterministic: bool = False


@dataclass(frozen=True)
class FinalRun:
    """One scheduled final run."""

    run_name: str
    system: FinalSystemConfig
    split_name: str
    seed: int
    episodes: int = 500


def build_final_run_matrix(
    systems: list[FinalSystemConfig],
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
    heldout_episodes: int = 500,
    random_episodes: int = 500,
) -> list[FinalRun]:
    """Builds the full final run matrix across splits and seeds."""
    runs: list[FinalRun] = []

    for sys in systems:
        seed_list = (seeds[0],) if sys.is_deterministic else seeds

        # Held-out treatment split (main results)
        for s in seed_list:
            runs.append(
                FinalRun(
                    run_name=f"F_{sys.name}_heldout_s{s}",
                    system=sys,
                    split_name="heldout_treatment_v1",
                    seed=s,
                    episodes=heldout_episodes,
                )
            )

        # Random episode split (supporting results) — only for LLM systems
        if sys.role in ("baseline", "calibrated"):
            for s in seed_list:
                runs.append(
                    FinalRun(
                        run_name=f"F_{sys.name}_random_s{s}",
                        system=sys,
                        split_name="random_episode_v1",
                        seed=s,
                        episodes=random_episodes,
                    )
                )

    return runs


def select_winner(
    results: list[dict[str, Any]],
    control_names: list[str],
    baseline_name: str,
    score_key: str = "calibration_score",
) -> dict[str, Any] | None:
    """Selects winner: must pass gate, beat controls, beat baseline on held-out."""
    candidates = [r for r in results if r.get("role") == "calibrated"]
    if not candidates:
        return None

    for c in candidates:
        # Must pass operational gate
        if not c.get("passed_gate", False):
            continue

        # Must beat all controls
        beats_controls = all(
            c.get(score_key, 99) < _get_score(results, cn, score_key) for cn in control_names
        )
        if not beats_controls:
            continue

        # Must beat baseline on held-out
        baseline_score = _get_score(results, baseline_name, score_key)
        if c.get(score_key, 99) < baseline_score:
            return c

    return None


def _get_score(results: list[dict[str, Any]], name: str, key: str) -> float:
    for r in results:
        if r.get("name") == name:
            return r.get(key, float("inf"))
    return float("inf")
