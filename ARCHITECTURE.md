# Focus Guardian - Architecture & File Structure

## Project Directory Structure

```
focus-guardian/
├── src/
│   ├── focus_guardian/
│   │   ├── __init__.py
│   │   ├── main.py                      # Application entry point
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py                # Configuration management
│   │   │   ├── database.py              # SQLite database interface
│   │   │   ├── models.py                # Data models (Session, Event, etc.)
│   │   │   └── state_machine.py         # Snapshot hysteresis fusion (K=3)
│   │   │
│   │   ├── capture/
│   │   │   ├── __init__.py
│   │   │   ├── snapshot_scheduler.py    # Wall-clock snapshot capture scheduler
│   │   │   ├── snapshot_uploader.py     # Upload worker pool for OpenAI Vision
│   │   │   ├── screen_capture.py        # Screen snapshot capture (mss)
│   │   │   └── recorder.py              # MP4 recording (ffmpeg-python)
│   │   │
│   │   ├── analysis/
│   │   │   ├── __init__.py
│   │   │   ├── screen_classifier.py     # Local CNN fallback (optional)
│   │   │   ├── distraction_detector.py  # Snapshot-based distraction detection
│   │   │   └── fusion_engine.py         # Snapshot hysteresis fusion
│   │   │
│   │   ├── session/
│   │   │   ├── __init__.py
│   │   │   ├── session_manager.py       # Orchestrates recording & snapshot pipeline
│   │   │   ├── task_manager.py          # Goal/task tracking
│   │   │   └── report_generator.py      # Generate session_report.json (v1.3)
│   │   │
│   │   ├── integrations/
│   │   │   ├── __init__.py
│   │   │   ├── openai_vision_client.py  # OpenAI Vision API client (realtime)
│   │   │   ├── hume_client.py           # Hume AI Expression API (post-proc)
│   │   │   ├── memories_client.py       # Memories.ai API (post-proc)
│   │   │   ├── calendar_sync.py         # Google Calendar/Outlook integration
│   │   │   └── backend_client.py        # Optional cloud backend API
│   │   │
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── main_window.py           # Main application window
│   │   │   ├── dashboard.py             # Dashboard view
│   │   │   ├── settings.py              # Settings panel (developer mode toggle)
│   │   │   ├── reports_view.py          # Session reports viewer
│   │   │   ├── onboarding.py            # First-time setup wizard
│   │   │   └── components/              # Reusable UI components
│   │   │       ├── __init__.py
│   │   │       ├── alert_overlay.py     # Distraction alert overlay
│   │   │       └── task_widget.py       # Task/goal display widget
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── threading_utils.py       # Thread management helpers
│   │       ├── queue_manager.py         # Inter-thread communication
│   │       ├── encryption.py            # API key encryption
│   │       ├── performance_monitor.py   # CPU/memory monitoring
│   │       └── logger.py                # Logging configuration
│   │
├── assets/
│   ├── models/
│   │   └── screen_classifier.onnx       # Local CNN fallback (optional)
│   ├── icons/
│   │   ├── app_icon.png
│   │   └── tray_icons/
│   └── sounds/
│       └── alert.wav
│
├── config/
│   ├── default_config.json              # Default configuration
│   └── schema.sql                       # SQLite database schema
│
├── data/                                # User data directory (gitignored)
│   ├── focus_guardian.db                # SQLite database
│   ├── sessions/                        # Per-session folders
│   │   └── <session_id>/
│   │       ├── cam.mp4                  # Webcam recording
│   │       ├── screen.mp4               # Screen recording
│   │       ├── snapshots/               # JPEG snapshots
│   │       │   ├── cam_*.jpg
│   │       │   └── screen_*.jpg
│   │       ├── vision/                  # OpenAI Vision API responses
│   │       │   ├── cam_*.json
│   │       │   └── screen_*.json
│   │       └── logs/                    # Session-specific logs
│   │           ├── runtime.log
│   │           └── uploads.log
│   ├── reports/                         # Generated JSON reports
│   │   └── <session_id>_report.json
│   └── config.encrypted.json            # User config (API keys)
│
├── tests/
│   ├── __init__.py
│   ├── test_distraction_detector.py
│   ├── test_session_manager.py
│   ├── test_database.py
│   └── fixtures/
│
├── scripts/
│   ├── build_installer.py               # PyInstaller build script
│   ├── generate_models.py               # Download/prepare ML models
│   └── cleanup_data.py                  # Data retention cleanup
│
├── pyproject.toml                       # Project dependencies
├── README.md
├── CLAUDE.md                            # Claude Code instructions
├── prd.md                               # Product requirements
├── ARCHITECTURE.md                      # This file
└── .env.template                        # API key template

```

