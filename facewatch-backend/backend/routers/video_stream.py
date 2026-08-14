"""
/api/stream — Video Feed & File Processing

Routes:
  GET  /api/stream/feed/{source}     — MJPEG stream for live camera/RTSP
  POST /api/stream/upload            — Process an uploaded MP4 video file
  GET  /api/stream/sources           — List available camera sources

The MJPEG approach: Each frame is sent as a multipart JPEG over one HTTP
connection. The React frontend renders it with a simple <img src="..."> tag.
No WebSockets needed for the video feed itself (WebSockets are used for alerts).
"""

import asyncio
import base64
import io
import os
import time
import uuid
import tempfile
from typing import AsyncGenerator

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from db.supabase_client import insert_alert
from services.recognition import recognize_faces_in_frame, draw_annotations, save_snapshot
from services.alert_broadcaster import broadcast_alert

router = APIRouter()

# ── Cooldown: only fire an alert once every N seconds per camera source ────
ALERT_COOLDOWN_SECONDS = 10
_last_alert_time: dict[str, float] = {}   # source_key → last alert timestamp


# ─── Core: Process one frame ────────────────────────────────────────────────

def _process_frame(frame_bgr: np.ndarray, source_key: str) -> np.ndarray:
    """
    1. Detect and classify all faces in the frame.
    2. Annotate the frame (green/red boxes).
    3. If any UNKNOWN face found and cooldown passed → save snapshot + fire alert.

    Returns the annotated frame.
    """
    face_results = recognize_faces_in_frame(frame_bgr)
    annotated = draw_annotations(frame_bgr.copy(), face_results)

    # Check for unknowns
    unknowns = [f for f in face_results if not f["is_known"]]
    if unknowns:
        now = time.time()
        last = _last_alert_time.get(source_key, 0)
        if now - last >= ALERT_COOLDOWN_SECONDS:
            _last_alert_time[source_key] = now
            snapshot_url = save_snapshot(annotated, source_key)
            confidence = unknowns[0]["confidence"]

            # Fire-and-forget: insert alert to DB and broadcast to WebSocket clients
            asyncio.create_task(_fire_alert(snapshot_url, source_key, confidence))

    return annotated


async def _fire_alert(snapshot_url: str, source_key: str, confidence: float):
    """Async: Insert alert to DB and broadcast via WebSocket."""
    loop = asyncio.get_event_loop()
    alert = await loop.run_in_executor(
        None, insert_alert, snapshot_url, source_key, confidence
    )
    await broadcast_alert({
        "type": "unknown_detected",
        "alert": alert,
    })


import threading

