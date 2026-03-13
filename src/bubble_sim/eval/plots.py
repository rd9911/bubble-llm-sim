from __future__ import annotations

from pathlib import Path

import pandas as pd


def plot_buy_rate_by_price_index(
    human_df: pd.DataFrame, agent_df: pd.DataFrame, output_dir: str | Path
) -> None:
    import matplotlib.pyplot as plt
    import seaborn as sns

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    # Pre-process safely
    h_df = human_df.copy()
    a_df = agent_df.copy()
    h_df["Source"] = "Human"
    a_df["Source"] = "Agent"

    df = pd.concat([h_df, a_df], ignore_index=True)
    if (
        "cap_type" not in df.columns
        or "action" not in df.columns
        or "price_index" not in df.columns
    ):
        return

    df["buy_flag"] = (df["action"] == "buy").astype(int)

    plt.figure(figsize=(10, 6))
    g = sns.catplot(
        data=df,
        x="price_index",
        y="buy_flag",
        hue="Source",
        col="cap_type",
        kind="point",
        dodge=True,
        errorbar=None,
    )
    g.set_axis_labels("Price Index", "Buy Rate")
    g.fig.suptitle("Buy Rate vs Price Index Across Treatments", y=1.05)
    g.savefig(path / "buy_rate_by_price_index.png", dpi=150, bbox_inches="tight")
    plt.close("all")


def plot_bucket_gap_heatmap(metrics_df: pd.DataFrame, output_dir: str | Path) -> None:
    import ast

    import matplotlib.pyplot as plt
    import seaborn as sns

    if metrics_df.empty or "micro_bucket_str" not in metrics_df.columns:
        return

    df = metrics_df[~metrics_df["is_sparse"]].copy()
    if df.empty:
        return

    # Expand string mappings cleanly plotting correctly across Tier metrics safely
    try:
        tuples = df["micro_bucket_str"].apply(ast.literal_eval)
        df["cap_type"] = tuples.apply(lambda x: x[0])
        df["price_index"] = tuples.apply(lambda x: x[1])
        df["previous_actions_len"] = tuples.apply(lambda x: x[2] if len(x) > 2 else 0)
    except Exception:
        return

    path = Path(output_dir)

    for cap_type, group in df.groupby("cap_type"):
        pivot = group.pivot_table(
            index="previous_actions_len", columns="price_index", values="buy_rate_gap"
        )
        if pivot.empty:
            continue

        plt.figure(figsize=(8, 6))
        sns.heatmap(pivot, annot=True, cmap="coolwarm", center=0, fmt=".2f")
        plt.title(f"Buy-Rate Gaps: Agent vs Human ({cap_type})")
        plt.ylabel("Previous Actions Length")
        plt.xlabel("Price Index")
        plt.savefig(path / f"bucket_gap_heatmap_{cap_type}.png", dpi=150, bbox_inches="tight")
        plt.close()


def plot_reliability_curve(calibration_data: dict, output_dir: str | Path) -> None:
    import matplotlib.pyplot as plt

    if "reliability" not in calibration_data:
        return

    path = Path(output_dir)
    d = calibration_data["reliability"]

    plt.figure(figsize=(6, 6))
    plt.plot([0, 1], [0, 1], "k--", label="Perfectly Calibrated")
    plt.plot(d["predicted_probs"], d["empirical_probs"], marker="o", label="Agent Beliefs")
    plt.xlabel("Predicted Belief (Resale)")
    plt.ylabel("Observed Frequency")
    plt.title("Reliability Diagram: Resale Predictions")
    plt.legend()
    plt.grid(True)
    plt.savefig(path / "reliability_curve.png", dpi=150, bbox_inches="tight")
    plt.close()
