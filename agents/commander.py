"""Commander agent for accepting and normalizing user goals."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CommanderAgent:
    """Accept a user goal and create a clean orchestration brief."""

    name: str = "CommanderAgent"

    def accept_goal(self, goal: str) -> dict[str, str]:
        """Validate and normalize a user goal."""
        normalized = " ".join(goal.strip().split())
        if not normalized:
            raise ValueError("Goal must not be empty.")
        return {
            "goal": normalized,
            "success_criteria": "Produce a clear draft, review it, and persist useful feedback.",
        }
