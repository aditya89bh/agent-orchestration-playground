"""Optional Postgres-backed persistence for orchestration memory and run history.

Postgres support is optional. The core project still runs with JSON and SQLite
backends without requiring a database server.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from memory.base import MemoryBackend, RunHistoryBackend


@dataclass
class PostgresStore(MemoryBackend, RunHistoryBackend):
    """Postgres persistence backend for distributed orchestration deployments."""

    database_url: str

    def __post_init__(self) -> None:
        try:
            import psycopg  # type: ignore
        except ImportError as error:
            raise RuntimeError(
                "PostgresStore requires the optional dependency: psycopg. "
                "Install with `pip install .[postgres]`."
            ) from error

        self._psycopg = psycopg
        self._initialize()

    def _connect(self):
        return self._psycopg.connect(self.database_url)

    def _initialize(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memories (
                        id BIGSERIAL PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        goal TEXT NOT NULL,
                        reviewer_feedback JSONB NOT NULL,
                        draft JSONB NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS run_history (
                        id BIGSERIAL PRIMARY KEY,
                        run_id TEXT NOT NULL UNIQUE,
                        timestamp TEXT NOT NULL,
                        goal TEXT NOT NULL,
                        approved BOOLEAN NOT NULL,
                        event_count INTEGER NOT NULL,
                        task_count INTEGER NOT NULL,
                        draft_section_count INTEGER NOT NULL
                    )
                    """
                )
            connection.commit()

    def append_memory(self, entry: dict[str, Any]) -> None:
        """Persist a reviewer feedback memory entry."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO memories (timestamp, goal, reviewer_feedback, draft)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        datetime.now(timezone.utc).isoformat(),
                        str(entry.get("goal", "")),
                        json.dumps(entry.get("reviewer_feedback", [])),
                        json.dumps(entry.get("draft", {})),
                    ),
                )
            connection.commit()

    def recall_feedback(self, goal: str, limit: int = 3) -> list[str]:
        """Recall recent feedback using deterministic keyword overlap."""
        goal_terms = self._keywords(goal)
        recalled: list[str] = []

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT goal, reviewer_feedback FROM memories ORDER BY id DESC"
                )
                rows = cursor.fetchall()

        for row_goal, reviewer_feedback in rows:
            if goal_terms & self._keywords(str(row_goal)):
                feedback = reviewer_feedback
                if isinstance(feedback, str):
                    feedback = json.loads(feedback)
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
            with connection.cursor() as cursor:
                cursor.execute(
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        record["run_id"],
                        record["timestamp"],
                        record["goal"],
                        record["approved"],
                        record["event_count"],
                        record["task_count"],
                        record["draft_section_count"],
                    ),
                )
            connection.commit()

        return record

    def list_runs(self) -> list[dict[str, Any]]:
        """Return all persisted run summaries."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT run_id, timestamp, goal, approved, event_count, task_count, draft_section_count
                    FROM run_history
                    ORDER BY id ASC
                    """
                )
                rows = cursor.fetchall()

        return [
            {
                "run_id": str(row[0]),
                "timestamp": str(row[1]),
                "goal": str(row[2]),
                "approved": bool(row[3]),
                "event_count": int(row[4]),
                "task_count": int(row[5]),
                "draft_section_count": int(row[6]),
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
