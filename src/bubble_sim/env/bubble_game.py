from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PriceDraw:
    cap_first_price: Literal[1, 10000]
    first_price: int
    distribution_support: list[int]
    distribution_probs: list[float]


@dataclass(frozen=True)
class BuyDecision:
    action: Literal["buy", "no_buy"]
    confidence: float | None = None
    belief_success_resale: float | None = None
    rationale_short: str | None = None


@dataclass(frozen=True)
class SubjectFeedback:
    actually_proposed: bool
    proposed_price: int | None
    period_gain: int
    cumulative_gain: int


@dataclass(frozen=True)
class PositionBelief:
    prob_first: float
    prob_second: float
    prob_third: float


@dataclass(frozen=True)
class MarketRealization:
    subject_ids: tuple[str, str, str]
    assigned_positions: dict[str, Literal[1, 2, 3]]
    offered_price_by_subject: dict[str, int]
    decision_by_subject: dict[str, BuyDecision]
    decision_relevant_by_subject: dict[str, bool]
    realized_trade_path_depth: int
    realized_bubble_size: Literal["none", "small", "medium", "large"]
    payoff_by_subject: dict[str, int]
    feedback_by_subject: dict[str, SubjectFeedback]


def get_price_draw(cap_first_price: Literal[1, 10000], rng: random.Random) -> PriceDraw:
    if cap_first_price == 10000:
        support = [1, 10, 100, 1000, 10000]
        probs = [1 / 2, 1 / 4, 1 / 8, 1 / 16, 1 / 16]
    elif cap_first_price == 1:
        support = [1]
        probs = [1.0]
    else:
        raise ValueError(f"Invalid cap_first_price: {cap_first_price}")

    first_price = rng.choices(support, weights=probs, k=1)[0]
    return PriceDraw(
        cap_first_price=cap_first_price,
        first_price=first_price,
        distribution_support=support,
        distribution_probs=probs
    )


def position_beliefs_from_observed_price(
    cap_first_price: Literal[1, 10000], observed_price: int
) -> PositionBelief:
    if cap_first_price == 10000:
        if observed_price == 1:
            return PositionBelief(1.0, 0.0, 0.0)
        elif observed_price == 10:
            return PositionBelief(1 / 3, 2 / 3, 0.0)
        elif observed_price in (100, 1000):
            return PositionBelief(1 / 7, 2 / 7, 4 / 7)
        elif observed_price == 10000:
            return PositionBelief(1 / 4, 1 / 4, 1 / 2)
        elif observed_price == 100000:
            return PositionBelief(0.0, 1 / 2, 1 / 2)
        elif observed_price == 1000000:
            return PositionBelief(0.0, 0.0, 1.0)
        else:
            raise ValueError(
                f"Unexpected observed price {observed_price} for cap 10000"
            )

    elif cap_first_price == 1:
        if observed_price == 1:
            return PositionBelief(1.0, 0.0, 0.0)
        elif observed_price == 10:
            return PositionBelief(0.0, 1.0, 0.0)
        elif observed_price == 100:
            return PositionBelief(0.0, 0.0, 1.0)
        else:
            raise ValueError(f"Unexpected observed price {observed_price} for cap 1")
    else:
        raise ValueError(f"Invalid cap_first_price: {cap_first_price}")


def resolve_market(
    subject_ids: tuple[str, str, str],
    decisions: dict[str, BuyDecision],
    first_price: int,
    assigned_positions: dict[str, Literal[1, 2, 3]],
    previous_cumulative_gains: dict[str, int],
) -> MarketRealization:
    # Reverse mapping from position to subject
    pos_to_sub = {pos: sub for sub, pos in assigned_positions.items()}

    # Deriving prices
    offered_price_by_subject = {
        pos_to_sub[1]: first_price,
        pos_to_sub[2]: first_price * 10,
        pos_to_sub[3]: first_price * 100,
    }

    dec_sub_1 = decisions[pos_to_sub[1]]
    dec_sub_2 = decisions[pos_to_sub[2]]
    dec_sub_3 = decisions[pos_to_sub[3]]

    # Resolve the path
    decision_relevant_by_subject = {s: False for s in subject_ids}

    # 1. First position always relevant
    decision_relevant_by_subject[pos_to_sub[1]] = True

    if dec_sub_1.action == "buy":
        # 2. Second position relevant only if first bought
        decision_relevant_by_subject[pos_to_sub[2]] = True
        if dec_sub_2.action == "buy":
            # 3. Third position relevant only if first and second bought
            decision_relevant_by_subject[pos_to_sub[3]] = True

    # Calculate depth and bubble size
    realized_trade_path_depth = sum(
        1 for sub in decision_relevant_by_subject if decision_relevant_by_subject[sub]
    )

    num_buys_realized = 0
    if dec_sub_1.action == "buy":
        num_buys_realized += 1
        if dec_sub_2.action == "buy":
            num_buys_realized += 1
            if dec_sub_3.action == "buy":
                num_buys_realized += 1

    if num_buys_realized == 0:
        realized_bubble_size = "none"
    elif num_buys_realized == 1:
        realized_bubble_size = "small"
    elif num_buys_realized == 2:
        realized_bubble_size = "medium"
    else:
        realized_bubble_size = "large"

    # Payoffs (+9 if successful resale, -1 if failed purchase, 0 if not reached / no_buy)
    # Equivalent to 10 ECU, 0 ECU, 1 ECU respectively
    payoff_by_subject = {}
    feedback_by_subject = {}

    for sub in subject_ids:
        pos = assigned_positions[sub]
        relevant = decision_relevant_by_subject[sub]
        action = decisions[sub].action

        if not relevant:
            payoff = 1
            feedback = SubjectFeedback(
                actually_proposed=False,
                proposed_price=None,
                period_gain=payoff,
                cumulative_gain=previous_cumulative_gains.get(sub, 0) + payoff,
            )
        else:
            if action == "no_buy":
                payoff = 1
            elif action == "buy":
                # Check outcome
                if pos == 1:
                    resold = dec_sub_2.action == "buy"
                elif pos == 2:
                    resold = dec_sub_3.action == "buy"
                else:  # pos 3
                    resold = False  # nobody to resell to

                payoff = 10 if resold else 0

            feedback = SubjectFeedback(
                actually_proposed=True,
                proposed_price=offered_price_by_subject[sub],
                period_gain=payoff,
                cumulative_gain=previous_cumulative_gains.get(sub, 0) + payoff,
            )

        payoff_by_subject[sub] = payoff
        feedback_by_subject[sub] = feedback

    return MarketRealization(
        subject_ids=subject_ids,
        assigned_positions=assigned_positions,
        offered_price_by_subject=offered_price_by_subject,
        decision_by_subject=decisions,
        decision_relevant_by_subject=decision_relevant_by_subject,
        realized_trade_path_depth=realized_trade_path_depth,
        realized_bubble_size=realized_bubble_size,
        payoff_by_subject=payoff_by_subject,
        feedback_by_subject=feedback_by_subject,
    )
