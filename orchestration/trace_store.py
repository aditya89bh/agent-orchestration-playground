"""Persistent trace storage for orchestration observability."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TraceStore:
    """SQLite-backed persistent trace store."""

    database_path: str | Path = "memory/traces.db"

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
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    workflow_namespace TEXT,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def persist(self, trace_payload: dict[str, Any]) -> None:
        """Persist a full trace payload."""
        tenant = trace_payload.get("tenant", {})
        tenant_data = tenant.get("tenant", {})

        tenant_id = tenant_data.get("tenant_id", "default-tenant")
        workflow_namespace = tenant.get("workflow_namespace", "default")

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO traces (
                    trace_id,
                    tenant_id,
                    workflow_namespace,
                    payload
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    trace_payload["trace_id"],
                    tenant_id,
                    workflow_namespace,
                    json.dumps(trace_payload),
                ),
            )
            connection.commit()

    def get_trace(
        self,
        trace_id: str,
        tenant_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Fetch one persisted trace."""
        with self._connect() as connection:
            if tenant_id:
                row = connection.execute(
                    """
                    SELECT payload
                    FROM traces
                    WHERE trace_id = ?
                    AND tenant_id = ?
                    """,
                    (trace_id, tenant_id),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT payload FROM traces WHERE trace_id = ?",
                    (trace_id,),
                ).fetchone()

        if row is None:
            return None

        return json.loads(row["payload"])

    def list_traces(
        self,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return persisted traces."""
        with self._connect() as connection:
            if tenant_id:
                rows = connection.execute(
                    """
                    SELECT payload
                    FROM traces
                    WHERE tenant_id = ?
                    """,
                    (tenant_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT payload FROM traces"
                ).fetchall()

        return [json.loads(row["payload"]) for row in rows]

    def list_tenant_namespaces(self, tenant_id: str) -> list[str]:
        """List workflow namespaces for one tenant."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT workflow_namespace
                FROM traces
                WHERE tenant_id = ?
                """,
                (tenant_id,),
            ).fetchall()

        return [row["workflow_namespace"] for row in rows]
