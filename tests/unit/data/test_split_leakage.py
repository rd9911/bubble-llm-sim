import pandas as pd

from bubble_sim.data.splits import apply_split_labels


def test_split_leakage():
    # Array mapping decisions loosely into overarching episodes independently
    decs_df = pd.DataFrame(
        {
            "row_id": range(10),
            "episode_id": [
                "ep_1",
                "ep_1",
                "ep_1",
                "ep_2",
                "ep_2",
                "ep_3",
                "ep_3",
                "ep_3",
                "ep_3",
                "ep_4",
            ],
        }
    )

    eps_df = pd.DataFrame({"episode_id": ["ep_1", "ep_2", "ep_3", "ep_4"]})

    # Implicitly missing `ep_4` verifying exclusion/dropna parameters inside the schema maps
    mapping = {
        "ep_1": "train",
        "ep_2": "val",
        "ep_3": "test",
    }

    labeled_decs, labeled_eps = apply_split_labels(decs_df, eps_df, mapping)

    # 1. Broadly ensures mapped lines map back entirely consistently
    # (i.e. single split type per episode mapping).
    ep1_labels = labeled_decs[labeled_decs["episode_id"] == "ep_1"]["dataset_split"]
    assert ep1_labels.nunique() == 1
    assert ep1_labels.iloc[0] == "train"

    # 2. Ensures unmapped/omitted episodes gracefully drop avoiding undefined state propagation.
    assert "ep_4" not in labeled_decs["episode_id"].values
    assert "ep_4" not in labeled_eps["episode_id"].values

    # 3. Overall integrity
    assert len(labeled_decs) == 9
    assert len(labeled_eps) == 3