## Module Interactions & Data Flow

### 1. Application Startup Flow

```
main.py
  ├─> config.py (load configuration including SNAPSHOT_INTERVAL_SEC)
  ├─> database.py (initialize SQLite)
  ├─> main_window.py (launch GUI)
  │     └─> onboarding.py (if first run)
  └─> session_manager.py (initialize, standby mode)
```

### 2. Session Recording & Snapshot Flow (IMAGE-ONLY PIPELINE)

```
UI Thread (main_window.py)
  └─> session_manager.py.start_session()
        │
        ├─> Create session folder: sessions/<session_id>/
        │
        ├─> recorder.py (start recording both streams)
        │     ├─> cam.mp4 (background thread, continuous H.264)
        │     └─> screen.mp4 (background thread, continuous H.264)
        │
        ├─> snapshot_scheduler.py (wall-clock scheduler)
        │     ├─> Every SNAPSHOT_INTERVAL_SEC (default 60s)
        │     ├─> Capture cam snapshot → sessions/<session_id>/snapshots/cam_YYYYMMDD_HHMMSS.jpg
        │     ├─> Capture screen snapshot → sessions/<session_id>/snapshots/screen_YYYYMMDD_HHMMSS.jpg
        │     └─> Queue snapshot pairs → snapshot_uploader.py
        │
        └─> snapshot_uploader.py (worker pool with MAX_PARALLEL_UPLOADS)
              ├─> Upload cam snapshot → OpenAI Vision API
              ├─> Upload screen snapshot → OpenAI Vision API
              ├─> Save responses → sessions/<session_id>/vision/*.json
              ├─> Insert into SQLite (snapshot_refs, vision_votes)
              └─> Send to fusion_engine.py via queue

AUDIO CAPTURE: DISABLED (no audio_capture.py, no audio analysis)
```

### 3. Real-time Snapshot Analysis Flow

```
Snapshot Uploader Threads (worker pool)
  │
  ├─> openai_vision_client.py
  │     └─> POST snapshot to OpenAI Vision API
  │           └─> Response: {HeadAway, EyesOffScreen, Absent, MicroSleep, PhoneLikely,
  │                         VideoOnScreen, SocialFeed, Code/Docs, ChatWindow, Games, Unknown}
  │                 └─> Save to vision/*.json
  │                       └─> Queue → fusion_engine.py
  │
  └─> screen_classifier.py (optional local CNN fallback)
        └─> outputs: {app_class, confidence}
              └─> Queue → fusion_engine.py

fusion_engine.py (hysteresis over K=3 snapshots)
  └─> state_machine.py (≥1 minute span debounce)
        └─> distraction_detector.py (emit snapshot-confirmed events)
              │
              ├─> database.py (log events to SQLite with vision_votes)
              │
              └─> UI Thread Queue → alert_overlay.py (show notification)
```

### 4. Post-Session Processing Flow

