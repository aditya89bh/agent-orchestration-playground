"""Plugin sandbox execution primitives."""

from __future__ import annotations

import multiprocessing
import queue
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class SandboxMode(str, Enum):
    """Execution isolation modes for plugins."""

    TRUSTED = "trusted"
    SUBPROCESS = "subprocess"


@dataclass
class ResourceLimits:
    """Execution constraints for sandboxed plugins."""

    timeout_seconds: int = 5
    memory_limit_mb: int = 128


@dataclass
class PluginExecutionPolicy:
    """Policy describing plugin execution permissions."""

    trusted: bool = False
    network_access: bool = False
    filesystem_access: bool = False
    mode: SandboxMode = SandboxMode.SUBPROCESS
    resource_limits: ResourceLimits = ResourceLimits()


@dataclass
class SandboxResult:
    """Result returned from sandbox execution."""

    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None
    mode: str = SandboxMode.SUBPROCESS.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "mode": self.mode,
        }


class SandboxRunner:
    """Execute plugins under lightweight sandbox policies."""

    def execute(
        self,
        plugin: Callable[..., dict[str, Any]],
        policy: PluginExecutionPolicy,
        **kwargs: Any,
    ) -> SandboxResult:
        """Execute a plugin using the configured isolation policy."""
        if policy.mode == SandboxMode.TRUSTED:
            try:
                return SandboxResult(
                    success=True,
                    result=plugin(**kwargs),
                    mode=SandboxMode.TRUSTED.value,
                )
            except Exception as error:
                return SandboxResult(
                    success=False,
                    error=f"{error.__class__.__name__}: {error}",
                    mode=SandboxMode.TRUSTED.value,
                )

        return self._execute_subprocess(plugin, policy, **kwargs)

    def _execute_subprocess(
        self,
        plugin: Callable[..., dict[str, Any]],
        policy: PluginExecutionPolicy,
        **kwargs: Any,
    ) -> SandboxResult:
        """Execute a plugin in a subprocess with timeout protection."""
        result_queue: multiprocessing.Queue = multiprocessing.Queue()

        process = multiprocessing.Process(
            target=self._worker,
            args=(result_queue, plugin, kwargs),
            daemon=True,
        )

        process.start()
        process.join(timeout=policy.resource_limits.timeout_seconds)

        if process.is_alive():
            process.terminate()
            process.join()
            return SandboxResult(
                success=False,
                error="Plugin execution timed out.",
            )

        try:
            payload = result_queue.get_nowait()
        except queue.Empty:
            return SandboxResult(
                success=False,
                error="Sandbox returned no result.",
            )

        return SandboxResult(**payload)

    @staticmethod
    def _worker(
        result_queue: multiprocessing.Queue,
        plugin: Callable[..., dict[str, Any]],
        kwargs: dict[str, Any],
    ) -> None:
        """Execute plugin code in isolated subprocess."""
        try:
            result = plugin(**kwargs)
            result_queue.put(
                {
                    "success": True,
                    "result": result,
                    "mode": SandboxMode.SUBPROCESS.value,
                }
            )
        except Exception:
            result_queue.put(
                {
                    "success": False,
                    "error": traceback.format_exc(),
                    "mode": SandboxMode.SUBPROCESS.value,
                }
            )
