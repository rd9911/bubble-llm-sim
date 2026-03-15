from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class SubjectRecord:
    subject_id: str
    session_id: str
    treatment_cap: int
    num_periods: int
    model_name: str
    assistant_id_hash: str
    quiz_attempt_count: int
    quiz_passed: bool
    seed: int | None

@dataclass(frozen=True)
class PeriodAssignmentRecord:
    session_id: str
    period_index: int
    market_id: str
    subject_id: str
    assigned_position: int
    offered_price: int
    belief_first: float
    belief_second: float
    belief_third: float

@dataclass(frozen=True)
class DecisionRecord:
    schema_version: str
    run_id: str | None
    source_type: str  # "human" | "agent"
    dataset_name: str
    dataset_split: str | None
    episode_id: str
    step_index: int
    trader_index: int
    env_name: str
    env_version: str
    treatment_name: str
    cap_type: str
    max_price: int | None
    price_path_id: str
    price_path: tuple[int, ...]
    offered_price: int
    price_index: int
    n_traders_total: int
    asset_value: int
    limited_liability: bool
    position_uncertainty: bool
    can_infer_from_price: bool
    previous_actions: tuple[str, ...]
    action: str
    confidence: float | None
    belief_resell: float | None
    rationale_short: str | None
    trader_id: str | None
    archetype_id: str | None
    reasoning_style: str | None
    risk_attitude: str | None
    noise_level: float | None
    depth_of_reasoning: int | None
    analogy_class_tendency: str | None
    resale_belief_sensitivity: float | None
    prompt_backstory_version: str | None
    terminal_after_action: bool
    terminal_reason: str | None
    immediate_reward: float
    realized_payoff_if_known: float | None
    config_hash: str | None
    prompt_template_id: str | None
    prompt_template_hash: str | None
    model_id: str | None
    manifest_run_id: str | None

@dataclass(frozen=True)
class QuizRecord:
    subject_id: str
    session_id: str
    attempt_index: int
    question_id: str
    answer_submitted: str
    answer_correct: bool

@dataclass(frozen=True)
class MarketOutcomeRecord:
    session_id: str
    period_index: int
    market_id: str
    first_price_draw: int
    bubble_depth: int
    bubble_size: str
    num_buys_all_elicited: int
    num_buys_realized: int
    terminal_holder_position: int | None
    treatment_cap: int


@dataclass(frozen=True)
class LabDecisionRecord:
    session_id: str
    period_index: int
    market_id: str
    subject_id: str
    action: str
    confidence: float | None
    belief_success_resale: float | None
    decision_relevant: bool
    actual_proposed_to_trade: bool
    payoff_this_period: int
    cumulative_payoff: int
    bubble_size: str
    first_price_draw: int
    cap_first_price: int

@dataclass(frozen=True)
class EpisodeRecord:
    schema_version: str

    # provenance
    run_id: str | None
    source_type: str  # "human" | "agent"
    dataset_name: str
    dataset_split: str | None

    # episode identity
    episode_id: str

    # treatment / environment identity
    env_name: str
    env_version: str
    treatment_name: str
    cap_type: str
    max_price: int | None
    price_path_id: str
    price_path: tuple[int, ...]
    n_traders_total: int

    # episode results
    actions: tuple[str, ...]
    stopped_at_price_index: int
    final_holder_index: int | None
    terminal_reason: str
    realized_payoffs: tuple[float, ...]
    n_steps: int
    bubble_depth: int

    # reproducibility
    config_hash: str | None
    manifest_run_id: str | None
