from orchestration.run_history import RunHistoryStore


SAMPLE_RESULT = {
    "goal": "Test orchestration goal",
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
        {"actor": "CommanderAgent", "event": "accepted_goal"},
        {"actor": "PlannerAgent", "event": "created_task_graph"},
    ],
}


def test_run_history_store_appends_records(tmp_path) -> None:
    store = RunHistoryStore(tmp_path / "run_history.json")

    record = store.append(SAMPLE_RESULT)
    records = store.load()

    assert len(records) == 1
    assert record["goal"] == SAMPLE_RESULT["goal"]
    assert record["approved"] is True
    assert record["event_count"] == 2
    assert record["task_count"] == 2
    assert record["draft_section_count"] == 1
    assert "run_id" in record
    assert "timestamp" in record


def test_run_history_store_persists_multiple_runs(tmp_path) -> None:
    store = RunHistoryStore(tmp_path / "run_history.json")

    store.append(SAMPLE_RESULT)
    store.append(SAMPLE_RESULT)

    records = store.load()

    assert len(records) == 2
    assert records[0]["run_id"] != records[1]["run_id"]
