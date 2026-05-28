"""Tenant-aware scheduled workflow infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class ScheduledWorkflow:
    """Represents one recurring workflow schedule."""

    workflow_id: str
    tenant_id: str
    cron_expression: str
    workflow_namespace: str = "default"
    schedule_id: str = field(default_factory=lambda: str(uuid4()))
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_run_at: str | None = None

    def mark_executed(self) -> None:
        """Record workflow execution timestamp."""
        self.last_run_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "workflow_id": self.workflow_id,
            "tenant_id": self.tenant_id,
            "workflow_namespace": self.workflow_namespace,
            "cron_expression": self.cron_expression,
            "enabled": self.enabled,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "last_run_at": self.last_run_at,
        }


@dataclass
class WorkflowScheduler:
    """Tenant-aware recurring workflow scheduler."""

    schedules: dict[str, ScheduledWorkflow] = field(default_factory=dict)

    def schedule_workflow(
        self,
        workflow_id: str,
        tenant_id: str,
        cron_expression: str,
        workflow_namespace: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> ScheduledWorkflow:
        """Register a recurring workflow schedule."""
        schedule = ScheduledWorkflow(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            cron_expression=cron_expression,
            workflow_namespace=workflow_namespace,
            metadata=metadata or {},
        )

        self.schedules[schedule.schedule_id] = schedule
        return schedule

    def get_schedule(
        self,
        schedule_id: str,
        tenant_id: str | None = None,
    ) -> ScheduledWorkflow:
        """Retrieve a scheduled workflow."""
        if schedule_id not in self.schedules:
            raise KeyError(f"Unknown schedule: {schedule_id}")

        schedule = self.schedules[schedule_id]

        if tenant_id and schedule.tenant_id != tenant_id:
            raise PermissionError(
                "Schedule does not belong to tenant."
            )

        return schedule

    def list_schedules(
        self,
        tenant_id: str | None = None,
        workflow_namespace: str | None = None,
    ) -> list[dict[str, Any]]:
        """List scheduled workflows."""
        schedules = list(self.schedules.values())

        if tenant_id:
            schedules = [
                schedule
                for schedule in schedules
                if schedule.tenant_id == tenant_id
            ]

        if workflow_namespace:
            schedules = [
                schedule
                for schedule in schedules
                if schedule.workflow_namespace == workflow_namespace
            ]

        return [schedule.to_dict() for schedule in schedules]

    def disable_schedule(
        self,
        schedule_id: str,
        tenant_id: str | None = None,
    ) -> ScheduledWorkflow:
        """Disable one workflow schedule."""
        schedule = self.get_schedule(
            schedule_id,
            tenant_id=tenant_id,
        )

        schedule.enabled = False
        return schedule

    def enable_schedule(
        self,
        schedule_id: str,
        tenant_id: str | None = None,
    ) -> ScheduledWorkflow:
        """Enable one workflow schedule."""
        schedule = self.get_schedule(
            schedule_id,
            tenant_id=tenant_id,
        )

        schedule.enabled = True
        return schedule
