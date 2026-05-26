"""Event logging for major agent actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class EventBus:
    """In-memory event bus that records timestamped orchestration events."""

    events: list[dict[str, Any]] = field(default_factory=list)

    def log(self, actor: str, action: str, details: dict[str, Any] | None = None) -> None:
        """Record a major action in the event log."""
        self.events.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": actor,
                "action": action,
                "details": details or {},
            }
        )

    def snapshot(self) -> list[dict[str, Any]]:
        """Return a shallow copy of the event log."""
        return list(self.events)
