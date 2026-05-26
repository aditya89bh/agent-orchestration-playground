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
                    payload TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def persist(self, trace_payload: dict[str, Any]) -> None:
        """Persist a full trace payload."""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO traces (trace_id, payload)
                VALUES (?, ?)
                """,
                (
                    trace_payload["trace_id"],
                    json.dumps(trace_payload),
                ),
            )
            connection.commit()

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        """Fetch one persisted trace."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM traces WHERE trace_id = ?",
                (trace_id,),
            ).fetchone()

        if row is None:
            return None

        return json.loads(row["payload"])

    def list_traces(self) -> list[dict[str, Any]]:
        """Return all persisted traces."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM traces"
            ).fetchall()

        return [json.loads(row["payload"]) for row in rows]
