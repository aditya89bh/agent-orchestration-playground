"""Queue primitives for orchestration jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from queue import Empty, Queue
from threading import Lock
from typing import Any
from uuid import uuid4


class JobStatus(str, Enum):
    """Lifecycle states for queued orchestration jobs."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class OrchestrationJob:
    """Queued orchestration job payload."""

    goal: str
    backend: str = "json"
    memory_path: str = "memory/shared_state.json"
    history_path: str = "memory/run_history.json"
    job_id: str = field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.QUEUED
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    result: dict[str, Any] | None = None
    error: str | None = None

    def mark_running(self) -> None:
        """Mark the job as running."""
        self.status = JobStatus.RUNNING
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def mark_succeeded(self, result: dict[str, Any]) -> None:
        """Mark the job as succeeded."""
        self.status = JobStatus.SUCCEEDED
        self.result = result
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def mark_failed(self, error: Exception) -> None:
        """Mark the job as failed."""
        self.status = JobStatus.FAILED
        self.error = f"{error.__class__.__name__}: {error}"
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the job for API responses."""
        return {
            "job_id": self.job_id,
            "goal": self.goal,
            "backend": self.backend,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class InMemoryJobQueue:
    """Thread-safe in-memory queue for orchestration jobs."""

    _queue: Queue[OrchestrationJob] = field(default_factory=Queue)
    _jobs: dict[str, OrchestrationJob] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def submit(self, job: OrchestrationJob) -> OrchestrationJob:
        """Submit a job to the queue."""
        with self._lock:
            self._jobs[job.job_id] = job
            self._queue.put(job)
        return job

    def get_nowait(self) -> OrchestrationJob | None:
        """Return the next queued job, if available."""
        try:
            return self._queue.get_nowait()
        except Empty:
            return None

    def get(self, job_id: str) -> OrchestrationJob | None:
        """Look up a job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> list[dict[str, Any]]:
        """List all known jobs."""
        with self._lock:
            return [job.to_dict() for job in self._jobs.values()]
