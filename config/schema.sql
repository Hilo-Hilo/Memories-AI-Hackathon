-- Focus Guardian Database Schema v1.3
-- SQLite database for storing sessions, snapshots, and distraction events

-- ============================================================================
-- Sessions Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,  -- ISO 8601 UTC timestamp
    ended_at TEXT,              -- ISO 8601 UTC timestamp
    task_name TEXT NOT NULL,
    quality_profile TEXT NOT NULL,  -- Low | Std | High
    screen_enabled INTEGER NOT NULL,  -- Boolean: 0 or 1
    status TEXT NOT NULL,       -- active | paused | completed | failed
    
    -- Paths (relative to data directory)
    cam_mp4_path TEXT NOT NULL,
    screen_mp4_path TEXT,
    snapshots_dir TEXT NOT NULL,
    vision_dir TEXT NOT NULL,
    logs_dir TEXT NOT NULL,
    
    -- Statistics
    total_snapshots INTEGER DEFAULT 0,
    uploaded_snapshots INTEGER DEFAULT 0,
    failed_snapshots INTEGER DEFAULT 0,
    total_events INTEGER DEFAULT 0,
    
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at);

-- ============================================================================
-- Snapshots Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,  -- ISO 8601 UTC timestamp
    kind TEXT NOT NULL,       -- cam | screen
    
    -- File references
    jpeg_path TEXT NOT NULL,
    jpeg_size_bytes INTEGER NOT NULL,
    
    -- Vision API results (nullable until processed)
    vision_json_path TEXT,
    vision_labels TEXT,       -- JSON string: {"label": confidence, ...}
    processed_at TEXT,        -- ISO 8601 UTC timestamp
    upload_status TEXT NOT NULL DEFAULT 'pending',  -- pending | uploading | success | failed
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_snapshots_session ON snapshots(session_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON snapshots(timestamp);
CREATE INDEX IF NOT EXISTS idx_snapshots_upload_status ON snapshots(upload_status);
CREATE INDEX IF NOT EXISTS idx_snapshots_kind ON snapshots(kind);

-- ============================================================================
-- Distraction Events Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS distraction_events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    started_at TEXT NOT NULL,  -- ISO 8601 UTC timestamp
    ended_at TEXT NOT NULL,    -- ISO 8601 UTC timestamp
    duration_seconds REAL NOT NULL,
    
    -- Classification
    event_type TEXT NOT NULL,  -- LookAway | Phone | Video | Social | Chat | Absent | MicroSleep | Unknown
    evidence TEXT NOT NULL,
    confidence REAL NOT NULL,
    
    -- Vision votes (snapshot hysteresis results) - SCHEMA v1.3
    vision_votes TEXT NOT NULL,  -- JSON string: {"HeadAway": 2, "EyesOffScreen": 1, ...}
    snapshot_refs TEXT NOT NULL,  -- JSON string: ["snapshot_id_1", "snapshot_id_2", ...]
    
    -- User interaction
    acknowledged INTEGER DEFAULT 0,  -- Boolean: 0 or 1
    acknowledged_at TEXT,
    
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_events_session ON distraction_events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_started_at ON distraction_events(started_at);
CREATE INDEX IF NOT EXISTS idx_events_type ON distraction_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_acknowledged ON distraction_events(acknowledged);

-- ============================================================================
-- Session Reports Table (stores generated JSON reports)
-- ============================================================================
CREATE TABLE IF NOT EXISTS session_reports (
    report_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    report_json TEXT NOT NULL,  -- Full SessionReport JSON (schema v1.3)
    generated_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    -- Post-processing flags
    hume_processed INTEGER DEFAULT 0,  -- Boolean: 0 or 1
    memories_processed INTEGER DEFAULT 0,  -- Boolean: 0 or 1
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reports_session ON session_reports(session_id);

-- ============================================================================
-- Settings Table (user preferences)
-- ============================================================================
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================================
-- Triggers for updated_at timestamps
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_sessions_timestamp 
    AFTER UPDATE ON sessions
BEGIN
    UPDATE sessions SET updated_at = datetime('now') WHERE session_id = NEW.session_id;
END;

CREATE TRIGGER IF NOT EXISTS update_settings_timestamp 
    AFTER UPDATE ON settings
BEGIN
    UPDATE settings SET updated_at = datetime('now') WHERE key = NEW.key;
END;

