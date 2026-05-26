"""Simple task graph objects used by the planner and orchestrator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskNode:
    """A deterministic unit of planned work."""

    id: str
    title: str
    description: str

    def to_dict(self) -> dict[str, str]:
        """Serialize the task node."""
        return {"id": self.id, "title": self.title, "description": self.description}


@dataclass(frozen=True)
class TaskGraph:
    """Ordered task graph for this playground's linear swarm flow."""

    goal: str
    nodes: list[TaskNode]

    def to_dict(self) -> dict[str, object]:
        """Serialize the task graph."""
        return {"goal": self.goal, "nodes": [node.to_dict() for node in self.nodes]}
