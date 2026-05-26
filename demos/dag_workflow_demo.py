"""Dependency-aware DAG orchestration demo."""

from __future__ import annotations

from orchestration.dag import DAGExecutor, DAGNode


def commander_step(context: dict) -> dict:
    return {
        "goal": context["goal"],
        "accepted": True,
    }


def planner_step(context: dict) -> dict:
    return {
        "tasks": [
            "Create hero section",
            "Generate CTA copy",
            "Prepare pricing structure",
        ]
    }


def builder_step(context: dict) -> dict:
    planner_output = context["dependency_outputs"]["planner"]

    return {
        "artifact": {
            "sections": planner_output["tasks"]
        }
    }


def reviewer_step(context: dict) -> dict:
    builder_output = context["dependency_outputs"]["builder"]

    return {
        "approved": True,
        "section_count": len(builder_output["artifact"]["sections"]),
    }


nodes = {
    "commander": DAGNode(
        node_id="commander",
        name="Commander",
        handler=commander_step,
    ),
    "planner": DAGNode(
        node_id="planner",
        name="Planner",
        handler=planner_step,
        dependencies=["commander"],
    ),
    "builder": DAGNode(
        node_id="builder",
        name="Builder",
        handler=builder_step,
        dependencies=["planner"],
    ),
    "reviewer": DAGNode(
        node_id="reviewer",
        name="Reviewer",
        handler=reviewer_step,
        dependencies=["builder"],
    ),
}

executor = DAGExecutor(nodes)

result = executor.execute(
    {
        "goal": "Create a startup landing page workflow."
    }
)

if __name__ == "__main__":
    print(result.to_dict())
