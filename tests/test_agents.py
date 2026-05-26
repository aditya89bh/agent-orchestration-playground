from agents import BuilderAgent, CommanderAgent, PlannerAgent, ReviewerAgent


def test_agents_work_together() -> None:
    commander = CommanderAgent()
    planner = PlannerAgent()
    builder = BuilderAgent()
    reviewer = ReviewerAgent()

    brief = commander.accept_goal("Create a landing page outline")
    graph = planner.plan(brief["goal"])
    draft = builder.build(brief["goal"], graph)
    review = reviewer.review(draft)

    assert brief["goal"] == "Create a landing page outline"
    assert graph.nodes
    assert draft["artifact_type"] == "landing_page_outline"
    assert review["approved"] is True
    assert review["feedback"]
