from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from bubble_sim.data.metadata import DatasetMeta
from bubble_sim.data.schemas import DecisionRecord, EpisodeRecord
from bubble_sim.utils.serialization import to_serializable


def write_decisions_parquet(records: Sequence[DecisionRecord], path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([to_serializable(r) for r in records])
    df.to_parquet(path, index=False)


def write_episodes_parquet(records: Sequence[EpisodeRecord], path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([to_serializable(r) for r in records])
    df.to_parquet(path, index=False)


def read_decisions_parquet(path: Path | str) -> list[DecisionRecord]:
    df = pd.read_parquet(path)
    # converting pandas to list of dicts safely with nans replaced for dataclass reconstruction
    records = df.where(pd.notnull(df), None).to_dict(orient="records")
    return [
        DecisionRecord(
            **{k: v if v is not None or k not in df.columns else None for k, v in r.items()}
        )
        for r in records
    ]


def read_episodes_parquet(path: Path | str) -> list[EpisodeRecord]:
    df = pd.read_parquet(path)
    records = df.where(pd.notnull(df), None).to_dict(orient="records")
    return [
        EpisodeRecord(
            **{k: v if v is not None or k not in df.columns else None for k, v in r.items()}
        )
        for r in records
    ]


def write_dataset_meta(meta: DatasetMeta, path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(to_serializable(meta), f, indent=2)


def read_dataset_meta(path: Path | str) -> DatasetMeta:
    with Path(path).open("r") as f:
        data = json.load(f)
    return DatasetMeta(**data)
