"""Memory agent for recalling and storing reviewer feedback."""

from dataclasses import dataclass
from typing import Any

from memory.memory_store import MemoryStore


@dataclass
class MemoryAgent:
    """Agent wrapper around the JSON-backed memory store."""

    store: MemoryStore
    name: str = "MemoryAgent"

    def recall(self, goal: str) -> list[str]:
        """Recall previous reviewer feedback relevant to the goal."""
        return self.store.recall_feedback(goal)

    def remember(self, goal: str, review: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
        """Store reviewer feedback and final draft information."""
        entry = {
            "goal": goal,
            "reviewer_feedback": list(review.get("feedback", [])),
            "approved": bool(review.get("approved", False)),
            "score": int(review.get("score", 0)),
            "draft_artifact_type": str(draft.get("artifact_type", "unknown")),
        }
        self.store.append(entry)
        return entry
