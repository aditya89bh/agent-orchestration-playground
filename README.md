# Agent Orchestration Playground

A deterministic Python playground for a commander-worker agent swarm with planning, building, review, event logging, and JSON-backed memory.

## Project thesis

Reliable multi-agent systems should be inspectable before they are impressive. This repository demonstrates the core architecture of a memory-aware agent swarm without external LLM calls, hidden state, or production framework complexity.

The project is intentionally deterministic so developers can review the orchestration loop, test the behavior, and reason about how memory changes later runs.

## Architecture diagram

```text
User Goal
   |
   v
CommanderAgent
   |
   v
MemoryAgent ---- recalls prior reviewer feedback
   |
   v
PlannerAgent --- creates memory-aware task graph
   |
   v
BuilderAgent --- creates deterministic draft
   |
   v
ReviewerAgent -- critiques draft and returns feedback
   |
   v
MemoryAgent ---- stores feedback and outcome
   |
   v
SwarmOrchestrator returns goal, task graph, draft, review, event log
```

## Quickstart

```bash
python run_demo.py
pytest
```

The project uses the Python standard library only. `pytest` is used for verification.

## Demo explanation

`run_demo.py` runs the startup landing page demo with this goal:

> Create a landing page outline for an AI consulting service.

It prints:

- goal
- task graph
- deterministic draft
- review feedback
- event log

Run it twice to see how recalled reviewer feedback influences later planning.

## Folder structure

```text
README.md
pyproject.toml
run_demo.py
agents/
  __init__.py
  commander.py
  planner.py
  builder.py
  reviewer.py
  memory_agent.py
orchestration/
  __init__.py
  swarm.py
  event_bus.py
  task_graph.py
memory/
  __init__.py
  memory_store.py
  shared_state.json
demos/
  __init__.py
  startup_landing_page_demo.py
tests/
  __init__.py
  test_agents.py
  test_memory_store.py
  test_orchestrator.py
docs/
  architecture.md
  memory_flow.md
  orchestration_patterns.md
```

## Not production

This is **not a production framework**. It is an experimental architecture playground for reliable, memory-aware multi-agent orchestration. The agents are simple by design and do not call external LLM APIs.

## Roadmap

- Add optional LLM-backed agent implementations behind interfaces.
- Add richer task graph execution states.
- Add memory scoring and better retrieval.
- Add CLI options for custom goals.
- Add examples for research planning, code review, and product strategy.
