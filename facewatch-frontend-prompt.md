# FaceWatch — React Dashboard (Master Build Prompt for Antigravity/Gemini)

## PROJECT OVERVIEW
Build a **React + Vite + Tailwind CSS** admin dashboard for FaceWatch, a real-time CCTV/Webcam unknown-person detection system. The dashboard has two main areas: (1) an Admin Panel to register and manage known people, (2) a Live Monitor to watch camera feeds and receive instant alerts when unknown faces appear.

---

## TECH STACK (strict — no deviations)
- **React 18** with Vite
- **Tailwind CSS** for all styling (no CSS modules, no styled-components)
- **React Query (TanStack Query v5)** for all API calls
- **React Router v6** for routing
- **Zustand** for global state (alert counter, WebSocket status)
- **Lucide React** for icons
- **Sonner** (`npm install sonner`) for toast notifications

**No Material UI, no Ant Design, no Chakra.**

---

## DESIGN SYSTEM

### Color Palette
```
--bg-primary:     #0a0e1a   (deep navy — main background)
--bg-card:        #111827   (card background)
--bg-elevated:    #1f2937   (input fields, table rows)
--border:         #374151   (card borders, dividers)
--accent-green:   #10b981   (known face indicators, success states)
--accent-red:     #ef4444   (unknown face alerts, danger)
--accent-blue:    #3b82f6   (primary action buttons)
--text-primary:   #f9fafb   (headings)
--text-secondary: #9ca3af   (labels, metadata)
```

### Typography
- Font: `Inter` (import from Google Fonts)
- Heading: `font-bold text-white`
- Label: `text-sm text-gray-400`
- Monospace (for IDs, confidence): `font-mono text-xs`

### Border Radius: `rounded-xl` for cards, `rounded-lg` for inputs/buttons
### Shadows: `shadow-lg shadow-black/40`

---

## ROUTES / PAGES

### `/` — Dashboard Home (redirect to `/monitor`)

### `/monitor` — Live Monitor (default page)

**Layout**: Split screen on desktop (left 60% = camera feed, right 40% = alerts panel)

**Left Panel — Camera Feed:**
- Big `<img>` tag showing MJPEG stream: `<img src={VITE_API_URL}/api/stream/feed/{selectedSource} />`
- Source selector dropdown: options `["0 — Webcam", "rtsp://... — Camera 1"]` plus a text input to add custom RTSP URL
- A pulsing green dot + "LIVE" badge when stream is active
- Overlay text showing current source label
- If stream fails to load: red banner "Stream unavailable. Check camera connection."

**Right Panel — Live Alerts:**
- Title: "⚠️ Alerts" with a red badge showing unreviewed count (from Zustand store)
- WebSocket connection to `ws://VITE_API_URL/api/alerts/ws`
  - On connect: show green dot "Connected"
  - On disconnect: show red dot "Reconnecting..." with auto-reconnect every 3s
  - On `unknown_detected` message: 
    - Add alert card to top of list (max 20 shown)
    - Show Sonner toast: `🚨 Unknown Person Detected on {camera_source}`
    - Play a beep sound (use Web Audio API, create a short 440Hz beep)
    - Increment unreviewed counter in Zustand
- Alert Card:
  ```
  [SNAPSHOT IMAGE]  Unknown Person
                    Camera: {camera_source}
                    Time: {relative time, e.g. "2 min ago"}
                    [Mark Reviewed] button → PUT /api/alerts/{id}/review
  ```
  Snapshot is clickable → opens full-size image in a modal
- Below live alerts: "Load History" button → GET /api/alerts?limit=50

### `/faces` — Face Registry (Admin Panel)

**Top Section — Register New Face:**
- Card with title "Register New Person"
- Form fields:
  - Text input: Full Name (required)
  - File drop zone: "Drop photo here or click to browse" (accepts JPG, PNG, WEBP)
    - Show image preview after selection
    - Show red warning if no face detected (from API error 422)
  - Submit button: "Register Face"
  - Loading state: spinner + "Encoding face..." text
  - Success: green checkmark + "Ahmed Khan registered ✅"
  - Error: red banner with API error message

- POST to `/api/faces/register` as multipart/form-data:
  ```
  FormData: { name: "Ahmed Khan", photo: File }
  ```
  On success: invalidate faces query, show success toast, reset form

**Bottom Section — Registered Faces:**
- Title: "Known Persons" + total count badge
- Grid: 3 columns on desktop, 2 on tablet, 1 on mobile
- Each face card:
  ```
  [PHOTO - 80x80px rounded-full]
  Name: Ahmed Khan
  ID: abc123...  (truncated, monospace)
  Registered: Jan 15, 2024
  [Remove] button (red, with confirmation dialog)
  ```
- Remove → DELETE /api/faces/{id} → confirm modal: "Remove Ahmed Khan? This cannot be undone." → on confirm: refetch list + toast "Removed."
- Empty state: "No faces registered yet. Add your first person above."
- Loading state: 6 skeleton cards (pulsing gray rectangles)

### `/upload` — Video File Analysis

