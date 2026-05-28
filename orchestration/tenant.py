"""Multi-tenant orchestration primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class Tenant:
    """Represents one isolated orchestration tenant."""

    name: str
    tenant_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class TenantContext:
    """Execution context injected into orchestration systems."""

    tenant: Tenant
    workflow_namespace: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant": self.tenant.to_dict(),
            "workflow_namespace": self.workflow_namespace,
        }


@dataclass
class TenantRegistry:
    """In-memory tenant registry."""

    tenants: dict[str, Tenant] = field(default_factory=dict)

    def create_tenant(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> Tenant:
        tenant = Tenant(
            name=name,
            metadata=metadata or {},
        )
        self.tenants[tenant.tenant_id] = tenant
        return tenant

    def get_tenant(self, tenant_id: str) -> Tenant:
        if tenant_id not in self.tenants:
            raise KeyError(f"Unknown tenant: {tenant_id}")

        return self.tenants[tenant_id]

    def list_tenants(self) -> list[dict[str, Any]]:
        return [
            tenant.to_dict()
            for tenant in self.tenants.values()
        ]
