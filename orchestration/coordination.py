"""Distributed worker coordination primitives.

This module introduces lightweight coordination semantics for multi-worker
orchestration systems: worker registration, heartbeats, lease ownership,
and stale worker detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4


@dataclass
class WorkerRecord:
    """Metadata for one orchestration worker node."""

    worker_id: str = field(default_factory=lambda: str(uuid4()))
    hostname: str = "localhost"
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_heartbeat: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    active_jobs: int = 0
    status: str = "active"

    def heartbeat(self) -> None:
        """Refresh the worker heartbeat timestamp."""
        self.last_heartbeat = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "hostname": self.hostname,
            "started_at": self.started_at,
            "last_heartbeat": self.last_heartbeat,
            "active_jobs": self.active_jobs,
            "status": self.status,
        }


@dataclass
class JobLease:
    """Lease ownership for distributed orchestration jobs."""

    job_id: str
    worker_id: str
    lease_timeout_seconds: int = 30
    acquired_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def expired(self) -> bool:
        """Return whether the lease has expired."""
        acquired = datetime.fromisoformat(self.acquired_at)
        expiry = acquired + timedelta(seconds=self.lease_timeout_seconds)
        return datetime.now(timezone.utc) > expiry


@dataclass
class CoordinationManager:
    """Manage worker registration and distributed leases."""

    heartbeat_timeout_seconds: int = 60
    workers: dict[str, WorkerRecord] = field(default_factory=dict)
    leases: dict[str, JobLease] = field(default_factory=dict)

    def register_worker(self, hostname: str = "localhost") -> WorkerRecord:
        """Register a new orchestration worker."""
        worker = WorkerRecord(hostname=hostname)
        self.workers[worker.worker_id] = worker
        return worker

    def heartbeat(self, worker_id: str) -> None:
        """Update worker heartbeat state."""
        worker = self.workers.get(worker_id)
        if worker:
            worker.heartbeat()

    def acquire_lease(self, job_id: str, worker_id: str) -> JobLease:
        """Assign a job lease to a worker."""
        lease = JobLease(job_id=job_id, worker_id=worker_id)
        self.leases[job_id] = lease

        worker = self.workers.get(worker_id)
        if worker:
            worker.active_jobs += 1

        return lease

    def release_lease(self, job_id: str) -> None:
        """Release a job lease."""
        lease = self.leases.pop(job_id, None)

        if lease:
            worker = self.workers.get(lease.worker_id)
            if worker and worker.active_jobs > 0:
                worker.active_jobs -= 1

    def stale_workers(self) -> list[dict[str, Any]]:
        """Return workers whose heartbeats expired."""
        stale: list[dict[str, Any]] = []

        for worker in self.workers.values():
            heartbeat = datetime.fromisoformat(worker.last_heartbeat)
            expiry = heartbeat + timedelta(seconds=self.heartbeat_timeout_seconds)

            if datetime.now(timezone.utc) > expiry:
                worker.status = "stale"
                stale.append(worker.to_dict())

        return stale

    def recoverable_leases(self) -> list[dict[str, Any]]:
        """Return expired leases that can be reassigned."""
        recoverable: list[dict[str, Any]] = []

        for lease in self.leases.values():
            if lease.expired():
                recoverable.append(
                    {
                        "job_id": lease.job_id,
                        "worker_id": lease.worker_id,
                        "expired": True,
                    }
                )

        return recoverable
