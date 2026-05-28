"""Tenant-aware workflow registry."""

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
    tenant_id: str
    workflow_namespace: str = "default"
    description: str = ""
    workflow_id: str = field(default_factory=lambda: str(uuid4()))
    versions: dict[str, WorkflowVersion] = field(default_factory=dict)
    active_version_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_version(
        self,
        definition: dict[str, Any],
        stage: WorkflowStage = WorkflowStage.DRAFT,
    ) -> WorkflowVersion:
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
            "tenant_id": self.tenant_id,
            "workflow_namespace": self.workflow_namespace,
            "description": self.description,
            "active_version_id": self.active_version_id,
            "active_version": self.active_version().to_dict() if self.active_version() else None,
            "versions": [version.to_dict() for version in self.versions.values()],
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class WorkflowRegistry:
    workflows: dict[str, WorkflowDefinition] = field(default_factory=dict)

    def create_workflow(
        self,
        name: str,
        tenant_id: str,
        workflow_namespace: str = "default",
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowDefinition:
        workflow = WorkflowDefinition(
            name=name,
            tenant_id=tenant_id,
            workflow_namespace=workflow_namespace,
            description=description,
            metadata=metadata or {},
        )

        self.workflows[workflow.workflow_id] = workflow
        return workflow

    def get_workflow(
        self,
        workflow_id: str,
        tenant_id: str | None = None,
    ) -> WorkflowDefinition:
        if workflow_id not in self.workflows:
            raise KeyError(f"Unknown workflow: {workflow_id}")

        workflow = self.workflows[workflow_id]

        if tenant_id and workflow.tenant_id != tenant_id:
            raise PermissionError("Workflow does not belong to tenant.")

        return workflow

    def list_workflows(
        self,
        tenant_id: str | None = None,
        workflow_namespace: str | None = None,
    ) -> list[dict[str, Any]]:
        workflows = list(self.workflows.values())

        if tenant_id:
            workflows = [
                workflow
                for workflow in workflows
                if workflow.tenant_id == tenant_id
            ]

        if workflow_namespace:
            workflows = [
                workflow
                for workflow in workflows
                if workflow.workflow_namespace == workflow_namespace
            ]

        return [workflow.to_dict() for workflow in workflows]

    def add_version(
        self,
        workflow_id: str,
        definition: dict[str, Any],
        stage: WorkflowStage = WorkflowStage.DRAFT,
        tenant_id: str | None = None,
    ) -> WorkflowVersion:
        workflow = self.get_workflow(workflow_id, tenant_id=tenant_id)
        return workflow.add_version(definition=definition, stage=stage)

    def set_active_version(
        self,
        workflow_id: str,
        version_id: str,
        tenant_id: str | None = None,
    ) -> WorkflowVersion:
        workflow = self.get_workflow(workflow_id, tenant_id=tenant_id)
        return workflow.set_active_version(version_id)

    def list_namespaces(self, tenant_id: str) -> list[str]:
        namespaces = {
            workflow.workflow_namespace
            for workflow in self.workflows.values()
            if workflow.tenant_id == tenant_id
        }

        return sorted(namespaces)
