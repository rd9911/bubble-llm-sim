import pandas as pd

from bubble_sim.data.splits import make_random_episode_split


def test_make_random_episode_split():
    # Construct a dummy DataFrame spanning multiple rows per episode
    df = pd.DataFrame(
        {
            "episode_id": [f"ep_{i}" for i in range(100) for _ in range(3)],
            "cap_type": ["capped" if i < 50 else "uncapped" for i in range(100) for _ in range(3)],
        }
    )

    mapping = make_random_episode_split(
        df, train_frac=0.7, val_frac=0.15, test_frac=0.15, stratify_cols=["cap_type"], seed=42
    )

    # 1. Dictionary keys ensure no episode maps to multiple splits
    assert len(mapping) == 100

    # 2. Verify roughly 70/15/15 ratio distribution
    counts = pd.Series(list(mapping.values())).value_counts()
    assert 65 <= counts["train"] <= 75
    assert 10 <= counts["val"] <= 20
    assert 10 <= counts["test"] <= 20

    # 3. Stratification verification: both groups present in 'test' split
    mapped_df = pd.DataFrame([{"episode_id": k, "split": v} for k, v in mapping.items()])
    merged = mapped_df.merge(df[["episode_id", "cap_type"]].drop_duplicates(), on="episode_id")

    test_caps = merged[merged["split"] == "test"]["cap_type"].unique()
    assert "capped" in test_caps
    assert "uncapped" in test_caps
