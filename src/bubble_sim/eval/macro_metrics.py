from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_macro_fidelity_summary(
    episodes_df: pd.DataFrame, decisions_df: pd.DataFrame
) -> dict[str, Any]:
    """Computes aggregate macro-fidelity metrics comparing against paper benchmarks."""
    
    if episodes_df.empty:
        return {}

    # 1. Mean Bubble Depth
    # The bubble_depth is already calculated during ingestion and stored in episodes.parquet
    mean_bubble_depth = float(episodes_df["bubble_depth"].mean())

    # 2. Terminal Holder Frequency
    # Frequency of episodes that ended because the last trader in the sequence bought
    n_episodes = len(episodes_df)
    n_terminal_holders = episodes_df["terminal_reason"].eq("terminal_holder").sum()
    terminal_holder_freq = float(n_terminal_holders / n_episodes) if n_episodes > 0 else 0.0

    # 3. Snowball Slope
    # Logistic regression of Buy (1) vs NoBuy (0) on number of previous buyers
    # This measures if agents are more likely to buy when they see a "momentum" of buyers.
    # Note: In our current 3-trader simple model, 'previous_actions' length serves as price index / momentum proxy.
    
    snowball_slope = 0.0
    if not decisions_df.empty:
        # Extract number of previous actions
        decisions_df = decisions_df.copy()
        decisions_df["prev_count"] = decisions_df["previous_actions"].apply(len)
        decisions_df["is_buy"] = decisions_df["action"].eq("buy").astype(int)
        
        # We need at least some variation to run a regression
        if decisions_df["is_buy"].nunique() > 1 and decisions_df["prev_count"].nunique() > 1:
            try:
                # Simple linear regression for the slope
                # y = ax + b
                X = decisions_df["prev_count"].values
                y = decisions_df["is_buy"].values
                slope, _ = np.polyfit(X, y, 1)
                snowball_slope = float(slope)
            except Exception:
                pass

    # 4. Treatment Gap
    # Difference in mean buy rate between capped and uncapped
    treatment_buy_rates = decisions_df.groupby("cap_type")["action"].apply(lambda x: (x == "buy").mean())
    capped_rate = treatment_buy_rates.get("capped", 0.0)
    uncapped_rate = treatment_buy_rates.get("uncapped", 0.0)
    treatment_gap = float(uncapped_rate - capped_rate)

    return {
        "mean_bubble_depth": mean_bubble_depth,
        "terminal_holder_freq": terminal_holder_freq,
        "snowball_slope": snowball_slope,
        "treatment_gap": treatment_gap,
    }


def compute_macro_gaps(agent_macro: dict[str, Any], targets: Any) -> dict[str, float]:
    """Computes deviations from replication targets."""
    return {
        "bubble_depth_gap": agent_macro.get("mean_bubble_depth", 0.0) - targets.mean_bubble_depth,
        "snowball_slope_error": agent_macro.get("snowball_slope", 0.0) - targets.snowball_slope,
        "treatment_gap_error": agent_macro.get("treatment_gap", 0.0) - targets.treatment_gap,
        "terminal_holder_gap": agent_macro.get("terminal_holder_freq", 0.0) - targets.terminal_holder_freq,
    }
