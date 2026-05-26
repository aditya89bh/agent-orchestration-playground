"""Runtime metrics for the orchestration API service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any


@dataclass
class RuntimeMetrics:
    """Thread-safe in-memory counters for orchestration service activity."""

    service_started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_requests: int = 0
    total_successes: int = 0
    total_failures: int = 0
    total_attempts: int = 0
    last_run: dict[str, Any] | None = None
    _lock: Lock = field(default_factory=Lock, repr=False)

    def record_success(self, result: dict[str, Any]) -> None:
        """Record a successful orchestration run."""
        with self._lock:
            self.total_requests += 1
            self.total_successes += 1
            self.total_attempts += int(result.get("attempts", 1))
            self.last_run = {
                "goal": result.get("goal"),
                "approved": result.get("review", {}).get("approved"),
                "attempts": result.get("attempts", 1),
                "backend": result.get("persistence_backend"),
                "event_count": len(result.get("event_log", [])),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def record_failure(self, error: Exception) -> None:
        """Record a failed orchestration request."""
        with self._lock:
            self.total_requests += 1
            self.total_failures += 1
            self.last_run = {
                "approved": False,
                "error": error.__class__.__name__,
                "message": str(error),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def snapshot(self) -> dict[str, Any]:
        """Return a point-in-time metrics snapshot."""
        with self._lock:
            average_attempts = (
                self.total_attempts / self.total_successes
                if self.total_successes
                else 0.0
            )
            return {
                "service_started_at": self.service_started_at,
                "total_requests": self.total_requests,
                "total_successes": self.total_successes,
                "total_failures": self.total_failures,
                "success_rate": (
                    self.total_successes / self.total_requests
                    if self.total_requests
                    else 0.0
                ),
                "average_attempts_per_success": average_attempts,
                "last_run": self.last_run,
            }
