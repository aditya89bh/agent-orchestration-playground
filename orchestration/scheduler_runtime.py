"""Recurring workflow execution runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from orchestration.scheduler import ScheduledWorkflow, WorkflowScheduler


@dataclass
class ScheduledExecutionRecord:
    """Represents one scheduled workflow execution."""

    schedule_id: str
    workflow_id: str
    tenant_id: str
    workflow_namespace: str
    executed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "workflow_id": self.workflow_id,
            "tenant_id": self.tenant_id,
            "workflow_namespace": self.workflow_namespace,
            "executed_at": self.executed_at,
            "success": self.success,
            "metadata": self.metadata,
        }


@dataclass
class SchedulerRuntime:
    """Executes tenant-aware scheduled workflows."""

    scheduler: WorkflowScheduler = field(default_factory=WorkflowScheduler)
    execution_history: list[ScheduledExecutionRecord] = field(default_factory=list)

    def execute_schedule(
        self,
        schedule_id: str,
        tenant_id: str,
    ) -> ScheduledExecutionRecord:
        """Execute one scheduled workflow."""
        schedule = self.scheduler.get_schedule(
            schedule_id,
            tenant_id=tenant_id,
        )

        if not schedule.enabled:
            raise RuntimeError("Scheduled workflow is disabled.")

        schedule.mark_executed()

        execution = ScheduledExecutionRecord(
            schedule_id=schedule.schedule_id,
            workflow_id=schedule.workflow_id,
            tenant_id=schedule.tenant_id,
            workflow_namespace=schedule.workflow_namespace,
            metadata={
                "cron_expression": schedule.cron_expression,
            },
        )

        self.execution_history.append(execution)

        return execution

    def list_execution_history(
        self,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List scheduled workflow executions."""
        history = self.execution_history

        if tenant_id:
            history = [
                execution
                for execution in history
                if execution.tenant_id == tenant_id
            ]

        return [execution.to_dict() for execution in history]

    def list_active_schedules(
        self,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List active schedules."""
        schedules = self.scheduler.list_schedules(
            tenant_id=tenant_id,
        )

        return [
            schedule
            for schedule in schedules
            if schedule["enabled"]
        ]
