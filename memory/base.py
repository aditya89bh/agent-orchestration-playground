"""Abstract storage interfaces for orchestration persistence backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MemoryBackend(ABC):
    """Abstract interface for memory persistence backends."""

    @abstractmethod
    def append_memory(self, entry: dict[str, Any]) -> None:
        """Persist a memory entry."""

    @abstractmethod
    def recall_feedback(self, goal: str, limit: int = 3) -> list[str]:
        """Recall feedback relevant to a goal."""


class RunHistoryBackend(ABC):
    """Abstract interface for orchestration run history backends."""

    @abstractmethod
    def append_run(self, result: dict[str, Any]) -> dict[str, Any]:
        """Persist a run summary."""

    @abstractmethod
    def list_runs(self) -> list[dict[str, Any]]:
        """List persisted orchestration runs."""
