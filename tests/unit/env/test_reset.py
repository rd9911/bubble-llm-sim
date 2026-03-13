from tests.fixtures.bubble_env_fixtures import make_capped_env


def test_reset_initializes_first_state() -> None:
    env = make_capped_env()
    state = env.reset(episode_id="ep_1", seed=42)

    assert state.episode_id == "ep_1"
    assert state.step_index == 0
    assert state.trader_index == 0
    assert state.offered_price == 1
    assert state.price_index == 0
    assert state.previous_actions == ()
    assert state.done is False


def test_reset_clears_prior_actions() -> None:
    env = make_capped_env()
    env.reset(episode_id="ep_1", seed=42)
    env.step("buy")

    assert env.current_state().previous_actions == ("buy",)

    state = env.reset(episode_id="ep_2", seed=43)
    assert state.previous_actions == ()
    assert state.step_index == 0
