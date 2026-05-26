"""Structured JSON logging utilities for orchestration runs."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class JsonLogFormatter(logging.Formatter):
    """Format log records as compact JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            payload.update(extra)

        return json.dumps(payload, sort_keys=True)


def build_json_logger(name: str = "agent_orchestration") -> logging.Logger:
    """Build a logger that emits JSON lines to stderr."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonLogFormatter())
        logger.addHandler(handler)

    return logger


@dataclass
class StructuredRunLogger:
    """Small helper for logging orchestration lifecycle events."""

    logger: logging.Logger
    run_id: str | None = None

    def __post_init__(self) -> None:
        if self.run_id is None:
            self.run_id = str(uuid4())

    def info(self, event: str, **details: Any) -> None:
        """Emit a structured info event."""
        self.logger.info(
            event,
            extra={
                "extra": {
                    "run_id": self.run_id,
                    "event": event,
                    **details,
                }
            },
        )
