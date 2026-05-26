"""Reviewer agent for deterministic draft critique."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReviewerAgent:
    """Critique draft artifacts and return actionable feedback."""

    name: str = "ReviewerAgent"

    def review(self, draft: dict[str, Any]) -> dict[str, Any]:
        """Review a draft for completeness, clarity, specificity, and actionability."""
        sections = draft.get("sections", [])
        titles = {str(section.get("title", "")).lower() for section in sections if isinstance(section, dict)}
        feedback: list[str] = []

        if {"hero", "problem", "offer", "proof", "call to action"}.issubset(titles):
            feedback.append("The draft has a complete landing-page arc from promise to CTA.")
        else:
            feedback.append("Add hero, problem, offer, proof, and CTA sections for a complete arc.")

        feedback.append("Make the audience more specific and include measurable business outcomes.")
        feedback.append("Add concrete proof points, such as examples, metrics, or short case studies.")

        return {
            "approved": len(sections) >= 6,
            "score": min(10, 4 + len(sections)),
            "feedback": feedback,
        }
