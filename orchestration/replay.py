"""Workflow replay primitives for trace-driven debugging."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class ReplayRecord:
    """Record produced by replaying a persisted trace."""

    trace_id: str
    replay_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    replayed_spans: list[dict[str, Any]] = field(default_factory=list)
    status: str = "completed"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the replay record."""
        return {
            "replay_id": self.replay_id,
            "trace_id": self.trace_id,
            "created_at": self.created_at,
            "status": self.status,
            "replayed_spans": self.replayed_spans,
            "notes": self.notes,
        }


@dataclass
class ReplayEngine:
    """Trace-driven replay engine for deterministic debugging."""

    replay_records: dict[str, ReplayRecord] = field(default_factory=dict)

    def replay_trace(self, trace_payload: dict[str, Any]) -> ReplayRecord:
        """Replay a full trace as a deterministic execution summary."""
        record = ReplayRecord(trace_id=str(trace_payload["trace_id"]))

        for span in trace_payload.get("spans", []):
            record.replayed_spans.append(
                {
                    "span_id": span.get("span_id"),
                    "name": span.get("name"),
                    "status": span.get("status"),
                    "attributes": span.get("attributes", {}),
                }
            )

        record.notes.append(
            "Replay is trace-driven and does not re-run external side effects."
        )
        self.replay_records[record.replay_id] = record
        return record

    def replay_node(self, trace_payload: dict[str, Any], span_name: str) -> ReplayRecord:
        """Replay spans matching a specific node/span name."""
        record = ReplayRecord(trace_id=str(trace_payload["trace_id"]))

        matching_spans = [
            span
            for span in trace_payload.get("spans", [])
            if span.get("name") == span_name
        ]

        for span in matching_spans:
            record.replayed_spans.append(
                {
                    "span_id": span.get("span_id"),
                    "name": span.get("name"),
                    "status": span.get("status"),
                    "attributes": span.get("attributes", {}),
                }
            )

        if not matching_spans:
            record.status = "empty"
            record.notes.append(f"No spans found for node/span name: {span_name}")
        else:
            record.notes.append(f"Replayed {len(matching_spans)} matching span(s).")

        self.replay_records[record.replay_id] = record
        return record

    def list_replays(self) -> list[dict[str, Any]]:
        """List all replay records."""
        return [record.to_dict() for record in self.replay_records.values()]

    def get_replay(self, replay_id: str) -> dict[str, Any] | None:
        """Return one replay record by ID."""
        record = self.replay_records.get(replay_id)
        return record.to_dict() if record else None
