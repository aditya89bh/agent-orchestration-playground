"""FastAPI service boundary for the orchestration engine."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from orchestration import SwarmOrchestrator
from orchestration.dashboard import DASHBOARD_HTML
from orchestration.metrics import RuntimeMetrics
from orchestration.plugins import registry as plugin_registry
from orchestration.queue import InMemoryJobQueue, OrchestrationJob
from orchestration.replay import ReplayEngine
from orchestration.trace_store import TraceStore
from orchestration.websocket_manager import WebSocketEventManager
from orchestration.worker_pool import WorkerPool


class OrchestrationRequest(BaseModel):
    """Request body for running an orchestration loop."""

    goal: str = Field(..., min_length=1, description="Goal to send into the swarm.")
    memory_path: str = Field(
        default="memory/shared_state.json",
        description="Path to JSON memory store.",
    )
    history_path: str = Field(
        default="memory/run_history.json",
        description="Path to JSON run history store.",
    )
    backend: str = Field(
        default="json",
        description="Persistence backend to use.",
    )


class PluginExecutionRequest(BaseModel):
    """Request body for plugin execution."""

    plugin: str
    payload: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str


app = FastAPI(
    title="Agent Orchestration Playground",
    description="Deterministic commander-worker swarm orchestration API.",
    version="0.1.0",
)

metrics = RuntimeMetrics()
job_queue = InMemoryJobQueue()
event_manager = WebSocketEventManager()
trace_store = TraceStore()
replay_engine = ReplayEngine()
worker_pool = WorkerPool(queue=job_queue)
worker_pool.start()


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    """Stream live orchestration events to dashboard clients."""
    await event_manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_manager.disconnect(websocket)


@app.get("/dashboard", response_class=HTMLResponse, tags=["dashboard"])
def dashboard() -> HTMLResponse:
    """Return the orchestration control plane dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/", tags=["metadata"])
def root() -> dict[str, str]:
    """Return service metadata."""
    return {
        "service": "agent-orchestration-playground",
        "mode": "deterministic",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "events": "/ws/events",
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(status="ok", service="agent-orchestration-playground")


@app.get("/metrics", tags=["metrics"])
def runtime_metrics() -> dict:
    """Return runtime orchestration metrics."""
    snapshot = metrics.snapshot()
    snapshot["worker_pool"] = worker_pool.snapshot()
    snapshot["websocket_clients"] = len(event_manager.active_connections)
    return snapshot


@app.get("/traces", tags=["traces"])
def list_traces() -> list[dict]:
    """List persisted orchestration traces."""
    return trace_store.list_traces()


@app.get("/traces/{trace_id}", tags=["traces"])
def get_trace(trace_id: str) -> dict:
    """Return one persisted trace."""
    trace = trace_store.get_trace(trace_id)

    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")

    return trace


@app.post("/replay/{trace_id}", tags=["replay"])
def replay_trace(trace_id: str) -> dict:
    """Replay a persisted orchestration trace."""
    trace = trace_store.get_trace(trace_id)

    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")

    replay = replay_engine.replay_trace(trace)

    event_manager.broadcast_sync(
        "trace_replayed",
        trace_id=trace_id,
        replay_id=replay.replay_id,
    )

    return replay.to_dict()


@app.post("/replay/{trace_id}/node/{span_name}", tags=["replay"])
def replay_node(trace_id: str, span_name: str) -> dict:
    """Replay one workflow node/span from a persisted trace."""
    trace = trace_store.get_trace(trace_id)

    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")

    replay = replay_engine.replay_node(trace, span_name)

    event_manager.broadcast_sync(
        "node_replayed",
        trace_id=trace_id,
        replay_id=replay.replay_id,
        span_name=span_name,
    )

    return replay.to_dict()


@app.get("/replays", tags=["replay"])
def list_replays() -> list[dict]:
    """List replay history."""
    return replay_engine.list_replays()


@app.get("/replays/{replay_id}", tags=["replay"])
def get_replay(replay_id: str) -> dict:
    """Return one replay record."""
    replay = replay_engine.get_replay(replay_id)

    if replay is None:
        raise HTTPException(status_code=404, detail="Replay not found")

    return replay


@app.get("/plugins", tags=["plugins"])
def list_plugins() -> list[dict]:
    """List registered orchestration plugins."""
    return plugin_registry.list_plugins()


@app.post("/plugins/execute", tags=["plugins"])
def execute_plugin(request: PluginExecutionRequest) -> dict:
    """Execute a registered plugin."""
    try:
        result = plugin_registry.execute(request.plugin, **request.payload)
        event_manager.broadcast_sync(
            "plugin_executed",
            plugin=request.plugin,
        )
        return result
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/jobs", tags=["queue"])
def list_jobs() -> list[dict]:
    """List queued and completed jobs."""
    return job_queue.list_jobs()


@app.get("/jobs/{job_id}", tags=["queue"])
def get_job(job_id: str) -> dict:
    """Return a single orchestration job."""
    job = job_queue.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job.to_dict()


@app.post("/jobs", tags=["queue"])
def submit_job(request: OrchestrationRequest) -> dict:
    """Submit a background orchestration job."""
    job = OrchestrationJob(
        goal=request.goal,
        backend=request.backend,
        memory_path=request.memory_path,
        history_path=request.history_path,
    )

    job_queue.submit(job)

    event_manager.broadcast_sync(
        "job_submitted",
        job_id=job.job_id,
        goal=job.goal,
        backend=job.backend,
    )

    return {
        "message": "Job submitted",
        "job_id": job.job_id,
        "status": job.status.value,
    }


@app.post("/orchestrate", tags=["orchestration"])
def orchestrate(request: OrchestrationRequest) -> dict:
    """Run the commander-worker orchestration loop."""
    try:
        orchestrator = SwarmOrchestrator(
            memory_path=Path(request.memory_path),
            history_path=Path(request.history_path),
            persistence_backend=request.backend,
        )

        event_manager.broadcast_sync(
            "orchestration_started",
            goal=request.goal,
            backend=request.backend,
        )

        result = orchestrator.run(request.goal)
        metrics.record_success(result)

        event_manager.broadcast_sync(
            "orchestration_completed",
            goal=request.goal,
            approved=result["review"]["approved"],
            trace_id=result["trace"]["trace_id"],
        )

        return result
    except Exception as error:
        metrics.record_failure(error)

        event_manager.broadcast_sync(
            "orchestration_failed",
            goal=request.goal,
            error=str(error),
        )

        raise HTTPException(status_code=500, detail=str(error)) from error
