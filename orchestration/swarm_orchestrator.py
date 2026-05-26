"""Commander-worker swarm orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents import BuilderAgent, CommanderAgent, MemoryAgent, PlannerAgent, ReviewerAgent
from memory import MemoryStore
from orchestration.event_bus import EventBus


@dataclass
class SwarmOrchestrator:
    """Coordinate planner, builder, reviewer, and memory agents for a goal."""

    memory_path: str | Path = "memory/runtime_memory.json"
    event_bus: EventBus = field(default_factory=EventBus)

    def __post_init__(self) -> None:
        """Initialize deterministic agents."""
        self.commander = CommanderAgent()
        self.planner = PlannerAgent()
        self.builder = BuilderAgent()
        self.reviewer = ReviewerAgent()
        self.memory = MemoryAgent(MemoryStore(self.memory_path))

    def run(self, goal: str) -> dict[str, Any]:
        """Execute the full swarm flow and return final result with logs."""
        self.event_bus.publish("Commander", "received_goal", {"goal": goal})

        recalled = self.memory.recall(goal)
        self.event_bus.publish("Memory", "recalled_feedback", {"items": recalled})

        brief = self.commander.create_brief(goal, recalled)
        self.event_bus.publish("Commander", "created_brief", {"brief": brief})

        plan = self.planner.plan(brief)
        self.event_bus.publish("Planner", "created_plan", {"steps": plan})

        draft = self.builder.build(str(brief["goal"]), plan, recalled)
        self.event_bus.publish("Builder", "built_draft", {"artifact_type": draft["artifact_type"]})

        review = self.reviewer.review(draft, recalled)
        self.event_bus.publish("Reviewer", "reviewed_draft", review)

        final_outcome = {
            "goal": brief["goal"],
            "draft": draft,
            "review": review,
        }
        memory_entry = self.memory.remember(str(brief["goal"]), review, final_outcome)
        self.event_bus.publish("Memory", "stored_outcome", {"approved": memory_entry["approved"]})

        result = {
            "final_result": final_outcome,
            "event_logs": self.event_bus.snapshot(),
        }
        self.event_bus.publish("Commander", "completed_run", {"approved": review["approved"]})
        result["event_logs"] = self.event_bus.snapshot()
        return result
