from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import orjson


class TraceWriter:
    def __init__(self, output_path: str | Path):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: dict[str, Any], flush: bool = True) -> None:
        """Append a JSON event to the traces file."""
        data = orjson.dumps(event)
        with open(self.output_path, "ab") as f:
            f.write(data + b"\n")
            if flush:
                os.fsync(f.fileno())

    def read_all(self) -> list[dict[str, Any]]:
        """Read all events from the traces file."""
        if not self.output_path.exists():
            return []

        events = []
        with open(self.output_path, "rb") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(orjson.loads(line))
        return events
