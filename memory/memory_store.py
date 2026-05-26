"""JSON-backed memory store for reviewer feedback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MemoryStore:
    """Persist and recall reviewer feedback in a JSON file."""

    def __init__(self, path: str | Path) -> None:
        """Initialize a memory store at the given path."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]\n", encoding="utf-8")

    def read_all(self) -> list[dict[str, Any]]:
        """Read all memory entries from disk."""
        raw = self.path.read_text(encoding="utf-8").strip() or "[]"
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("Memory store must contain a JSON list.")
        return data

    def append(self, entry: dict[str, Any]) -> None:
        """Append one entry to memory."""
        entries = self.read_all()
        entries.append(entry)
        self.path.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def recall_feedback(self, goal: str, limit: int = 3) -> list[str]:
        """Recall recent feedback with simple keyword overlap against the goal."""
        goal_terms = self._keywords(goal)
        recalled: list[str] = []
        for entry in reversed(self.read_all()):
            if goal_terms & self._keywords(str(entry.get("goal", ""))):
                recalled.extend(str(item) for item in entry.get("reviewer_feedback", []))
            if len(recalled) >= limit:
                break
        return recalled[:limit]

    @staticmethod
    def _keywords(text: str) -> set[str]:
        """Extract simple deterministic keywords from text."""
        return {token.strip(".,:;!?()[]{}\"'").lower() for token in text.split() if len(token) > 3}
