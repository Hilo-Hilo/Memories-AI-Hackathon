"""
Data models for Focus Guardian.

Defines all dataclasses used throughout the application following
the schema v1.3 specification from SPECIFICATION.md.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any


# ============================================================================
# Enums
# ============================================================================

class SessionStatus(Enum):
    """Session lifecycle states."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class QualityProfile(Enum):
    """Video quality profiles with resolution/fps/bitrate presets."""
    LOW = "Low"      # 256p/10fps/200kbps
    STD = "Std"      # 480p/15fps/500kbps
    HIGH = "High"    # 720p/15fps/1000kbps


class SnapshotKind(Enum):
    """Type of snapshot (camera or screen)."""
    CAM = "cam"
    SCREEN = "screen"


class UploadStatus(Enum):
    """Snapshot upload lifecycle states."""
    PENDING = "pending"
    UPLOADING = "uploading"
    SUCCESS = "success"
    FAILED = "failed"


class DistractionType(Enum):
    """Types of distraction events."""
    LOOK_AWAY = "LookAway"           # Head/eyes off screen
    PHONE = "Phone"                   # Phone detected in frame
    VIDEO = "Video"                   # Video content on screen
    SOCIAL = "Social"                 # Social media detected
    CHAT = "Chat"                     # Chat window open
    ABSENT = "Absent"                 # User not visible
    MICRO_SLEEP = "MicroSleep"        # Eyes closed/drowsy
    UNKNOWN = "Unknown"               # Could not classify


class State(Enum):
    """Focus state machine states."""
    FOCUSED = "focused"
    DISTRACTED = "distracted"
    BREAK = "break"
    ABSENT = "absent"


class SegmentLabel(Enum):
    """Session segment classification."""
    FOCUS = "Focus"
    BREAK = "Break"
    ADMIN = "Admin"
    SETUP = "Setup"


# ============================================================================
# Core Data Models
# ============================================================================

@dataclass
class Session:
    """Represents a focus session."""
    session_id: str                    # UUID v4
    started_at: datetime               # ISO 8601 UTC
    ended_at: Optional[datetime]       # ISO 8601 UTC
    task_name: str                     # User-provided task description
    quality_profile: QualityProfile    # Low | Std | High
    screen_enabled: bool               # Screen capture toggle
    status: SessionStatus              # Active | Paused | Completed | Failed

    # Paths (relative to data directory)
    cam_mp4_path: str                  # sessions/<id>/cam.mp4
    screen_mp4_path: Optional[str]     # sessions/<id>/screen.mp4
    snapshots_dir: str                 # sessions/<id>/snapshots/
    vision_dir: str                    # sessions/<id>/vision/
    logs_dir: str                      # sessions/<id>/logs/

    # Statistics
    total_snapshots: int = 0           # Count of captured snapshots
    uploaded_snapshots: int = 0        # Count of successfully uploaded snapshots
    failed_snapshots: int = 0          # Count of failed uploads
    total_events: int = 0              # Count of distraction events


@dataclass
class Snapshot:
    """Represents a single snapshot (cam or screen)."""
    snapshot_id: str                   # UUID v4
    session_id: str                    # Foreign key to Session
    timestamp: datetime                # ISO 8601 UTC
    kind: SnapshotKind                 # cam | screen

    # File references
    jpeg_path: str                     # Relative path to JPEG file
    jpeg_size_bytes: int               # File size in bytes

    # Vision API results (nullable until processed)
    vision_json_path: Optional[str] = None          # Relative path to vision/*.json
    vision_labels: Optional[Dict[str, float]] = None  # {label: confidence}
    processed_at: Optional[datetime] = None         # When OpenAI Vision API returned
    upload_status: UploadStatus = UploadStatus.PENDING
    retry_count: int = 0                            # Number of upload attempts
    error_message: Optional[str] = None             # Error details if failed


