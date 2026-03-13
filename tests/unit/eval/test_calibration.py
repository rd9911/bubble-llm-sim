import pandas as pd

from bubble_sim.eval.calibration import compute_resale_calibration


def test_perfect_calibration_brier_score():
    df = pd.DataFrame(
        [
            {"action": "buy", "belief_resell": 1.0, "resale_success": True},
            {"action": "buy", "belief_resell": 0.0, "resale_success": False},
        ]
    )
    res = compute_resale_calibration(df)
    assert res["brier_score"] == 0.0
    assert res["ece"] == 0.0


def test_calibration_ignores_no_buy():
    # `no_buy` action records safely ignored natively
    df = pd.DataFrame(
        [
            {"action": "buy", "belief_resell": 1.0, "resale_success": True},
            {"action": "no_buy", "belief_resell": 0.9, "resale_success": False},
        ]
    )
    res = compute_resale_calibration(df)
    assert res["brier_score"] == 0.0
