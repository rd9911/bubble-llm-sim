import pandas as pd

from bubble_sim.data.splits import make_heldout_pricepath_split


def test_make_heldout_pricepath_split():
    df = pd.DataFrame(
        {
            "episode_id": [f"ep_{i}" for i in range(100)],
            "price_path_id": ["path_a" if i < 30 else "path_b" for i in range(100)],
        }
    )

    mapping = make_heldout_pricepath_split(df, holdout_price_path_ids=["path_a"], seed=42)

    mapped_df = pd.DataFrame([{"episode_id": k, "split": v} for k, v in mapping.items()])
    merged = mapped_df.merge(df, on="episode_id")

    test_merged = merged[merged["split"] == "test"]
    assert (test_merged["price_path_id"] == "path_a").all()
    assert len(test_merged) == 30

    tv_merged = merged[merged["split"].isin(["train", "val"])]
    assert (tv_merged["price_path_id"] == "path_b").all()
