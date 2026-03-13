from tests.fixtures.bubble_env_fixtures import make_capped_env


def test_same_seed_same_initial_state() -> None:
    env1 = make_capped_env()
    env2 = make_capped_env()

    s1 = env1.reset(episode_id="ep", seed=42)
    s2 = env2.reset(episode_id="ep", seed=42)

    assert s1 == s2


def test_same_actions_same_summary() -> None:
    env1 = make_capped_env()
    env2 = make_capped_env()

    env1.reset(episode_id="ep", seed=42)
    env2.reset(episode_id="ep", seed=42)

    for a in ["buy", "buy", "no_buy"]:
        env1.step(a)
        env2.step(a)

    assert env1.episode_summary() == env2.episode_summary()
