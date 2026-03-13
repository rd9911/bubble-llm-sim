from tests.fixtures.bubble_env_fixtures import make_capped_env


def test_buy_advances_to_next_price() -> None:
    env = make_capped_env()
    env.reset(episode_id="ep_buy", seed=1)

    out = env.step("buy")
    s = out.next_state

    assert out.done is False
    assert out.reward == 0.0
    assert s.step_index == 1
    assert s.trader_index == 1
    assert s.price_index == 1
    assert s.offered_price == 10
    assert s.previous_actions == ("buy",)


def test_previous_actions_accumulate() -> None:
    env = make_capped_env()
    env.reset(episode_id="ep_buy", seed=1)

    env.step("buy")
    out = env.step("buy")

    s = out.next_state
    assert s.previous_actions == ("buy", "buy")
    assert s.offered_price == 100


def test_next_state_respects_treatment_metadata() -> None:
    env = make_capped_env()
    cfg = env.config
    env.reset(episode_id="ep_buy", seed=1)

    s = env.step("buy").next_state

    assert s.cap_type == cfg.cap_type
    assert s.max_price == cfg.max_price
    assert s.price_path == cfg.price_path
