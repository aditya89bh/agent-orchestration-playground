"""Swarm orchestrator for the commander-worker agent flow."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents.builder import BuilderAgent
from agents.commander import CommanderAgent
from agents.memory_agent import MemoryAgent
from agents.planner import PlannerAgent
from agents.reviewer import ReviewerAgent
from memory import MemoryStore
from memory.base import MemoryBackend, RunHistoryBackend
from memory.sqlite_store import SQLiteStore
from orchestration.event_bus import EventBus
from orchestration.retry_policy import RetryPolicy
from orchestration.run_history import RunHistoryStore
from orchestration.structured_logger import StructuredRunLogger, build_json_logger


@dataclass
class SwarmOrchestrator:
    """Coordinate commander, planner, builder, reviewer, and memory agents."""

    memory_path: str | Path = "memory/shared_state.json"
    history_path: str | Path = "memory/run_history.json"
    persistence_backend: str = "json"
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    event_bus: EventBus = field(default_factory=EventBus)

    def __post_init__(self) -> None:
        """Initialize deterministic orchestration components."""
        self.commander = CommanderAgent()
        self.planner = PlannerAgent()
        self.builder = BuilderAgent()
        self.reviewer = ReviewerAgent()

        self.memory_backend: MemoryBackend
        self.history_backend: RunHistoryBackend

        if self.persistence_backend == "sqlite":
            sqlite_store = SQLiteStore("memory/orchestration.db")
            self.memory_backend = sqlite_store
            self.history_backend = sqlite_store
        else:
            self.memory_backend = MemoryStore(self.memory_path)
            self.history_backend = RunHistoryStore(self.history_path)

        self.memory = MemoryAgent(self.memory_backend)

        self.structured_logger = StructuredRunLogger(
            logger=build_json_logger(),
        )

    def run(self, goal: str) -> dict[str, Any]:
        """Run the full orchestration loop for a user goal."""
        self.structured_logger.info(
            "orchestration_started",
            backend=self.persistence_backend,
            goal=goal,
        )

        self.event_bus.log("CommanderAgent", "accepted_goal", {"goal": goal})
        brief = self.commander.accept_goal(goal)

        recalled_feedback = self.memory.recall(brief["goal"])
        self.event_bus.log("MemoryAgent", "recalled_feedback", {"feedback": recalled_feedback})

        task_graph = self.planner.plan(brief["goal"], recalled_feedback)
        self.event_bus.log("PlannerAgent", "created_task_graph", task_graph.to_dict())

        draft, review, attempts = self._run_retry_loop(
            brief["goal"],
            task_graph,
            recalled_feedback,
        )

        memory_entry = self.memory.remember(brief["goal"], review, draft)
        self.event_bus.log("MemoryAgent", "stored_feedback", memory_entry)

        result = self._build_result(brief["goal"], task_graph.to_dict(), draft, review)
        result["attempts"] = attempts

        return self._complete_run(result, review)

    async def arun(self, goal: str) -> dict[str, Any]:
        """Run the orchestration loop through an async-compatible entrypoint."""
        self.structured_logger.info(
            "async_orchestration_started",
            backend=self.persistence_backend,
            goal=goal,
        )

        self.event_bus.log("CommanderAgent", "accepted_goal", {"goal": goal})
        brief = await asyncio.to_thread(self.commander.accept_goal, goal)

        recalled_feedback = await asyncio.to_thread(self.memory.recall, brief["goal"])
        self.event_bus.log("MemoryAgent", "recalled_feedback", {"feedback": recalled_feedback})

        task_graph = await asyncio.to_thread(
            self.planner.plan,
            brief["goal"],
            recalled_feedback,
        )
        self.event_bus.log("PlannerAgent", "created_task_graph", task_graph.to_dict())

        draft, review, attempts = await self._arun_retry_loop(
            brief["goal"],
            task_graph,
            recalled_feedback,
        )

        memory_entry = await asyncio.to_thread(
            self.memory.remember,
            brief["goal"],
            review,
            draft,
        )
        self.event_bus.log("MemoryAgent", "stored_feedback", memory_entry)

        result = self._build_result(brief["goal"], task_graph.to_dict(), draft, review)
        result["attempts"] = attempts

        return await asyncio.to_thread(self._complete_run, result, review)

    def _run_retry_loop(
        self,
        goal: str,
        task_graph: Any,
        recalled_feedback: list[str],
    ) -> tuple[dict[str, Any], dict[str, Any], int]:
        """Run a bounded synchronous retry loop."""
        attempt = 1

        while True:
            draft = self.builder.build(goal, task_graph, recalled_feedback)
            self.event_bus.log(
                "BuilderAgent",
                "created_draft",
                {
                    "artifact_type": draft["artifact_type"],
                    "attempt": attempt,
                },
            )

            review = self.reviewer.review(draft)
            self.event_bus.log(
                "ReviewerAgent",
                "reviewed_draft",
                {
                    **review,
                    "attempt": attempt,
                },
            )

            retry_decision = self.retry_policy.decide(attempt, review)
            self.event_bus.log(
                "RetryPolicy",
                retry_decision.reason,
                {
                    "attempt": attempt,
                    "should_retry": retry_decision.should_retry,
                },
            )

            if not retry_decision.should_retry:
                return draft, review, attempt

            attempt = retry_decision.next_attempt
            recalled_feedback.extend(review.get("feedback", []))

    async def _arun_retry_loop(
        self,
        goal: str,
        task_graph: Any,
        recalled_feedback: list[str],
    ) -> tuple[dict[str, Any], dict[str, Any], int]:
        """Run a bounded asynchronous retry loop."""
        attempt = 1

        while True:
            draft = await asyncio.to_thread(
                self.builder.build,
                goal,
                task_graph,
                recalled_feedback,
            )
            self.event_bus.log(
                "BuilderAgent",
                "created_draft",
                {
                    "artifact_type": draft["artifact_type"],
                    "attempt": attempt,
                },
            )

            review = await asyncio.to_thread(self.reviewer.review, draft)
            self.event_bus.log(
                "ReviewerAgent",
                "reviewed_draft",
                {
                    **review,
                    "attempt": attempt,
                },
            )

            retry_decision = self.retry_policy.decide(attempt, review)
            self.event_bus.log(
                "RetryPolicy",
                retry_decision.reason,
                {
                    "attempt": attempt,
                    "should_retry": retry_decision.should_retry,
                },
            )

            if not retry_decision.should_retry:
                return draft, review, attempt

            attempt = retry_decision.next_attempt
            recalled_feedback.extend(review.get("feedback", []))

    def _build_result(
        self,
        goal: str,
        task_graph: dict[str, Any],
        draft: dict[str, Any],
        review: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the public orchestration result payload."""
        return {
            "goal": goal,
            "task_graph": task_graph,
            "draft": draft,
            "review": review,
            "event_log": self.event_bus.snapshot(),
            "persistence_backend": self.persistence_backend,
            "structured_run_id": self.structured_logger.run_id,
        }

    def _complete_run(self, result: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
        """Finalize event logging and persist the run summary."""
        self.event_bus.log(
            "SwarmOrchestrator",
            "completed_run",
            {
                "approved": review["approved"],
                "backend": self.persistence_backend,
            },
        )

        result["event_log"] = self.event_bus.snapshot()
        run_record = self.history_backend.append_run(result)
        result["run_record"] = run_record

        self.structured_logger.info(
            "orchestration_completed",
            backend=self.persistence_backend,
            approved=review["approved"],
            event_count=len(result["event_log"]),
            attempts=result.get("attempts", 1),
        )

        return result
