from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyCallEvent:
    run_id: str
    episode_id: str
    step_index: int
    trader_index: int
    prompt_template_id: str
    prompt_template_hash: str
    model_id: str | None
    retry_count: int
    fallback_used: bool
    parse_success: bool
    raw_response: str | None
    parsed_action: str | None


@dataclass(frozen=True)
class TransitionEvent:
    run_id: str
    episode_id: str
    step_index: int
    action: str
    reward: float
    done: bool
    terminal_reason: str | None
