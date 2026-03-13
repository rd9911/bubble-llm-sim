from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RetentionConfig:
    """Configurable retention windows in days."""

    keep_failed_runs_days: int = 30
    keep_prompt_samples_days: int = 90
    keep_eval_artifacts_days: int = 365


def identify_expired_runs(
    runs_dir: str | Path,
    max_age_days: int = 30,
) -> list[Path]:
    """Returns run directories older than max_age_days."""
    cutoff = time.time() - (max_age_days * 86400)
    expired: list[Path] = []
    runs_path = Path(runs_dir)
    if not runs_path.exists():
        return expired
    for child in runs_path.iterdir():
        if child.is_dir() and child.stat().st_mtime < cutoff:
            expired.append(child)
    return sorted(expired)
