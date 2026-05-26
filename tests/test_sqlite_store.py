from memory.sqlite_store import SQLiteStore


SAMPLE_MEMORY = {
    "goal": "Create a landing page outline",
    "reviewer_feedback": [
        "Improve specificity around target customer.",
    ],
    "draft": {
        "sections": [
            {"title": "Hero", "body": "Demo body."},
        ]
    },
}


SAMPLE_RESULT = {
    "goal": "Create a landing page outline",
    "task_graph": {
        "nodes": [
            {"title": "Plan", "description": "Create a plan."},
            {"title": "Build", "description": "Create a draft."},
        ]
    },
    "draft": {
        "sections": [
            {"title": "Hero", "body": "Demo body."},
        ]
    },
    "review": {
        "approved": True,
    },
    "event_log": [
        {"actor": "CommanderAgent", "action": "accepted_goal"},
        {"actor": "PlannerAgent", "action": "created_task_graph"},
    ],
}


def test_sqlite_store_persists_memory(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "orchestration.db")

    store.append_memory(SAMPLE_MEMORY)
    feedback = store.recall_feedback("landing page outline")

    assert feedback
    assert "target customer" in feedback[0]


def test_sqlite_store_persists_run_history(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "orchestration.db")

    record = store.append_run(SAMPLE_RESULT)
    runs = store.list_runs()

    assert record["goal"] == SAMPLE_RESULT["goal"]
    assert len(runs) == 1
    assert runs[0]["goal"] == SAMPLE_RESULT["goal"]
    assert runs[0]["approved"] is True
    assert runs[0]["event_count"] == 2
