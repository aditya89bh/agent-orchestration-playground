"""Optional Redis-backed queue for distributed orchestration jobs.

Redis support is intentionally optional. The core project still runs with the
in-memory queue when Redis is not installed or configured.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from orchestration.queue import JobStatus, OrchestrationJob


@dataclass
class RedisJobQueue:
    """Redis-backed orchestration queue for distributed workers."""

    redis_url: str = "redis://localhost:6379/0"
    queue_key: str = "agent_orchestration:jobs"
    job_key_prefix: str = "agent_orchestration:job"

    def __post_init__(self) -> None:
        try:
            import redis  # type: ignore
        except ImportError as error:
            raise RuntimeError(
                "RedisJobQueue requires the optional dependency: redis. "
                "Install with `pip install redis`."
            ) from error

        self.client = redis.Redis.from_url(self.redis_url, decode_responses=True)

    def submit(self, job: OrchestrationJob) -> OrchestrationJob:
        """Submit a job to Redis."""
        payload = job.to_dict()
        self.client.set(self._job_key(job.job_id), json.dumps(payload))
        self.client.rpush(self.queue_key, job.job_id)
        return job

    def get_nowait(self) -> OrchestrationJob | None:
        """Return the next queued job, if available."""
        job_id = self.client.lpop(self.queue_key)
        if not job_id:
            return None

        return self.get(str(job_id))

    def get(self, job_id: str) -> OrchestrationJob | None:
        """Look up a job by ID."""
        raw = self.client.get(self._job_key(job_id))
        if raw is None:
            return None

        data = json.loads(raw)
        return self._deserialize_job(data)

    def update(self, job: OrchestrationJob) -> None:
        """Persist the latest job state."""
        self.client.set(self._job_key(job.job_id), json.dumps(job.to_dict()))

    def list_jobs(self) -> list[dict[str, Any]]:
        """List all known Redis-backed jobs."""
        keys = self.client.keys(f"{self.job_key_prefix}:*")
        jobs: list[dict[str, Any]] = []

        for key in keys:
            raw = self.client.get(key)
            if raw:
                jobs.append(json.loads(raw))

        return sorted(jobs, key=lambda item: str(item.get("created_at", "")))

    def _job_key(self, job_id: str) -> str:
        return f"{self.job_key_prefix}:{job_id}"

    @staticmethod
    def _deserialize_job(data: dict[str, Any]) -> OrchestrationJob:
        job = OrchestrationJob(
            goal=str(data["goal"]),
            backend=str(data.get("backend", "json")),
            memory_path=str(data.get("memory_path", "memory/shared_state.json")),
            history_path=str(data.get("history_path", "memory/run_history.json")),
            job_id=str(data["job_id"]),
        )
        job.status = JobStatus(str(data.get("status", JobStatus.QUEUED.value)))
        job.created_at = str(data.get("created_at", job.created_at))
        job.updated_at = str(data.get("updated_at", job.updated_at))
        job.result = data.get("result")
        job.error = data.get("error")
        return job
