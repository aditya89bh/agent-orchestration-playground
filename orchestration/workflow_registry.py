"""Workflow version registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class WorkflowStage(str, Enum):
    DRAFT = "draft"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class WorkflowVersion:
    workflow_id: str
    version_id: str
    definition: dict[str, Any]
    stage: WorkflowStage = WorkflowStage.DRAFT
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "version_id": self.version_id,
            "definition": self.definition,
            "stage": self.stage.value,
            "created_at": self.created_at,
        }


@dataclass
class WorkflowDefinition:
    name: str
    description: str = ""
    workflow_id: str = field(default_factory=lambda: str(uuid4()))
    versions: dict[str, WorkflowVersion] = field(default_factory=dict)
    active_version_id: str | None = None

    def add_version(self, definition: dict[str, Any], stage: WorkflowStage = WorkflowStage.DRAFT) -> WorkflowVersion:
        version = WorkflowVersion(
            workflow_id=self.workflow_id,
            version_id=str(uuid4()),
            definition=definition,
            stage=stage,
        )
        self.versions[version.version_id] = version
        if self.active_version_id is None or stage == WorkflowStage.PRODUCTION:
            self.active_version_id = version.version_id
        return version

    def active_version(self) -> WorkflowVersion | None:
        if self.active_version_id is None:
            return None
        return self.versions.get(self.active_version_id)

    def set_active_version(self, version_id: str) -> WorkflowVersion:
        if version_id not in self.versions:
            raise KeyError(f"Unknown workflow version: {version_id}")
        self.active_version_id = version_id
        return self.versions[version_id]

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "active_version_id": self.active_version_id,
            "active_version": self.active_version().to_dict() if self.active_version() else None,
            "versions": [version.to_dict() for version in self.versions.values()],
        }


@dataclass
class WorkflowRegistry:
    workflows: dict[str, WorkflowDefinition] = field(default_factory=dict)

    def create_workflow(self, name: str, description: str = "") -> WorkflowDefinition:
        workflow = WorkflowDefinition(name=name, description=description)
        self.workflows[workflow.workflow_id] = workflow
        return workflow

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition:
        if workflow_id not in self.workflows:
            raise KeyError(f"Unknown workflow: {workflow_id}")
        return self.workflows[workflow_id]

    def list_workflows(self) -> list[dict[str, Any]]:
        return [workflow.to_dict() for workflow in self.workflows.values()]

    def add_version(self, workflow_id: str, definition: dict[str, Any], stage: WorkflowStage = WorkflowStage.DRAFT) -> WorkflowVersion:
        return self.get_workflow(workflow_id).add_version(definition=definition, stage=stage)

    def set_active_version(self, workflow_id: str, version_id: str) -> WorkflowVersion:
        return self.get_workflow(workflow_id).set_active_version(version_id)
