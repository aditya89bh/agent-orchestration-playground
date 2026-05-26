"""In-memory event logging for orchestration runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class EventBus:
    """Collect timestamped orchestration events for inspection."""

    events: list[dict[str, Any]] = field(default_factory=list)

    def publish(self, actor: str, action: str, details: dict[str, Any] | None = None) -> None:
        """Append an event to the log."""
        self.events.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": actor,
                "action": action,
                "details": details or {},
            }
        )

    def snapshot(self) -> list[dict[str, Any]]:
        """Return a copy of the current event log."""
        return list(self.events)
