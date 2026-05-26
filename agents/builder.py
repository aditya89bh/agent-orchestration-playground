"""Builder agent for producing deterministic draft artifacts."""

from dataclasses import dataclass
from typing import Any



@dataclass(frozen=True)
class BuilderAgent:
    """Create a readable draft from a goal and task graph."""

    name: str = "BuilderAgent"

    def build(self, goal: str, task_graph: Any, recalled_feedback: list[str] | None = None) -> dict[str, Any]:
        """Build a deterministic draft output."""
        sections = [
            {
                "title": "Hero",
                "content": "AI consulting that turns messy workflows into reliable automated systems.",
            },
            {
                "title": "Audience",
                "content": "Founders and operators who need practical AI systems, not vague AI strategy.",
            },
            {
                "title": "Problem",
                "content": "Teams lose time to manual processes, scattered knowledge, and fragile handoffs.",
            },
            {
                "title": "Offer",
                "content": "Workflow audits, agent prototypes, memory systems, evaluations, and deployment plans.",
            },
            {
                "title": "Proof",
                "content": "Show examples of automation wins, prototype speed, and reliability improvements.",
            },
            {
                "title": "Call to Action",
                "content": "Book a focused discovery call to identify one high-leverage AI workflow.",
            },
        ]
        if recalled_feedback:
            sections.append(
                {
                    "title": "Memory-Informed Revision Notes",
                    "content": "Applied prior feedback: " + " | ".join(recalled_feedback),
                }
            )
        return {
            "goal": goal,
            "artifact_type": "landing_page_outline" if "landing page" in goal.lower() else "structured_outline",
            "task_ids_used": [node.id for node in task_graph.nodes],
            "sections": sections,
        }
