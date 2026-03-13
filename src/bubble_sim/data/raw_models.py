from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawDecisionRow:
    episode_id: str
    trader_id: str | None
    offered_price: int | None
    action: str | None
    treatment_name: str | None
    cap_type: str | None
    price_index: int | None
    realized_payoff_if_known: float | None
    raw_payload: dict[str, Any]
