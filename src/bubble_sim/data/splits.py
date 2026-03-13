from __future__ import annotations

import json
import random
from pathlib import Path

import pandas as pd


def _stratified_split(
    df: pd.DataFrame,
    train_frac: float,
    val_frac: float,
    test_frac: float,
    stratify_cols: list[str] | None,
    seed: int,
) -> dict[str, str]:
    if stratify_cols and not all(c in df.columns for c in stratify_cols):
        raise ValueError("stratify_cols missing in df")

    rng = random.Random(seed)
    mapping = {}

    if stratify_cols:
        groups = df.groupby(stratify_cols)
    else:
        # Dummy group
        groups = [("all", df)]

    for _, group_df in groups:
        ep_ids = group_df["episode_id"].unique().tolist()
        rng.shuffle(ep_ids)

        n = len(ep_ids)
        n_train = int(n * train_frac)
        n_val = int(n * val_frac)

        # Ensure at least 1 per split if n >= 3, else distribute greedily
        if n >= 3 and n_train == 0:
            n_train = 1
        if n >= 3 and n_val == 0:
            n_val = 1

        train_ids = ep_ids[:n_train]
        val_ids = ep_ids[n_train : n_train + n_val]
        test_ids = ep_ids[n_train + n_val :]

        for e in train_ids:
            mapping[e] = "train"
        for e in val_ids:
            mapping[e] = "val"
        for e in test_ids:
            mapping[e] = "test"

    return mapping


def make_random_episode_split(
    episodes_df: pd.DataFrame,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    test_frac: float = 0.15,
    stratify_cols: list[str] | None = None,
    seed: int = 42,
) -> dict[str, str]:
    """
    Returns mapping: episode_id -> split label
    """
    if "episode_id" not in episodes_df.columns:
        raise ValueError("episodes_df must contain 'episode_id'")

    return _stratified_split(episodes_df, train_frac, val_frac, test_frac, stratify_cols, seed)


def make_heldout_treatment_split(
    episodes_df: pd.DataFrame,
    holdout_col: str = "cap_type",
    holdout_values: list[str] | None = None,
    val_frac_within_train: float = 0.15,
    seed: int = 42,
) -> dict[str, str]:
    if holdout_col not in episodes_df.columns:
        raise ValueError(f"episodes_df must contain '{holdout_col}'")

    if not holdout_values:
        raise ValueError("holdout_values must be provided")

    mapping = {}

    is_holdout = episodes_df[holdout_col].isin(holdout_values)
    holdout_eps = episodes_df[is_holdout]["episode_id"].unique().tolist()

    for e in holdout_eps:
        mapping[e] = "test"

    train_eps_df = episodes_df[~is_holdout].copy()

    train_val_map = _stratified_split(
        train_eps_df,
        train_frac=1.0 - val_frac_within_train,
        val_frac=val_frac_within_train,
        test_frac=0.0,
        stratify_cols=None,
        seed=seed,
    )

    for e, split in train_val_map.items():
        if split == "test":  # Should not happen due to test_frac=0.0
            split = "train"
        mapping[e] = split

    return mapping


def make_heldout_pricepath_split(
    episodes_df: pd.DataFrame,
    holdout_price_path_ids: list[str],
    val_frac_within_train: float = 0.15,
    seed: int = 42,
) -> dict[str, str]:
    return make_heldout_treatment_split(
        episodes_df,
        holdout_col="price_path_id",
        holdout_values=holdout_price_path_ids,
        val_frac_within_train=val_frac_within_train,
        seed=seed,
    )


def apply_split_labels(
    decisions_df: pd.DataFrame, episodes_df: pd.DataFrame, split_mapping: dict[str, str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    decisions_df = decisions_df.copy()
    episodes_df = episodes_df.copy()

    decisions_df["dataset_split"] = decisions_df["episode_id"].map(split_mapping)
    episodes_df["dataset_split"] = episodes_df["episode_id"].map(split_mapping)

    # Drop rows not mapped
    decisions_df = decisions_df.dropna(subset=["dataset_split"])
    episodes_df = episodes_df.dropna(subset=["dataset_split"])

    return decisions_df, episodes_df


def write_split_manifest(
    output_dir: Path, manifest_data: dict, split_mapping: dict[str, str]
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "split_manifest.json").open("w") as f:
        json.dump(manifest_data, f, indent=2)

    for split_name in ["train", "val", "test"]:
        ids = [e for e, s in split_mapping.items() if s == split_name]
        ids.sort()
        with (output_dir / f"{split_name}_episode_ids.txt").open("w") as f:
            for ep_id in ids:
                f.write(f"{ep_id}\n")
