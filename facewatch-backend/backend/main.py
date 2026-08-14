"""
FaceWatch - Real-Time Unknown Person Detection System
Main FastAPI Application Entry Point
"""

import asyncio
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import base64
import os
from contextlib import asynccontextmanager

import cv2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db.supabase_client import init_db
from routers import faces, video_stream, alerts
from services.face_cache import FaceEncodingCache

# ─── Startup / Shutdown ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load known face encodings into memory cache on startup."""
    print("Initializing local DB...")
    await init_db()
    print("Loading face encodings from database into cache...")
    await FaceEncodingCache.refresh()
    print(f"Loaded {len(FaceEncodingCache.encodings)} known faces.")
    yield
    print("Shutting down FaceWatch...")


# ─── App Init ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="FaceWatch API",
    description="Real-Time Unknown Person Detection System",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS (allow React frontend on Vercel) ──────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "https://facewatch-intruder-detector.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Serve snapshots as static files ────────────────────────────────────────

os.makedirs("snapshots", exist_ok=True)
app.mount("/snapshots", StaticFiles(directory="snapshots"), name="snapshots")

os.makedirs("storage", exist_ok=True)
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# ─── Routers ─────────────────────────────────────────────────────────────────

app.include_router(faces.router,        prefix="/api/faces",   tags=["Face Management"])
app.include_router(video_stream.router, prefix="/api/stream",  tags=["Video Stream"])
app.include_router(alerts.router,       prefix="/api/alerts",  tags=["Alerts"])


@app.get("/")
async def root():
    return {"status": "FaceWatch is running 🟢", "version": "1.0.0"}


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "known_faces_loaded": len(FaceEncodingCache.encodings),
    }
