"""Swarm orchestrator for the commander-worker agent flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents.builder import BuilderAgent
from agents.commander import CommanderAgent
from agents.memory_agent import MemoryAgent
from agents.planner import PlannerAgent
from agents.reviewer import ReviewerAgent
from memory import MemoryStore
from orchestration.event_bus import EventBus
from orchestration.run_history import RunHistoryStore


@dataclass
class SwarmOrchestrator:
    """Coordinate commander, planner, builder, reviewer, and memory agents."""

    memory_path: str | Path = "memory/shared_state.json"
    history_path: str | Path = "memory/run_history.json"
    event_bus: EventBus = field(default_factory=EventBus)

    def __post_init__(self) -> None:
        """Initialize all deterministic agents."""
        self.commander = CommanderAgent()
        self.planner = PlannerAgent()
        self.builder = BuilderAgent()
        self.reviewer = ReviewerAgent()
        self.memory = MemoryAgent(MemoryStore(self.memory_path))
        self.history = RunHistoryStore(self.history_path)

    def run(self, goal: str) -> dict[str, Any]:
        """Run the full orchestration loop for a user goal."""
        self.event_bus.log("CommanderAgent", "accepted_goal", {"goal": goal})
        brief = self.commander.accept_goal(goal)

        recalled_feedback = self.memory.recall(brief["goal"])
        self.event_bus.log("MemoryAgent", "recalled_feedback", {"feedback": recalled_feedback})

        task_graph = self.planner.plan(brief["goal"], recalled_feedback)
        self.event_bus.log("PlannerAgent", "created_task_graph", task_graph.to_dict())

        draft = self.builder.build(brief["goal"], task_graph, recalled_feedback)
        self.event_bus.log("BuilderAgent", "created_draft", {"artifact_type": draft["artifact_type"]})

        review = self.reviewer.review(draft)
        self.event_bus.log("ReviewerAgent", "reviewed_draft", review)

        memory_entry = self.memory.remember(brief["goal"], review, draft)
        self.event_bus.log("MemoryAgent", "stored_feedback", memory_entry)

        result = {
            "goal": brief["goal"],
            "task_graph": task_graph.to_dict(),
            "draft": draft,
            "review": review,
            "event_log": self.event_bus.snapshot(),
        }

        self.event_bus.log(
            "SwarmOrchestrator",
            "completed_run",
            {"approved": review["approved"]},
        )

        result["event_log"] = self.event_bus.snapshot()

        run_record = self.history.append(result)
        result["run_record"] = run_record

        return result
