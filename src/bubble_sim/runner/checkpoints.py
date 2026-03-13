from __future__ import annotations

import json
from pathlib import Path


class CheckpointManager:
    """Manages resumable episode trackers avoiding explicit crash restarts."""

    def __init__(self, run_dir: str | Path) -> None:
        self.run_dir = Path(run_dir)
        self.checkpoint_path = self.run_dir / "checkpoint.json"

        self.completed_episodes: set[str] = set()
        self.failed_episodes: set[str] = set()

        self.metrics = {
            "n_episodes_completed": 0,
            "n_episodes_failed": 0,
            "total_parse_failures": 0,
            "total_fallback_uses": 0,
        }

        self.load()

    def load(self) -> None:
        if self.checkpoint_path.exists():
            with open(self.checkpoint_path) as f:
                data = json.load(f)
            self.completed_episodes = set(data.get("completed_episodes", []))
            self.failed_episodes = set(data.get("failed_episodes", []))
            self.metrics = data.get("metrics", self.metrics)

    def save(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "completed_episodes": list(self.completed_episodes),
            "failed_episodes": list(self.failed_episodes),
            "metrics": self.metrics,
        }
        with open(self.checkpoint_path, "w") as f:
            json.dump(data, f, indent=2)

    def mark_completed(self, episode_id: str, parse_failures: int, fallback_uses: int) -> None:
        self.completed_episodes.add(episode_id)
        self.metrics["n_episodes_completed"] += 1
        self.metrics["total_parse_failures"] += parse_failures
        self.metrics["total_fallback_uses"] += fallback_uses
        self.save()

    def mark_failed(self, episode_id: str) -> None:
        self.failed_episodes.add(episode_id)
        self.metrics["n_episodes_failed"] += 1
        self.save()

    def is_completed(self, episode_id: str) -> bool:
        return episode_id in self.completed_episodes
