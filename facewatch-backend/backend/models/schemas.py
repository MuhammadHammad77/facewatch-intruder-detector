"""
Pydantic schemas — request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── Face Registration ────────────────────────────────────────────────────────

class FaceRegisterResponse(BaseModel):
    id: str
    name: str
    photo_url: str
    message: str


class FaceListItem(BaseModel):
    id: str
    name: str
    photo_url: Optional[str]
    created_at: Optional[datetime]


# ─── Alerts ──────────────────────────────────────────────────────────────────

class AlertItem(BaseModel):
    id: str
    snapshot_url: str
    camera_source: str
    confidence: float
    is_reviewed: bool
    detected_at: Optional[datetime]


class AlertMarkReviewedResponse(BaseModel):
    id: str
    message: str


# ─── Stream Config ────────────────────────────────────────────────────────────

class StreamSource(BaseModel):
    """Body for starting/stopping a video source."""
    source: str = Field(
        ...,
        description="'0' for webcam, RTSP URL, or 'upload' for file stream",
        examples=["0", "rtsp://192.168.1.100:554/stream", "upload"]
    )
    label: Optional[str] = Field(None, description="Human-readable camera name")
