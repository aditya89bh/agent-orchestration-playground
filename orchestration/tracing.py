"""Lightweight tracing primitives for orchestration runs.

This module intentionally keeps tracing dependency-free while preserving concepts that
map cleanly to OpenTelemetry later: trace IDs, span IDs, parent-child relationships,
span names, timestamps, status, and attributes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class TraceSpan:
    """Single trace span for an orchestration lifecycle step."""

    name: str
    trace_id: str
    parent_span_id: str | None = None
    span_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ended_at: str | None = None
    status: str = "running"
    attributes: dict[str, Any] = field(default_factory=dict)

    def finish(self, status: str = "ok", **attributes: Any) -> None:
        """Mark the span complete and merge final attributes."""
        self.status = status
        self.ended_at = datetime.now(timezone.utc).isoformat()
        self.attributes.update(attributes)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the span."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "status": self.status,
            "attributes": self.attributes,
        }


@dataclass
class TraceRecorder:
    """In-memory trace recorder for one orchestration run."""

    trace_id: str = field(default_factory=lambda: str(uuid4()))
    spans: list[TraceSpan] = field(default_factory=list)

    def start_span(
        self,
        name: str,
        parent_span_id: str | None = None,
        **attributes: Any,
    ) -> TraceSpan:
        """Start and store a trace span."""
        span = TraceSpan(
            name=name,
            trace_id=self.trace_id,
            parent_span_id=parent_span_id,
            attributes=attributes,
        )
        self.spans.append(span)
        return span

    def snapshot(self) -> dict[str, Any]:
        """Return the current trace payload."""
        return {
            "trace_id": self.trace_id,
            "spans": [span.to_dict() for span in self.spans],
        }
