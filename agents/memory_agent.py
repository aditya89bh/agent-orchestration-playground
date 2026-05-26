"""Memory agent wrapper around the JSON memory store."""

from dataclasses import dataclass
from typing import Any

from memory.memory_store import MemoryStore


@dataclass
class MemoryAgent:
    """Persist and recall reviewer feedback for orchestration runs."""

    store: MemoryStore
    name: str = "Memory"

    def recall(self, goal: str) -> list[str]:
        """Recall reviewer feedback related to the current goal."""
        return self.store.recall_feedback(goal)

    def remember(self, goal: str, review: dict[str, Any], final_outcome: dict[str, Any]) -> dict[str, Any]:
        """Persist review feedback and final outcome."""
        entry = {
            "goal": goal,
            "reviewer_feedback": list(review.get("feedback", [])),
            "approved": bool(review.get("approved", False)),
            "final_outcome": final_outcome,
        }
        self.store.append(entry)
        return entry
