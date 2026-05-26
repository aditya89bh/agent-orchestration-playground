# Orchestration Patterns

## Commander-worker

A commander accepts the goal and coordinates a set of specialized worker agents. Each worker has one clear responsibility.

## Review loop

The builder does not directly finalize the output. The reviewer critiques it first, producing feedback that is both returned to the user and stored in memory.

## Memory-aware planning

Prior reviewer feedback is recalled before planning. When memory exists, the planner turns it into an explicit planning step so future runs can improve without hidden behavior.

## Event logging

`EventBus` records major actions from the commander, memory agent, planner, builder, reviewer, and orchestrator. This creates an audit trail for debugging and demonstration.
