from orchestration import SwarmOrchestrator


GOAL = "Create a landing page outline for an AI consulting service."


def test_orchestrator_runs_full_loop(tmp_path) -> None:
    orchestrator = SwarmOrchestrator(memory_path=tmp_path / "memory.json")
    result = orchestrator.run(GOAL)

    actors = [event["actor"] for event in result["event_log"]]

    assert result["goal"] == GOAL
    assert result["task_graph"]["nodes"]
    assert result["draft"]["sections"]
    assert result["review"]["approved"] is True
    assert "CommanderAgent" in actors
    assert "PlannerAgent" in actors
    assert "BuilderAgent" in actors
    assert "ReviewerAgent" in actors
    assert "MemoryAgent" in actors


def test_memory_influences_second_run(tmp_path) -> None:
    memory_path = tmp_path / "memory.json"
    first = SwarmOrchestrator(memory_path=memory_path)
    first.run(GOAL)

    second = SwarmOrchestrator(memory_path=memory_path)
    result = second.run(GOAL)

    task_titles = [node["title"] for node in result["task_graph"]["nodes"]]
    section_titles = [section["title"] for section in result["draft"]["sections"]]

    assert "Apply recalled reviewer feedback" in task_titles
    assert "Memory-Informed Revision Notes" in section_titles
