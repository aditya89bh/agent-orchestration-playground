"""Run the startup landing page swarm demo."""

from __future__ import annotations

import json

from demos.startup_landing_page_demo import run_demo


def main() -> None:
    """Print the goal, task graph, draft, review feedback, and event log."""
    result = run_demo()
    print("GOAL")
    print(result["goal"])
    print("\nTASK GRAPH")
    print(json.dumps(result["task_graph"], indent=2))
    print("\nDRAFT")
    print(json.dumps(result["draft"], indent=2))
    print("\nREVIEW FEEDBACK")
    print(json.dumps(result["review"], indent=2))
    print("\nEVENT LOG")
    print(json.dumps(result["event_log"], indent=2))


if __name__ == "__main__":
    main()
