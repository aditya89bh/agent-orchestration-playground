from fastapi.testclient import TestClient

from orchestration.api import app


client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200

    payload = response.json()

    assert payload["service"] == "agent-orchestration-playground"
    assert payload["mode"] == "deterministic"


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"


def test_orchestrate_endpoint(tmp_path) -> None:
    response = client.post(
        "/orchestrate",
        json={
            "goal": "Review an orchestration architecture",
            "memory_path": str(tmp_path / "memory.json"),
            "history_path": str(tmp_path / "history.json"),
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["goal"] == "Review an orchestration architecture"
    assert payload["task_graph"]
    assert payload["draft"]
    assert payload["review"]
    assert payload["event_log"]
    assert payload["run_record"]
