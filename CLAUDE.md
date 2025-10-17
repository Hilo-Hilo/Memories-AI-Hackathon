# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

```bash
# Run application
python src/focus_guardian/main.py

# Run tests
python tests/test_components.py

# Format & lint
black src/ tests/ && ruff src/ tests/

# Install dependencies
uv pip install -e ".[dev]"
```

## Project Overview

**Focus Guardian** - A PyQt6 desktop application for ADHD distraction analysis using snapshot-based cloud vision AI. This Memories AI Hackathon project uses:

- **Snapshot-based detection** - Captures webcam + screen images every 60 seconds (configurable)
- **OpenAI Vision API** - Primary detection engine for real-time analysis (REQUIRED for operation)
- **K=3 hysteresis voting** - Requires 3 consecutive snapshots spanning ≥1 minute to confirm state changes
- **Local video recording** - Full MP4 recordings stay local (cam.mp4, screen.mp4)
- **Optional post-processing** - Hume AI (emotion) and Memories.ai (pattern analysis) cloud APIs
- **SQLite storage** - All session data stored in `data/focus_guardian.db`

**CRITICAL ARCHITECTURE CHANGE**: This app does NOT use MediaPipe or local real-time processing. It's a snapshot-based system that sends images to OpenAI Vision API every 60 seconds. The app requires internet connectivity during sessions.

## Development Commands

### Running the Application

```bash
# Quick start (recommended)
python src/focus_guardian/main.py

# Or using module syntax
python -m focus_guardian.main

# Background mode (frees terminal)
python src/focus_guardian/main.py &
```

### Dependencies & Environment

```bash
# Install dependencies (use uv package manager)
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"

# Install with build tools
uv pip install -e ".[dist]"

# Activate virtual environment
source .venv/bin/activate
```

### Testing

```bash
# Run all unit tests
pytest tests/

# Run component test script
python tests/test_components.py

# Run full integration test with GUI
# See TEST_GUIDE.md for detailed step-by-step testing instructions
python src/focus_guardian/main.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff src/ tests/

# Type checking
mypy src/
```

### Database Management

```bash
# Initialize database
python -c "from focus_guardian.core.database import Database; Database.initialize('data/focus_guardian.db', 'config/schema.sql')"

# Check database schema
sqlite3 data/focus_guardian.db ".schema"

# Query sessions
sqlite3 data/focus_guardian.db "SELECT * FROM sessions;"
```

### Building Standalone Application

```bash
# macOS
pyinstaller --clean --noconfirm \
  --name "Focus Guardian" \
  --windowed \
  --icon assets/icons/app_icon.icns \
  --add-data "config:config" \
  --add-data "assets:assets" \
  src/focus_guardian/main.py

# Windows
pyinstaller --clean --noconfirm \
  --name "FocusGuardian" \
  --windowed \
  --icon assets/icons/app_icon.ico \
  --add-data "config;config" \
  --add-data "assets;assets" \
  src/focus_guardian/main.py
```

## API Information

### OpenAI Vision API (REQUIRED)

**Authentication**: Set `OPENAI_API_KEY` in `.env` file

**Usage**: Primary detection engine - analyzes webcam and screen snapshots every 120 seconds (configurable)

**Model**: `gpt-5-nano` (default, configurable via `openai_vision_model`)

**Detail Level**: `high` (1100 tokens/image) - provides superior accuracy for 120s intervals

**Cost Optimization Strategy**:
- **Recommended (gpt-5-nano, 120s interval, high detail)**: ~$6.60 per 2-hour session (60 pairs × $0.11)
  - Best balance: 3x cheaper than gpt-4o-mini with comparable accuracy
  - Trades snapshot frequency for image quality → better pattern detection
  - K=3 hysteresis requires 3.5+ minute span, so 120s intervals provide timely detection
- **Ultra-budget (gpt-5-nano, 120s interval, low detail)**: ~$0.51 per 2-hour session (60 pairs × $0.0085)
  - Set `openai_vision_detail: "low"` in config for 85 tokens/image
  - May miss subtle behaviors (phone detection, eye gaze)
- **Alternative (gpt-4o-mini, 120s interval, high detail)**: ~$19.80 per 2-hour session
  - Use if gpt-5-nano accuracy insufficient (rare)
  - Set `openai_vision_model: "gpt-4o-mini"` in config

