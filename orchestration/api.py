"""FastAPI service boundary for the orchestration engine."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from orchestration import SwarmOrchestrator
from orchestration.auth import AuthManager, Permission, Role
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


class APIKeyCreateRequest(BaseModel):
    """Request body for creating API keys."""

    role: Role = Role.OPERATOR


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
auth_manager = AuthManager()
bootstrap_admin_key = auth_manager.create_api_key(Role.ADMIN)
worker_pool = WorkerPool(queue=job_queue)
worker_pool.start()


def require_permission(permission: Permission):
    """Build a FastAPI dependency that requires one RBAC permission."""

    def dependency(x_api_key: Annotated[str | None, Header()] = None) -> dict:
        try:
            record = auth_manager.authorize(x_api_key, permission)
            return record.to_dict()
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    return dependency


AdminAuth = Depends(require_permission(Permission.WORKFLOW_MANAGE))
MetricsAuth = Depends(require_permission(Permission.METRICS_READ))
JobReadAuth = Depends(require_permission(Permission.JOB_READ))
JobSubmitAuth = Depends(require_permission(Permission.JOB_SUBMIT))
TraceReadAuth = Depends(require_permission(Permission.TRACE_READ))
ReplayAuth = Depends(require_permission(Permission.REPLAY_EXECUTE))
PluginReadAuth = Depends(require_permission(Permission.PLUGIN_READ))
PluginExecuteAuth = Depends(require_permission(Permission.PLUGIN_EXECUTE))
OrchestrationExecuteAuth = Depends(require_permission(Permission.ORCHESTRATION_EXECUTE))


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
        "auth_note": "Use X-API-Key for protected endpoints.",
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(status="ok", service="agent-orchestration-playground")


@app.get("/auth/bootstrap", tags=["auth"])
def auth_bootstrap() -> dict:
    """Return the initial admin key for local demo environments."""
    return {
        "warning": "Demo bootstrap endpoint. Disable or protect this in real deployments.",
        **bootstrap_admin_key,
    }


@app.post("/auth/api-keys", tags=["auth"])
def create_api_key(request: APIKeyCreateRequest, _: dict = AdminAuth) -> dict:
    """Create an API key for a role."""
    return auth_manager.create_api_key(request.role)


@app.get("/auth/api-keys", tags=["auth"])
def list_api_keys(_: dict = AdminAuth) -> list[dict]:
    """List API key metadata."""
    return auth_manager.list_api_keys()


@app.delete("/auth/api-keys/{key_id}", tags=["auth"])
def revoke_api_key(key_id: str, _: dict = AdminAuth) -> dict:
    """Revoke an API key."""
    revoked = auth_manager.revoke_api_key(key_id)

    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")

    return {"revoked": True, "key_id": key_id}


@app.get("/metrics", tags=["metrics"])
def runtime_metrics(_: dict = MetricsAuth) -> dict:
    """Return runtime orchestration metrics."""
    snapshot = metrics.snapshot()
    snapshot["worker_pool"] = worker_pool.snapshot()
    snapshot["websocket_clients"] = len(event_manager.active_connections)
    return snapshot


@app.get("/traces", tags=["traces"])
def list_traces(_: dict = TraceReadAuth) -> list[dict]:
    """List persisted orchestration traces."""
    return trace_store.list_traces()


@app.get("/traces/{trace_id}", tags=["traces"])
def get_trace(trace_id: str, _: dict = TraceReadAuth) -> dict:
    """Return one persisted trace."""
    trace = trace_store.get_trace(trace_id)

    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")

    return trace


@app.post("/replay/{trace_id}", tags=["replay"])
def replay_trace(trace_id: str, _: dict = ReplayAuth) -> dict:
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
def replay_node(trace_id: str, span_name: str, _: dict = ReplayAuth) -> dict:
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
def list_replays(_: dict = TraceReadAuth) -> list[dict]:
    """List replay history."""
    return replay_engine.list_replays()


@app.get("/replays/{replay_id}", tags=["replay"])
def get_replay(replay_id: str, _: dict = TraceReadAuth) -> dict:
    """Return one replay record."""
    replay = replay_engine.get_replay(replay_id)

    if replay is None:
        raise HTTPException(status_code=404, detail="Replay not found")

    return replay


@app.get("/plugins", tags=["plugins"])
def list_plugins(_: dict = PluginReadAuth) -> list[dict]:
    """List registered orchestration plugins."""
    return plugin_registry.list_plugins()


@app.post("/plugins/execute", tags=["plugins"])
def execute_plugin(request: PluginExecutionRequest, _: dict = PluginExecuteAuth) -> dict:
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
def list_jobs(_: dict = JobReadAuth) -> list[dict]:
    """List queued and completed jobs."""
    return job_queue.list_jobs()


@app.get("/jobs/{job_id}", tags=["queue"])
def get_job(job_id: str, _: dict = JobReadAuth) -> dict:
    """Return a single orchestration job."""
    job = job_queue.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job.to_dict()


@app.post("/jobs", tags=["queue"])
def submit_job(request: OrchestrationRequest, _: dict = JobSubmitAuth) -> dict:
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
def orchestrate(request: OrchestrationRequest, _: dict = OrchestrationExecuteAuth) -> dict:
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
