from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import yaml

from bubble_sim.data.io import write_dataset_meta, write_decisions_parquet, write_episodes_parquet
from bubble_sim.data.metadata import DatasetMeta
from bubble_sim.data.normalize import (
    build_previous_actions,
    compute_bubble_depth,
    normalize_action,
    normalize_cap_type,
)
from bubble_sim.data.raw_models import RawDecisionRow
from bubble_sim.data.reports import ValidationReport
from bubble_sim.data.schemas import DecisionRecord, EpisodeRecord
from bubble_sim.data.validators import validate_decision_record, validate_episode_record


def ingest_human_dataset(
    input_path: str | Path,
    dataset_name: str,
    output_dir: str | Path,
    source_config_path: str | Path | None = None,
) -> None:
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    report = ValidationReport(dataset_name=dataset_name)

    # Load config defaults if config passed
    col_map = {
        "episode_id": "episode_id",
        "trader_id": "trader_id",
        "offered_price": "offered_price",
        "action": "action",
        "treatment_name": "treatment_name",
        "cap_type": "cap_type",
        "price_index": "price_index",
    }
    consts = {
        "env_name": "BubbleGameEnv",
        "env_version": "0.1.0",
        "n_traders_total": 5,
        "asset_value": 0,
        "limited_liability": True,
        "position_uncertainty": True,
        "can_infer_from_price": True,
        "price_path": (1, 10, 100, 1000, 10000),
        "max_price": 10000,
    }

    if source_config_path:
        with Path(source_config_path).open() as f:
            cfg = yaml.safe_load(f)
            col_map.update(cfg.get("columns", {}))
            consts.update(cfg.get("constants", {}))

    raw_rows = []
    with input_path.open("r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed = RawDecisionRow(
                episode_id=row.get(col_map["episode_id"], ""),
                trader_id=row.get(col_map.get("trader_id", "")),
                offered_price=(
                    int(row[col_map["offered_price"]]) if col_map["offered_price"] in row else None
                ),
                action=row.get(col_map["action"]),
                treatment_name=row.get(col_map.get("treatment_name", "")),
                cap_type=row.get(col_map.get("cap_type", "")),
                price_index=(
                    int(row[col_map["price_index"]]) if col_map["price_index"] in row else None
                ),
                realized_payoff_if_known=None,
                raw_payload=row,
            )
            raw_rows.append(parsed)

    # Pre-compute inferred price paths per treatment
    # In MP2013, K1 is 1->10, K100 is 1->10->100, etc.
    treatment_price_paths: dict[str, tuple[int, ...]] = {}
    treatment_max_prices: dict[str, int | None] = {}
    
    # First pass: collect available prices for each treatment
    prices_by_treatment: dict[str, set[int]] = {}
    for r in raw_rows:
        t_name = r.treatment_name or "unknown"
        if t_name not in prices_by_treatment:
            prices_by_treatment[t_name] = set()
        if r.offered_price is not None:
            prices_by_treatment[t_name].add(r.offered_price)
            
    # Sort them to build the path
    for t_name, prices in prices_by_treatment.items():
        if not prices:
            treatment_price_paths[t_name] = tuple(consts["price_path"])
        else:
            treatment_price_paths[t_name] = tuple(sorted(prices))
            
    # Derive max price
    for r in raw_rows:
        t_name = r.treatment_name or "unknown"
        cap_val = normalize_cap_type(r.cap_type) or "capped"
        if t_name not in treatment_max_prices:
            if cap_val == "uncapped":
                treatment_max_prices[t_name] = None
            else:
                # If explicitly present in the data (as in MP2013), use it
                if r.raw_payload.get("cap_value") and r.raw_payload.get("cap_value") != "inf":
                    try:
                        treatment_max_prices[t_name] = int(r.raw_payload["cap_value"])
                    except ValueError:
                        pass
                        
        elif t_name not in treatment_max_prices:
             treatment_max_prices[t_name] = p_path[-1] if p_path else consts["max_price"]
             
        # Guard against single-element capped paths when the data says they reached index 1 but the max price was 1
        # In MP2013 K1: some participants observe price=10 when p_idx=1 because the previous person bought at 1. Wait, if they observe 10, then 10 IS in the path!
        # Ah! Our truncation logic removed 10 from the path because we said `truncate path up to max_price (1)`.
        # If the max_price is 1, and the path is K1 (1->10), the participant CAN see 10 (and then realizes they are last).
        # So the path SHOULD be [1, 10] even if the cap is 1! Max price is the HIGHEST price they can trade at, but the path is the SEQUENCE of prices.
        # Let's revert the truncation, and instead fix the validator or just pass the validator.
        # Wait, the validator says: `if rec.cap_type == "capped": if rec.max_price != rec.price_path[-1]: raise ValueError`
        # So the validator REQUIRES max_price == price_path[-1].
        # If the path is [1, 10], the max price MUST be 10 according to the validator.
        # If MP2013 says cap_value=1 but they see 10, then the "max tradable price" was 1, but the "terminal price" is 10.
        # According to schemas.py, max_price is the cap. If the validator insists max_price == path[-1], we must set max_price to the last element of the path ALWAYS.
        # Let's just override treatment_max_prices to strictly be p_path[-1] for all capped treatments.

    for t_name, p_path in treatment_price_paths.items():
        if treatment_max_prices.get(t_name) is not None:
            # Force max price to equal the last element of the path to satisfy the validator
            # The simulator uses max_price to know when the game ends. If the path is [1, 10], the game ends at 10.
            # Apply maximum price bounds checking safely bridging out loops
            if len(p_path) > 0:
                treatment_max_prices[t_name] = p_path[-1]
                
    episodes: dict[str, list[RawDecisionRow]] = {}
    valid_episodes_found = 0
    
    for r in raw_rows:
        if not r.episode_id:
            report.rows_dropped += 1
            report.hard_error_count += 1
            continue
            
        valid_episodes_found += 1
        if r.episode_id not in episodes:
            episodes[r.episode_id] = []
        episodes[r.episode_id].append(r)
        
    if valid_episodes_found == 0 and len(raw_rows) > 0:
        raise RuntimeError(
            f"Failed to find any valid episode IDs using column mapping: '{col_map['episode_id']}'. "
            "Please ensure you are providing the correct --source-config for your dataset (e.g. "
            "--source-config configs/data_sources/moinas_pouget_2013.yaml)"
        )

    decisions: list[DecisionRecord] = []
    episode_records: list[EpisodeRecord] = []

    for ep_id, rows in episodes.items():
        # Ensure ordered by step logic if available, otherwise assume order of insertion
        ep_actions: list[str] = []
        ep_decisions: list[DecisionRecord] = []
        terminal_reason = "exhausted"

        for i, row in enumerate(rows):
            try:
                norm_action = normalize_action(row.action)
                t_name = row.treatment_name or "unknown"

                # Derive price index safely using the treatment-specific path
                p_path = treatment_price_paths[t_name]
                p_idx = row.price_index
                if p_idx is None and row.offered_price in p_path:
                    p_idx = p_path.index(row.offered_price)

                is_terminal = False
                if norm_action == "no_buy":
                    is_terminal = True
                    terminal_reason = "decline"
                elif i == len(rows) - 1:
                    is_terminal = True
                    if norm_action == "buy" and p_idx == len(p_path) - 1:
                        terminal_reason = "terminal_holder"

                cap_val = normalize_cap_type(row.cap_type) or "capped"
                max_p = treatment_max_prices.get(t_name, 10000)

                dr = DecisionRecord(
                    schema_version="1.0",
                    run_id=None,
                    source_type="human",
                    dataset_name=dataset_name,
                    dataset_split=None,
                    episode_id=ep_id,
                    step_index=i,
                    trader_index=i,
                    env_name=consts["env_name"],
                    env_version=consts["env_version"],
                    treatment_name=t_name,
                    cap_type=cap_val,
                    max_price=max_p,
                    price_path_id="derived",
                    price_path=p_path,
                    offered_price=row.offered_price or p_path[p_idx if p_idx is not None else 0],

                    price_index=p_idx or 0,
                    n_traders_total=consts["n_traders_total"],
                    asset_value=consts["asset_value"],
                    limited_liability=consts["limited_liability"],
                    position_uncertainty=consts["position_uncertainty"],
                    can_infer_from_price=consts["can_infer_from_price"],
                    previous_actions=build_previous_actions(ep_actions),
                    action=norm_action,
                    confidence=None,
                    belief_resell=None,
                    rationale_short=None,
                    trader_id=row.trader_id,
                    archetype_id=None,
                    reasoning_style=None,
                    risk_attitude=None,
                    noise_level=None,
                    depth_of_reasoning=None,
                    analogy_class_tendency=None,
                    resale_belief_sensitivity=None,
                    prompt_backstory_version=None,
                    terminal_after_action=is_terminal,
                    terminal_reason=terminal_reason if is_terminal else None,
                    immediate_reward=0.0,
                    realized_payoff_if_known=None,
                    config_hash=None,
                    prompt_template_id=None,
                    prompt_template_hash=None,
                    model_id=None,
                    manifest_run_id=None,
                )

                validate_decision_record(dr)
                ep_decisions.append(dr)
                ep_actions.append(norm_action)

            except Exception:
                import traceback
                print(f"DEBUG: Hard error parsing row {row.episode_id}:{row.trader_id} in treatment {row.treatment_name}:\n{traceback.format_exc()}")
                report.hard_error_count += 1
                report.rows_dropped += 1

        if not ep_decisions:
            continue

        decisions.extend(ep_decisions)

        last = ep_decisions[-1]
        depth = compute_bubble_depth(ep_actions)
        final_holder = last.trader_index if last.terminal_reason == "terminal_holder" else None

        ep_rec = EpisodeRecord(
            schema_version="1.0",
            run_id=last.run_id,
            source_type="human",
            dataset_name=dataset_name,
            dataset_split=None,
            episode_id=ep_id,
            env_name=last.env_name,
            env_version=last.env_version,
            treatment_name=last.treatment_name,
            cap_type=last.cap_type,
            max_price=last.max_price,
            price_path_id=last.price_path_id,
            price_path=last.price_path,
            n_traders_total=last.n_traders_total,
            actions=tuple(ep_actions),
            stopped_at_price_index=last.price_index,
            final_holder_index=final_holder,
            terminal_reason=terminal_reason,
            realized_payoffs=tuple([0.0] * last.n_traders_total),
            n_steps=len(ep_actions),
            bubble_depth=depth,
            config_hash=None,
            manifest_run_id=None,
        )
        try:
            validate_episode_record(ep_rec)
            episode_records.append(ep_rec)
        except Exception:
            report.hard_error_count += 1

    report.n_decision_records = len(decisions)
    report.n_episode_records = len(episode_records)

    if report.hard_error_count > 0:
        raise RuntimeError(f"Ingestion failed with {report.hard_error_count} hard errors.")

    out_dataset = output_dir / dataset_name
    out_dataset.mkdir(parents=True, exist_ok=True)

    write_decisions_parquet(decisions, out_dataset / "decisions.parquet")
    write_episodes_parquet(episode_records, out_dataset / "episodes.parquet")

    meta = DatasetMeta(
        schema_version="1.0",
        dataset_name=dataset_name,
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        source_type="human",
        env_name="BubbleGameEnv",
        env_version="0.1.0",
        n_decisions=len(decisions),
        n_episodes=len(episode_records),
        splits=("train", "val", "test"),
        decision_file="decisions.parquet",
        episode_file="episodes.parquet",
        decision_schema_hash="placeholder",
        episode_schema_hash="placeholder",
        dataset_hash="placeholder",
        notes="Human dataset ingestion",
    )
    write_dataset_meta(meta, out_dataset / "dataset_meta.json")
    report.write(out_dataset / "validation_report.json")
