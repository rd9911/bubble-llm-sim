from __future__ import annotations

from bubble_sim.data.schemas import DecisionRecord, EpisodeRecord


def validate_decision_record(rec: DecisionRecord) -> None:
    if rec.action not in {"buy", "no_buy"}:
        raise ValueError(f"Invalid action: {rec.action}")
    if rec.cap_type not in {"capped", "uncapped"}:
        raise ValueError(f"Invalid cap_type: {rec.cap_type}")
    if not (0 <= rec.price_index < len(rec.price_path)):
        raise IndexError(
            f"price_index {rec.price_index} out of bounds for path len {len(rec.price_path)}"
        )
    if rec.offered_price != rec.price_path[rec.price_index]:
        raise ValueError(
            f"offered_price {rec.offered_price} does not match "
            f"price_path[{rec.price_index}] = {rec.price_path[rec.price_index]}"
        )
    if rec.cap_type == "capped":
        if rec.max_price != rec.price_path[-1]:
            raise ValueError(f"capped treatment must have max_price == {rec.price_path[-1]}")
    if rec.terminal_after_action and rec.terminal_reason is None:
        raise ValueError("terminal_after_action == True requires non-null terminal_reason")


def validate_episode_record(rec: EpisodeRecord) -> None:
    if len(rec.actions) != rec.n_steps:
        raise ValueError(f"len(actions) {len(rec.actions)} != n_steps {rec.n_steps}")
    if len(rec.realized_payoffs) != rec.n_traders_total:
        raise ValueError(
            f"len(realized_payoffs) {len(rec.realized_payoffs)} != "
            f"n_traders_total {rec.n_traders_total}"
        )
    if rec.bubble_depth > rec.n_steps:
        raise ValueError(f"bubble_depth {rec.bubble_depth} > n_steps {rec.n_steps}")
