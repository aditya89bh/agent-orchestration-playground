"""Tenant-aware orchestration replay engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from orchestration.trace_store import TraceStore


@dataclass
class ReplayResult:
    """Replay execution result."""

    trace_id: str
    tenant_id: str
    workflow_namespace: str
    replayed: bool
    trace_payload: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "tenant_id": self.tenant_id,
            "workflow_namespace": self.workflow_namespace,
            "replayed": self.replayed,
            "trace_payload": self.trace_payload,
            "error": self.error,
        }


@dataclass
class ReplayEngine:
    """Replay persisted orchestration traces with tenant isolation."""

    trace_store: TraceStore = field(default_factory=TraceStore)

    def replay(
        self,
        trace_id: str,
        tenant_id: str,
    ) -> ReplayResult:
        """Replay one trace scoped to a tenant."""
        trace_payload = self.trace_store.get_trace(
            trace_id=trace_id,
            tenant_id=tenant_id,
        )

        if trace_payload is None:
            return ReplayResult(
                trace_id=trace_id,
                tenant_id=tenant_id,
                workflow_namespace="unknown",
                replayed=False,
                error="Trace not found for tenant.",
            )

        tenant_context = trace_payload.get("tenant", {})

        return ReplayResult(
            trace_id=trace_id,
            tenant_id=tenant_id,
            workflow_namespace=tenant_context.get(
                "workflow_namespace",
                "default",
            ),
            replayed=True,
            trace_payload=trace_payload,
        )

    def list_replayable_traces(
        self,
        tenant_id: str,
    ) -> list[dict[str, Any]]:
        """List replayable traces for one tenant."""
        traces = self.trace_store.list_traces(tenant_id=tenant_id)

        return [
            {
                "trace_id": trace["trace_id"],
                "tenant": trace.get("tenant", {}),
                "span_count": len(trace.get("spans", [])),
            }
            for trace in traces
        ]
