# Memory Flow

Memory is stored as a JSON list of entries. Each entry captures:

- the goal
- reviewer feedback
- approval status
- final outcome

## Recall behavior

Before planning and building, the orchestrator asks `MemoryAgent` for relevant prior feedback. The JSON store performs simple keyword overlap between the current goal and previous goals.

This means a second run with a similar goal can include prior reviewer feedback in the builder and reviewer context.

## Why simple memory?

The point is to demonstrate the orchestration seam, not to build a vector database. A JSON store is transparent, inspectable, and deterministic.
