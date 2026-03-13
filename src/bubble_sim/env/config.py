from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class BubbleGameConfig:
    env_version: str = "1.0.0"
    mode: str = "lab_repeated_mp2021"
    treatment_name: str = "baseline"
    cap_first_price: Literal[1, 10000] = 10000
    num_periods: int = 10
    group_size: int = 3
    subject_endowment_per_period: int = 1
    exchange_rate_eur_per_ecu: int = 1
    decision_protocol: str = "simultaneous_private_partial_strategy"
    feedback_protocol: str = "own_realized_info_only"
    quiz_required: bool = True
    stranger_matching: bool = True
