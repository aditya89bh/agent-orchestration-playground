# Agent Orchestration Playground

A portfolio-grade Python playground for experimenting with a deterministic commander-worker multi-agent swarm.

## Thesis

Reliable multi-agent systems need more than clever prompts. They need visible orchestration, review loops, structured memory, and audit-friendly event logs. This repository demonstrates those ideas without depending on external LLM APIs.

The goal is to make the architecture easy to inspect:

- a `CommanderAgent` accepts a user goal and coordinates the run
- a `PlannerAgent` breaks the goal into actionable steps
- a `BuilderAgent` creates a draft outcome from those steps
- a `ReviewerAgent` evaluates the draft and gives feedback
- a `MemoryAgent` records outcomes and recalls prior feedback
- a `SwarmOrchestrator` wires the full flow together

## Not production

This is **not a production framework**. It is an experimental architecture playground for reliable, memory-aware multi-agent orchestration. The agents are deterministic and intentionally simple so developers can focus on orchestration patterns rather than model behavior.

## Architecture overview

```text
User Goal
   ↓
CommanderAgent
   ↓
PlannerAgent ──→ plan steps
   ↓
BuilderAgent ──→ draft artifact
   ↓
ReviewerAgent ─→ feedback + approval signal
   ↓
MemoryAgent ───→ JSON memory store
   ↓
Final result + event logs
```

Memory influences later runs by recalling previous reviewer feedback for similar goal keywords and passing those lessons into the builder and reviewer context.

## Quickstart

```bash
python run_demo.py
pytest
```

No external APIs or services are required.

## Demo

The included demo runs this goal:

> Create a landing page outline for an AI consulting service.

It prints the final result and event log entries so you can inspect the commander, planner, builder, reviewer, and memory flow.

## Repository layout

```text
agents/           Deterministic agent classes
orchestration/    Event bus and swarm orchestrator
memory/           JSON-backed memory store
demos/            Example scenarios
tests/            Pytest test suite
docs/             Architecture and design notes
run_demo.py       Root demo entrypoint
```
