from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetMeta:
    schema_version: str
    dataset_name: str
    created_at_utc: str
    source_type: str
    env_name: str
    env_version: str
    n_decisions: int
    n_episodes: int
    splits: tuple[str, ...]
    decision_file: str
    episode_file: str
    decision_schema_hash: str
    episode_schema_hash: str
    dataset_hash: str
    notes: str | None = None
