import cv2
import asyncio
import sys
import os

# Add the backend path to sys.path so we can import services
sys.path.append(r"C:\Users\Majid\Downloads\intruder detector\facewatch-backend\backend")
from services.recognition import recognize_faces_in_frame
from db.supabase_client import init_db
from services.face_cache import FaceEncodingCache
import face_recognition

async def test_frame():
    await init_db()
    await FaceEncodingCache.refresh()

    filepath = r"C:\Users\Majid\Downloads\WhatsApp Video 2026-07-26 at 11.01.13 AM.mp4"
    cap = cv2.VideoCapture(filepath)

    for _ in range(50):
        cap.read()

    ret, frame = cap.read()
    print(f"Original shape: {frame.shape}")

    # Test upscaling
    for scale in [1, 2, 3, 4]:
        small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        locs = face_recognition.face_locations(rgb_small, model="hog")
        print(f"Scale {scale}x ({small_frame.shape}): found {len(locs)} faces")
        
    locs_cnn = face_recognition.face_locations(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), model="cnn")
    print(f"CNN model found {len(locs_cnn)} faces")
    
if __name__ == "__main__":
    asyncio.run(test_frame())
