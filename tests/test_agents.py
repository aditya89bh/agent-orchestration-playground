from agents import BuilderAgent, CommanderAgent, PlannerAgent, ReviewerAgent


def test_agents_have_distinct_responsibilities() -> None:
    commander = CommanderAgent()
    planner = PlannerAgent()
    builder = BuilderAgent()
    reviewer = ReviewerAgent()

    brief = commander.create_brief("Create a landing page outline")
    steps = planner.plan(brief)
    draft = builder.build(str(brief["goal"]), steps)
    review = reviewer.review(draft)

    assert brief["goal"] == "Create a landing page outline"
    assert any("hero" in step.lower() for step in steps)
    assert draft["artifact_type"] == "landing_page_outline"
    assert review["approved"] is True
    assert review["feedback"]
