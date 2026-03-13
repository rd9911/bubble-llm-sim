from __future__ import annotations

import numpy as np
import pytest

from bubble_sim.data.io import (
    read_decisions_parquet,
    write_decisions_parquet,
)
from bubble_sim.data.schemas import DecisionRecord, EpisodeRecord
from bubble_sim.data.validators import validate_decision_record, validate_episode_record


def test_decision_record_validation():
    rec = DecisionRecord(
        schema_version="1.0",
        run_id="run_1",
        source_type="agent",
        dataset_name="test_data",
        dataset_split="train",
        episode_id="ep_1",
        step_index=0,
        trader_index=0,
        env_name="BubbleGameEnv",
        env_version="1.0",
        treatment_name="baseline",
        cap_type="capped",
        max_price=100,
        price_path_id="path_1",
        price_path=(1, 10, 100),
        offered_price=1,
        price_index=0,
        n_traders_total=3,
        asset_value=0,
        limited_liability=True,
        position_uncertainty=True,
        can_infer_from_price=True,
        previous_actions=(),
        action="buy",
        confidence=0.9,
        belief_resell=0.8,
        rationale_short="seems good",
        trader_id="tr_1",
        archetype_id="arch_1",
        reasoning_style=None,
        risk_attitude=None,
        noise_level=None,
        depth_of_reasoning=None,
        analogy_class_tendency=None,
        resale_belief_sensitivity=None,
        prompt_backstory_version=None,
        terminal_after_action=False,
        terminal_reason=None,
        immediate_reward=0.0,
        realized_payoff_if_known=None,
        config_hash=None,
        prompt_template_id=None,
        prompt_template_hash=None,
        model_id=None,
        manifest_run_id=None,
    )
    validate_decision_record(rec)  # should pass

    # Test bad action
    import dataclasses

    bad_rec = dataclasses.replace(rec, action="sell")
    with pytest.raises(ValueError):
        validate_decision_record(bad_rec)

    # Test bad offered price
    bad_rec = dataclasses.replace(rec, offered_price=5)
    with pytest.raises(ValueError):
        validate_decision_record(bad_rec)


def test_decision_record_round_trip(tmp_path):
    rec = DecisionRecord(
        schema_version="1.0",
        run_id="run_1",
        source_type="agent",
        dataset_name="test_data",
        dataset_split="train",
        episode_id="ep_1",
        step_index=0,
        trader_index=0,
        env_name="BubbleGameEnv",
        env_version="1.0",
        treatment_name="baseline",
        cap_type="capped",
        max_price=100,
        price_path_id="path_1",
        price_path=(1, 10, 100),
        offered_price=1,
        price_index=0,
        n_traders_total=3,
        asset_value=0,
        limited_liability=True,
        position_uncertainty=True,
        can_infer_from_price=True,
        previous_actions=("buy", "no_buy"),
        action="buy",
        confidence=np.nan,  # handles nans converting to None or read back as null
        belief_resell=0.8,
        rationale_short="seems good",
        trader_id="tr_1",
        archetype_id="arch_1",
        reasoning_style=None,
        risk_attitude=None,
        noise_level=None,
        depth_of_reasoning=None,
        analogy_class_tendency=None,
        resale_belief_sensitivity=None,
        prompt_backstory_version=None,
        terminal_after_action=False,
        terminal_reason=None,
        immediate_reward=0.0,
        realized_payoff_if_known=None,
        config_hash=None,
        prompt_template_id=None,
        prompt_template_hash=None,
        model_id=None,
        manifest_run_id=None,
    )

    path = tmp_path / "decisions.parquet"
    write_decisions_parquet([rec], path)
    read_recs = read_decisions_parquet(path)

    assert len(read_recs) == 1
    # Check simple scalar
    assert read_recs[0].action == "buy"
    # Numpy arrays get converted back to ndarray in pandas parquet roundtrips
    assert list(read_recs[0].price_path) == [1, 10, 100]
    assert list(read_recs[0].previous_actions) == ["buy", "no_buy"]


def test_episode_record_validation():
    rec = EpisodeRecord(
        schema_version="1.0",
        run_id=None,
        source_type="human",
        dataset_name="test",
        dataset_split=None,
        episode_id="ep1",
        env_name="e",
        env_version="v1",
        treatment_name="baseline",
        cap_type="baseline",
        max_price=None,
        price_path_id="path",
        price_path=(1, 10),
        n_traders_total=2,
        actions=("buy", "no_buy"),
        stopped_at_price_index=1,
        final_holder_index=None,
        terminal_reason="decline",
        realized_payoffs=(9.0, 0.0),
        n_steps=2,
        bubble_depth=1,
        config_hash=None,
        manifest_run_id=None,
    )
    validate_episode_record(rec)

    import dataclasses

    bad_rec = dataclasses.replace(rec, actions=("buy",))
    with pytest.raises(ValueError):
        validate_episode_record(bad_rec)