```
session_manager.py.end_session()
  │
  ├─> recorder.py.stop() (finalize cam.mp4 + screen.mp4)
  │
  ├─> snapshot_uploader.py.wait() (ensure all uploads complete)
  │
  ├─> report_generator.py.generate()
  │     ├─> database.py (query session events with vision_votes)
  │     ├─> compute KPIs (focus_ratio, alerts, top_triggers)
  │     └─> write session_report.json (schema v1.3)
  │
  └─> Optional cloud upload (if enabled):
        │
        ├─> memories_client.py.upload_session()
        │     ├─> Upload cam.mp4, screen.mp4, snapshots/*.jpg
        │     └─> POST to Memories.ai Chat API with schema prompt
        │           └─> Poll job → fetch structured analysis
        │                 └─> Merge with realtime vision results
        │
        ├─> hume_client.py.analyze_video()
        │     └─> POST cam.mp4 to Hume Expression API
        │           └─> Poll job → fetch 1Hz emotion timeline
        │                 └─> Align to segments
        │
        └─> report_generator.py.merge_cloud_data()
              ├─> Timestamp join {Memories segments, Hume expressions, OpenAI Vision}
              ├─> Update session_report.json with merged data
              └─> database.py (store cloud results)
```

### 5. Threading Architecture

```
Main Thread (UI)
  ├─> CustomTkinter/PyQt6 event loop
  └─> Receives events via queue_manager.py

Snapshot Scheduler Thread
  ├─> Wall-clock timer (SNAPSHOT_INTERVAL_SEC)
  ├─> Captures cam + screen snapshots
  └─> Queues snapshot pairs for upload

Snapshot Uploader Worker Pool (MAX_PARALLEL_UPLOADS threads)
  ├─> Pulls snapshot pairs from upload queue
  ├─> Uploads to OpenAI Vision API with retry/backoff
  ├─> Saves vision/*.json responses
  └─> Sends results to fusion queue

Fusion Thread
  ├─> Pulls snapshot vision results from queue
  ├─> Applies hysteresis over K=3 snapshots
  ├─> Runs state machine with ≥1 minute debounce
  └─> Sends distraction events to UI queue & database

Recording Threads (2x)
  ├─> Webcam recorder (ffmpeg-python, continuous)
  └─> Screen recorder (ffmpeg-python, continuous)

Database Writer Thread
  └─> Processes all writes via db_queue

Post-Processing Upload Thread (optional)
  └─> Background uploads to Hume/Memories.ai after session ends
```

## Key Python Files - Detailed Breakdown

### main.py
```python
"""Application entry point"""
- Parse command line arguments
- Load configuration (including developer settings)
- Initialize database
- Launch GUI application
- Setup signal handlers for clean shutdown
```

### core/config.py
```python
"""Configuration management"""
- Load default_config.json
- Merge with user config.encrypted.json
- Load developer settings from .env or config.yaml:
  - SNAPSHOT_INTERVAL_SEC (default 60, min 10)
  - VIDEO_BITRATE_KBPS_CAM, VIDEO_BITRATE_KBPS_SCREEN
  - VIDEO_RES_PROFILE ∈ {Low, Std, High}
  - OPENAI_VISION_ENABLED (default on)
  - MAX_PARALLEL_UPLOADS (default 3)
- Provide config access interface
- Handle API key encryption/decryption
```

### core/database.py
```python
"""SQLite database interface"""
Classes:
  - Database: Connection manager
  - SessionRepository: CRUD for sessions
  - EventRepository: CRUD for events (with vision_votes, snapshot_refs)
  - SettingsRepository: User preferences
Methods:
  - create_session() → session_id
  - log_snapshot_inference(session_id, kind, ts, label_set, file_ref)
  - log_event(session_id, event_type, data, vision_votes)
  - query_session_events(session_id) → List[Event]
Schema v1.3:
  - Adds vision_votes JSON field per distraction
  - Adds snapshot_refs array per segment
```

