"""Replay visualization showcase.

Demonstrates:
- tenant-scoped orchestration traces
- failed workflow reconstruction
- replay isolation
- replay introspection timeline
"""

from __future__ import annotations

from orchestration.replay_engine import ReplayEngine
from orchestration.tenant import Tenant, TenantContext
from orchestration.trace_store import TraceStore
from orchestration.tracing import TraceRecorder


def build_failure_trace() -> dict:
    """Create a deterministic failed orchestration trace."""
    tenant = Tenant(
        name="Orangewood Robotics Factory",
    )

    tenant_context = TenantContext(
        tenant=tenant,
        workflow_namespace="robotics",
    )

    recorder = TraceRecorder()

    orchestration_span = recorder.start_span(
        "robotics.cnc_deployment_workflow",
        tenant_id=tenant.tenant_id,
        workflow_namespace="robotics",
    )

    perception_span = recorder.start_span(
        "robotics.inspect_cell_state",
        orchestration_span.span_id,
    )

    perception_span.finish(
        machine_state="ready",
        gripper_state="attached",
    )

    validation_span = recorder.start_span(
        "robotics.validate_robot_program",
        orchestration_span.span_id,
    )

    validation_span.finish(
        program_hash="cnc-v14",
        simulation_status="passed",
    )

    deployment_span = recorder.start_span(
        "robotics.deploy_robot_workflow",
        orchestration_span.span_id,
    )

    deployment_span.finish(
        deployment_status="failed",
        failure_reason="Collision risk detected near CNC door axis.",
    )

    orchestration_span.finish(
        workflow_status="failed",
        escalation_required=True,
    )

    trace_payload = {
        **recorder.snapshot(),
        "tenant": tenant_context.to_dict(),
        "workflow": {
            "name": "CNC Deployment Readiness Workflow",
            "status": "failed",
        },
    }

    return trace_payload


def build_replay_showcase() -> dict:
    """Persist and replay an isolated orchestration trace."""
    trace_store = TraceStore()
    replay_engine = ReplayEngine(trace_store=trace_store)

    trace_payload = build_failure_trace()
    trace_store.persist(trace_payload)

    tenant_id = trace_payload["tenant"]["tenant"]["tenant_id"]
    trace_id = trace_payload["trace_id"]

    replay_result = replay_engine.replay(
        trace_id=trace_id,
        tenant_id=tenant_id,
    )

    replayable_traces = replay_engine.list_replayable_traces(
        tenant_id=tenant_id,
    )

    replay_timeline = []

    for span in replay_result.trace_payload.get("spans", []):
        replay_timeline.append(
            {
                "span_name": span["name"],
                "attributes": span.get("attributes", {}),
            }
        )

    return {
        "demo": "replay_visualization_showcase",
        "tenant_id": tenant_id,
        "trace_id": trace_id,
        "replay_result": replay_result.to_dict(),
        "replayable_trace_count": len(replayable_traces),
        "replay_timeline": replay_timeline,
        "failure_summary": {
            "workflow": "CNC Deployment Readiness Workflow",
            "failure_reason": "Collision risk detected near CNC door axis.",
            "escalation_required": True,
        },
    }


if __name__ == "__main__":
    import json

    print(json.dumps(build_replay_showcase(), indent=2))
