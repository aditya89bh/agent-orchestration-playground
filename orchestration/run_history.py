"""Persistent run history for orchestration executions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from memory.base import RunHistoryBackend


@dataclass
class RunHistoryStore(RunHistoryBackend):
    """Append-only JSON store for completed orchestration runs."""

    path: str | Path = "memory/run_history.json"

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def load(self) -> list[dict[str, Any]]:
        """Load all recorded runs."""
        raw = self.path.read_text(encoding="utf-8").strip()
        if not raw:
            return []
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("Run history store must contain a JSON list.")
        return data

    def append_run(self, result: dict[str, Any]) -> dict[str, Any]:
        """Append a compact run summary and return it."""
        runs = self.load()
        record = {
            "run_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "goal": result["goal"],
            "approved": result["review"]["approved"],
            "event_count": len(result["event_log"]),
            "task_count": len(result["task_graph"]["nodes"]),
            "draft_section_count": len(result["draft"]["sections"]),
        }
        runs.append(record)
        self.path.write_text(json.dumps(runs, indent=2), encoding="utf-8")
        return record

    def list_runs(self) -> list[dict[str, Any]]:
        """List all orchestration run summaries."""
        return self.load()

    def clear(self) -> None:
        """Clear all run history."""
        self.path.write_text("[]", encoding="utf-8")
