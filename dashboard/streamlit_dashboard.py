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