**Detection Classes**:
- Webcam: `HeadAway`, `EyesOffScreen`, `Absent`, `MicroSleep`, `PhoneLikely`, `Focused`
- Screen: `VideoOnScreen`, `SocialFeed`, `Code`, `Docs`, `Email`, `VideoCall`, `ChatWindow`, `Games`, etc.

### Hume AI API (Optional - Post-processing)

**Authentication**: Set `HUME_API_KEY` in `.env` file

**Usage**: Post-session emotion analysis of recorded video

**Cost**: ~$0.50 per 2-hour session

### Memories.ai API (Optional - Post-processing)

**Authentication**: Set `MEMORIES_API_KEY` in `.env` file

**Usage**: Post-session pattern analysis via multimodal chat

**Cost**: ~$1.00 per 2-hour session

## Architecture: Snapshot-Based Detection Pipeline

This application uses a **snapshot-based inference pipeline** fundamentally different from traditional real-time video analysis:

### Core Data Flow (Image-Only Pipeline)

```
1. Wall-clock timer (60s) → snapshot_scheduler.py
   ↓
2. Capture cam.jpg + screen.jpg → save to sessions/<id>/snapshots/
   ↓ [snapshot_upload_queue]
3. Worker pool (3 threads) → snapshot_uploader.py
   ↓
4. OpenAI Vision API → classify_image(cam.jpg) + classify_image(screen.jpg)
   ↓
5. Save responses → sessions/<id>/vision/*.json + SQLite
   ↓ [fusion_queue]
6. fusion_engine.py → accumulate K=3 snapshots in rolling buffer
   ↓
7. Check: span ≥1 min? If yes, vote across K snapshots (majority rule)
   ↓
8. state_machine.py → transition if ≥2 of 3 snapshots agree
   ↓
9. distraction_detector.py → emit distraction_event with vision_votes evidence
   ↓ [splits to 2 destinations]
   ├→ database.py (persistence)
   └→ main_window.py (UI alert)
```

### Threading Architecture (7 Threads)

1. **Main Thread (UI)** - PyQt6 event loop, receives events via queue
2. **Snapshot Scheduler** - Wall-clock timer, captures snapshots every 60s
3. **Worker Pool (3x)** - Upload snapshots to OpenAI Vision API with retry/backoff
4. **Fusion Thread** - Hysteresis voting over K=3 snapshots
5. **Webcam Recorder** - ffmpeg-python continuous H.264 recording
6. **Screen Recorder** - ffmpeg-python continuous H.264 recording
7. **Database Writer** - Single writer pattern for all SQLite writes

**CRITICAL**: UI thread must NEVER block on I/O. All API calls, database writes, and snapshot processing happen in background threads.

### K=3 Hysteresis Voting Logic

Located in `src/focus_guardian/core/state_machine.py`:

```python
# Requires 3 consecutive snapshots spanning ≥1 minute
if len(snapshot_buffer) < K:  # Need K=3 snapshots
    return None

if span_seconds < 60:  # Need ≥1 minute span
    return None

# Vote: if ≥2 of 3 snapshots show "HeadAway" → DISTRACTED
majority_threshold = max(2, K // 2 + 1)  # At least 2 votes
```

**State Priorities** (checked in order):
1. `ABSENT` - User absent from desk (cam: Absent, MicroSleep dominant)
2. `DISTRACTED` - Distraction detected (cam: HeadAway/PhoneLikely OR screen: Video/Social/Games)
3. `FOCUSED` - Focus confirmed (cam: Focused AND screen: Code/Docs/Terminal)
4. Default - Maintain current state with low confidence

### Session Directory Structure

Each session creates:
```
data/sessions/<session_id>/
├── cam.mp4                          # Local webcam recording (never uploaded unless user opts in)
├── screen.mp4                       # Local screen recording (never uploaded unless user opts in)
├── snapshots/
│   ├── cam_20250101_120000.jpg     # Snapshot sent to OpenAI Vision
│   ├── screen_20250101_120000.jpg
│   └── ...
├── vision/
│   ├── cam_20250101_120000.json    # OpenAI Vision response
│   ├── screen_20250101_120000.json
│   └── ...
└── logs/
    ├── runtime.log                  # Session execution log
    └── uploads.log                  # Upload success/failures
```

### Camera Enumeration (macOS)

**EMPIRICAL FINDING**: On macOS, the **highest working OpenCV index** is typically the built-in FaceTime HD Camera.

