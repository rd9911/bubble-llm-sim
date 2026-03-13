from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_eval_report(
    eval_dir: str | Path,
    eval_manifest: dict[str, Any],
    run_health: dict[str, Any],
    micro: dict[str, Any],
    macro: dict[str, Any],
    calibration: dict[str, Any],
    gate_result: dict[str, Any],
    scorecard: dict[str, Any],
) -> None:
    """Assembles a complete evaluation report bundle."""
    path = Path(eval_dir)
    path.mkdir(parents=True, exist_ok=True)

    _write_json(path / "eval_manifest.json", eval_manifest)
    _write_json(path / "run_health.json", run_health)
    _write_json(path / "micro_summary.json", micro)
    _write_json(path / "macro_summary.json", macro)
    _write_json(path / "calibration_summary.json", calibration)
    _write_json(
        path / "leaderboard_row.json",
        {**calibration, **gate_result},
    )

    md = _render_markdown(
        eval_manifest,
        run_health,
        micro,
        macro,
        calibration,
        gate_result,
        scorecard,
    )
    (path / "report.md").write_text(md)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _render_markdown(
    manifest: dict[str, Any],
    run_health: dict[str, Any],
    micro: dict[str, Any],
    macro: dict[str, Any],
    calibration: dict[str, Any],
    gate_result: dict[str, Any],
    scorecard: dict[str, Any],
) -> str:
    lines = [
        f"# Evaluation Report: {manifest.get('eval_id', 'unknown')}",
        "",
        "## Run Health",
    ]
    for k, v in run_health.items():
        lines.append(f"- **{k}**: {v}")

    lines += ["", "## Micro Fidelity"]
    for k, v in micro.items():
        lines.append(f"- **{k}**: {v}")

    lines += ["", "## Macro Fidelity"]
    for k, v in macro.items():
        lines.append(f"- **{k}**: {v}")

    lines += ["", "## Calibration"]
    for k, v in calibration.items():
        lines.append(f"- **{k}**: {v}")

    lines += ["", "## Promotion Gates"]
    passed = gate_result.get("passed_gate", False)
    symbol = "✅" if passed else "❌"
    lines.append(f"**Overall**: {symbol} {'PASSED' if passed else 'FAILED'}")
    for k in ["gate1_operational", "gate2_micro", "gate3_macro", "gate4_heldout"]:
        v = gate_result.get(k, False)
        s = "✅" if v else "❌"
        lines.append(f"- {k}: {s}")

    lines += ["", "## Scorecard"]
    for category, items in scorecard.items():
        lines.append(f"### {category}")
        for metric, color in items.items():
            emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(color, "⚪")
            lines.append(f"- {metric}: {emoji} {color}")

    lines.append("")
    return "\n".join(lines)
