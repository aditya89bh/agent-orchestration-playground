# Architecture

This project uses a deterministic commander-worker swarm architecture.

## Components

- `CommanderAgent`: accepts and normalizes the user goal, then creates a run brief.
- `PlannerAgent`: converts the brief into ordered execution steps.
- `BuilderAgent`: creates a structured draft artifact from the plan.
- `ReviewerAgent`: evaluates the artifact and returns feedback.
- `MemoryAgent`: recalls and stores reviewer feedback through a JSON-backed store.
- `SwarmOrchestrator`: coordinates the sequence and returns the final result plus event logs.
- `EventBus`: records each meaningful orchestration event.

## Data flow

```text
goal -> commander -> planner -> builder -> reviewer -> memory -> result
```

The system intentionally avoids external LLM calls. This keeps behavior deterministic and easy to test.
