# Memory Flow

Memory is stored in `memory/shared_state.json` as a JSON list.

## Recall

Before planning, `MemoryAgent` asks `MemoryStore` for prior reviewer feedback related to the current goal. The store uses deterministic keyword overlap rather than embeddings or external services.

## Write

After review, `MemoryAgent` writes a compact entry containing:

- goal
- reviewer feedback
- approval status
- score
- draft artifact type

## Memory-influenced planning

On later runs, recalled feedback is passed into `PlannerAgent`. The planner adds an explicit task called `Apply recalled reviewer feedback`, making memory influence visible in the task graph.
