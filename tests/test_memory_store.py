from memory import MemoryStore


def test_memory_store_reads_writes_and_recalls(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.json")
    store.append(
        {
            "goal": "Create a landing page outline for AI consulting",
            "reviewer_feedback": ["Add measurable business outcomes."],
            "approved": True,
        }
    )

    assert len(store.read_all()) == 1
    assert store.recall_feedback("AI consulting landing page") == ["Add measurable business outcomes."]
