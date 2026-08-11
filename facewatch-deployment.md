# FaceWatch — Deployment Guide

## LOCAL SETUP (Run First)

### Step 1: Install System Dependencies

**Ubuntu/Debian (Railway/Linux):**
```bash
sudo apt-get update
sudo apt-get install -y cmake build-essential libopenblas-dev liblapack-dev
sudo apt-get install -y python3-dev libx264-dev
```

**Windows:**
- Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Install [CMake](https://cmake.org/download/)
- Then: `pip install dlib face_recognition`

**macOS:**
```bash
brew install cmake
pip install dlib face_recognition
```

### Step 2: Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and fill in .env
cp .env.example .env
# Edit .env with your Supabase URL and SERVICE KEY

# Start server
uvicorn main:app --reload --port 8000
```

### Step 3: Database Setup
1. Go to [supabase.com](https://supabase.com) → your project
2. SQL Editor → New Query
3. Paste entire content of `facewatch-database.sql` → Run
4. Storage → New Bucket → name: `face-photos` → make it **Public**

### Step 4: Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local: VITE_API_URL=http://localhost:8000
npm run dev
```

Open: `http://localhost:5173`

---

## TESTING THE SYSTEM LOCALLY

```bash
# 1. Test health endpoint
curl http://localhost:8000/api/health

# 2. Register a known face (use curl or the UI)
curl -X POST http://localhost:8000/api/faces/register \
  -F "name=Ahmed Khan" \
  -F "photo=@/path/to/ahmed.jpg"

# 3. Open the React dashboard → go to /monitor
# 4. Select "0 — Webcam" → see live MJPEG feed
# 5. Walk in front of camera — should show RED box (unknown) → alert fires
```

---

## RAILWAY DEPLOYMENT (Backend)

### Important: dlib compilation on Railway

dlib and OpenCV require system dependencies like `cmake` and `libgl1`. To handle this perfectly, we use a **Dockerfile**.

1. Push your entire repository to GitHub.
2. Go to [Railway.app](https://railway.app/) → New Project → Deploy from GitHub repo.
3. Once imported, go to **Settings** → **Build**:
   - Change **Root Directory** to `/facewatch-backend/backend`
   - Railway will automatically detect the `Dockerfile` and build the image.

**Environment Variables on Railway:**
```
SUPABASE_URL         = https://xxxx.supabase.co
SUPABASE_SERVICE_KEY = eyJhbGciOi...
FRONTEND_URL         = https://your-frontend-app.vercel.app
```

**⚠️ Known Issue:** Railway free tier sleeps after inactivity → the MJPEG stream
will stall for ~5 seconds on first connect (cold start). 
**Fix:** Use Railway's "Always On" option OR ping `/api/health` every 5 minutes with UptimeRobot.

**⚠️ Snapshot Storage:** Railway has ephemeral filesystem — snapshots saved to disk
are deleted on redeploy. 
**Fix (Production):** Upload snapshots to Supabase Storage instead of local disk.
Update `save_snapshot()` in `services/recognition.py` to upload bytes and return a
public Supabase Storage URL.

---

## VERCEL DEPLOYMENT (Frontend)

1. Push frontend folder to GitHub
2. Go to [vercel.com](https://vercel.com) → New Project → Import repo
3. Framework: **Vite**
4. Build command: `npm run build`
5. Output directory: `dist`
6. **Environment Variables:**
   ```
   VITE_API_URL = https://your-railway-app.up.railway.app
   ```
7. Deploy!

---

## RTSP CAMERA SETUP (CCTV)

For real CCTV cameras:
```python
# Typical RTSP URL formats:
"rtsp://admin:password@192.168.1.100:554/stream1"      # Hikvision
"rtsp://admin:password@192.168.1.100:554/cam/realmonitor?channel=1"  # Dahua
"rtsp://192.168.1.100/live/ch00_0"                     # Generic

# Test RTSP stream locally:
ffplay rtsp://admin:password@192.168.1.100:554/stream1
```

In the React dashboard, type the full RTSP URL in the custom source input field.

---

## COMMON ERRORS & FIXES

| Error | Cause | Fix |
|-------|-------|-----|
| `dlib not found` | cmake not installed | `sudo apt install cmake build-essential` |
| `No face detected` | Photo angle/lighting | Use a clear, front-facing, well-lit photo |
| `RTSP stream timeout` | Camera URL wrong / firewall | Test URL with ffplay first |
| `CORS error` | Frontend URL not in env | Set `FRONTEND_URL` in backend .env |
| `ModuleNotFoundError: face_recognition` | Not installed | `pip install face_recognition` |
| `Supabase 403` | Using anon key instead of service key | Use SERVICE_ROLE key |
| `Stream lag/buffering` | Processing at full resolution | Already handled — we resize to 1/4 |
| `Too many alerts` | Cooldown too low | Increase `ALERT_COOLDOWN_SECONDS` in `recognition.py` |

---

## PRODUCTION CHECKLIST

- [ ] SUPABASE_SERVICE_KEY set in Railway env vars
- [ ] FRONTEND_URL set to Vercel URL in Railway env vars  
- [ ] VITE_API_URL set to Railway URL in Vercel env vars
- [ ] `face-photos` storage bucket created and set to Public
- [ ] SQL schema applied to Supabase (all tables exist)
- [ ] At least one face registered via `/faces` admin panel
- [ ] WebSocket `wss://` (not `ws://`) used in production (Vercel uses HTTPS)
- [ ] Snapshot upload moved to Supabase Storage for persistence

---

## ARCHITECTURE SUMMARY

```
React Dashboard (Vercel)
    │
    ├── MJPEG stream → GET /api/stream/feed/0 ──────────────────┐
    ├── REST API calls → GET/POST/DELETE /api/faces              │
    ├── REST API calls → GET /api/alerts                         │
    └── WebSocket → ws://backend/api/alerts/ws                  │
                                                                  │
FastAPI Backend (Railway)                                         │
    │                                                             │
    ├── FaceEncodingCache (RAM) ← Supabase known_faces table     │
    ├── OpenCV VideoCapture(0) ← Webcam/RTSP ───────────────────┘
    ├── face_recognition → 128D encoding comparison
    ├── Unknown detected → save snapshot → insert alert → WebSocket broadcast
    └── Supabase Client ↔ Supabase PostgreSQL + Storage
```