- Title: "Analyze Recorded Video"
- Large drop zone: accepts MP4, AVI, MKV, MOV (max 100MB shown as UI hint)
- After file selected: show filename + size
- "Analyze Video" button → POST /api/stream/upload (multipart)
- Progress: animated progress bar + "Processing frame {n}..." text (poll or fake progress)
- Results card (after completion):
  - Total frames analyzed
  - Unknown detections found: N
  - List of detection events:
    ```
    [SNAPSHOT] Frame 250 (10.0s) — 1 unknown face detected
               Known: [Ahmed, Sara]
    ```
  - Each snapshot clickable → modal
- Error state: "No faces found in this video" or API error banner

### `/settings` — System Settings (simple page)

- **Cache Control:** "Known faces in memory: {count}" + "Refresh Cache" button → POST /api/faces/refresh-cache
- **Alert Cooldown:** informational text "Alerts fire max once every 10 seconds per camera to prevent spam"
- **API Status:** call GET /api/health, show green/red status + loaded face count
- **Theme:** (cosmetic — dark mode only, no toggle needed)

---

## GLOBAL COMPONENTS

### Sidebar Navigation
- Fixed left sidebar (64px wide, icons only; expands to 220px on hover)
- Items:
  - 📹 Monitor (`/monitor`)
  - 👤 Faces (`/faces`)
  - 📁 Upload (`/upload`)
  - ⚙️ Settings (`/settings`)
- Active item: blue left border + accent color
- Bottom: app version "FaceWatch v1.0"

### Top Header
- Logo: camera icon + "FaceWatch" text
- Right side: 
  - WebSocket status dot (green = connected, red = disconnected)
  - Alert bell icon with unread count badge (from Zustand)

### Alert Modal (global)
- Triggered by clicking any snapshot anywhere
- Full-screen overlay: dark background + centered image
- Below image: camera source, detection time, confidence
- Close on Escape key or clicking outside

---

## API ENDPOINTS

Base URL from env: `import.meta.env.VITE_API_URL` (default: `http://localhost:8000`)

| Method | URL | Purpose |
|--------|-----|---------|
| GET | `/api/faces` | List registered faces |
| POST | `/api/faces/register` | Register new face (multipart) |
| DELETE | `/api/faces/{id}` | Remove face |
| POST | `/api/faces/refresh-cache` | Reload encodings |
| GET | `/api/stream/feed/{source}` | MJPEG video stream |
| POST | `/api/stream/upload` | Analyze MP4 file |
| GET | `/api/alerts` | Alert history |
| PUT | `/api/alerts/{id}/review` | Mark reviewed |
| GET | `/api/health` | System health |
| WS | `/api/alerts/ws` | Real-time alert push |

---

## STATE MANAGEMENT (Zustand)

```typescript
interface FaceWatchStore {
  unreviewedCount: number
  wsStatus: 'connected' | 'disconnected' | 'reconnecting'
  liveAlerts: Alert[]           // max 20 items
  selectedCameraSource: string  // "0" by default
  
  incrementUnreviewed: () => void
  decrementUnreviewed: () => void
  setWsStatus: (status: string) => void
  addLiveAlert: (alert: Alert) => void
  setSelectedSource: (source: string) => void
}
```

---

## WEBSOCKET HOOK

Create `hooks/useAlertWebSocket.ts`:
```typescript
// Connect to ws://{API_URL}/api/alerts/ws
// Send "ping" every 30s to keep connection alive
// On message: parse JSON, if type === "unknown_detected" → addLiveAlert, incrementUnreviewed, toast, beep
// On close: wait 3s, reconnect (max 5 attempts then show "Connection lost" banner)
// On open: setWsStatus('connected')
```

---

## ENV FILE (.env.local)
```
VITE_API_URL=http://localhost:8000
```

---

## RESPONSIVE BREAKPOINTS
- Mobile (<768px): Stack everything vertically. Sidebar becomes bottom nav bar (4 icons).
- Tablet (768-1024px): Sidebar collapses to icons. Monitor: feed on top, alerts below.
- Desktop (>1024px): Full split-screen layout with expanded sidebar.

---

## LOADING & ERROR STATES (required for every data fetch)
- **Loading**: Show pulsing skeleton cards/bars — never show blank screens
- **Error**: Red banner with error message + "Retry" button
- **Empty**: Helpful icon + message + CTA to add data

---

## ANIMATIONS
- Alert cards: slide in from the right with fade (`transition-all duration-300`)
- New alert: brief red glow on entry (`animate-pulse` for 2 seconds)
- Face cards: hover → scale up slightly (`hover:scale-105 transition-transform`)
- Sidebar: smooth width transition on hover (`transition-width duration-200`)
- Success states: checkmark with scale-in animation

---

## PACKAGE.JSON SCRIPTS
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }
}
```

## VITE CONFIG
Set proxy to avoid CORS in dev:
```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/snapshots': 'http://localhost:8000'
  }
}
```

---

## IMPORTANT NOTES
1. The MJPEG stream is just `<img src="...">` — no special streaming logic needed in React
2. WebSocket auto-reconnect is critical — implement it properly
3. All dark theme — no light mode toggle needed
4. The beep sound on alert should be subtle (short, 200ms, low volume 0.3)
5. Snapshot images from alerts: prefix with `VITE_API_URL` if URL starts with `/snapshots/`
