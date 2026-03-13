from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


def to_serializable(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, tuple):
        return [to_serializable(x) for x in obj]
    if isinstance(obj, list):
        return [to_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    return obj
