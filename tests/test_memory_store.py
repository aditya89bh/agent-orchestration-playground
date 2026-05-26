from memory import MemoryStore


def test_memory_store_appends_and_recalls_feedback(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.json")
    store.append(
        {
            "goal": "Create a landing page outline for AI consulting",
            "reviewer_feedback": ["Add measurable outcomes."],
            "approved": True,
            "final_outcome": {},
        }
    )

    assert len(store.all()) == 1
    assert store.recall_feedback("AI consulting landing page") == ["Add measurable outcomes."]
