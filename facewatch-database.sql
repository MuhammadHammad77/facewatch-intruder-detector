-- ============================================================
-- FaceWatch Database Schema — Supabase / PostgreSQL
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================


-- ── Enable UUID generation ───────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ── Table 1: known_faces ─────────────────────────────────────────────────────
-- Stores registered people and their 128D face encodings.
-- Admin adds entries via the /api/faces/register endpoint — never manually.

CREATE TABLE IF NOT EXISTS known_faces (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT        NOT NULL,                   -- Full name of person
    encoding    JSONB       NOT NULL,                   -- 128D float array as JSON
    photo_url   TEXT,                                   -- Public URL from Supabase Storage
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,      -- FALSE = soft-deleted
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index: fast lookup of active faces (used on every cache refresh)
CREATE INDEX IF NOT EXISTS idx_known_faces_active
    ON known_faces (is_active)
    WHERE is_active = TRUE;

-- Index: search by name
CREATE INDEX IF NOT EXISTS idx_known_faces_name
    ON known_faces (name);

-- Auto-update updated_at on row change
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_known_faces_updated_at
    BEFORE UPDATE ON known_faces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ── Table 2: alerts ──────────────────────────────────────────────────────────
-- Every unknown-person detection event is recorded here.

CREATE TABLE IF NOT EXISTS alerts (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_url    TEXT        NOT NULL,               -- Path to saved JPEG snapshot
    camera_source   TEXT        NOT NULL,               -- "0", RTSP URL, or filename
    confidence      FLOAT       NOT NULL DEFAULT 0.0,   -- 0.0 for pure unknowns
    is_reviewed     BOOLEAN     NOT NULL DEFAULT FALSE,  -- Admin has seen this alert
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index: dashboard always loads newest alerts first
CREATE INDEX IF NOT EXISTS idx_alerts_detected_at
    ON alerts (detected_at DESC);

-- Index: filter unreviewed alerts quickly
CREATE INDEX IF NOT EXISTS idx_alerts_unreviewed
    ON alerts (is_reviewed)
    WHERE is_reviewed = FALSE;

-- Index: filter by camera source
CREATE INDEX IF NOT EXISTS idx_alerts_camera
    ON alerts (camera_source);


-- ── Row Level Security (RLS) ─────────────────────────────────────────────────
-- Since the backend uses SERVICE_ROLE key, RLS is bypassed server-side.
-- Enable anyway as a safety net to block direct anon/client access.

ALTER TABLE known_faces ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts      ENABLE ROW LEVEL SECURITY;

-- Block all direct anon access (backend uses service key → bypasses RLS)
CREATE POLICY "No public access to known_faces"
    ON known_faces FOR ALL TO anon USING (FALSE);

CREATE POLICY "No public access to alerts"
    ON alerts FOR ALL TO anon USING (FALSE);


-- ── Supabase Storage Bucket ──────────────────────────────────────────────────
-- Run this OR create manually in: Storage → New Bucket → "face-photos" (Public)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('face-photos', 'face-photos', true);


-- ── Sample Seed Data (optional — for testing) ────────────────────────────────
-- INSERT INTO known_faces (name, encoding, photo_url)
-- VALUES (
--     'Ahmed Khan',
--     '[0.123, 0.456, ...]',   -- paste a real 128D encoding here
--     'https://your-bucket.supabase.co/storage/v1/object/public/face-photos/ahmed.jpg'
-- );


-- ── Useful Views ─────────────────────────────────────────────────────────────

-- View: active face count
CREATE OR REPLACE VIEW v_face_stats AS
SELECT
    COUNT(*) FILTER (WHERE is_active = TRUE)  AS total_registered,
    COUNT(*) FILTER (WHERE is_active = FALSE) AS total_removed;

-- View: alert summary by camera
CREATE OR REPLACE VIEW v_alert_summary AS
SELECT
    camera_source,
    COUNT(*)                                          AS total_alerts,
    COUNT(*) FILTER (WHERE is_reviewed = FALSE)       AS unreviewed,
    MAX(detected_at)                                  AS last_detected
FROM alerts
GROUP BY camera_source
ORDER BY last_detected DESC;

-- View: today's unreviewed alerts
CREATE OR REPLACE VIEW v_todays_alerts AS
SELECT * FROM alerts
WHERE detected_at >= CURRENT_DATE
  AND is_reviewed = FALSE
ORDER BY detected_at DESC;
