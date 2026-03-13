from tests.fixtures.bubble_env_fixtures import make_short_env


def test_buy_at_terminal_offer_creates_terminal_holder_loss() -> None:
    env = make_short_env()
    env.reset(episode_id="ep_terminal", seed=1)

    env.step("buy")  # moves from 1 to 10
    out = env.step("buy")  # buys final offer

    assert out.done is True
    assert out.reward == -10.0
    assert out.info["terminal_reason"] == "terminal_holder"

    summary = env.episode_summary()
    assert summary.final_holder_index == 1
    assert summary.terminal_reason == "terminal_holder"
