# Agent Orchestration Playground

> A deterministic commander-worker swarm for studying planner-builder-reviewer coordination, event traces, and memory-influenced execution.

[![Tests](https://github.com/aditya89bh/agent-orchestration-playground/actions/workflows/tests.yml/badge.svg)](https://github.com/aditya89bh/agent-orchestration-playground/actions/workflows/tests.yml)

Most agent demos optimize for spectacle. This repo optimizes for inspectability.

It shows the smallest useful version of a memory-aware orchestration loop: a commander receives a goal, a planner decomposes it, a builder creates an output, a reviewer critiques it, and a memory agent stores feedback that can change later runs.

No external LLM calls. No hidden prompt magic. No fake autonomy theater.

## Why this matters

Multi-agent systems become useful only when their behavior can be traced, reviewed, and improved. The core problem is not merely getting agents to talk to each other. The harder problem is making coordination visible enough that a developer can debug it.

This playground focuses on four primitives:

| Primitive | Purpose |
|---|---|
| Role separation | Each agent has one clear responsibility. |
| Event logging | Every major step leaves an inspectable trace. |
| Review loop | Output is critiqued before being treated as final. |
| Memory influence | Prior feedback can affect future planning. |

## Dashboard Visualization

The repo now includes a lightweight orchestration dashboard built with Streamlit.

The dashboard visualizes:

- Multi-tenant orchestration
- Workflow schedules
- Replay visualization
- Execution timelines
- Tenant-aware orchestration state
- Governance and quotas

### Run dashboard

```bash
pip install -r requirements.txt
export PYTHONPATH=$(pwd)
streamlit run dashboard/streamlit_dashboard.py
```

The dashboard includes:

| View | Purpose |
|---|---|
| Tenant Overview | View isolated orchestration tenants and workflow counts. |
| Replay Visualization | Inspect failed orchestration replay traces. |
| Execution Timeline | Step-by-step orchestration execution reconstruction. |

## Architecture

```text
User Goal
   |
   v
CommanderAgent
   |
   v
SwarmOrchestrator
   |
   +--> MemoryAgent
   |       recalls prior reviewer feedback
   |
   +--> PlannerAgent
   |       creates a memory-aware task graph
   |
   +--> BuilderAgent
   |       creates a deterministic draft
   |
   +--> ReviewerAgent
   |       critiques the draft
   |
   +--> MemoryAgent
   |       stores reviewer feedback
   |
   v
Final Result
   +--> goal
   +--> task graph
   +--> draft
   +--> review
   +--> event log
```

## Current orchestration loop

```text
1. Commander accepts the user goal.
2. Memory recalls prior reviewer feedback.
3. Planner creates a task plan.
4. Builder produces a draft from the plan.
5. Reviewer critiques the draft.
6. Memory stores the reviewer feedback.
7. Orchestrator returns the output and event trace.
```

## Quickstart

```bash
python run_demo.py
```

Run tests:

```bash
pytest
```

The project uses the Python standard library only. `pytest` is used for verification.

## Demo

`run_demo.py` executes the startup landing page demo with this goal:

```text
Create a landing page outline for an AI consulting service.
```

The demo prints:

- goal
- task graph
- deterministic draft
- review feedback
- event log

Run it twice to see recalled reviewer feedback influence the next plan.

## Multi-tenant orchestration showcase

The repo includes a multi-tenant orchestration showcase with:

- Tenant-aware workflows
- Workflow versioning
- Replay infrastructure
- Governance policies
- Recurring workflow scheduling
- Tenant isolation semantics

Run:

```bash
python demos/multi_tenant_showcase.py
```

Replay showcase:

```bash
python demos/replay_visualization_demo.py
```

## Repository structure

```text
README.md
pyproject.toml
requirements.txt
run_demo.py
agents/
  commander.py
  planner.py
  builder.py
  reviewer.py
  memory_agent.py
orchestration/
  swarm.py
  event_bus.py
  task_graph.py
  workflow_registry.py
  scheduler.py
  replay_engine.py
  policy_engine.py
memory/
  memory_store.py
  shared_state.json
dashboard/
  streamlit_dashboard.py
demos/
  startup_landing_page_demo.py
  multi_tenant_showcase.py
  replay_visualization_demo.py
tests/
  test_agents.py
  test_memory_store.py
  test_orchestrator.py
docs/
  architecture.md
  memory_flow.md
  orchestration_patterns.md
.github/workflows/
  tests.yml
```

## Agent roles

| Agent | Responsibility |
|---|---|
| CommanderAgent | Accepts and validates the user goal. |
| MemoryAgent | Recalls prior feedback and stores new feedback. |
| PlannerAgent | Converts the goal into a task plan. |
| BuilderAgent | Creates a deterministic draft output. |
| ReviewerAgent | Critiques the draft and returns feedback. |
| SwarmOrchestrator | Coordinates the full loop and returns the trace. |

## Not production

This is not a production orchestration framework. It is an experimental architecture playground for understanding reliable, memory-aware multi-agent coordination.

The agents are intentionally simple. The point is to make the coordination pattern legible before adding model calls, tools, retries, queues, or distributed execution.

## Roadmap

- Add replay DAG visualization.
- Add orchestration execution graph rendering.
- Add richer tenant analytics.
- Add workflow execution persistence metrics.
- Add architecture diagrams and deployment examples.
- Add optional LLM-backed agent implementations behind interfaces.
- Add production orchestration deployment examples.
