from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class AlignmentRegime:
    """One model alignment variant."""

    name: str
    model_id: str
    alignment_level: str  # aligned | less_aligned | base


def build_capacity_benchmark(
    results: list[dict[str, Any]],
) -> pd.DataFrame:
    """Stage A capacity benchmark: completion, refusal, violation rates."""
    rows = []
    for r in results:
        rows.append(
            {
                "regime": r.get("regime", ""),
                "completion_rate": r.get("completion_rate", 0.0),
                "refusal_rate": r.get("refusal_rate", 0.0),
                "assistant_commentary_rate": r.get("assistant_commentary_rate", 0.0),
                "schema_violation_rate": r.get("schema_violation_rate", 0.0),
                "persona_inconsistency_rate": r.get("persona_inconsistency_rate", 0.0),
            }
        )
    return pd.DataFrame(rows)


def build_refusal_violation_table(
    events: list[dict[str, Any]],
) -> pd.DataFrame:
    """Structured refusal and constraint-violation tracking."""
    rows = []
    for e in events:
        rows.append(
            {
                "regime": e.get("regime", ""),
                "episode_id": e.get("episode_id", ""),
                "step_index": e.get("step_index", 0),
                "event_type": e.get("event_type", ""),
                "raw_response": e.get("raw_response", ""),
            }
        )
    return pd.DataFrame(rows)
