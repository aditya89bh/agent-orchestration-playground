"""Planner agent for creating memory-aware task graphs."""

from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class PlannerAgent:
    """Break a goal into deterministic steps, using recalled memory when available."""

    name: str = "PlannerAgent"

    def plan(self, goal: str, recalled_feedback: list[str] | None = None) -> TaskGraph:
        """Create a task graph for the goal.

        Recalled reviewer feedback becomes an explicit planning step on later runs.
        """
        from orchestration.task_graph import TaskGraph, TaskNode

        feedback = recalled_feedback or []
        nodes = [
            TaskNode("task-1", "Clarify user goal", f"Normalize the target outcome: {goal}"),
            TaskNode("task-2", "Identify audience", "Name the audience, pains, and desired transformation."),
        ]
        if feedback:
            nodes.append(
                TaskNode(
                    "task-3",
                    "Apply recalled reviewer feedback",
                    "Use prior lessons: " + " | ".join(feedback),
                )
            )
        nodes.extend(
            [
                TaskNode("task-4", "Draft artifact", "Create a structured, deterministic first draft."),
                TaskNode("task-5", "Review artifact", "Critique clarity, specificity, and completeness."),
                TaskNode("task-6", "Persist learning", "Store reviewer feedback for future runs."),
            ]
        )
        return TaskGraph(goal=goal, nodes=nodes)
