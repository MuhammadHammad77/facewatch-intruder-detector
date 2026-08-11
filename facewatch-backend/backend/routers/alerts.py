"""
/api/alerts — Alert History & Real-time WebSocket

Routes:
  WS   /api/alerts/ws                 — WebSocket for real-time alert push
  GET  /api/alerts                    — List alert history (paginated)
  PUT  /api/alerts/{alert_id}/review  — Mark alert as reviewed
"""

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from db.supabase_client import fetch_alerts, mark_alert_reviewed
from models.schemas import AlertItem, AlertMarkReviewedResponse
from services.alert_broadcaster import get_manager

router = APIRouter()


# ─── WS /api/alerts/ws ───────────────────────────────────────────────────────

@router.websocket("/ws")
async def alert_websocket(ws: WebSocket):
    """
    React dashboard connects here to receive real-time unknown-person alerts.
    Message format:
    {
        "type": "unknown_detected",
        "alert_id": "uuid",
        "snapshot_url": "/snapshots/unknown_0_...",
        "camera_source": "0",
        "confidence": 0.0,
        "detected_at": "2024-01-01T12:00:00"
    }
    """
    manager = get_manager()
    await manager.connect(ws)
    try:
        while True:
            # Keep connection alive — receive pings from client
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ─── GET /api/alerts ─────────────────────────────────────────────────────────

@router.get("", response_model=list[AlertItem])
async def get_alert_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Paginated alert history, newest first."""
    loop = asyncio.get_event_loop()
    alerts = await loop.run_in_executor(None, fetch_alerts, limit, offset)
    return [
        AlertItem(
            id=a["id"],
            snapshot_url=a["snapshot_url"],
            camera_source=a["camera_source"],
            confidence=a.get("confidence", 0.0),
            is_reviewed=a.get("is_reviewed", False),
            detected_at=a.get("detected_at"),
        )
        for a in alerts
    ]


# ─── PUT /api/alerts/{alert_id}/review ──────────────────────────────────────

@router.put("/{alert_id}/review", response_model=AlertMarkReviewedResponse)
async def review_alert(alert_id: str):
    """Mark an alert as reviewed by admin."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, mark_alert_reviewed, alert_id)
    return AlertMarkReviewedResponse(
        id=alert_id,
        message="Alert marked as reviewed.",
    )
