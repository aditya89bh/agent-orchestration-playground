"""DAG scheduling primitives for workflow-style orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class NodeStatus(str, Enum):
    """Execution states for DAG nodes."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


NodeHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class DAGNode:
    """One executable node inside a workflow DAG."""

    node_id: str
    name: str
    handler: NodeHandler
    dependencies: list[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the node state."""
        return {
            "node_id": self.node_id,
            "name": self.name,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class DAGExecutionResult:
    """Final DAG execution result."""

    succeeded: bool
    node_results: dict[str, dict[str, Any]]
    execution_order: list[str]
    failed_nodes: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the DAG execution result."""
        return {
            "succeeded": self.succeeded,
            "node_results": self.node_results,
            "execution_order": self.execution_order,
            "failed_nodes": self.failed_nodes,
        }


@dataclass
class DAGExecutor:
    """Dependency-aware DAG executor for deterministic workflow execution."""

    nodes: dict[str, DAGNode]

    def validate(self) -> None:
        """Validate that all dependencies exist and the graph is acyclic."""
        for node in self.nodes.values():
            for dependency in node.dependencies:
                if dependency not in self.nodes:
                    raise ValueError(
                        f"Node {node.node_id} depends on missing node {dependency}."
                    )

        self._topological_order()

    def execute(self, initial_context: dict[str, Any] | None = None) -> DAGExecutionResult:
        """Execute the DAG in dependency order."""
        self.validate()

        context = dict(initial_context or {})
        execution_order: list[str] = []
        failed_nodes: list[str] = []
        node_results: dict[str, dict[str, Any]] = {}

        for node_id in self._topological_order():
            node = self.nodes[node_id]

            if any(self.nodes[dep].status == NodeStatus.FAILED for dep in node.dependencies):
                node.status = NodeStatus.BLOCKED
                failed_nodes.append(node.node_id)
                continue

            node.status = NodeStatus.RUNNING

            try:
                dependency_outputs = {
                    dep: self.nodes[dep].result
                    for dep in node.dependencies
                }
                node_context = {
                    **context,
                    "dependency_outputs": dependency_outputs,
                    "node_id": node.node_id,
                }
                node.result = node.handler(node_context)
                node.status = NodeStatus.COMPLETED
                node_results[node.node_id] = node.result
                execution_order.append(node.node_id)
                context[node.node_id] = node.result
            except Exception as error:
                node.status = NodeStatus.FAILED
                node.error = f"{error.__class__.__name__}: {error}"
                failed_nodes.append(node.node_id)

        return DAGExecutionResult(
            succeeded=not failed_nodes,
            node_results=node_results,
            execution_order=execution_order,
            failed_nodes=failed_nodes,
        )

    def _topological_order(self) -> list[str]:
        """Return dependency-safe execution order or raise on cycles."""
        visited: set[str] = set()
        temporary: set[str] = set()
        order: list[str] = []

        def visit(node_id: str) -> None:
            if node_id in temporary:
                raise ValueError("DAG contains a cycle.")
            if node_id in visited:
                return

            temporary.add(node_id)

            for dependency in self.nodes[node_id].dependencies:
                visit(dependency)

            temporary.remove(node_id)
            visited.add(node_id)
            order.append(node_id)

        for node_id in self.nodes:
            visit(node_id)

        return order
