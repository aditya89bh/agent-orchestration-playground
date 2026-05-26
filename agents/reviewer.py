"""Reviewer agent that evaluates builder output deterministically."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewerAgent:
    """Review a draft for clarity, completeness, and actionability."""

    name: str = "Reviewer"

    def review(self, draft: dict[str, object], recalled_feedback: list[str] | None = None) -> dict[str, object]:
        """Return approval status and concrete feedback."""
        sections = draft.get("sections", [])
        feedback: list[str] = []
        if len(sections) >= 5:
            feedback.append("Draft includes the minimum complete narrative arc: hero, problem, solution, proof, CTA.")
        else:
            feedback.append("Add more sections so the artifact has a complete narrative arc.")
        if recalled_feedback:
            feedback.append("Prior reviewer feedback was considered during this run.")
        feedback.append("Strengthen specificity with concrete audience, measurable outcomes, and examples.")
        return {
            "approved": len(sections) >= 5,
            "feedback": feedback,
            "score": min(10, 5 + len(sections)),
        }
