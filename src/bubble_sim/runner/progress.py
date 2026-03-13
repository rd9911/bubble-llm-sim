from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProgressTracker:
    run_dir: Path

    def emit_metrics(self, checkpoint_metrics: dict, total_requested: int) -> None:
        """Safely calculate clean averages computing metrics cleanly."""
        completed = checkpoint_metrics.get("n_episodes_completed", 0)
        fallbacks = checkpoint_metrics.get("total_fallback_uses", 0)
        parses = checkpoint_metrics.get("total_parse_failures", 0)

        rate = 0.0
        if completed > 0:
            rate = max(0.0, (completed - fallbacks) / completed)

        data = {
            "n_episodes_requested": total_requested,
            "n_episodes_completed": completed,
            "n_episodes_failed": checkpoint_metrics.get("n_episodes_failed", 0),
            "clean_completion_rate": round(rate, 4),
            "total_parse_failures": parses,
            "total_fallback_uses": fallbacks,
        }

        out_path = self.run_dir / "metrics.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
