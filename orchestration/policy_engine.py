"""Tenant-aware orchestration policy engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionQuota:
    """Execution limits for a tenant."""

    max_concurrent_workflows: int = 10
    max_scheduled_workflows: int = 25
    max_replays_per_hour: int = 50
    max_plugin_executions_per_hour: int = 100
    max_workflow_executions_per_hour: int = 250

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_concurrent_workflows": self.max_concurrent_workflows,
            "max_scheduled_workflows": self.max_scheduled_workflows,
            "max_replays_per_hour": self.max_replays_per_hour,
            "max_plugin_executions_per_hour": self.max_plugin_executions_per_hour,
            "max_workflow_executions_per_hour": self.max_workflow_executions_per_hour,
        }


@dataclass
class TenantPolicy:
    """Governance policy for one tenant."""

    tenant_id: str
    quotas: ExecutionQuota = field(default_factory=ExecutionQuota)
    allow_replay: bool = True
    allow_plugins: bool = True
    allow_scheduling: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "quotas": self.quotas.to_dict(),
            "allow_replay": self.allow_replay,
            "allow_plugins": self.allow_plugins,
            "allow_scheduling": self.allow_scheduling,
        }


@dataclass
class PolicyDecision:
    """Result of policy evaluation."""

    allowed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
        }


@dataclass
class PolicyEngine:
    """Tenant-aware orchestration governance engine."""

    policies: dict[str, TenantPolicy] = field(default_factory=dict)

    def register_policy(
        self,
        tenant_id: str,
        quotas: ExecutionQuota | None = None,
        allow_replay: bool = True,
        allow_plugins: bool = True,
        allow_scheduling: bool = True,
    ) -> TenantPolicy:
        """Register governance policy for one tenant."""
        policy = TenantPolicy(
            tenant_id=tenant_id,
            quotas=quotas or ExecutionQuota(),
            allow_replay=allow_replay,
            allow_plugins=allow_plugins,
            allow_scheduling=allow_scheduling,
        )

        self.policies[tenant_id] = policy
        return policy

    def get_policy(self, tenant_id: str) -> TenantPolicy:
        """Retrieve tenant policy."""
        if tenant_id not in self.policies:
            raise KeyError(f"Unknown tenant policy: {tenant_id}")

        return self.policies[tenant_id]

    def evaluate_replay(
        self,
        tenant_id: str,
        replay_count: int = 0,
    ) -> PolicyDecision:
        """Evaluate replay permissions and quotas."""
        policy = self.get_policy(tenant_id)

        if not policy.allow_replay:
            return PolicyDecision(
                allowed=False,
                reason="Replay disabled for tenant.",
            )

        if replay_count >= policy.quotas.max_replays_per_hour:
            return PolicyDecision(
                allowed=False,
                reason="Replay quota exceeded.",
            )

        return PolicyDecision(
            allowed=True,
            reason="Replay allowed.",
        )

    def evaluate_scheduling(
        self,
        tenant_id: str,
        active_schedule_count: int,
    ) -> PolicyDecision:
        """Evaluate scheduling permissions and quotas."""
        policy = self.get_policy(tenant_id)

        if not policy.allow_scheduling:
            return PolicyDecision(
                allowed=False,
                reason="Scheduling disabled for tenant.",
            )

        if (
            active_schedule_count
            >= policy.quotas.max_scheduled_workflows
        ):
            return PolicyDecision(
                allowed=False,
                reason="Tenant scheduling quota exceeded.",
            )

        return PolicyDecision(
            allowed=True,
            reason="Scheduling allowed.",
        )

    def evaluate_plugins(
        self,
        tenant_id: str,
        plugin_execution_count: int = 0,
    ) -> PolicyDecision:
        """Evaluate plugin execution permissions and quotas."""
        policy = self.get_policy(tenant_id)

        if not policy.allow_plugins:
            return PolicyDecision(
                allowed=False,
                reason="Plugins disabled for tenant.",
            )

        if (
            plugin_execution_count
            >= policy.quotas.max_plugin_executions_per_hour
        ):
            return PolicyDecision(
                allowed=False,
                reason="Plugin execution quota exceeded.",
            )

        return PolicyDecision(
            allowed=True,
            reason="Plugins allowed.",
        )

    def evaluate_workflow_execution(
        self,
        tenant_id: str,
        concurrent_workflow_count: int,
        workflow_execution_count: int,
    ) -> PolicyDecision:
        """Evaluate workflow runtime quotas."""
        policy = self.get_policy(tenant_id)

        if (
            concurrent_workflow_count
            >= policy.quotas.max_concurrent_workflows
        ):
            return PolicyDecision(
                allowed=False,
                reason="Concurrent workflow quota exceeded.",
            )

        if (
            workflow_execution_count
            >= policy.quotas.max_workflow_executions_per_hour
        ):
            return PolicyDecision(
                allowed=False,
                reason="Workflow execution quota exceeded.",
            )

        return PolicyDecision(
            allowed=True,
            reason="Workflow execution allowed.",
        )
