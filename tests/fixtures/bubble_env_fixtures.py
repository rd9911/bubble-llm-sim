from bubble_sim.env.bubble_game import BubbleGameEnv
from bubble_sim.env.config import BubbleGameConfig


def make_capped_env() -> BubbleGameEnv:
    cfg = BubbleGameConfig(
        treatment_name="capped_baseline",
        cap_type="capped",
        price_path=(1, 10, 100, 1000, 10000),
        max_price=10000,
        n_traders_total=5,
    )
    return BubbleGameEnv(cfg)


def make_uncapped_env() -> BubbleGameEnv:
    cfg = BubbleGameConfig(
        treatment_name="uncapped_baseline",
        cap_type="uncapped",
        price_path=(1, 10, 100, 1000, 10000),
        max_price=None,
        n_traders_total=5,
    )
    return BubbleGameEnv(cfg)


def make_short_env() -> BubbleGameEnv:
    cfg = BubbleGameConfig(
        treatment_name="short_path",
        cap_type="capped",
        price_path=(1, 10),
        max_price=10,
        n_traders_total=2,
    )
    return BubbleGameEnv(cfg)
