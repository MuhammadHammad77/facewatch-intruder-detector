# FaceWatch Backend

## Quick Start
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Fill in Supabase credentials
uvicorn main:app --reload --port 8000
```

## API Docs
Open: http://localhost:8000/docs (Swagger UI auto-generated)

## Project Structure
```
main.py              ← FastAPI app + startup
requirements.txt     ← All dependencies (pinned)
.env.example         ← Copy to .env and fill in
routers/
  faces.py           ← POST /register, GET /, DELETE /{id}
  video_stream.py    ← GET /feed/{source}, POST /upload
  alerts.py          ← WS /ws, GET /, PUT /{id}/review
models/
  schemas.py         ← Pydantic request/response models
services/
  recognition.py     ← 128D encoding, frame analysis, annotation
  face_cache.py      ← In-memory encoding cache
  alert_broadcaster.py ← WebSocket connection manager
db/
  supabase_client.py ← All DB queries (Supabase wrapper)
snapshots/           ← Saved JPEG snapshots of unknowns
```