@dataclass
class DistractionEvent:
    """Represents a detected distraction event."""
    event_id: str                      # UUID v4
    session_id: str                    # Foreign key to Session
    started_at: datetime               # ISO 8601 UTC
    ended_at: datetime                 # ISO 8601 UTC
    duration_seconds: float            # Calculated duration

    # Classification
    event_type: DistractionType        # Type of distraction
    evidence: str                      # Human-readable explanation
    confidence: float                  # 0.0 - 1.0

    # Vision votes (snapshot hysteresis results)
    vision_votes: Dict[str, int]       # {label: count} e.g. {"HeadAway": 2, "EyesOffScreen": 1}
    snapshot_refs: List[str]           # List of snapshot_ids that contributed

    # User interaction
    acknowledged: bool = False         # User dismissed alert
    acknowledged_at: Optional[datetime] = None


@dataclass
class SnapshotResult:
    """Results from processing a snapshot pair (cam + screen)."""
    timestamp: datetime
    cam_labels: Dict[str, float]       # {label: confidence}
    screen_labels: Dict[str, float]    # {label: confidence}
    span_minutes: float                # Time since first snapshot in buffer


@dataclass
class FocusState:
    """Current focus state with hysteresis buffer."""
    state: State                       # Current state
    entered_at: datetime               # When entered this state
    duration_seconds: float            # Time in current state
    snapshot_buffer: List[SnapshotResult]  # Last K snapshots for hysteresis
    confidence: float                  # State confidence 0.0-1.0


@dataclass
class StateTransition:
    """Represents a state machine transition."""
    from_state: State
    to_state: State
    timestamp: datetime
    confidence: float
    evidence: Dict[str, Any]           # Vision votes and reasoning


# ============================================================================
# Session Report Models (Schema v1.3)
# ============================================================================

@dataclass
class SessionMeta:
    """Session metadata for reports."""
    started_at: str                    # ISO 8601
    ended_at: str                      # ISO 8601
    profile: str                       # Low | Std | High
    total_duration_minutes: float
    snapshot_interval_sec: int         # SNAPSHOT_INTERVAL_SEC used


@dataclass
class AppUsage:
    """Application usage breakdown."""
    app_class: str                     # IDE | Docs | Browser | Video | Social | Chat | Terminal | Unknown
    share: float                       # 0.0 - 1.0 (percentage of segment time)


@dataclass
class DistractionDetail:
    """Detailed distraction information for reports."""
    t0: float                          # Seconds from session start
    t1: float                          # Seconds from session start
    distraction_type: str              # LookAway | Phone | Video | Social | Chat
    evidence: str                      # Explanation
    vision_votes: Dict[str, int]       # Label vote counts from K snapshots


@dataclass
class PostureAnalysis:
    """Posture analysis for a segment."""
    mode: str                          # Neutral | Slouch | HeadAway | Down | Absent
    pct: float                         # 0.0 - 1.0 (percentage of segment)


@dataclass
class ExpressionAnalysis:
    """Emotion analysis from Hume AI."""
    frustration_mean: float            # 0.0 - 1.0
    valence_mean: float                # -1.0 to 1.0
    arousal_mean: float                # 0.0 - 1.0


@dataclass
class Segment:
    """A time segment within a session."""
    t0: float                          # Seconds from session start
    t1: float                          # Seconds from session start
    label: SegmentLabel                # Focus | Break | Admin | Setup
    task_hypothesis: str               # Inferred task description

    # App usage breakdown
    apps: List[AppUsage] = field(default_factory=list)

    # Distraction details
    distractions: List[DistractionDetail] = field(default_factory=list)

    # Posture analysis
    posture: Optional[PostureAnalysis] = None

    # Emotion analysis (from Hume AI)
    expressions: Optional[ExpressionAnalysis] = None

    # Snapshot references
    snapshot_refs: List[str] = field(default_factory=list)


