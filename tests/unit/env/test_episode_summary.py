from tests.fixtures.bubble_env_fixtures import make_capped_env, make_short_env


def test_episode_summary_after_decline() -> None:
    env = make_capped_env()
    env.reset(episode_id="ep_summary_decline", seed=1)
    env.step("no_buy")

    summary = env.episode_summary()

    assert summary.episode_id == "ep_summary_decline"
    assert summary.cap_type == "capped"
    assert summary.actions == ("no_buy",)
    assert summary.terminal_reason == "decline"
    assert summary.final_holder_index is None
    assert len(summary.realized_payoffs) == 5


def test_episode_summary_after_terminal_holder() -> None:
    env = make_short_env()
    env.reset(episode_id="ep_summary_term", seed=1)

    env.step("buy")
    env.step("buy")

    summary = env.episode_summary()

    assert summary.episode_id == "ep_summary_term"
    assert summary.actions == ("buy", "buy")
    assert summary.terminal_reason == "terminal_holder"
    assert summary.final_holder_index == 1
    assert len(summary.realized_payoffs) == 2


def test_episode_summary_contains_treatment() -> None:
    env = make_capped_env()
    env.reset(episode_id="ep_sum_treat", seed=1)

    env.step("no_buy")
    summary = env.episode_summary()

    assert summary.treatment_name == env.config.treatment_name
    assert summary.cap_type == env.config.cap_type
    assert summary.price_path == env.config.price_path
