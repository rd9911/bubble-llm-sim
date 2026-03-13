import pytest

from tests.fixtures.bubble_env_fixtures import make_capped_env


def test_no_buy_ends_episode_immediately() -> None:
    env = make_capped_env()
    env.reset(episode_id="ep_decline", seed=1)

    out = env.step("no_buy")

    assert out.done is True
    assert out.reward == 0.0
    assert out.info["terminal_reason"] == "decline"
    assert out.next_state.previous_actions == ("no_buy",)


def test_cannot_step_after_decline_terminal() -> None:
    env = make_capped_env()
    env.reset(episode_id="ep_decline", seed=1)
    env.step("no_buy")

    with pytest.raises(RuntimeError):
        env.step("buy")
