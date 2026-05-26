"""SQLite-backed persistence for memories and orchestration run history."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from memory.base import MemoryBackend, RunHistoryBackend


@dataclass
class SQLiteStore(MemoryBackend, RunHistoryBackend):
    """SQLite persistence layer for production-oriented local storage."""

    path: str | Path = "memory/orchestration.db"

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    reviewer_feedback TEXT NOT NULL,
                    draft TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS run_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    approved INTEGER NOT NULL,
                    event_count INTEGER NOT NULL,
                    task_count INTEGER NOT NULL,
                    draft_section_count INTEGER NOT NULL
                )
                """
            )

    def append_memory(self, entry: dict[str, Any]) -> None:
        """Persist a reviewer feedback memory entry."""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO memories (timestamp, goal, reviewer_feedback, draft)
                VALUES (?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    str(entry.get("goal", "")),
                    json.dumps(entry.get("reviewer_feedback", [])),
                    json.dumps(entry.get("draft", {})),
                ),
            )

    def recall_feedback(self, goal: str, limit: int = 3) -> list[str]:
        """Recall recent feedback using deterministic keyword overlap."""
        goal_terms = self._keywords(goal)
        recalled: list[str] = []

        with self._connect() as connection:
            rows = connection.execute(
                "SELECT goal, reviewer_feedback FROM memories ORDER BY id DESC"
            ).fetchall()

        for row in rows:
            if goal_terms & self._keywords(str(row["goal"])):
                feedback = json.loads(str(row["reviewer_feedback"]))
                recalled.extend(str(item) for item in feedback)
            if len(recalled) >= limit:
                break

        return recalled[:limit]

    def append_run(self, result: dict[str, Any]) -> dict[str, Any]:
        """Persist a compact orchestration run summary."""
        record = {
            "run_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "goal": result["goal"],
            "approved": bool(result["review"]["approved"]),
            "event_count": len(result["event_log"]),
            "task_count": len(result["task_graph"]["nodes"]),
            "draft_section_count": len(result["draft"]["sections"]),
        }

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO run_history (
                    run_id,
                    timestamp,
                    goal,
                    approved,
                    event_count,
                    task_count,
                    draft_section_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["run_id"],
                    record["timestamp"],
                    record["goal"],
                    int(record["approved"]),
                    record["event_count"],
                    record["task_count"],
                    record["draft_section_count"],
                ),
            )

        return record

    def list_runs(self) -> list[dict[str, Any]]:
        """Return all persisted run summaries."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT run_id, timestamp, goal, approved, event_count, task_count, draft_section_count
                FROM run_history
                ORDER BY id ASC
                """
            ).fetchall()

        return [
            {
                "run_id": str(row["run_id"]),
                "timestamp": str(row["timestamp"]),
                "goal": str(row["goal"]),
                "approved": bool(row["approved"]),
                "event_count": int(row["event_count"]),
                "task_count": int(row["task_count"]),
                "draft_section_count": int(row["draft_section_count"]),
            }
            for row in rows
        ]

    @staticmethod
    def _keywords(text: str) -> set[str]:
        """Extract simple deterministic keywords from text."""
        return {
            token.strip(".,:;!?()[]{}\"'").lower()
            for token in text.split()
            if len(token) > 3
        }
