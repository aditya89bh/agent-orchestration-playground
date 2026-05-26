"""Builder agent that turns plan steps into a simple artifact."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BuilderAgent:
    """Build a deterministic draft from plan steps and recalled feedback."""

    name: str = "Builder"

    def build(self, goal: str, steps: list[str], recalled_feedback: list[str] | None = None) -> dict[str, object]:
        """Create a structured draft artifact."""
        lessons = recalled_feedback or []
        sections = [
            {"title": "Hero", "content": f"State the promise clearly: {goal}"},
            {"title": "Problem", "content": "Describe the operational pain the audience already recognizes."},
            {"title": "Solution", "content": "Show how AI systems, workflows, and automation reduce that pain."},
            {"title": "Proof", "content": "Include examples, metrics, case studies, or credible founder/operator context."},
            {"title": "Call to Action", "content": "Invite visitors to book a focused discovery call."},
        ]
        if lessons:
            sections.append({"title": "Memory-Informed Improvements", "content": " | ".join(lessons)})
        return {
            "goal": goal,
            "steps_used": steps,
            "artifact_type": "landing_page_outline" if "landing page" in goal.lower() else "general_outline",
            "sections": sections,
        }
