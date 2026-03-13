from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from bubble_sim.data.io import write_dataset_meta, write_decisions_parquet, write_episodes_parquet
from bubble_sim.data.metadata import DatasetMeta
from bubble_sim.data.normalize import (
    build_previous_actions,
    compute_bubble_depth,
    normalize_action,
    normalize_cap_type,
    normalize_price_path,
)
from bubble_sim.data.raw_models import RawDecisionRow
from bubble_sim.data.reports import ValidationReport
from bubble_sim.data.schemas import DecisionRecord, EpisodeRecord
from bubble_sim.data.validators import validate_decision_record, validate_episode_record


def ingest_agent_dataset(
    traces_path: str | Path,
    dataset_name: str,
    output_dir: str | Path,
) -> None:
    traces_path = Path(traces_path)
    output_dir = Path(output_dir)

    report = ValidationReport(dataset_name=dataset_name)

    raw_rows: list[dict] = []
    with traces_path.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw_rows.append(json.loads(line))

    # Convert to RawDecisionRow
    parsed_rows: list[RawDecisionRow] = []
    for row in raw_rows:
        try:
            state = row.get("state", {})
            action = row.get("output", {}).get("action")

            parsed = RawDecisionRow(
                episode_id=state.get("episode_id"),  # type: ignore
                trader_id=row.get("profile", {}).get("trader_id"),
                offered_price=state.get("offered_price"),
                action=action,
                treatment_name=row.get("config", {}).get("treatment_name"),
                cap_type=state.get("cap_type"),
                price_index=state.get("price_index"),
                realized_payoff_if_known=row.get("reward", {}).get("realized_payoff_if_known"),
                raw_payload=row,
            )
            parsed_rows.append(parsed)
        except Exception:
            report.rows_dropped += 1

    report.n_raw_rows = len(parsed_rows) + report.rows_dropped

    # Group by episode
    episodes: dict[str, list[RawDecisionRow]] = {}
    for r in parsed_rows:
        if not r.episode_id:
            report.log_warning("missing_episode_id")
            report.hard_error_count += 1
            report.rows_dropped += 1
            continue

        if r.episode_id not in episodes:
            episodes[r.episode_id] = []
        episodes[r.episode_id].append(r)

    decisions: list[DecisionRecord] = []
    episode_records: list[EpisodeRecord] = []

    for ep_id, rows in episodes.items():
        # Order rows by price index / step index heuristically since agent trace has it
        rows.sort(key=lambda x: x.price_index if x.price_index is not None else 0)

        ep_actions: list[str] = []
        ep_payoffs: list[float] = [0.0] * rows[0].raw_payload.get("config", {}).get(
            "n_traders_total", len(rows)
        )  # crude fallback
        terminal_reason = "exhausted"

        ep_decisions: list[DecisionRecord] = []

        for i, row in enumerate(rows):
            state = row.raw_payload.get("state", {})
            cfg = row.raw_payload.get("config", {})
            profile = row.raw_payload.get("profile", {})
            out = row.raw_payload.get("output", {})

            try:
                norm_action = normalize_action(row.action)
                norm_cap = normalize_cap_type(row.cap_type)

                if norm_cap is None:
                    raise ValueError("Missing cap_type")

                is_terminal = False
                if norm_action == "no_buy":
                    is_terminal = True
                    terminal_reason = "decline"
                elif i == len(rows) - 1:
                    is_terminal = True
                    if (
                        norm_action == "buy"
                        and row.price_index == len(cfg.get("price_path", [])) - 1
                    ):
                        terminal_reason = "terminal_holder"

                dr = DecisionRecord(
                    schema_version="1.0",
                    run_id=row.raw_payload.get("manifest_run_id"),
                    source_type="agent",
                    dataset_name=dataset_name,
                    dataset_split=None,
                    episode_id=ep_id,
                    step_index=state.get("step_index", i),
                    trader_index=state.get("trader_index", i),
                    env_name="BubbleGameEnv",
                    env_version="0.1.0",
                    treatment_name=cfg.get("treatment_name", "unknown"),
                    cap_type=norm_cap,
                    max_price=cfg.get("max_price"),
                    price_path_id="derived",
                    price_path=normalize_price_path(cfg.get("price_path", [])),
                    offered_price=row.offered_price or 0,
                    price_index=row.price_index or 0,
                    n_traders_total=cfg.get("n_traders_total", 0),
                    asset_value=cfg.get("asset_value", 0),
                    limited_liability=cfg.get("limited_liability", True),
                    position_uncertainty=cfg.get("position_uncertainty", True),
                    can_infer_from_price=cfg.get("can_infer_from_price", True),
                    previous_actions=build_previous_actions(ep_actions),
                    action=norm_action,
                    confidence=out.get("confidence"),
                    belief_resell=out.get("belief_resell"),
                    rationale_short=out.get("rationale_short"),
                    trader_id=profile.get("trader_id"),
                    archetype_id=profile.get("archetype_id"),
                    reasoning_style=profile.get("reasoning_style"),
                    risk_attitude=profile.get("risk_attitude"),
                    noise_level=profile.get("noise_level"),
                    depth_of_reasoning=profile.get("depth_of_reasoning"),
                    analogy_class_tendency=profile.get("analogy_class_tendency"),
                    resale_belief_sensitivity=profile.get("resale_belief_sensitivity"),
                    prompt_backstory_version=profile.get("prompt_backstory_version"),
                    terminal_after_action=is_terminal,
                    terminal_reason=terminal_reason if is_terminal else None,
                    immediate_reward=0.0,  # Will refine
                    realized_payoff_if_known=row.realized_payoff_if_known,
                    config_hash=None,
                    prompt_template_id=row.raw_payload.get("prompt_template_id"),
                    prompt_template_hash=row.raw_payload.get("prompt_template_hash"),
                    model_id=row.raw_payload.get("model_id"),
                    manifest_run_id=row.raw_payload.get("manifest_run_id"),
                )

                validate_decision_record(dr)
                ep_decisions.append(dr)
                ep_actions.append(norm_action)

            except Exception:
                import traceback
                print(f"DEBUG: Hard error parsing agent row:\n{traceback.format_exc()}")
                report.hard_error_count += 1
                report.rows_dropped += 1

        if not ep_decisions:
            continue

        decisions.extend(ep_decisions)

        last = ep_decisions[-1]

        # Simple reconstruction of payoffs if not provided
        # Accurate evaluation happens inside bubble env, here we guess or leave 0
        depth = compute_bubble_depth(ep_actions)
        final_holder = last.trader_index if last.terminal_reason == "terminal_holder" else None

        ep_rec = EpisodeRecord(
            schema_version="1.0",
            run_id=last.run_id,
            source_type="agent",
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
            realized_payoffs=tuple(ep_payoffs),
            n_steps=len(ep_actions),
            bubble_depth=depth,
            config_hash=last.config_hash,
            manifest_run_id=last.manifest_run_id,
        )

        try:
            validate_episode_record(ep_rec)
            episode_records.append(ep_rec)
        except Exception:
            import traceback
            print(f"DEBUG: Hard error validating episode:\n{traceback.format_exc()}")
            report.hard_error_count += 1

    report.n_decision_records = len(decisions)
    report.n_episode_records = len(episode_records)

    if report.hard_error_count > 0:
        raise RuntimeError(
            f"Ingestion failed with {report.hard_error_count} hard "
            "errors. Validate report for details."
        )

    out_dataset = output_dir / dataset_name
    out_dataset.mkdir(parents=True, exist_ok=True)

    write_decisions_parquet(decisions, out_dataset / "decisions.parquet")
    write_episodes_parquet(episode_records, out_dataset / "episodes.parquet")

    meta = DatasetMeta(
        schema_version="1.0",
        dataset_name=dataset_name,
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        source_type="agent",
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
        notes="Agent dataset ingestion",
    )
    write_dataset_meta(meta, out_dataset / "dataset_meta.json")
    report.write(out_dataset / "validation_report.json")