### core/state_machine.py
```python
"""Snapshot hysteresis fusion state machine"""
States: FOCUSED, DISTRACTED, BREAK, ABSENT
Transitions based on:
  - Hysteresis over last K snapshots (default K=3)
  - Requires ≥1 minute span across K snapshots for debounce
  - Detection classes from OpenAI Vision API
  - No audio heuristics (audio disabled)
Logic:
  - Accumulates last K snapshot results in rolling buffer
  - If ≥2 of K snapshots show same distraction label → DISTRACTED
  - If ≥2 of K snapshots show focus labels → FOCUSED
  - Emits state changes only after debounce period satisfied
```

### session/session_manager.py
```python
"""Orchestrates entire session lifecycle"""
Methods:
  - start_session(task_name) → session_id
    - Create sessions/<session_id>/ directory structure
    - Start cam.mp4 and screen.mp4 recorders
    - Start snapshot_scheduler
    - Start snapshot_uploader worker pool
    - Start fusion_engine thread
  - pause_session()
  - resume_session()
  - end_session()
    - Stop snapshot scheduler
    - Wait for all uploads to complete
    - Finalize recordings
    - Generate report (schema v1.3)
    - Trigger optional cloud upload
Manages thread lifecycle and cleanup
```

### capture/snapshot_scheduler.py
```python
"""Wall-clock snapshot capture scheduler"""
- Independent of video frame rate
- Timer-based: triggers every SNAPSHOT_INTERVAL_SEC
- Captures cam + screen snapshots simultaneously
- Saves to sessions/<session_id>/snapshots/ as JPEG
- Queues snapshot pairs for upload
Threading:
  - Runs in dedicated thread
  - Uses threading.Timer for wall-clock accuracy
```

### capture/snapshot_uploader.py
```python
"""Upload worker pool for OpenAI Vision API"""
- Worker pool pattern with MAX_PARALLEL_UPLOADS threads
- Consumes snapshot pairs from upload queue
- Calls openai_vision_client for each snapshot
- Implements retry with exponential backoff (429/5xx)
- Saves responses to sessions/<session_id>/vision/*.json
- Inserts results into SQLite
- Sends to fusion queue for realtime processing
Error handling:
  - Retries on transient failures
  - Logs permanent failures
  - Continues processing remaining snapshots
```

### integrations/openai_vision_client.py
```python
"""OpenAI Vision API client"""
Uses: requests library with OpenAI Vision API
Methods:
  - classify_image(image_path, kind) → label_set
    - Uploads snapshot to OpenAI Vision API
    - Prompt engineering for detection classes
    - Returns: {label: confidence, ...}
  - parse_response(api_response) → structured_labels
Detection classes (image-only):
  - Webcam: {HeadAway, EyesOffScreen, Absent, MicroSleep, PhoneLikely}
  - Screen: {VideoOnScreen, SocialFeed, Code/Docs/Slides/Terminal,
             ChatWindow, Games, Unknown}
Handles:
  - Rate limiting (backoff on 429)
  - Timeout handling
  - Local JSON caching
```

### analysis/fusion_engine.py
```python
"""Snapshot hysteresis fusion"""
Receives snapshot classification results from uploader
Maintains rolling buffer of last K snapshots (K=3)
Logic:
  - Accumulates {ts, cam_labels, screen_labels} per snapshot
  - Checks if span of K snapshots ≥1 minute (debounce)
  - Votes across K snapshots: majority label → state
  - Emits focus_event or distract_event with reason codes + vision_votes
Sends to:
  - state_machine.py (state tracking)
  - distraction_detector.py (event emission with evidence)
```

### analysis/distraction_detector.py
```python
"""Snapshot-based distraction detection logic"""
Receives fused state from fusion_engine
Applies business rules:
  - Threshold: ≥N snapshot-confirmed distract_events in 20 min → micro-break
  - Screen label ∈ {Video, Social, Games} across ≥2 consecutive snapshots → prompt
  - Cam labels {HeadAway, MicroSleep} dominate last 3 snapshots → ergonomic alert
Emits events:
  - distract_event(type, duration, evidence, vision_votes)
  - focus_event(duration)
Sends to:
  - database.py (persistence with vision_votes)
  - UI queue (real-time alerts)
```

