from orchestration import SwarmOrchestrator


def test_orchestrator_runs_full_flow(tmp_path) -> None:
    orchestrator = SwarmOrchestrator(memory_path=tmp_path / "memory.json")
    result = orchestrator.run("Create a landing page outline for an AI consulting service.")

    logs = result["event_logs"]
    actors = [event["actor"] for event in logs]

    assert result["final_result"]["review"]["approved"] is True
    assert "Commander" in actors
    assert "Planner" in actors
    assert "Builder" in actors
    assert "Reviewer" in actors
    assert "Memory" in actors


def test_memory_influences_later_runs(tmp_path) -> None:
    memory_path = tmp_path / "memory.json"
    first = SwarmOrchestrator(memory_path=memory_path)
    first.run("Create a landing page outline for an AI consulting service.")

    second = SwarmOrchestrator(memory_path=memory_path)
    result = second.run("Create another landing page outline for AI consulting.")

    sections = result["final_result"]["draft"]["sections"]
    assert any(section["title"] == "Memory-Informed Improvements" for section in sections)
    assert any(
        event["actor"] == "Memory" and event["action"] == "recalled_feedback" and event["details"]["items"]
        for event in result["event_logs"]
    )
