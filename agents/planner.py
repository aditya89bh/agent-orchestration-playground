"""Planner agent that breaks a goal into deterministic work steps."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlannerAgent:
    """Create a small execution plan for a user goal."""

    name: str = "Planner"

    def plan(self, brief: dict[str, object]) -> list[str]:
        """Return deterministic steps tailored lightly to the goal text."""
        goal = str(brief["goal"])
        steps = [
            f"Clarify the target outcome for: {goal}",
            "Identify the primary audience and their pain points.",
            "Draft the core sections of the deliverable.",
            "Add a concise call to action and success criteria.",
        ]
        if "landing page" in goal.lower():
            steps.insert(2, "Define the hero, trust, offer, proof, and CTA sections.")
        return steps
