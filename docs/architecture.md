# Architecture

The project demonstrates a deterministic commander-worker flow.

## Commander-worker flow

The `CommanderAgent` accepts the raw user goal and turns it into a clean brief. The `SwarmOrchestrator` then coordinates specialized worker agents:

1. `MemoryAgent` recalls prior reviewer feedback.
2. `PlannerAgent` creates a task graph and includes recalled lessons when available.
3. `BuilderAgent` creates a deterministic draft from the task graph.
4. `ReviewerAgent` critiques the draft.
5. `MemoryAgent` writes the review feedback back to JSON memory.

The orchestration is deliberately linear so the responsibilities are easy to inspect and test.

```text
Commander -> Memory Recall -> Planner -> Builder -> Reviewer -> Memory Write
```