### integrations/hume_client.py
```python
"""Hume AI Expression API client (POST-PROCESSING ONLY)"""
Uses: Hume Python SDK
Methods:
  - analyze_video(video_path) → job_id
  - poll_job(job_id) → status
  - fetch_results(job_id) → emotion_timeline
Outputs:
  - 1Hz emotion tracks: valence, arousal, stress, frustration
  - Aligned to session segments
Handles:
  - Async job submission
  - Polling with exponential backoff
  - Rate limiting (1 QPS)
Usage:
  - Only called during post-session processing
  - NOT used during realtime monitoring
```

### integrations/memories_client.py
```python
"""Memories.ai API client (POST-PROCESSING ONLY)"""
Uses: requests library
Methods:
  - upload_session_assets(cam_mp4, screen_mp4, snapshots) → object_ids
  - chat_session_analysis(object_ids, schema_prompt) → job_id
  - poll_job(job_id) → session_report_data
  - merge_with_realtime_vision(memories_data, vision_data) → merged_report
Implements:
  - Chunked upload for large MP4 files
  - Resumable upload on network failure
  - Schema-constrained prompt for v1.3 output
Usage:
  - Only called during post-session processing
  - Reconciles with realtime OpenAI Vision snapshot results
```

### session/report_generator.py
```python
"""Generate session_report.json (schema v1.3)"""
Methods:
  - generate(session_id) → session_report.json
  - merge_cloud_data(realtime_data, memories_data, hume_data) → final_report
Schema v1.3 fields:
  - vision_votes: {label: count} per distraction
  - snapshot_refs: array of snapshot file paths per segment
  - Reconciles realtime OpenAI Vision with post-hoc Memories/Hume analysis
Output:
  - sessions/<session_id>_report.json
  - Stored in SQLite for query access
```

### ui/main_window.py
```python
"""Main application window"""
Framework: CustomTkinter or PyQt6
Components:
  - Menu bar (File, Edit, View, Help)
  - Status bar (snapshot upload status, session timer)
  - System tray integration
  - Tab container:
    - dashboard.py (active session view)
    - reports_view.py (history)
    - settings.py (developer mode panel for API toggles)
Event handlers:
  - Start/stop session buttons
  - Pause/resume monitoring
  - Alert acknowledgement
  - Developer mode toggle (shows SNAPSHOT_INTERVAL_SEC, etc.)
Runs in main thread, updates from queue
```

### utils/queue_manager.py
```python
"""Inter-thread communication"""
Provides thread-safe queues:
  - snapshot_upload_queue: scheduler → uploader workers
  - fusion_queue: uploader → fusion_engine
  - event_queue: fusion_engine → UI
  - db_queue: events → database writer thread
Implements:
  - Queue size limits (prevent memory overflow)
  - Timeout handling
  - Graceful shutdown signaling
```

## Data Flow Example: Snapshot-Based Distraction Detection

