from __future__ import annotations

from pathlib import Path

from bubble_sim.data.ingest_agent import ingest_agent_dataset
from bubble_sim.data.ingest_human import ingest_human_dataset
from bubble_sim.data.io import read_dataset_meta, read_decisions_parquet, read_episodes_parquet


def test_ingest_human_toy_dataset(tmp_path: Path):
    fixture_path = Path("tests/fixtures/raw/human_toy.csv")
    out_dir = tmp_path / "data" / "clean"

    # We pass the real config file for defaults mappings
    config_path = Path("configs/data_sources/human_default.yaml")

    ingest_human_dataset(
        input_path=fixture_path,
        dataset_name="human_toy",
        output_dir=out_dir,
        source_config_path=config_path,
    )

    ds_path = out_dir / "human_toy"
    assert ds_path.exists()

    decs = read_decisions_parquet(ds_path / "decisions.parquet")
    eps = read_episodes_parquet(ds_path / "episodes.parquet")
    meta = read_dataset_meta(ds_path / "dataset_meta.json")

    assert len(decs) == 6
    assert len(eps) == 2
    assert meta.n_decisions == 6
    assert meta.n_episodes == 2

    # Check simple values
    assert [d.action for d in decs] == ["no_buy", "buy", "buy", "buy", "buy", "buy"]

    ep_decline = next(e for e in eps if e.episode_id == "ep_decline")
    assert ep_decline.terminal_reason == "decline"
    assert ep_decline.n_steps == 1
    assert ep_decline.bubble_depth == 0

    ep_term = next(e for e in eps if e.episode_id == "ep_term")
    assert ep_term.terminal_reason == "terminal_holder"
    assert ep_term.n_steps == 5
    assert ep_term.bubble_depth == 5  # 5 buys including terminal


def test_ingest_agent_toy_dataset(tmp_path: Path):
    fixture_path = Path("tests/fixtures/raw/agent_toy.jsonl")
    out_dir = tmp_path / "data" / "clean"

    ingest_agent_dataset(
        traces_path=fixture_path,
        dataset_name="agent_toy",
        output_dir=out_dir,
    )

    ds_path = out_dir / "agent_toy"
    assert ds_path.exists()

    decs = read_decisions_parquet(ds_path / "decisions.parquet")
    eps = read_episodes_parquet(ds_path / "episodes.parquet")

    assert len(decs) == 3
    assert len(eps) == 2

    ep1 = next(e for e in eps if e.episode_id == "ep1")
    assert ep1.terminal_reason == "terminal_holder"
    assert ep1.n_steps == 2
    assert ep1.bubble_depth == 2

    ep2 = next(e for e in eps if e.episode_id == "ep2")
    assert ep2.terminal_reason == "decline"
    assert ep2.n_steps == 1
    assert ep2.bubble_depth == 0

    assert decs[0].trader_id == "t1"
    assert decs[1].trader_id == "t2"
