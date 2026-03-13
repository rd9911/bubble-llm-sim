from __future__ import annotations

import pandas as pd


def assign_micro_buckets(decisions_df: pd.DataFrame, bucket_scheme: str = "tier2") -> pd.DataFrame:
    """
    Assigns a decision bucket structure to each row.
    tier1: cap_type, price_index
    tier2: cap_type, price_index, previous_actions_len
    tier3: cap_type, price_index, previous_actions_len, offered_price
    """
    if decisions_df.empty:
        decisions_df["micro_bucket"] = ""
        return decisions_df

    df = decisions_df.copy()

    if bucket_scheme == "tier1":
        cols = ["cap_type", "price_index"]
    elif bucket_scheme == "tier2":
        cols = ["cap_type", "price_index", "previous_actions_len"]
    elif bucket_scheme == "tier3":
        # Add price path sequence length explicitly formatting
        cols = ["cap_type", "price_index", "previous_actions_len", "offered_price"]
    else:
        raise ValueError(f"Unknown bucket_scheme: {bucket_scheme}")

    for c in cols:
        if c not in df.columns:
            # Fallback handling dynamically reconstructing array lengths
            if c == "previous_actions_len" and "previous_actions" in df.columns:
                df["previous_actions_len"] = df["previous_actions"].apply(
                    lambda x: len(x) if isinstance(x, (list, tuple)) else 0
                )
            else:
                raise ValueError(f"Missing required column for bucketing: {c}")

    # Build discrete tuples mapping exact hashing boundaries
    df["micro_bucket"] = df[cols].apply(lambda row: tuple(row), axis=1)

    return df
