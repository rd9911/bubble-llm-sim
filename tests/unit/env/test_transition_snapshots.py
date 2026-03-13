from bubble_sim.env.bubble_game import BubbleGameEnv
from bubble_sim.env.config import BubbleGameConfig


def state_view(state):
    return (
        state.step_index,
        state.trader_index,
        state.offered_price,
        state.price_index,
        state.previous_actions,
        state.done,
    )


def test_transition_snapshot_buy_then_decline() -> None:
    env = BubbleGameEnv(
        BubbleGameConfig(
            treatment_name="snapshot",
            cap_type="capped",
            price_path=(1, 10, 100),
            max_price=100,
            n_traders_total=3,
        )
    )

    s0 = env.reset(episode_id="ep_snap", seed=1)
    s1 = env.step("buy").next_state
    s2 = env.step("no_buy").next_state

    assert state_view(s0) == (0, 0, 1, 0, (), False)
    assert state_view(s1) == (1, 1, 10, 1, ("buy",), False)
    assert state_view(s2) == (1, 1, 10, 1, ("buy", "no_buy"), True)
