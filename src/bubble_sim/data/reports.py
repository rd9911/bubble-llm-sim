from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from bubble_sim.utils.serialization import to_serializable


@dataclass
class ValidationReport:
    dataset_name: str
    n_raw_rows: int = 0
    n_decision_records: int = 0
    n_episode_records: int = 0
    rows_dropped: int = 0
    hard_error_count: int = 0
    warning_count: int = 0
    warnings_by_type: dict[str, int] = field(default_factory=dict)
    null_rates: dict[str, float] = field(default_factory=dict)
    duplicates_removed: int = 0

    def log_warning(self, warn_type: str) -> None:
        self.warning_count += 1
        self.warnings_by_type[warn_type] = self.warnings_by_type.get(warn_type, 0) + 1

    def write(self, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w") as f:
            json.dump(to_serializable(self), f, indent=2)
