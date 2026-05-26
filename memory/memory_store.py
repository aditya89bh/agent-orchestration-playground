"""Simple JSON-backed memory store for deterministic orchestration runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MemoryStore:
    """Persist orchestration memories in a JSON file.

    The file stores a list of entries. Each entry may include a goal,
    reviewer feedback, approval status, and final outcome.
    """

    def __init__(self, path: str | Path) -> None:
        """Create a store at the given path, initializing it if needed."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]\n", encoding="utf-8")

    def all(self) -> list[dict[str, Any]]:
        """Return all memory entries."""
        raw = self.path.read_text(encoding="utf-8").strip() or "[]"
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("Memory store must contain a JSON list.")
        return data

    def append(self, entry: dict[str, Any]) -> None:
        """Append a memory entry to disk."""
        entries = self.all()
        entries.append(entry)
        self.path.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def recall_feedback(self, goal: str, limit: int = 3) -> list[str]:
        """Recall recent reviewer feedback sharing keywords with the goal."""
        goal_terms = {token.strip(".,:;!?()[]{}\"").lower() for token in goal.split() if len(token) > 3}
        matches: list[str] = []
        for entry in reversed(self.all()):
            entry_goal = str(entry.get("goal", ""))
            entry_terms = {token.strip(".,:;!?()[]{}\"").lower() for token in entry_goal.split() if len(token) > 3}
            if goal_terms & entry_terms:
                matches.extend(str(item) for item in entry.get("reviewer_feedback", []))
            if len(matches) >= limit:
                break
        return matches[:limit]
