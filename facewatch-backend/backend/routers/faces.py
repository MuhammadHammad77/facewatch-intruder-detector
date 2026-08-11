"""
/api/faces — Face Registration & Management

Routes:
  POST   /api/faces/register      — Upload photo + name → encode → store in DB
  GET    /api/faces                — List all registered faces
  DELETE /api/faces/{face_id}      — Remove a face (soft delete)
  POST   /api/faces/refresh-cache  — Manually reload in-memory cache
"""

import os
import uuid
import asyncio
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status

from db.supabase_client import insert_face, fetch_all_faces, delete_face, get_supabase
from models.schemas import FaceRegisterResponse, FaceListItem
from services.face_cache import FaceEncodingCache
from services.recognition import encode_image_bytes

router = APIRouter()

SUPABASE_BUCKET = "face-photos"   # Create this bucket in Supabase Storage


# ─── POST /api/faces/register ────────────────────────────────────────────────

@router.post("/register", response_model=FaceRegisterResponse, status_code=201)
async def register_face(
    name: Annotated[str, Form(description="Full name of the person")],
    photo: Annotated[UploadFile, File(description="Clear front-facing photo (JPG/PNG)")],
):
    """
    Admin endpoint: Upload a photo and name.
    System encodes the face into a 128D vector and stores it in Supabase.
    No code update needed — just call this API!
    """
    # ── Validate file type ──────────────────────────────────────────────────
    if photo.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPG, PNG, or WEBP images are accepted.",
        )

    image_bytes = await photo.read()

    if len(image_bytes) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image must be under 10 MB.",
        )

    # ── Extract 128D encoding from image ────────────────────────────────────
    try:
        loop = asyncio.get_event_loop()
        encoding = await loop.run_in_executor(None, encode_image_bytes, image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # ── Upload photo to Supabase Storage ────────────────────────────────────
    ext = photo.filename.rsplit(".", 1)[-1] if "." in photo.filename else "jpg"
    storage_path = f"{uuid.uuid4().hex}.{ext}"

    try:
        supabase = get_supabase()
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=image_bytes,
            file_options={"content-type": photo.content_type},
        )
        photo_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")

    # ── Insert face record into DB ───────────────────────────────────────────
    try:
        loop = asyncio.get_event_loop()
        new_face = await loop.run_in_executor(
            None, insert_face, name.strip(), encoding, photo_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database insert failed: {str(e)}")

    # ── Refresh in-memory cache so recognition picks up the new face ─────────
    await FaceEncodingCache.refresh()

    return FaceRegisterResponse(
        id=new_face["id"],
        name=new_face["name"],
        photo_url=new_face["photo_url"],
        message=f"✅ '{name}' registered successfully and cache updated.",
    )


# ─── GET /api/faces ──────────────────────────────────────────────────────────

@router.get("", response_model=list[FaceListItem])
async def list_faces():
    """Return all active registered faces."""
    loop = asyncio.get_event_loop()
    faces = await loop.run_in_executor(None, fetch_all_faces)
    return [
        FaceListItem(
            id=f["id"],
            name=f["name"],
            photo_url=f.get("photo_url"),
            created_at=f.get("created_at"),
        )
        for f in faces
    ]


# ─── DELETE /api/faces/{face_id} ─────────────────────────────────────────────

@router.delete("/{face_id}", status_code=200)
async def remove_face(face_id: str):
    """Soft-delete a face and refresh cache."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, delete_face, face_id)
    await FaceEncodingCache.refresh()
    return {"message": f"Face {face_id} removed and cache updated."}


# ─── POST /api/faces/refresh-cache ───────────────────────────────────────────

@router.post("/refresh-cache")
async def refresh_cache():
    """Manually reload in-memory face encodings from DB."""
    await FaceEncodingCache.refresh()
    return {
        "message": "Cache refreshed.",
        "loaded": len(FaceEncodingCache.encodings),
    }
