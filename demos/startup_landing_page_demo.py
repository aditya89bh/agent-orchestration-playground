"""Demo: create a landing page outline for an AI consulting service."""

from __future__ import annotations

import json
from pathlib import Path

from orchestration import SwarmOrchestrator

DEMO_GOAL = "Create a landing page outline for an AI consulting service."


def run_demo(memory_path: str | Path = "memory/demo_memory.json") -> dict[str, object]:
    """Run the startup landing page demo and return the orchestrator result."""
    orchestrator = SwarmOrchestrator(memory_path=memory_path)
    return orchestrator.run(DEMO_GOAL)


def main() -> None:
    """Print the demo result as formatted JSON."""
    print(json.dumps(run_demo(), indent=2))


if __name__ == "__main__":
    main()
