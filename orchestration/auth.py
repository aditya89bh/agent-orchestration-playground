"""Lightweight RBAC and API key authorization for orchestration APIs."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class Role(str, Enum):
    """Built-in orchestration platform roles."""

    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Permission scopes for orchestration API surfaces."""

    ORCHESTRATION_EXECUTE = "orchestration.execute"
    JOB_SUBMIT = "job.submit"
    JOB_READ = "job.read"
    TRACE_READ = "trace.read"
    REPLAY_EXECUTE = "replay.execute"
    PLUGIN_EXECUTE = "plugin.execute"
    PLUGIN_READ = "plugin.read"
    METRICS_READ = "metrics.read"
    WORKFLOW_MANAGE = "workflow.manage"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: set(Permission),
    Role.OPERATOR: {
        Permission.ORCHESTRATION_EXECUTE,
        Permission.JOB_SUBMIT,
        Permission.JOB_READ,
        Permission.TRACE_READ,
        Permission.REPLAY_EXECUTE,
        Permission.PLUGIN_EXECUTE,
        Permission.PLUGIN_READ,
        Permission.METRICS_READ,
    },
    Role.VIEWER: {
        Permission.JOB_READ,
        Permission.TRACE_READ,
        Permission.PLUGIN_READ,
        Permission.METRICS_READ,
    },
}


@dataclass(frozen=True)
class APIKeyRecord:
    """Stored API key metadata. Only the key hash is retained."""

    key_id: str
    key_hash: str
    role: Role
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize API key metadata without exposing the secret."""
        return {
            "key_id": self.key_id,
            "role": self.role.value,
            "created_at": self.created_at,
        }


@dataclass
class AuthManager:
    """In-memory API key manager with role-based permissions."""

    keys: dict[str, APIKeyRecord] = field(default_factory=dict)

    def create_api_key(self, role: Role = Role.OPERATOR) -> dict[str, str]:
        """Create and store a new API key."""
        key_id = str(uuid4())
        secret = secrets.token_urlsafe(32)
        key = f"aop_{key_id}_{secret}"
        record = APIKeyRecord(
            key_id=key_id,
            key_hash=self._hash_key(key),
            role=role,
        )
        self.keys[key_id] = record
        return {
            "key_id": key_id,
            "api_key": key,
            "role": role.value,
        }

    def list_api_keys(self) -> list[dict[str, Any]]:
        """List API key metadata."""
        return [record.to_dict() for record in self.keys.values()]

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke one API key."""
        return self.keys.pop(key_id, None) is not None

    def authorize(self, api_key: str | None, permission: Permission) -> APIKeyRecord:
        """Authorize an API key for one permission."""
        if not api_key:
            raise PermissionError("Missing API key.")

        key_hash = self._hash_key(api_key)
        for record in self.keys.values():
            if record.key_hash == key_hash:
                allowed = ROLE_PERMISSIONS[record.role]
                if permission not in allowed:
                    raise PermissionError(
                        f"Role {record.role.value} lacks permission {permission.value}."
                    )
                return record

        raise PermissionError("Invalid API key.")

    @staticmethod
    def _hash_key(api_key: str) -> str:
        """Hash an API key before storage or comparison."""
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()
