import asyncio

from orchestration import SwarmOrchestrator


GOAL = "Design a memory-aware orchestration workflow"


async def _run_async_orchestrator(tmp_path):
    orchestrator = SwarmOrchestrator(
        memory_path=tmp_path / "memory.json",
        history_path=tmp_path / "run_history.json",
        persistence_backend="json",
    )

    return await orchestrator.arun(GOAL)


def test_async_orchestrator_runs_successfully(tmp_path) -> None:
    result = asyncio.run(_run_async_orchestrator(tmp_path))

    assert result["goal"] == GOAL
    assert result["task_graph"]["nodes"]
    assert result["draft"]["sections"]
    assert result["review"]
    assert result["event_log"]
    assert result["run_record"]


def test_async_orchestrator_supports_sqlite_backend(tmp_path) -> None:
    async def _run() -> dict:
        orchestrator = SwarmOrchestrator(
            persistence_backend="sqlite",
        )
        return await orchestrator.arun(GOAL)

    result = asyncio.run(_run())

    assert result["persistence_backend"] == "sqlite"
    assert result["run_record"]
