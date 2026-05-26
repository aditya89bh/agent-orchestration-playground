"""Commander agent responsible for accepting and framing user goals."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CommanderAgent:
    """Normalize a user goal into a run brief for the swarm."""

    name: str = "Commander"

    def create_brief(self, goal: str, recalled_feedback: list[str] | None = None) -> dict[str, object]:
        """Create a deterministic run brief from a goal and prior feedback."""
        clean_goal = " ".join(goal.strip().split())
        if not clean_goal:
            raise ValueError("Goal must not be empty.")
        return {
            "goal": clean_goal,
            "intent": "Produce a clear, reviewable deliverable.",
            "recalled_feedback": recalled_feedback or [],
        }
