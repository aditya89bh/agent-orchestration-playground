"""Streamlit dashboard for orchestration platform visualization."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from demos.multi_tenant_showcase import build_showcase
from demos.replay_visualization_demo import build_replay_showcase


st.set_page_config(
    page_title="Agent Orchestration Playground",
    layout="wide",
)

showcase = build_showcase()
replay = build_replay_showcase()

st.title("Agent Orchestration Playground")
st.caption("Multi-tenant orchestration runtime visualization")

st.divider()

st.header("Platform Analytics")

analytics_rows = []
for row in showcase["showcase_rows"]:
    tenant = row["tenant"]
    policy = row["policy"]
    schedule = row["schedule"]

    analytics_rows.append(
        {
            "tenant": tenant["name"],
            "namespace": row["workflow"]["workflow_namespace"],
            "workflows": row["tenant_workflow_count"],
            "schedules": row["tenant_schedule_count"],
            "max_concurrent_workflows": policy["quotas"]["max_concurrent_workflows"],
            "max_replays_per_hour": policy["quotas"]["max_replays_per_hour"],
            "schedule_enabled": bool(schedule),
        }
    )

total_workflows = sum(row["workflows"] for row in analytics_rows)
total_schedules = sum(row["schedules"] for row in analytics_rows)
replay_count = replay["replayable_trace_count"]
escalation_count = 1 if replay["failure_summary"]["escalation_required"] else 0

col_a, col_b, col_c, col_d, col_e = st.columns(5)

with col_a:
    st.metric("Tenants", showcase["tenant_count"])

with col_b:
    st.metric("Workflows", total_workflows)

with col_c:
    st.metric("Schedules", total_schedules)

with col_d:
    st.metric("Replay Traces", replay_count)

with col_e:
    st.metric("Escalations", escalation_count)

st.subheader("Tenant Analytics")
st.dataframe(
    analytics_rows,
    use_container_width=True,
    hide_index=True,
)

st.divider()

st.header("Failure Escalation Center")

incident_rows = [
    {
        "incident_id": "INC-001",
        "tenant": "Orangewood Robotics Factory",
        "workflow": "CNC Deployment Readiness Workflow",
        "severity": "High",
        "status": "Escalated",
        "resolution": "Replay generated for operator review",
    },
    {
        "incident_id": "INC-002",
        "tenant": "Northstar Marketing Studio",
        "workflow": "Content Research Pipeline",
        "severity": "Low",
        "status": "Auto-Recovered",
        "resolution": "Retried with prior reviewer feedback",
    },
    {
        "incident_id": "INC-003",
        "tenant": "Atlas Research Lab",
        "workflow": "Paper Review Automation Workflow",
        "severity": "Medium",
        "status": "Replayed",
        "resolution": "Trace inspected and replay accepted",
    },
]

esc_a, esc_b, esc_c, esc_d = st.columns(4)

with esc_a:
    st.metric("Auto-Recovered", 1)

with esc_b:
    st.metric("Replayed", 1)

with esc_c:
    st.metric("Escalated", 1)

with esc_d:
    st.metric("Human Review Required", 1)

st.subheader("Recent Incidents")
st.dataframe(
    incident_rows,
    use_container_width=True,
    hide_index=True,
)

st.divider()

st.header("Event Stream Viewer")

event_rows = [
    {"time": "09:01", "source": "CommanderAgent", "event": "workflow_started", "status": "ok"},
    {"time": "09:01", "source": "MemoryAgent", "event": "prior_feedback_retrieved", "status": "ok"},
    {"time": "09:02", "source": "PlannerAgent", "event": "task_graph_created", "status": "ok"},
    {"time": "09:02", "source": "PolicyEngine", "event": "quota_check_passed", "status": "ok"},
    {"time": "09:03", "source": "WorkflowRuntime", "event": "collision_risk_detected", "status": "failed"},
    {"time": "09:03", "source": "ReplayEngine", "event": "trace_replay_triggered", "status": "replayed"},
    {"time": "09:04", "source": "EscalationCenter", "event": "operator_review_required", "status": "escalated"},
]

for event in event_rows:
    status = event["status"]
    label = f"{event['time']} · {event['source']} · {event['event']}"

    if status == "failed":
        st.error(label)
    elif status == "escalated":
        st.warning(label)
    elif status == "replayed":
        st.info(label)
    else:
        st.success(label)

st.divider()

st.header("Tenant Overview")

columns = st.columns(3)

for index, row in enumerate(showcase["showcase_rows"]):
    tenant = row["tenant"]
    workflow = row["workflow"]
    schedule = row["schedule"]

    with columns[index]:
        st.subheader(tenant["name"])

        st.metric(
            "Workflows",
            row["tenant_workflow_count"],
        )

        st.metric(
            "Schedules",
            row["tenant_schedule_count"],
        )

        st.metric(
            "Namespaces",
            len(row["tenant_namespaces"]),
        )

        st.write("Workflow Namespace")
        st.code(workflow["workflow_namespace"])

        st.write("Schedule")
        st.code(schedule["cron_expression"])

st.divider()

st.header("Replay DAG Visualization")

st.graphviz_chart(
    """
    digraph {
        rankdir=TB;
        node [shape=box style=rounded];

        Goal -> Planner;
        Planner -> TaskGraph;

        TaskGraph -> ValidateRobotProgram;
        TaskGraph -> ExecuteWorkflow;
        TaskGraph -> ReviewExecution;
        TaskGraph -> EscalationPath;

        ExecuteWorkflow -> CollisionRiskDetected;
        CollisionRiskDetected -> ReplayEngine;

        ReplayEngine -> ReplayTrace;
        ReplayTrace -> GovernanceCheckpoint;
        GovernanceCheckpoint -> StreamlitDashboard;
    }
    """
)

st.divider()

st.header("Replay Visualization")

failure = replay["failure_summary"]

col1, col2 = st.columns(2)

with col1:
    st.subheader("Workflow Failure")

    st.error(failure["failure_reason"])

    st.json(
        {
            "workflow": failure["workflow"],
            "escalation_required": failure["escalation_required"],
            "trace_id": replay["trace_id"],
        }
    )

with col2:
    st.subheader("Replay Metadata")

    st.json(
        {
            "tenant_id": replay["tenant_id"],
            "replayed": replay["replay_result"]["replayed"],
            "replayable_trace_count": replay["replayable_trace_count"],
        }
    )

st.divider()

st.header("Execution Timeline")

for item in replay["replay_timeline"]:
    with st.container(border=True):
        st.write(item["span_name"])
        st.json(item["attributes"])

st.divider()

st.header("Platform Capabilities")

st.markdown(
    """
- Multi-tenant orchestration
- Workflow versioning
- Tenant-aware replay
- Governance and quotas
- Recurring workflow scheduling
- Trace persistence
- Replay introspection
"""
)
