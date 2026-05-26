"""WebSocket event broadcasting for live orchestration updates."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


@dataclass
class WebSocketEventManager:
    """Manage live WebSocket clients and broadcast orchestration events."""

    active_connections: list[WebSocket] = field(default_factory=list)

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.send_personal_message(
            websocket,
            {
                "event": "connected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Connected to orchestration event stream.",
            },
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        """Send one event payload to one WebSocket client."""
        await websocket.send_json(payload)

    async def broadcast(self, event: str, **payload: Any) -> None:
        """Broadcast an event payload to all connected clients."""
        message = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload,
        }

        stale_connections: list[WebSocket] = []

        for websocket in list(self.active_connections):
            try:
                await websocket.send_json(message)
            except Exception:
                stale_connections.append(websocket)

        for websocket in stale_connections:
            self.disconnect(websocket)

    def broadcast_sync(self, event: str, **payload: Any) -> None:
        """Best-effort synchronous broadcast helper for worker threads."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        if loop.is_running():
            asyncio.create_task(self.broadcast(event, **payload))