When you enumerate cameras in Settings UI:
```python
cameras = WebcamCapture.enumerate_cameras()
# Returns (REVERSED): [{"index": 2, "name": "Camera 2 (1920x1080)"}, {"index": 1, ...}, {"index": 0, ...}]
# Highest index appears FIRST in dropdown (most likely to be built-in camera)
```

**How it works**:
1. Tests each OpenCV index (0-4) by briefly opening and reading a frame
2. Uses generic names: "Camera N (resolution)" since we can't reliably map to device names
3. **Reverses the list** on macOS so highest index appears first
4. User verifies with "Show Live Preview"

**Why we reverse the list**:
- Empirical observation: Highest working index is usually the built-in FaceTime camera
- Lower indices are often virtual cameras (OBS, Persona, etc.) or Continuity Camera
- Reversing puts the most-likely built-in camera at the top of the dropdown
- Works dynamically for systems with 1, 2, or 3+ cameras

**User Experience**:
- Clicking "Refresh List" will briefly activate all cameras (LED flash)
- Camera names are generic: "Camera 2 (1920x1080)", "Camera 1 (1920x1080)", etc.
- First camera in dropdown is usually the built-in FaceTime camera
- Use "Show Live Preview" to verify which camera is which

**Auto-detect behavior**:
- Scans indices 0-4 to find all working cameras
- On macOS: Selects **highest** working index (empirically the built-in camera)
- On other platforms: Selects **lowest** working index
- Example: If cameras at indices [0, 1, 2] work, auto-detect selects index 2 on macOS

### Configuration Management

Developer settings (in `.env` or exposed in Settings UI):

```bash
# Snapshot & Detection Settings
SNAPSHOT_INTERVAL_SEC=120          # Snapshot frequency (min: 10, default: 120)
                                   # Cost optimization: longer intervals → fewer API calls
K_HYSTERESIS=3                     # Number of snapshots for voting (default: 3)
MIN_SPAN_MINUTES=3.5               # Minimum span across K snapshots (default: 3.5)

# OpenAI Vision API Settings
OPENAI_VISION_ENABLED=true         # If false, uses local CNN fallback
OPENAI_VISION_MODEL=gpt-5-nano     # Model to use (default: gpt-5-nano)
                                   # Options: gpt-5-nano ($0.055/image), gpt-4o-mini ($0.165/image)
OPENAI_VISION_DETAIL=high          # Image detail: "low" (85 tokens) or "high" (1100 tokens)
                                   # gpt-5-nano: high=$0.055/image, low=$0.00425/image
                                   # High detail recommended for 120s intervals

# Upload & Threading
MAX_PARALLEL_UPLOADS=3             # Worker pool size (1-5)

# Video Recording
VIDEO_RES_PROFILE=Std              # Low|Std|High (affects recording quality)

# Camera Selection
CAMERA_INDEX=-1                    # Camera to use (-1 = auto-detect FaceTime HD)
CAMERA_NAME="Auto-detect"          # Display name for selected camera
```

Loaded via `core/config.py`:
```python
config = Config()  # Merges default_config.json + config.encrypted.json + .env
interval = config.get_snapshot_interval_sec()  # Returns 120 by default
api_key = config.get_openai_api_key()  # Decrypted from config.encrypted.json
camera_index = config.get_camera_index()  # Returns -1 for auto-detect
vision_model = config.get_config_value("openai_vision_model", "gpt-5-nano")
vision_detail = config.get_config_value("openai_vision_detail", "high")
```

## Module Structure

The application is organized into focused modules under `src/focus_guardian/`:

- **core/** - Configuration, database, state machine, and data models
- **capture/** - Snapshot scheduling, uploading, screen capture, and video recording
- **analysis/** - Fusion engine and distraction detection logic
- **session/** - Session management and report generation
- **integrations/** - External API clients (OpenAI Vision, Hume AI, Memories.ai)
- **ui/** - PyQt6 main window and UI components
- **utils/** - Threading, queues, encryption, logging, performance monitoring

## Key Module Responsibilities

### Core Orchestrator: `session/session_manager.py`

The central coordinator - initializes and manages all components:

```python
session_manager.start_session(task_name, quality_profile, screen_enabled)
# Creates:
# - Session directory structure
# - Database record
# - All components (recorders, scheduler, uploader, fusion, detector)
# - Starts all threads in correct order

session_manager.stop_session()
# Cleanup sequence:
# 1. Stop snapshot scheduler (no more captures)
# 2. Wait for uploader to finish pending uploads (30s timeout)
# 3. Stop fusion engine and distraction detector
# 4. Stop video recorders (finalize MP4 files)
# 5. Update database with final stats
```

**Thread startup order matters**: Recorders → Uploader → Fusion → Detector → Scheduler (last)

### State Management: `core/state_machine.py`

Implements hysteresis voting with debounce:

```python
state_machine.update(snapshot_result) → Optional[StateTransition]

# Returns StateTransition only when:
# 1. Have K=3 snapshots in buffer
# 2. Span ≥1 minute across buffer
# 3. Majority vote (≥2 of 3) shows new state
# 4. New state differs from current state
```

**Confidence weighting**: Camera evidence weighted 70%, screen evidence 30% for distraction detection.

### Queue Communication: `utils/queue_manager.py`

Four queues for inter-thread communication:

1. `snapshot_upload_queue` - Scheduler → Uploader (holds snapshot file paths)
2. `fusion_queue` - Uploader → Fusion (holds vision API results)
3. `event_queue` - Fusion → Detector (holds state transitions)
4. `ui_queue` - Detector → Main Window (holds alert messages)

**Queue size limits**: Default 100 items to prevent memory overflow during upload lag.

### Database: `core/database.py`

**Single writer pattern** - All writes go through dedicated thread:

```python
# Schema v1.3 tables:
sessions         # Session metadata
snapshots        # Per-snapshot file references
distraction_events  # Events with vision_votes JSON field
session_reports  # Generated analysis reports
```

**Critical fields**:
- `vision_votes` - JSON dict of {label: count} per distraction event
- `snapshot_refs` - Array of snapshot file paths per segment
- `total_snapshots`, `uploaded_snapshots`, `failed_snapshots` - Upload tracking

### Component Lifecycle Pattern

Every background component follows this pattern:

```python
class Component:
    def __init__(self, queues, ...):
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run_loop)
        self._thread.start()

    def _run_loop(self):
        while self._running:
            # Process work
            pass

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
```

**Graceful shutdown**: Set `_running = False`, then join with timeout to prevent hangs.

## Critical Implementation Details

### Error Handling & Resilience

**OpenAI Vision API failures**:
- `openai_vision_client.py` implements exponential backoff on 429/5xx errors
- Retries up to 3 times per snapshot
- Failed snapshots logged to `sessions/<id>/logs/uploads.log`
- Session continues even if some snapshots fail

**Upload lag handling**:
- Queue manager enforces max 100 items in snapshot_upload_queue
- If queue full, oldest snapshots dropped (prevents memory overflow)
- UI shows upload queue depth and ETA

**Thread crash recovery**:
- Each thread wrapped in try/except
- Errors logged to `sessions/<id>/logs/runtime.log`
- Critical threads (scheduler) trigger session pause
- Non-critical threads (Hume API) fail gracefully

**Database locks**:
- Single writer thread pattern prevents locks
- All writes go through `db_queue`
- Reads use separate connections (SQLite allows concurrent reads)

### Performance Considerations

**Memory management**:
- Snapshot buffer limited to K=3 items (rolling deque)
- Vision API responses saved to disk, not held in memory
- MP4 recording uses streaming write (no buffering)

**CPU throttling**:
- If CPU >80% for >30s, auto-increase snapshot interval
- Monitored by `utils/performance_monitor.py`

**Disk space**:
- Checked before starting session (requires ≥1GB free)
- Auto-pause if drops below threshold during session

### PyQt6 UI Patterns

**Main window structure** ([ui/main_window.py](src/focus_guardian/ui/main_window.py)):

The UI is implemented as a single main window with embedded dashboard, reports, and settings views. Key patterns:

```python
class MainWindow(QMainWindow):
    def __init__(self, config, database):
        # Tab widget with Dashboard, Reports, Settings sections
        self.tab_widget = QTabWidget()

        # Session manager passed ui_queue for alerts
        self.ui_queue = Queue()
        self.session_manager = SessionManager(config, database, self.ui_queue)

        # Timer checks ui_queue every 100ms for background thread messages
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self._check_ui_queue)
        self.ui_timer.start(100)

    def _check_ui_queue(self):
        # Process messages from background threads
        while not self.ui_queue.empty():
            msg = self.ui_queue.get_nowait()
            self._handle_ui_message(msg)
```

**CRITICAL: NEVER call session_manager methods directly from UI** - Always use background threads:
```python
# Good: Non-blocking pattern
self.start_button.clicked.connect(self._on_start_clicked)

def _on_start_clicked(self):
    # Run session start in background thread
    threading.Thread(target=self._start_session_worker).start()

# Bad: Blocks UI thread for 2-3 seconds
def _on_start_clicked(self):
    self.session_manager.start_session(...)  # WRONG - freezes UI!
```

## Development Guidelines

### Adding New Detection Labels

When adding labels to `core/models.py`:

```python
# Add to appropriate label set
CAM_DISTRACTION_LABELS = {"HeadAway", "EyesOffScreen", "PhoneLikely", "YourNewLabel"}

# Update OpenAI Vision prompt in integrations/openai_vision_client.py
WEBCAM_PROMPT = """
Analyze this webcam image and detect:
- HeadAway: User looking away from screen
- YourNewLabel: Description of new behavior
...
Return JSON: {"HeadAway": 0.0, "YourNewLabel": 0.0, ...}
"""
```

**IMPORTANT**: New labels must be added to both the model constants AND the OpenAI Vision prompt.

### Configuration Changes

Developer settings exposed in UI (`ui/settings.py`):
- Toggle between `.env` values and UI overrides
- Changes saved to `config.encrypted.json`
- Some settings require session restart (snapshot interval, API keys)
- Others take effect immediately (upload worker count)

**Config hierarchy** (later overrides earlier):
1. `config/default_config.json` (version controlled)
2. `data/config.encrypted.json` (user overrides)
3. `.env` file (developer settings)

### Database Schema Changes

When modifying schema in `config/schema.sql`:

```bash
# Create migration script (manual, no ORM)
sqlite3 data/focus_guardian.db "ALTER TABLE sessions ADD COLUMN new_field TEXT;"

# Update database.py with new field accessors
class Database:
    def get_session(self, session_id):
        # Add new_field to SELECT
        pass
```

**Schema versioning**: Increment `schema_version` in `schema.sql` header.

### Testing Patterns

**Snapshot upload mocking** (for offline development):
```python
# In tests/test_uploader.py
class MockVisionClient:
    def classify_image(self, image_path, kind):
        return {"HeadAway": 0.8} if kind == "cam" else {"VideoOnScreen": 0.9}

uploader = SnapshotUploader(..., vision_client=MockVisionClient())
```

**State machine testing**:
```python
# Inject fake snapshots to test K=3 hysteresis
for i in range(3):
    result = SnapshotResult(
        timestamp=datetime.now() + timedelta(seconds=i*30),
        cam_labels={"HeadAway": 0.8},
        screen_labels={"VideoOnScreen": 0.9}
    )
    transition = state_machine.update(result)

assert transition.to_state == State.DISTRACTED
```

### Common Pitfalls

1. **Blocking UI thread**: Session start/stop takes 2-3 seconds - always use background thread
2. **Queue full errors**: Monitor queue sizes, especially during upload lag
3. **Database locks**: Never write to DB from multiple threads - use db_queue
4. **Thread cleanup**: Always call `join(timeout=5.0)` to prevent zombie threads
5. **API key exposure**: Never log or print API keys - use masking: `key[:8] + "..."`
6. **Missing API keys**: Application requires `OPENAI_API_KEY` in `.env` file to function
7. **Camera enumeration**: On macOS, use `WebcamCapture.enumerate_cameras()` which uses AVFoundation and does NOT activate cameras (no LED flash). Only use OpenCV's `cv2.VideoCapture()` when actually capturing frames.
8. **Camera selection consistency**: CRITICAL - The same `camera_index` must be passed to BOTH `WebcamRecorder` and `SnapshotScheduler` ([session_manager.py:173-198](src/focus_guardian/session/session_manager.py#L173-L198)). If user selects camera index 0, both components must use index 0 (not auto-detect). The preview, snapshots, and video recording must all use the identical camera.

## Project Documentation

- **TEST_GUIDE.md** - Comprehensive step-by-step testing guide with expected outputs
- **ARCHITECTURE.md** - Complete module breakdown and data flow diagrams
- **SETUP.md** - Installation and first-run setup instructions
- **SPECIFICATION.md** - Technical specification and API contracts
- **prd.md** - Product requirements and feature definitions
- **QUICKSTART.md** - Quick launch guide for development

**API Documentation** (for optional integrations):
- `documentation/hume-expression-measurement-docs/` - Hume AI API details
- `documentation/openai_vision_api_docs/` - OpenAI Vision models and pricing
- `testing/memories-ai-api-testing/` - Memories.ai integration examples