```
1. Wall-clock timer triggers (60s elapsed since last snapshot)
   ↓
2. snapshot_scheduler.py: Captures cam + screen snapshots → JPEG files
   ↓ [snapshot_upload_queue]
3. snapshot_uploader.py: Worker thread pulls snapshot pair
   ↓
4. openai_vision_client.py: POST cam_snapshot.jpg to OpenAI Vision API
   ↓ (API response)
5. openai_vision_client.py: Response → {HeadAway: 0.85, EyesOffScreen: 0.12}
   ↓ (save to vision/cam_YYYYMMDD_HHMMSS.json)
6. openai_vision_client.py: POST screen_snapshot.jpg to OpenAI Vision API
   ↓ (API response)
7. openai_vision_client.py: Response → {VideoOnScreen: 0.92}
   ↓ (save to vision/screen_YYYYMMDD_HHMMSS.json)
8. snapshot_uploader.py: Insert both results into SQLite
   ↓ [fusion_queue]
9. fusion_engine.py: Add to rolling buffer (now K=1/3 snapshots)
   ↓ (wait for more snapshots...)
10. After K=3 snapshots collected spanning ≥1 minute:
   ↓
11. fusion_engine.py: Vote across 3 snapshots → majority=HeadAway
   ↓
12. state_machine.py: Transition FOCUSED → DISTRACTED
   ↓
13. distraction_detector.py: Emit distract_event(
      type="HeadAway",
      duration=calculated,
      evidence="OpenAI Vision confirmed across 3 snapshots",
      vision_votes={HeadAway:2, EyesOffScreen:1, VideoOnScreen:3}
    )
   ↓ [splits to 2 destinations]
   ├─> [db_queue] → database.py: INSERT INTO events (includes vision_votes)
   └─> [event_queue] → main_window.py → alert_overlay.py: Show notification
```

## Critical Inter-Module Dependencies

### Capture ← Upload ← Analysis
- `snapshot_scheduler.py` captures snapshots → `snapshot_uploader.py` (upload queue)
- `snapshot_uploader.py` uploads → `openai_vision_client.py` (API calls)
- `openai_vision_client.py` returns labels → `fusion_engine.py` (fusion queue)

### Analysis → Fusion → Detection
- `fusion_engine.py` (hysteresis voting) → `state_machine.py` (state tracking)
- `state_machine.py` → `distraction_detector.py` (event emission)

### Detection → Storage & UI
- `distraction_detector.py` → `database.py` (persistence with vision_votes)
- `distraction_detector.py` → `main_window.py` (UI updates)

### Session → Everything
- `session_manager.py` orchestrates all modules
- Creates/destroys threads
- Manages lifecycle of capture, recording, upload, fusion

### Integrations ← Session (POST-PROCESSING ONLY)
- `session_manager.py` → `hume_client.py` (post-session emotion analysis)
- `session_manager.py` → `memories_client.py` (post-session cloud upload)
- Both integrations → `report_generator.py` (merge with realtime vision data)

## Configuration Flow

```
Startup:
  config/default_config.json (version controlled defaults)
    ↓ [merged with]
  data/config.encrypted.json (user overrides, API keys)
    ↓ [merged with]
  .env or config.yaml (developer settings)
    - SNAPSHOT_INTERVAL_SEC
    - VIDEO_BITRATE_KBPS_CAM, VIDEO_BITRATE_KBPS_SCREEN
    - VIDEO_RES_PROFILE
    - OPENAI_VISION_ENABLED
    - MAX_PARALLEL_UPLOADS
    ↓ [loaded by]
  core/config.py (runtime config object)
    ↓ [accessed by]
  All modules (read-only access)

Settings Update:
  ui/settings.py (developer mode panel)
    ↓
  core/config.py.save()
    ↓
  config.encrypted.json or config.yaml (persisted)
    ↓
  Affected modules reloaded (e.g., snapshot_scheduler restarts with new interval)
```

## Error Handling & Resilience

### Thread Crashes
- Each thread wrapped in try/except
- Errors logged to `sessions/<session_id>/logs/runtime.log`
- UI notified via error queue
- Non-critical threads (e.g., Hume API) fail gracefully
- Critical threads (e.g., snapshot_scheduler) trigger session pause

### API Failures
- `openai_vision_client.py`: Retry with exponential backoff on 429/5xx
- Falls back to local CNN if OpenAI Vision unavailable (fallback must be implemented for graceful degradation)
- `hume_client.py`: Retry with exponential backoff → skip if post-proc fails
- `memories_client.py`: Queue uploads for later → offline mode

### Upload Failures
- Resumable uploads for large MP4 files
- Snapshot upload failures logged to `sessions/<session_id>/logs/uploads.log`
- Failed snapshots retried up to 3 times
- Session continues even if some snapshots fail to upload

