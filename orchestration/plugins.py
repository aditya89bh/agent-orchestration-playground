"""Built-in plugins for orchestration runtime extensions."""

from __future__ import annotations

from typing import Any

from orchestration.plugin_registry import PluginDefinition, PluginRegistry


registry = PluginRegistry()


def summarize_goal(goal: str, **_: Any) -> dict[str, Any]:
    """Generate a deterministic goal summary."""
    tokens = goal.split()

    return {
        "summary": " ".join(tokens[:12]),
        "word_count": len(tokens),
    }


def classify_goal(goal: str, **_: Any) -> dict[str, Any]:
    """Classify orchestration goals into simple categories."""
    lowered = goal.lower()

    if "api" in lowered or "backend" in lowered:
        category = "backend"
    elif "ui" in lowered or "frontend" in lowered:
        category = "frontend"
    elif "memory" in lowered or "agent" in lowered:
        category = "agent_system"
    else:
        category = "general"

    return {
        "goal": goal,
        "category": category,
    }


registry.register(
    PluginDefinition(
        name="goal_summarizer",
        description="Summarize orchestration goals.",
        handler=summarize_goal,
        tags=["analysis", "summary"],
    )
)

registry.register(
    PluginDefinition(
        name="goal_classifier",
        description="Classify orchestration goals.",
        handler=classify_goal,
        tags=["analysis", "classification"],
    )
)
