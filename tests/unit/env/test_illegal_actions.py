import pytest

from tests.fixtures.bubble_env_fixtures import make_capped_env


def test_illegal_action_raises() -> None:
    env = make_capped_env()
    env.reset(episode_id="ep_illegal", seed=1)

    with pytest.raises(ValueError):
        env.step("sell")


def test_empty_string_raises() -> None:
    env = make_capped_env()
    env.reset(episode_id="ep_illegal", seed=1)

    with pytest.raises(ValueError):
        env.step("")


def test_none_raises() -> None:
    env = make_capped_env()
    env.reset(episode_id="ep_illegal", seed=1)

    with pytest.raises(ValueError):
        env.step(None)  # type: ignore
