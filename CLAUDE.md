# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Focus Guardian** - A PyInstaller-packaged desktop application for ADHD distraction analysis and focus assistance. This Memories AI Hackathon project combines:

- **Real-time distraction detection** using MediaPipe and OpenCV for webcam-based face/eye tracking
- **Emotion analysis** via Hume AI Expression API (optional, cloud-based)
- **Long-term pattern tracking** via Memories.ai API (optional, cloud-based)
- **Local-first architecture** with SQLite storage - all core functionality works offline
- **Session recording** with post-processing analysis (webcam + screen capture to MP4)

The app runs as a native desktop application on macOS, Windows, and Linux, packaged with PyInstaller for easy distribution.

## API Information

### Memories.ai API

**Base URL**: `https://api.memories.ai/v1.2`

**Authentication**: Bearer token in Authorization header
```
Authorization: Bearer YOUR_API_KEY
```

API key is stored in `.env` as `MEM_AI_API_KEY`. Create your key at https://memories.ai/docs/Create%20your%20key/

### Hume AI API

**Base URL**: `https://api.hume.ai/v0`

**Authentication**: API key in `X-Hume-Api-Key` header or use Hume Python SDK

API key is stored in `.env` as `HUME_API_KEY`. Create your key at https://platform.hume.ai/

**Expression Measurement**: Analyzes facial expressions and vocal tone to detect emotions (frustration, boredom, focus, stress)

## Core Architecture Concepts

**Memory Augmented Generation (MAG)**: The platform retrieves from unlimited visual memory to generate context-aware outputs grounded in persistent visual context and past experiences.

**Multimodal Encoding**: Processes visual, audio, text, and metadata sources simultaneously to build a knowledge graph for comprehensive video understanding.

**Asynchronous Processing**: Video encoding/indexing is time-consuming. Use callback URLs to receive notifications when processing completes rather than polling.

**Video Status Lifecycle**:
- `UNPARSE` - Just uploaded, not yet processed
- `PARSE` - Processing complete, ready for search/chat
- `FAIL` - Processing failed (usually due to unsupported codec)

## Key API Parameters

**unique_id**: Multi-tenant namespace identifier. Groups videos by user/workspace/folder. Defaults to "default".

**callback**: Public URL to receive POST notifications when video processing completes. Returns `{"videoNo": "...", "status": "PARSE"}`.

**videoNo**: Unique identifier returned from upload endpoints, required for search/chat operations.

**session_id**: Chat session identifier for multi-turn conversations.

## API Endpoints by Category

### Upload API
- Local file: `POST /serve/api/v1/upload` (multipart/form-data with file)
- Direct URL: `POST /serve/api/v1/upload_url` (streamable video URL)
- Platform URL: `POST /serve/api/v1/scraper_url` (TikTok/YouTube/Instagram)
- Public platform: `POST /serve/api/v1/scraper_url_public` (contributes to shared library)
- Images: `POST /serve/api/v1/upload_img` (supports multiple files)

**Video Requirements**: h264, h265, vp9, or hevc codec. Include audio track for transcription features.

**Metadata Support**: datetime_taken, camera_model, latitude, longitude

### Search API
- Private library: `POST /serve/api/v1/search`
- Public videos: `POST /serve/api/v1/search_public` (TikTok/YouTube/Instagram)
- Audio transcripts: `POST /v1/search_audio_transcripts`
- Similar images: `POST /v1/search_similar_images`
- Similar public images: `POST /v1/search_public_similar_images`

**Search Modes**: `BY_VIDEO`, `BY_AUDIO`, `BY_IMAGE`

**Parameters**: search_param (natural language, English only), top_k, filtering_level (low/medium/high)

### Chat API
- Video chat: `POST /serve/api/v1/chat` (non-streaming)
- Video chat stream: `POST /serve/api/v1/chat_stream` (SSE)
- Video marketer: `POST /serve/api/v1/marketer_chat` (1M+ indexed TikTok videos)
- Marketer stream: `POST /serve/api/v1/marketer_chat_stream`
- Personal media: `POST /v1/chat_personal`
- Personal stream: `POST /v1/chat_personal_stream`

**Response Types**:
- `thinking`: AI reasoning process
- `ref`: Reference timestamps and video segments
- `content`: Generated response text

**Common Use Cases**: Summaries, highlights with timestamps, chapter divisions, editing suggestions, hashtag generation, TikTok optimization, audience analysis

**Marketer Features**: Use "@creator" or "#hashtag" to filter public video pool

### Transcription API
- Video visual transcription (BY_VIDEO)
- Audio transcription (BY_AUDIO) with speaker recognition
- Summary generation by chapter or topic

### Utils API
- List videos: Get all videos under a unique_id
- List sessions: Get chat sessions
- Delete videos: Remove from library
- Get task status: Check scraper/upload task progress

### Caption & Human ReID
**Host**: `https://security.memories.ai` (requires special API key)

- Video caption: `POST /v1/understand/upload`
- Image caption: `POST /v1/understand/uploadFile`

**Human Re-identification**: Track specific people across frames by providing reference images in `persons` parameter (max 5 reference images)

