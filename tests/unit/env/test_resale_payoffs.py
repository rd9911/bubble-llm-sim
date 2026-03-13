from tests.fixtures.bubble_env_fixtures import make_capped_env, make_short_env


def test_resale_profit_assigned_correctly() -> None:
    env = make_capped_env()
    env.reset(episode_id="ep_resale", seed=1)

    env.step("buy")  # trader 0 buys at 1
    env.step("buy")  # trader 1 buys at 10

    summary = env.episode_summary()
    payoffs = summary.realized_payoffs

    # Trader 0 should have 9 (10 - 1)
    # Trader 1 is not final yet, so 0
    assert payoffs[0] == 9.0
    assert payoffs[1] == 0.0


def test_later_terminal_holder_loses_purchase_price() -> None:
    env = make_short_env()
    env.reset(episode_id="ep_terminal_resale", seed=1)

    env.step("buy")  # trader 0 buys at 1
    env.step("buy")  # trader 1 buys at 10 (which is max price)

    summary = env.episode_summary()
    payoffs = summary.realized_payoffs

    # Trader 0 gets 10 - 1 = 9
    # Trader 1 gets -10 (final holder)
    assert payoffs[0] == 9.0
    assert payoffs[1] == -10.0
