import pandas as pd

from bubble_sim.data.splits import make_heldout_treatment_split


def test_make_heldout_treatment_split():
    df = pd.DataFrame(
        {
            "episode_id": [f"ep_{i}" for i in range(100)],
            "cap_type": ["capped" if i < 20 else "uncapped" for i in range(100)],
        }
    )

    mapping = make_heldout_treatment_split(
        df, holdout_col="cap_type", holdout_values=["capped"], val_frac_within_train=0.2, seed=42
    )

    mapped_df = pd.DataFrame([{"episode_id": k, "split": v} for k, v in mapping.items()])
    merged = mapped_df.merge(df, on="episode_id")

    # Strategy constraint: `test` segment natively contains purely the held-out element
    test_merged = merged[merged["split"] == "test"]
    assert (test_merged["cap_type"] == "capped").all()
    assert len(test_merged) == 20

    # Strategy constraint: `train` and `val` sets are strictly uncontaminated
    train_val_merged = merged[merged["split"].isin(["train", "val"])]
    assert (train_val_merged["cap_type"] == "uncapped").all()
    assert len(train_val_merged) == 80
