import sqlite3
import json
import uuid
from datetime import datetime
import os

DB_PATH = "local_database.db"
STORAGE_DIR = "storage"

os.makedirs(STORAGE_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

async def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS known_faces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            encoding TEXT NOT NULL,
            photo_url TEXT,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            snapshot_url TEXT NOT NULL,
            camera_source TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 0.0,
            is_reviewed BOOLEAN NOT NULL DEFAULT 0,
            detected_at TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Local SQLite DB initialized.")

def fetch_all_faces() -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT id, name, encoding, photo_url, created_at FROM known_faces WHERE is_active = 1").fetchall()
    conn.close()
    faces = []
    for r in rows:
        face = dict(r)
        face['encoding'] = json.loads(face['encoding'])
        faces.append(face)
    return faces

def insert_face(name: str, encoding: list[float], photo_url: str) -> dict:
    conn = get_db()
    face_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO known_faces (id, name, encoding, photo_url, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (face_id, name, json.dumps(encoding), photo_url, 1, now, now)
    )
    conn.commit()
    conn.close()
    return {"id": face_id, "name": name, "photo_url": photo_url}

def delete_face(face_id: str) -> bool:
    conn = get_db()
    conn.execute("UPDATE known_faces SET is_active = 0 WHERE id = ?", (face_id,))
    conn.commit()
    conn.close()
    return True

def insert_alert(snapshot_url: str, camera_source: str, confidence: float) -> dict:
    conn = get_db()
    alert_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO alerts (id, snapshot_url, camera_source, confidence, is_reviewed, detected_at) VALUES (?, ?, ?, ?, ?, ?)",
        (alert_id, snapshot_url, camera_source, confidence, 0, now)
    )
    conn.commit()
    conn.close()
    return {"id": alert_id, "snapshot_url": snapshot_url, "camera_source": camera_source, "confidence": confidence, "detected_at": now}

def fetch_alerts(limit: int = 50, offset: int = 0) -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM alerts ORDER BY detected_at DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_alert_reviewed(alert_id: str) -> bool:
    conn = get_db()
    conn.execute("UPDATE alerts SET is_reviewed = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
    return True

def delete_all_alerts() -> int:
    """Delete all alerts and return the count of deleted rows."""
    conn = get_db()
    cursor = conn.execute("SELECT COUNT(*) FROM alerts")
    count = cursor.fetchone()[0]
    conn.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()
    return count

class StorageStorage:
    def upload(self, path, file, file_options):
        with open(os.path.join(STORAGE_DIR, path), 'wb') as f:
            f.write(file)
    def get_public_url(self, path):
        return f"/storage/{path}"
        
class StorageMock:
    def from_(self, bucket):
        return StorageStorage()

class SupabaseMock:
    storage = StorageMock()

def get_supabase():
    return SupabaseMock()
