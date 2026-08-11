"""
Face Recognition Service
─────────────────────────
Handles:
  1. Extracting 128D face encodings from an uploaded image (registration)
  2. Comparing a live-frame encoding against the in-memory cache
  3. Drawing bounding boxes + labels on frames
"""

import os
import time
import uuid
from io import BytesIO
from typing import Optional

import cv2
import face_recognition   # dlib-based; 128D encodings
import numpy as np
from PIL import Image

from services.face_cache import FaceEncodingCache

# ─── Constants ────────────────────────────────────────────────────────────────

TOLERANCE = 0.50          # Lower = stricter match (0.6 is face_recognition default)
SNAPSHOT_DIR = "snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# ─── 1. Registration: Image → 128D Encoding ──────────────────────────────────

def encode_image_bytes(image_bytes: bytes) -> list[float]:
    """
    Given raw image bytes (from upload), return a 128D face encoding.
    Raises ValueError if no face (or >1 face) is found.
    """
    img_array = np.frombuffer(image_bytes, dtype=np.uint8)
    img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img_bgr is None:
        raise ValueError("Cannot decode image. Unsupported format.")

    # face_recognition expects RGB
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Detect face locations first
    face_locations = face_recognition.face_locations(img_rgb, model="hog")

    if len(face_locations) == 0:
        raise ValueError("No face detected in the uploaded image.")
    if len(face_locations) > 1:
        raise ValueError(
            f"Multiple faces detected ({len(face_locations)}). "
            "Please upload a photo with exactly one face."
        )

    # Compute 128D encoding
    encodings = face_recognition.face_encodings(img_rgb, face_locations)
    return encodings[0].tolist()  # Convert numpy → plain Python list for JSON/DB


# ─── 2. Live Frame Recognition ────────────────────────────────────────────────

def recognize_faces_in_frame(frame_bgr: np.ndarray) -> list[dict]:
    """
    Given a BGR frame from OpenCV, detect all faces and classify each as
    Known (matched in cache) or Unknown.

    Returns a list of dicts:
        [
            {
                "name": "Ahmed",          # or "Unknown"
                "is_known": True,
                "confidence": 0.87,       # 1 - distance (higher = more confident)
                "box": (top, right, bottom, left),  # face bounding box pixels
            },
            ...
        ]
    """
    # Scale down frame for faster detection (target width ~500px for balance of speed/accuracy)
    h, w = frame_bgr.shape[:2]
    scale = 500.0 / w if w > 500 else 1.0
    
    small_frame = cv2.resize(frame_bgr, (0, 0), fx=scale, fy=scale)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Detect faces
    face_locations = face_recognition.face_locations(rgb_small, model="hog")
    if not face_locations:
        return []

    # Compute encodings for all faces found
    live_encodings = face_recognition.face_encodings(rgb_small, face_locations)

    results = []
    for live_enc, location in zip(live_encodings, face_locations):
        # Scale bounding box back to original frame size
        top, right, bottom, left = [int(coord / scale) for coord in location]

        name = "Unknown"
        confidence = 0.0
        is_known = False

        if not FaceEncodingCache.is_empty():
            # Compute L2 distances to all cached encodings (vectorized, fast)
            distances = face_recognition.face_distance(FaceEncodingCache.encodings, live_enc)
            best_idx = int(np.argmin(distances))
            best_dist = float(distances[best_idx])

            if best_dist <= TOLERANCE:
                name = FaceEncodingCache.names[best_idx]
                confidence = round(1.0 - best_dist, 3)
                is_known = True

        results.append({
            "name": name,
            "is_known": is_known,
            "confidence": confidence,
            "box": (top, right, bottom, left),
        })

    return results


# ─── 3. Draw Bounding Boxes on Frame ─────────────────────────────────────────

def draw_annotations(frame_bgr: np.ndarray, face_results: list[dict]) -> np.ndarray:
    """
    Draw green boxes for Known, red boxes for Unknown.
    Modifies frame in-place and returns it.
    """
    h, w = frame_bgr.shape[:2]
    # Dynamic scaling for text and boxes based on frame size
    font_scale = max(0.5, w / 1000.0)
    thickness = max(1, int(w / 800.0))
    box_thickness = max(2, int(w / 600.0))

    for face in face_results:
        top, right, bottom, left = face["box"]
        color = (0, 200, 0) if face["is_known"] else (0, 0, 220)  # BGR: Green / Red
        label = face["name"]
        if face["is_known"]:
            label += f" ({int(face['confidence'] * 100)}%)"

        # Draw bounding box
        cv2.rectangle(frame_bgr, (left, top), (right, bottom), color, box_thickness)

        # Draw label background (above the box for better visibility)
        label_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, font_scale, thickness)
        
        # Ensure we don't draw outside the top of the frame
        start_y = max(0, top - label_size[1] - 10)
        
        cv2.rectangle(
            frame_bgr,
            (left, start_y),
            (left + label_size[0] + 10, top),
            color, cv2.FILLED
        )

        # Draw label text
        cv2.putText(
            frame_bgr, label,
            (left + 5, top - 5),
            cv2.FONT_HERSHEY_DUPLEX, font_scale,
            (255, 255, 255), thickness
        )

    return frame_bgr


# ─── 4. Save Snapshot ─────────────────────────────────────────────────────────

def save_snapshot(frame_bgr: np.ndarray, camera_source: str) -> str:
    """
    Save the annotated frame as a JPEG file.
    Returns the relative URL path to serve via /snapshots/ static route.
    """
    timestamp = int(time.time())
    safe_source = camera_source.replace("/", "_").replace(":", "-")
    filename = f"unknown_{safe_source}_{timestamp}_{uuid.uuid4().hex[:6]}.jpg"
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    cv2.imwrite(filepath, frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return f"/snapshots/{filename}"
