import json

import pytest

from orchestration.cli import format_human_output, run


CUSTOM_GOAL = "Review an API design for a memory-aware agent service."


def test_cli_accepts_custom_goal(tmp_path, capsys) -> None:
    exit_code = run([
        "--goal",
        CUSTOM_GOAL,
        "--memory-path",
        str(tmp_path / "memory.json"),
        "--history-path",
        str(tmp_path / "history.json"),
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert CUSTOM_GOAL in captured.out
    assert "AGENT ORCHESTRATION PLAYGROUND" in captured.out
    assert "EVENT LOG" in captured.out
    assert "RUN RECORD" in captured.out


def test_cli_json_output_is_parseable(tmp_path, capsys) -> None:
    exit_code = run([
        "--goal",
        CUSTOM_GOAL,
        "--memory-path",
        str(tmp_path / "memory.json"),
        "--history-path",
        str(tmp_path / "history.json"),
        "--json",
    ])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["goal"] == CUSTOM_GOAL
    assert payload["task_graph"]["nodes"]
    assert payload["event_log"]
    assert payload["run_record"]


def test_cli_rejects_empty_goal() -> None:
    with pytest.raises(SystemExit):
        run(["--goal", "   "])


def test_human_output_contains_core_sections() -> None:
    result = {
        "goal": "Test goal",
        "task_graph": {
            "nodes": [
                {"title": "Plan", "description": "Create a plan."},
            ]
        },
        "draft": {
            "sections": [
                {"title": "Hero", "body": "Demo body."},
            ]
        },
        "review": {
            "approved": True,
            "feedback": ["Looks good."],
        },
        "run_record": {
            "run_id": "demo-run-id",
            "event_count": 1,
        },
        "event_log": [
            {"actor": "CommanderAgent", "action": "accepted_goal"},
        ],
    }

    output = format_human_output(result)

    assert "TASK GRAPH" in output
    assert "DRAFT" in output
    assert "REVIEW" in output
    assert "EVENT LOG" in output
    assert "RUN RECORD" in output
    assert "accepted_goal" in output
