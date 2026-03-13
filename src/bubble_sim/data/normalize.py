from __future__ import annotations

from collections.abc import Sequence


def normalize_action(value: str | None) -> str:
    if value is None:
        raise ValueError("Missing action")
    val = str(value).strip().lower()
    if val in {"buy", "yes", "1", "true"}:
        return "buy"
    if val in {"no_buy", "no", "0", "false"}:
        return "no_buy"
    raise ValueError(f"Cannot normalize action: {value}")


def normalize_cap_type(value: str | None) -> str | None:
    if value is None:
        return None
    val = str(value).strip().lower()
    if val == "capped":
        return "capped"
    if val == "uncapped":
        return "uncapped"
    if val in {"yes", "true", "1"}:
        return "capped"
    if val in {"no", "false", "0"}:
        return "uncapped"
    return val


def normalize_price_path(raw_value: str | Sequence[int]) -> tuple[int, ...]:
    if isinstance(raw_value, str):
        # Handle "1,10,100" or "[1, 10, 100]"
        import ast

        try:
            val = ast.literal_eval(raw_value)
            if isinstance(val, (list, tuple)):
                return tuple(int(x) for x in val)
        except Exception:
            pass
        parts = raw_value.replace("[", "").replace("]", "").split(",")
        return tuple(int(p.strip()) for p in parts if p.strip())
    return tuple(int(x) for x in raw_value)


def build_previous_actions(actions_so_far: Sequence[str]) -> tuple[str, ...]:
    return tuple(actions_so_far)


def compute_bubble_depth(actions: Sequence[str]) -> int:
    """Number of consecutive successful buys before termination"""
    purchases = 0
    for a in actions:
        if a == "buy":
            purchases += 1
        elif a == "no_buy":
            break
    return purchases
