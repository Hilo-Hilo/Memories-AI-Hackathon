# Focus Guardian - Setup Instructions

This guide explains how to set up the development environment for Focus Guardian, an ADHD distraction analysis desktop application.

## Overview

Focus Guardian uses snapshot-based cloud vision AI to detect distraction patterns during focus sessions. The system captures periodic snapshots (default: 60s intervals) and sends them to OpenAI Vision API for analysis, with full video recordings stored locally.

## Prerequisites

- **Python 3.10 or higher**
- **UV package manager** (install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **FFmpeg** (for video recording)
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`
  - Windows: Download from https://ffmpeg.org/download.html
- **Webcam** (for camera-based distraction detection)
- **OpenAI API Key** (REQUIRED - primary detection engine)

## Project Structure

```
focus-guardian/
├── src/
│   └── focus_guardian/
│       ├── __init__.py
│       ├── main.py                      # Application entry point
│       ├── core/                        # Config, database, state machine
│       ├── capture/                     # Snapshot scheduler, video recording
│       ├── analysis/                    # Fusion engine, distraction detection
│       ├── session/                     # Session manager, report generator
│       ├── integrations/                # OpenAI, Hume, Memories.ai clients
│       ├── ui/                          # Desktop GUI
│       └── utils/                       # Threading, queues, logging
├── config/
│   ├── default_config.json              # Default configuration
│   └── schema.sql                       # SQLite database schema
├── data/                                # User data directory (gitignored)
│   ├── focus_guardian.db                # SQLite database
│   ├── sessions/                        # Per-session recordings
│   └── config.encrypted.json            # User config (API keys)
├── assets/
│   ├── models/                          # Optional local CNN models
│   └── icons/                           # Application icons
├── tests/                               # Unit tests
├── pyproject.toml                       # Python dependencies
├── .env                                 # Environment variables (gitignored)
└── README.md
```

## Environment Setup

### 1. Create Virtual Environment with UV

```bash
uv venv
```

### 2. Activate Virtual Environment

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
uv pip install -e .
```

This will install all required dependencies:

**Core Application:**
- `openai` - OpenAI Vision API client (REQUIRED)
- `opencv-python` - Webcam/screen capture
- `ffmpeg-python` - Video recording (MP4/H.264)
- `mss` - Fast screen capture
- `customtkinter` - Cross-platform GUI framework
- `pillow` - Image processing
- `numpy` - Array operations

**Optional Cloud Services:**
- `hume` - Hume AI Expression API (emotion analysis)
- `requests` - Memories.ai API client

**Data & Storage:**
- `python-dotenv` - Environment variables
- `cryptography` - API key encryption

### 4. Install Development Dependencies (Optional)

```bash
uv pip install -e ".[dev]"
```

This includes:
- `pytest` - Unit testing
- `black` - Code formatting
- `ruff` - Linting
- `pyinstaller` - Application packaging

## API Keys Setup

### Required API Keys

**OpenAI Vision API (REQUIRED):**
- Sign up at https://platform.openai.com
- Create an API key at https://platform.openai.com/api-keys
- Cost: ~$2.40 per 2-hour session (see PRD cost model)

### Optional API Keys

**Hume AI Expression API (Optional - for post-session emotion analysis):**
- Sign up at https://www.hume.ai
- Generate API key in dashboard
- Cost: ~$0.50 per 2-hour video analysis

**Memories.ai (Optional - for post-session pattern analysis):**
- Sign up at https://memories.ai
- Create API key
- Cost: ~$1.00 per 2-hour session

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Optional Cloud Services
HUME_API_KEY=your_hume_api_key_here
MEMORIES_API_KEY=your_memories_api_key_here

# Developer Settings (Optional - defaults to values below)
SNAPSHOT_INTERVAL_SEC=60          # Snapshot frequency (default: 60, min: 10)
VIDEO_BITRATE_KBPS_CAM=500        # Camera video bitrate
VIDEO_BITRATE_KBPS_SCREEN=500     # Screen video bitrate
VIDEO_RES_PROFILE=Std             # Low | Std | High
MAX_PARALLEL_UPLOADS=3            # Concurrent snapshot uploads
OPENAI_VISION_ENABLED=true        # Enable OpenAI Vision (false = local CNN fallback)
```

**IMPORTANT:** Add `.env` to `.gitignore` to protect your API keys.

## Database Setup

### Initialize SQLite Database

```bash
python -c "from focus_guardian.core.database import Database; Database.initialize('data/focus_guardian.db', 'config/schema.sql')"
```

This creates:
- SQLite database at `data/focus_guardian.db`
- Tables: sessions, snapshots, distraction_events, session_reports
- Schema version: v1.3

### Database Schema

The database schema (`config/schema.sql`) includes:
- **sessions** - Focus session metadata
- **snapshots** - Per-snapshot JPEG paths and vision results
- **distraction_events** - Detected distraction episodes with vision_votes
- **session_reports** - Generated session analysis reports

## Configuration Setup

### Default Configuration

Copy default configuration:

```bash
cp config/default_config.json data/config.encrypted.json
```

Edit `data/config.encrypted.json` to customize:

```json
{
  "snapshot": {
    "interval_sec": 60,
    "quality_profile": "Std"
  },
  "video": {
    "bitrate_kbps_cam": 500,
    "bitrate_kbps_screen": 500
  },
  "detection": {
    "hysteresis_k": 3,
    "min_span_minutes": 1.0
  },
  "api_keys": {
    "openai": "encrypted_key_here",
    "hume": null,
    "memories": null
  }
}
```

**Note:** The application will encrypt API keys on first run if stored in plain text.

## Running the Application

### Development Mode

```bash
python src/focus_guardian/main.py
```

This will:
1. Load configuration from `.env` and `data/config.encrypted.json`
2. Initialize SQLite database if needed
3. Launch the desktop GUI
4. Show onboarding wizard on first run

### First Run Setup

On first launch, the onboarding wizard will:
1. Request camera permissions (required)
2. Verify OpenAI API key
3. Guide through optional integrations (Hume AI, Memories.ai, calendar sync)
4. Allow testing a short focus session
5. Show example session report

### Starting a Focus Session

1. Click "Start Session"
2. Enter task name (e.g., "Work on presentation")
3. Choose quality profile (Low/Std/High)
4. Enable/disable screen capture
5. Session begins:
   - Continuous video recording (cam.mp4, screen.mp4)
   - Snapshot capture every 60 seconds
   - Realtime OpenAI Vision analysis
   - Live distraction alerts

### Ending a Focus Session

1. Click "End Session"
2. Wait for final snapshot uploads
3. View session report
4. Optionally upload to Hume AI for emotion analysis
5. Optionally upload to Memories.ai for pattern analysis

## Building Standalone Application

### macOS

```bash
pyinstaller --clean --noconfirm \
  --name "Focus Guardian" \
  --windowed \
  --icon assets/icons/app_icon.icns \
  --add-data "config:config" \
  --add-data "assets:assets" \
  --osx-bundle-identifier com.focusguardian.app \
  src/focus_guardian/main.py
```

Creates: `dist/Focus Guardian.app`

Sign the application:
```bash
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" "dist/Focus Guardian.app"
```

### Windows

```bash
pyinstaller --clean --noconfirm \
  --name "FocusGuardian" \
  --windowed \
  --icon assets/icons/app_icon.ico \
  --add-data "config;config" \
  --add-data "assets;assets" \
  src/focus_guardian/main.py
```

Creates: `dist/FocusGuardian.exe`

### Linux

```bash
pyinstaller --clean --noconfirm \
  --name "focus-guardian" \
  --windowed \
  --add-data "config:config" \
  --add-data "assets:assets" \
  src/focus_guardian/main.py
```

Creates: `dist/focus-guardian`

Package as AppImage:
```bash
# Follow AppImage packaging guide
# https://docs.appimage.org/packaging-guide/index.html
```

## Testing

### Run Unit Tests

```bash
pytest tests/
```

### Test Individual Components

**Test Snapshot Capture:**
```bash
python -m focus_guardian.capture.snapshot_scheduler --test
```

**Test OpenAI Vision Client:**
```bash
python -m focus_guardian.integrations.openai_vision_client --test test_image.jpg
```

**Test Database:**
```bash
python -m focus_guardian.core.database --test
```

**Test State Machine:**
```bash
python -m focus_guardian.core.state_machine --test
```

## Troubleshooting

### Camera Access Denied

**macOS:**
- Go to System Preferences > Security & Privacy > Camera
- Grant permission to Terminal or your Python executable

**Windows:**
- Go to Settings > Privacy > Camera
- Enable camera access for desktop apps

**Linux:**
- Check camera device: `ls -l /dev/video*`
- Add user to video group: `sudo usermod -a -G video $USER`

### OpenAI API Errors

**Rate Limiting (429 errors):**
- System implements exponential backoff automatically
- Reduce snapshot frequency: Set `SNAPSHOT_INTERVAL_SEC=90` or `120`
- Check API quota: https://platform.openai.com/account/usage

**Authentication Errors:**
- Verify API key in `.env` is correct
- Check key has Vision API access
- Ensure no extra spaces/quotes in environment variable

### FFmpeg Not Found

**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

**Solution:**
- Install FFmpeg (see Prerequisites)
- Verify installation: `ffmpeg -version`
- On Windows, add FFmpeg to PATH

### Database Locked Errors

**Error:** `sqlite3.OperationalError: database is locked`

**Solution:**
- Close all other connections to the database
- Check for zombie processes: `ps aux | grep focus_guardian`
- Delete database lock file: `rm data/focus_guardian.db-journal`

### Screen Capture Fails

**macOS:**
- Grant Screen Recording permission
- System Preferences > Security & Privacy > Screen Recording

**Linux (Wayland):**
- Screen capture may not work on Wayland
- Switch to X11 session: `export XDG_SESSION_TYPE=x11`

### High CPU Usage

If CPU usage exceeds 30% average:
1. Check `SNAPSHOT_INTERVAL_SEC` - increase to 90 or 120
2. Lower quality profile to "Low"
3. Disable screen capture if not needed
4. Check background processes competing for resources

### Network Connectivity Issues

**Snapshots Not Uploading:**
- Check internet connection
- System queues snapshots and retries automatically
- View queue status in UI
- Logs available in `data/sessions/<session_id>/logs/uploads.log`

**Session Paused Automatically:**
- Network outage >5 minutes triggers auto-pause
- Resume session when connectivity restores
- Queued snapshots will upload automatically

## Performance Optimization

### Reduce Costs

To minimize OpenAI API costs:
1. **Increase snapshot interval:** `SNAPSHOT_INTERVAL_SEC=90` (saves 33%)
2. **Use Economy profile:** Lower quality but acceptable accuracy
3. **Disable screen capture:** If only monitoring camera distractions
4. **Set cost caps:** Configure max monthly spend in UI

### Improve Battery Life

For laptop users:
1. Use "Low" quality profile (256p/10fps)
2. Increase snapshot interval to 90s or 120s
3. Disable screen capture
4. Close unnecessary background apps

### Hardware Acceleration

GPU acceleration (if available) reduces CPU load:
- **macOS:** Automatically uses VideoToolbox
- **Windows:** Uses DirectML if available
- **Linux:** Install CUDA for NVIDIA GPUs

Check GPU acceleration:
```bash
python -c "import cv2; print(cv2.cuda.getCudaEnabledDeviceCount())"
```

## Developer Mode

### Enable Developer Settings

In UI: Settings > Developer Mode (toggle on)

Shows advanced configuration:
- `SNAPSHOT_INTERVAL_SEC`
- `VIDEO_BITRATE_KBPS_CAM`, `VIDEO_BITRATE_KBPS_SCREEN`
- `VIDEO_RES_PROFILE`
- `OPENAI_VISION_ENABLED` (toggle cloud vs local CNN)
- `MAX_PARALLEL_UPLOADS`

### Local CNN Fallback

If `OPENAI_VISION_ENABLED=false`:
- System uses local CNN classifier
- No cloud API calls (reduced cost, offline capable)
- Lower accuracy than OpenAI Vision
- Model: `assets/models/screen_classifier.onnx`

Download local model:
```bash
# TODO: Add model download script
python scripts/download_models.py
```

## Documentation

- **PRD:** `prd.md` - Product requirements and features
- **Architecture:** `ARCHITECTURE.md` - System architecture and file structure
- **Specification:** `SPECIFICATION.md` - Technical specification and API contracts

## Support

For issues and bug reports:
- GitHub Issues: https://github.com/[your-repo]/focus-guardian/issues
- Documentation: See `prd.md`, `ARCHITECTURE.md`, `SPECIFICATION.md`

## Security Notes

### API Key Protection

- **Never commit `.env` or `data/config.encrypted.json` to git**
- Add to `.gitignore`:
  ```
  .env
  data/
  *.encrypted.json
  ```
- API keys are encrypted at rest using `cryptography` library
- Encryption key stored in system keyring

### Privacy

Per PRD Privacy Model:
- **Snapshots uploaded to OpenAI Vision API** - required for detection
- **Full video stays local** - unless explicitly uploaded for optional analysis
- **No audio capture** - audio disabled by design
- **User controls all uploads** - explicit consent for Hume/Memories.ai

### Data Retention

Configure in Settings:
- **Keep recordings:** 0 days (delete after report) / 24 hours / 7 days / forever
- **Auto-delete after upload:** Delete local files after successful cloud merge
- **Export data:** Export all session data to JSON

## Next Steps

After setup:
1. Complete onboarding wizard
2. Run a test session (5-10 minutes)
3. Review session report
4. Adjust settings as needed
5. Start using for real focus sessions

For development:
1. Read `ARCHITECTURE.md` - understand module structure
2. Read `SPECIFICATION.md` - understand data models and APIs
3. Run tests: `pytest tests/`
4. Check code style: `black src/ && ruff src/`
5. Start implementing modules per architecture
