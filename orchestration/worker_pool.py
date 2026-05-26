"""Background worker pool for orchestration jobs."""

from __future__ import annotations

import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from orchestration.coordination import CoordinationManager
from orchestration.queue import InMemoryJobQueue, JobStatus
from orchestration.swarm import SwarmOrchestrator


@dataclass
class WorkerPool:
    """Small threaded worker pool for orchestration execution."""

    queue: InMemoryJobQueue
    worker_count: int = 2
    poll_interval_seconds: float = 0.1
    coordination: CoordinationManager = field(default_factory=CoordinationManager)
    _threads: list[threading.Thread] = field(default_factory=list, init=False)
    _running: bool = field(default=False, init=False)

    def start(self) -> None:
        """Start background worker threads."""
        if self._running:
            return

        self._running = True

        for index in range(self.worker_count):
            thread = threading.Thread(
                target=self._worker_loop,
                args=(index,),
                name=f"orchestration-worker-{index}",
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)

    def stop(self) -> None:
        """Stop background worker threads."""
        self._running = False

        for thread in self._threads:
            thread.join(timeout=1.0)

        self._threads.clear()

    def _worker_loop(self, index: int) -> None:
        """Continuously process queued orchestration jobs."""
        worker = self.coordination.register_worker(
            hostname=f"{socket.gethostname()}-{index}"
        )

        while self._running:
            self.coordination.heartbeat(worker.worker_id)

            job = self.queue.get_nowait()

            if job is None:
                time.sleep(self.poll_interval_seconds)
                continue

            lease = self.coordination.acquire_lease(
                job_id=job.job_id,
                worker_id=worker.worker_id,
            )

            job.mark_running()

            try:
                orchestrator = SwarmOrchestrator(
                    memory_path=job.memory_path,
                    history_path=job.history_path,
                    persistence_backend=job.backend,
                )
                result = orchestrator.run(job.goal)
                job.mark_succeeded(result)
            except Exception as error:
                job.mark_failed(error)
            finally:
                self.coordination.release_lease(lease.job_id)

    def snapshot(self) -> dict[str, Any]:
        """Return worker pool state."""
        running_jobs = [
            job
            for job in self.queue.list_jobs()
            if job["status"] == JobStatus.RUNNING.value
        ]

        return {
            "worker_count": self.worker_count,
            "running": self._running,
            "queued_jobs": len(self.queue.list_jobs()),
            "running_jobs": len(running_jobs),
            "workers": [
                worker.to_dict()
                for worker in self.coordination.workers.values()
            ],
            "stale_workers": self.coordination.stale_workers(),
            "recoverable_leases": self.coordination.recoverable_leases(),
        }
