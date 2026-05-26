"""Startup landing page demo for the deterministic swarm."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from orchestration import SwarmOrchestrator

DEMO_GOAL = "Create a landing page outline for an AI consulting service."


def run_demo(memory_path: str | Path = "memory/shared_state.json") -> dict[str, Any]:
    """Run the startup landing page demo."""
    orchestrator = SwarmOrchestrator(memory_path=memory_path)
    return orchestrator.run(DEMO_GOAL)
