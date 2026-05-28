"""Persistent storage for scheduled workflow executions."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SchedulerExecutionStore:
    """SQLite-backed scheduled execution persistence."""

    database_path: str | Path = "memory/scheduler.db"

    def __post_init__(self) -> None:
        self.database_path = str(self.database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scheduled_executions (
                    execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    workflow_namespace TEXT,
                    executed_at TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def persist_execution(
        self,
        execution_payload: dict[str, Any],
    ) -> None:
        """Persist one scheduled workflow execution."""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scheduled_executions (
                    schedule_id,
                    workflow_id,
                    tenant_id,
                    workflow_namespace,
                    executed_at,
                    success,
                    payload
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution_payload["schedule_id"],
                    execution_payload["workflow_id"],
                    execution_payload["tenant_id"],
                    execution_payload["workflow_namespace"],
                    execution_payload["executed_at"],
                    int(execution_payload["success"]),
                    json.dumps(execution_payload),
                ),
            )
            connection.commit()

    def list_executions(
        self,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List persisted scheduled executions."""
        with self._connect() as connection:
            if tenant_id:
                rows = connection.execute(
                    """
                    SELECT payload
                    FROM scheduled_executions
                    WHERE tenant_id = ?
                    ORDER BY executed_at DESC
                    """,
                    (tenant_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT payload
                    FROM scheduled_executions
                    ORDER BY executed_at DESC
                    """
                ).fetchall()

        return [json.loads(row["payload"]) for row in rows]

    def list_namespace_executions(
        self,
        tenant_id: str,
        workflow_namespace: str,
    ) -> list[dict[str, Any]]:
        """List executions for one tenant namespace."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload
                FROM scheduled_executions
                WHERE tenant_id = ?
                AND workflow_namespace = ?
                ORDER BY executed_at DESC
                """,
                (tenant_id, workflow_namespace),
            ).fetchall()

        return [json.loads(row["payload"]) for row in rows]