### Database Locks
- `database.py`: Single writer thread pattern
- All writes go through db_queue
- Reads use separate connections (SQLite allows concurrent reads)

### Memory Management
- `queue_manager.py`: Enforce max queue sizes (drop old snapshots if upload lags)
- `recorder.py`: Monitor disk space before recording
- `snapshot_scheduler.py`: Auto-pause if disk space <1GB
- `performance_monitor.py`: Auto-throttle snapshot frequency if CPU >80% for >30s

### Network Management
- Bandwidth caps enforced via adaptive JPEG quality
- Pre-flight estimate: snapshot_count × JPEG_avg + video_bitrate × duration
- Expose upload progress and ETA in UI
- Queue snapshots if network unavailable, upload when restored

## Build & Distribution

### PyInstaller Configuration
```python
# scripts/build_installer.py
- Bundle optional screen_classifier.onnx from assets/models/
- Include SQLite schema from config/schema.sql
- Platform detection: macOS/Windows/Linux
- Code signing: Apple Developer / Authenticode
- Create installer: DMG / MSI / AppImage
```

### Platform-Specific
- macOS: Request camera permissions via Info.plist (NO microphone - audio disabled)
- Windows: Package with Visual C++ Runtime
- Linux: Include .desktop file for app launcher

## Key Architectural Differences from MediaPipe Design

### Removed Components (Audio & Local MediaPipe Processing)
- **REMOVED**: `capture/audio_capture.py` - Audio detection not implemented; system uses vision-only approach
- **REMOVED**: `analysis/face_tracker.py` - Replaced by OpenAI Vision API snapshot analysis
- **REMOVED**: `analysis/posture_detector.py` - Replaced by OpenAI Vision API snapshot analysis
- **REMOVED**: `analysis/audio_analyzer.py` - Audio analysis not part of current architecture
- **REMOVED**: `assets/models/mediapipe/` - MediaPipe models no longer used; all vision processing via OpenAI API

### Added Components
- **ADDED**: `capture/snapshot_scheduler.py` (wall-clock timer)
- **ADDED**: `capture/snapshot_uploader.py` (worker pool for uploads)
- **ADDED**: `integrations/openai_vision_client.py` (primary inference engine)

### Modified Components
- **MODIFIED**: `core/state_machine.py` → Now implements hysteresis over K=3 snapshots (not continuous sensor fusion)
- **MODIFIED**: `analysis/fusion_engine.py` → Now fuses snapshot results (not multi-modal sensor streams)
- **MODIFIED**: `analysis/distraction_detector.py` → Snapshot-confirmed events only (no audio triggers)
- **MODIFIED**: `session/report_generator.py` → Schema v1.3 with vision_votes and snapshot_refs

### Architectural Shift Summary
- **FROM**: Continuous multi-modal sensor fusion (video frames + audio + screen via MediaPipe)
- **TO**: Periodic snapshot-based inference with cloud API (camera + screen images only, 60s default cadence)
- **NETWORK**: **Required during sessions** for OpenAI Vision API snapshot uploads (not offline-capable)
- **LATENCY**: Pattern-confirmed detection in 2-3 minutes (K=3 hysteresis) vs sub-second MediaPipe - deliberate trade-off for accuracy
- **COST**: ~$2.40 per 2-hour session (OpenAI API) vs free local MediaPipe inference
- **PRIVACY**: Snapshots uploaded to OpenAI; full video stays local unless user opts in for post-session analysis

### Label Taxonomy Reference
All components must use the canonical label taxonomy defined in prd.md:
- **Webcam Labels**: HeadAway, EyesOffScreen, Absent, MicroSleep, PhoneLikely, Focused
- **Screen Labels**: VideoOnScreen, SocialFeed, Code, Docs, Email, VideoCall, Reading, Slides, Terminal, ChatWindow, Games, MultipleMonitors, Unknown
- See prd.md "Detection Label Taxonomy" section for complete definitions and confidence thresholds