class CameraReader:
    def __init__(self, source):
        self.source = source
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.frame = None
        self.ret = False
        self.running = True
        self.lock = threading.Lock()
        self.simulated = False
        
        if self.cap.isOpened():
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
        else:
            # Fallback for webcam source 0 in cloud environments
            if source == 0 or str(source).isdigit():
                print("Webcam physical capture device not found. Starting simulated CCTV stream...")
                self.simulated = True
                self.thread = threading.Thread(target=self._update_simulated, daemon=True)
                self.thread.start()

    def _update(self):
        while self.running:
            ret, frame = self.cap.read()
            with self.lock:
                self.ret = ret
                if ret:
                    self.frame = frame
            if not ret:
                time.sleep(0.01)
        self.cap.release()

    def _update_simulated(self):
        from datetime import datetime
        face_images = []
        img_paths = ["images/majid.jpeg", "images/hammad.jpeg"]
        for p in img_paths:
            if os.path.exists(p):
                img = cv2.imread(p)
                if img is not None:
                    img = cv2.resize(img, (160, 160))
                    face_images.append(img)

        # If no face images are found, generate a mock human-like face structure for CV2
        if not face_images:
            dummy = np.zeros((160, 160, 3), dtype=np.uint8)
            cv2.circle(dummy, (80, 80), 60, (200, 200, 200), -1)  # Face
            cv2.circle(dummy, (55, 65), 8, (50, 50, 50), -1)     # Left Eye
            cv2.circle(dummy, (105, 65), 8, (50, 50, 50), -1)    # Right Eye
            cv2.ellipse(dummy, (80, 105), (25, 15), 0, 0, 180, (50, 50, 50), 3) # Mouth
            face_images.append(dummy)

        width, height = 640, 480
        x, y = 100, 120
        dx, dy = 5, 4
        face_idx = 0
        last_face_change = time.time()

        while self.running:
            # CCTV grid overlay background
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Subtle grid lines
            for i in range(0, width, 80):
                cv2.line(frame, (i, 0), (i, height), (22, 22, 22), 1)
            for j in range(0, height, 80):
                cv2.line(frame, (0, j), (width, j), (22, 22, 22), 1)
                
            # Header info
            cv2.putText(frame, "CCTV FEED - SIMULATED WEBCAM (DEMO)", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, f"REC: {now_str}", (15, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
            cv2.putText(frame, f"CAM: {self.source} | CLOUD HOST", (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
            
            # Bouncing movement
            x += dx
            y += dy
            if x <= 15 or x >= width - 175:
                dx = -dx
            if y <= 90 or y >= height - 175:
                dy = -dy
                
            # Place the face on the grid frame
            current_face = face_images[face_idx]
            fh, fw, _ = current_face.shape
            frame[y:y+fh, x:x+fw] = current_face
            
            # Swap face image every 8 seconds
            if time.time() - last_face_change > 8.0:
                face_idx = (face_idx + 1) % len(face_images)
                last_face_change = time.time()

            with self.lock:
                self.ret = True
                self.frame = frame
                
            time.sleep(0.04)

    def read(self):
        with self.lock:
            if self.frame is not None:
                return self.ret, self.frame.copy()
            return self.ret, None
            
    def isOpened(self):
        return self.simulated or self.cap.isOpened()

    def release(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=2.0)

async def _mjpeg_generator(source: str | int) -> AsyncGenerator[bytes, None]:
    """
    Async generator that captures frames from a camera/RTSP source
    and yields them as multipart JPEG chunks (MJPEG protocol).
    """
    cap = CameraReader(source)

    if not cap.isOpened():
        # Yield a placeholder frame instead of raising HTTPException, which breaks the connection.
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank, f"Source Offline: {source}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(blank, "Run backend locally for webcam [0]", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(blank, "or configure remote RTSP source.", (50, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        _, jpeg_buf = cv2.imencode(".jpg", blank, [cv2.IMWRITE_JPEG_QUALITY, 70])
        frame_bytes = (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg_buf.tobytes() + b"\r\n")
        try:
            while True:
                yield frame_bytes
                await asyncio.sleep(2.0)
        except asyncio.CancelledError:
            pass
        return

    source_key = str(source)
    frame_idx = 0
    
    last_results_container = {"results": []}
    is_processing = {"status": False}
    failed_reads = 0

    try:
        loop = asyncio.get_event_loop()
        while True:
            # Non-blocking read from our background reader
            ret, frame = cap.read()
            if not ret or frame is None:
                failed_reads += 1
                if failed_reads > 50:
                    # Too many failures, yield a blank black frame with text
                    blank = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(blank, "Stream Offline / Reconnecting...", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    _, jpeg_buf = cv2.imencode(".jpg", blank, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg_buf.tobytes() + b"\r\n")
                    await asyncio.sleep(2)
                    cap.release()
                    cap = CameraReader(source)
                    failed_reads = 0
                else:
                    await asyncio.sleep(0.1)
                continue
            
            failed_reads = 0
            frame_idx += 1

            # Run AI without blocking the camera read loop
            if frame_idx % 5 == 1 and not is_processing["status"]:
                is_processing["status"] = True
                
                def _background_ai(f):
                    try:
                        res = recognize_faces_in_frame(f)
                        last_results_container["results"] = res
                    except Exception as e:
                        print(f"Error in background AI: {e}")
                    finally:
                        is_processing["status"] = False

                loop.run_in_executor(None, _background_ai, frame.copy())

            # Check unknowns and alert in the main thread (async safe)
            current_results = last_results_container["results"]
            unknowns = [f for f in current_results if not f["is_known"]]
            if unknowns:
                now = time.time()
                last = _last_alert_time.get(source_key, 0)
                if now - last >= ALERT_COOLDOWN_SECONDS:
                    _last_alert_time[source_key] = now
                    # We can use the current frame to capture the snapshot
                    annotated_snap = draw_annotations(frame.copy(), current_results)
                    snapshot_url = save_snapshot(annotated_snap, source_key)
                    confidence = unknowns[0]["confidence"]
                    asyncio.create_task(_fire_alert(snapshot_url, source_key, confidence))

            # Draw the cached boxes on the current fast frame
            annotated = draw_annotations(frame.copy(), current_results)

            # Encode frame to JPEG
            _, jpeg_buf = await loop.run_in_executor(
                None, lambda: cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
            )

            # Yield MJPEG part
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpeg_buf.tobytes()
                + b"\r\n"
            )
            # Sleep slightly to cap framerate and yield to other async tasks
            await asyncio.sleep(0.01)

    finally:
        cap.release()


# ─── GET /api/stream/feed/{source} ──────────────────────────────────────────

@router.get("/feed/{source:path}")
async def live_feed(source: str):
    """
    MJPEG stream endpoint.
    Usage in React: <img src="http://localhost:8000/api/stream/feed/0" />
    
    source examples:
      - "0"           → default webcam
      - "rtsp://..."  → CCTV camera (URL-encode the RTSP URL before passing)
    """
    # Parse source: "0" → int (webcam index), else string (RTSP URL)
    video_source: str | int = int(source) if source.isdigit() else source

    return StreamingResponse(
        _mjpeg_generator(video_source),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# ─── POST /api/stream/upload ─────────────────────────────────────────────────

@router.post("/upload")
async def process_uploaded_video(
    file: UploadFile = File(..., description="MP4 video file"),
):
    """
    Upload an MP4 file for offline face recognition.
    Processes every 5th frame (skip frames for speed).
    Returns a summary of detections.
    """
    if not file.filename.lower().endswith((".mp4", ".avi", ".mkv", ".mov")):
        raise HTTPException(status_code=415, detail="Only MP4/AVI/MKV/MOV files accepted.")

    # Save uploaded file to temp location
    temp_dir = tempfile.gettempdir()
    ext = os.path.splitext(file.filename)[1] if file.filename else ".mp4"
    temp_path = os.path.join(temp_dir, f"upload_{uuid.uuid4().hex}{ext}")
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Process video
        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            raise HTTPException(status_code=422, detail="Cannot open video file.")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        frame_idx = 0
        detections = []
        source_key = f"upload:{file.filename}"

        fps_int = int(fps) if fps > 0 else 25
        frame_idx = 0
        processed_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            processed_count += 1

            # Process 1 frame per second for fast offline analysis
            loop = asyncio.get_event_loop()
            face_results = await loop.run_in_executor(
                None, recognize_faces_in_frame, frame
            )
            unknowns = [f for f in face_results if not f["is_known"]]
            if unknowns:
                annotated = draw_annotations(frame.copy(), face_results)
                snapshot_url = save_snapshot(annotated, source_key)
                alert = await loop.run_in_executor(
                    None, insert_alert, snapshot_url, source_key, unknowns[0]["confidence"]
                )
                detections.append({
                    "frame": frame_idx,
                    "timestamp_sec": round(frame_idx / fps, 2),
                    "snapshot_url": snapshot_url,
                    "unknown_count": len(unknowns),
                    "known_faces": [f["name"] for f in face_results if f["is_known"]],
                })
                
            # Skip frames using grab() which is much faster than set(POS_FRAMES)
            skip_frames = fps_int - 1
            for _ in range(skip_frames):
                if not cap.grab():
                    break
                frame_idx += 1
            frame_idx += 1

        cap.release()
        return {
            "filename": file.filename,
            "total_frames": total_frames,
            "processed_frames": processed_count,
            "unknown_detections": len(detections),
            "detections": detections,
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
