"""
WebSocket Alert Broadcaster
────────────────────────────
When an unknown face is detected, this pushes a real-time JSON message
to every connected React dashboard client.

Usage:
  1. React connects to ws://localhost:8000/api/alerts/ws
  2. Backend calls broadcast_alert({...}) when unknown is found
  3. React receives the JSON and shows a toast/notification
"""

import json
from fastapi import WebSocket
from typing import List


class _ConnectionManager:
    """Manages all active WebSocket connections."""

    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        print(f"🔌 Dashboard connected. Total clients: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        print(f"🔌 Dashboard disconnected. Remaining: {len(self.active)}")

    async def broadcast(self, payload: dict):
        """Send JSON payload to all connected dashboards."""
        message = json.dumps(payload)
        dead: List[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        # Clean up disconnected clients
        for ws in dead:
            self.disconnect(ws)


# Singleton instance
_manager = _ConnectionManager()


async def broadcast_alert(payload: dict):
    """Module-level function — import this in routers/stream."""
    await _manager.broadcast(payload)


def get_manager() -> _ConnectionManager:
    """Used by the WebSocket router endpoint to get the manager."""
    return _manager
