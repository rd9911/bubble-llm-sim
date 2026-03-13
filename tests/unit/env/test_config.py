import pytest

from bubble_sim.env.config import BubbleGameConfig


def test_valid_capped_config() -> None:
    cfg = BubbleGameConfig(
        cap_type="capped",
        price_path=(1, 10, 100),
        max_price=100,
    )
    assert cfg.cap_type == "capped"


def test_capped_requires_max_price() -> None:
    with pytest.raises(ValueError):
        BubbleGameConfig(
            cap_type="capped",
            price_path=(1, 10, 100),
            max_price=None,
        )


def test_capped_requires_max_price_match_path() -> None:
    with pytest.raises(ValueError):
        BubbleGameConfig(
            cap_type="capped",
            price_path=(1, 10, 100),
            max_price=1000,
        )


def test_uncapped_requires_no_max_price() -> None:
    with pytest.raises(ValueError):
        BubbleGameConfig(
            cap_type="uncapped",
            price_path=(1, 10, 100),
            max_price=100,
        )


def test_asset_value_zero() -> None:
    with pytest.raises(ValueError):
        BubbleGameConfig(
            cap_type="uncapped",
            price_path=(1, 10, 100),
            max_price=None,
            asset_value=1,
        )


def test_invalid_path_length() -> None:
    with pytest.raises(ValueError):
        BubbleGameConfig(
            cap_type="capped",
            price_path=(1,),
            max_price=1,
        )