@dataclass
class KPIs:
    """Key Performance Indicators for a session."""
    focus_ratio: float                 # 0.0 - 1.0
    avg_focus_bout_min: float          # Average focused period duration
    num_alerts: int                    # Total distraction alerts
    top_triggers: List[str]            # Most common distraction types
    peak_distraction_hour: str         # e.g. "15:00-16:00"


@dataclass
class Recommendation:
    """Personalized recommendation based on session analysis."""
    rec_type: str                      # BreakSchedule | AppBlock | TaskSplit | Ergonomics
    message: str                       # Human-readable recommendation
    priority: int                      # 1 (high) to 5 (low)


@dataclass
class Artifacts:
    """References to external artifacts (cloud services)."""
    memories_urls: Dict[str, str]      # {cam: url, screen: url}
    hume_job_id: Optional[str]         # Hume API job ID


@dataclass
class SessionReport:
    """Complete session report (schema v1.3)."""
    session_id: str
    meta: SessionMeta
    segments: List[Segment]
    kpis: KPIs
    recommendations: List[Recommendation]
    artifacts: Artifacts


# ============================================================================
# Detection Label Taxonomy (Canonical - from prd.md)
# ============================================================================

# Webcam Labels
CAM_LABELS = {
    "HeadAway",        # Head turned >45° from screen
    "EyesOffScreen",   # Gaze not directed at screen
    "Absent",          # No person visible in frame
    "MicroSleep",      # Eyes closed, drowsy appearance
    "PhoneLikely",     # Phone visible in hand or being viewed
    "Focused"          # Engaged posture, eyes on screen (positive class)
}

# Screen Labels
SCREEN_LABELS = {
    "VideoOnScreen",      # Video player or streaming content
    "SocialFeed",         # Social media feed scrolling
    "Code",               # Code editor or IDE
    "Docs",               # Documentation, technical reading, wikis
    "Email",              # Email client (borderline - context-dependent)
    "VideoCall",          # Video conferencing UI (borderline - context-dependent)
    "Reading",            # Long-form reading (ebooks, PDFs, news)
    "Slides",             # Presentation software
    "Terminal",           # Command line terminal or shell
    "ChatWindow",         # Chat/messaging applications
    "Games",              # Gaming applications or entertainment
    "MultipleMonitors",   # Multiple windows visible (borderline - context switching)
    "Unknown"             # Cannot determine content type
}

# Category mappings for state machine logic
CAM_DISTRACTION_LABELS = {"HeadAway", "EyesOffScreen", "MicroSleep", "PhoneLikely"}
CAM_FOCUS_LABELS = {"Focused"}
CAM_ABSENCE_LABELS = {"Absent"}

SCREEN_DISTRACTION_LABELS = {"VideoOnScreen", "SocialFeed", "Games", "ChatWindow"}
SCREEN_FOCUS_LABELS = {"Code", "Docs", "Reading", "Slides", "Terminal"}
SCREEN_BORDERLINE_LABELS = {"Email", "VideoCall", "MultipleMonitors"}  # Context-dependent
SCREEN_NEUTRAL_LABELS = {"Unknown"}


# Confidence thresholds (from prd.md Detection Label Taxonomy)
CONFIDENCE_THRESHOLDS = {
    # Webcam thresholds
    "HeadAway": 0.7,
    "EyesOffScreen": 0.7,
    "Absent": 0.8,
    "MicroSleep": 0.7,
    "PhoneLikely": 0.75,
    "Focused": 0.6,
    
    # Screen thresholds
    "VideoOnScreen": 0.7,
    "SocialFeed": 0.75,
    "Code": 0.7,
    "Docs": 0.65,
    "Email": 0.6,
    "VideoCall": 0.7,
    "Reading": 0.65,
    "Slides": 0.7,
    "Terminal": 0.75,
    "ChatWindow": 0.7,
    "Games": 0.8,
    "MultipleMonitors": 0.6,
    "Unknown": 0.5,
}