## Rate Limits

- Search API: 10 QPS
- Chat API: 1 QPS
- Exceeding limits returns HTTP 429

## Free Credits

New users receive 100 free credits. Pricing is pay-as-you-go per 1,000 minutes, 1,000 queries, or per GB storage.

## Documentation

`memories_ai_api_docs/` contains detailed API documentation:
- 00_Introduction.md - Platform overview
- 01_Getting_Started.md - Authentication
- 02_Upload_API.md - Upload methods
- 03_Search_API.md - Search capabilities
- 04_Chat_API.md - Chat examples
- 05_Transcription_API.md - Transcription features
- 06_Utils_API.md - Management utilities
- 07_Caption_API.md - Caption & ReID
- 08_Code_Examples.md - Implementation samples
- 09_Pricing_and_Rate_Limits.md - Pricing details

## Desktop Application Architecture

**Tech Stack**:
- **GUI**: CustomTkinter or PyQt6 for modern, cross-platform UI
- **CV/ML**: MediaPipe (face/pose tracking), OpenCV (video capture/processing)
- **Audio**: sounddevice or pyaudio with NumPy/SciPy for FFT analysis
- **Screen Capture**: mss library for cross-platform screen recording
- **Recording**: OpenCV VideoWriter or ffmpeg-python for MP4 encoding
- **Storage**: SQLite for local data (sessions, events, KPIs, recommendations)
- **Threading**: Python threading/multiprocessing for concurrent operations
- **Packaging**: PyInstaller with platform-specific installers (DMG/MSI/AppImage)

**Core Modules**:
- `distraction_detector.py` - MediaPipe-based gaze/posture detection
- `session_manager.py` - Orchestrates recording and analysis
- `screen_recorder.py` - Screen capture functionality
- `audio_monitor.py` - Audio analysis and speech detection
- `report_generator.py` - Generate session_report.json
- `api_integrations.py` - Hume AI and Memories.ai API wrappers
- `desktop_app.py` - Main GUI application entry point

**Database Schema** (SQLite):
- `focus_sessions` - Session metadata (start/end time, duration, task)
- `segments` - Time segments (focus/break/distraction intervals)
- `distraction_events` - Individual distraction occurrences with type/duration
- `expressions` - Emotion analysis results (if Hume AI enabled)
- `recommendations` - Generated suggestions for improvement
- `session_recordings` - File paths to MP4 recordings

**Session Report Format** (session_report.json):
```json
{
  "session_id": "uuid",
  "meta": {"started_at": "iso", "ended_at": "iso", "profile": "Low|Std|High"},
  "segments": [
    {
      "t0": "s", "t1": "s", "label": "Focus|Break|Distraction",
      "task_hypothesis": "string",
      "apps": [{"class": "IDE|Browser|Video|Social", "share": 0.0}],
      "distractions": [{"t0": "s", "t1": "s", "type": "LookAway|Phone", "evidence": "string"}],
      "posture": {"mode": "Neutral|Slouch|HeadAway", "pct": 0.0},
      "expressions": {"frustration_mean": 0.0, "valence_mean": 0.0}
    }
  ],
  "kpis": {
    "focus_ratio": 0.0, "avg_focus_bout_min": 0.0, "num_alerts": 0,
    "top_triggers": ["Video", "Phone"], "peak_distraction_hour": "15:00-16:00"
  },
  "recommendations": [{"type": "BreakSchedule|AppBlock", "msg": "string"}]
}
```

## Development Guidelines

**Python Dependencies**:
- Use `requests` library for API calls
- Use Hume Python SDK for emotion analysis
- All dependencies managed via `pyproject.toml`

**API Integration**:
- **Memories.ai**: Upload session MP4s via `/serve/api/v1/upload`, query via Chat API for structured analysis
- **Hume AI**: Send video frames or audio samples to Expression API, parse emotion features
- Both APIs are **optional features** - app must work completely offline

**Error Handling**:
- Check video status before Memories.ai search/chat (must be "PARSE")
- Handle 429 rate limit errors with backoff
- Use callbacks for async workflows
- Gracefully degrade if APIs unavailable (queue uploads, continue local operation)

**Threading Best Practices**:
- UI thread must remain responsive - never block on I/O or computation
- Use separate threads for: video analysis, audio monitoring, screen capture, API calls
- Use thread-safe queues for inter-thread communication
- Properly cleanup threads on session end

**Privacy & Security**:
- No raw video/audio sent to cloud unless user explicitly enables upload
- Store API keys encrypted in local config
- All session recordings stored locally in user's app data directory
- Clear user consent required before any cloud upload

**Testing**:
- Test distraction detection with various lighting conditions and head positions
- Verify memory usage doesn't grow during long sessions (8+ hours)
- Test offline functionality - all core features should work without internet
- Use tools like Beeceptor for callback URL testing during development

**PyInstaller Packaging**:
- Bundle all MediaPipe model files as data files
- Include hidden imports for all CV/ML dependencies
- Test executable on clean system without Python installed
- Code sign for macOS (notarization) and Windows (Authenticode)
