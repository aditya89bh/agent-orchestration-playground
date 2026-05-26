"""Command-line interface for the agent orchestration playground."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from orchestration import SwarmOrchestrator

DEFAULT_GOAL = "Create a landing page outline for an AI consulting service."


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="agent-swarm",
        description="Run a deterministic commander-worker agent orchestration loop.",
    )
    parser.add_argument(
        "--goal",
        default=DEFAULT_GOAL,
        help="Goal to send into the swarm.",
    )
    parser.add_argument(
        "--memory-path",
        default="memory/shared_state.json",
        help="Path to the JSON memory store.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full orchestration result as JSON.",
    )
    return parser


def format_human_output(result: dict) -> str:
    """Format an orchestration result for terminal readability."""
    lines: list[str] = []
    lines.append("AGENT ORCHESTRATION PLAYGROUND")
    lines.append("=" * 38)
    lines.append(f"Goal: {result['goal']}")

    lines.append("\nTASK GRAPH")
    for node in result["task_graph"]["nodes"]:
        lines.append(f"- {node['title']}: {node['description']}")

    lines.append("\nDRAFT")
    for section in result["draft"]["sections"]:
        lines.append(f"- {section['title']}: {section['body']}")

    lines.append("\nREVIEW")
    lines.append(f"Approved: {result['review']['approved']}")
    for note in result["review"].get("feedback", []):
        lines.append(f"- {note}")

    lines.append("\nEVENT LOG")
    for event in result["event_log"]:
        lines.append(f"[{event['actor']}] {event['event']}")

    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    goal = args.goal.strip()
    if not goal:
        parser.error("--goal cannot be empty")

    memory_path = Path(args.memory_path)
    orchestrator = SwarmOrchestrator(memory_path=memory_path)
    result = orchestrator.run(goal)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_human_output(result))

    return 0


def main() -> None:
    """Console script entry point."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()
