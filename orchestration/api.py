"""FastAPI service boundary for the orchestration engine."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from orchestration import SwarmOrchestrator
from orchestration.metrics import RuntimeMetrics


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


@app.get("/", tags=["metadata"])
def root() -> dict[str, str]:
    """Return service metadata."""
    return {
        "service": "agent-orchestration-playground",
        "mode": "deterministic",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(status="ok", service="agent-orchestration-playground")


@app.get("/metrics", tags=["metrics"])
def runtime_metrics() -> dict:
    """Return runtime orchestration metrics."""
    return metrics.snapshot()


@app.post("/orchestrate", tags=["orchestration"])
def orchestrate(request: OrchestrationRequest) -> dict:
    """Run the commander-worker orchestration loop."""
    try:
        orchestrator = SwarmOrchestrator(
            memory_path=Path(request.memory_path),
            history_path=Path(request.history_path),
            persistence_backend=request.backend,
        )
        result = orchestrator.run(request.goal)
        metrics.record_success(result)
        return result
    except Exception as error:
        metrics.record_failure(error)
        raise HTTPException(status_code=500, detail=str(error)) from error
