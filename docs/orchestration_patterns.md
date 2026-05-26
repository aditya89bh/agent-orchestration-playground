# Orchestration Patterns

## Commander-worker flow

A commander receives the user goal and delegates specialized work to deterministic worker agents.

## Review loop

The builder does not directly produce a final answer. Its output is reviewed first, making quality checks explicit.

## Event-sourced inspection

The event bus records each major step. This creates an audit trail showing which agent acted and what happened.

## Memory-aware execution

Reviewer feedback is stored after each run and recalled before later runs. This lets the swarm improve future outputs without changing agent code.

## Deliberate constraints

The project avoids overengineering:

- no external APIs
- no async runtime
- no model router
- no plugin system
- no production claims

Those can be added later once the orchestration behavior is clear.
