# Focus Guardian - Technical Specification

**Version:** 1.3
**Date:** October 10, 2025
**Author:** Technical Architecture Team

**IMPORTANT**: This specification references the canonical label taxonomy defined in prd.md "Detection Label Taxonomy" section. All label definitions, confidence thresholds, and category mappings are authoritative in that document. This specification provides implementation details that conform to those canonical definitions.

## Table of Contents

1. [Data Models & Schemas](#data-models--schemas)
2. [Module Interfaces](#module-interfaces)
3. [Configuration Specification](#configuration-specification)
4. [Queue Message Formats](#queue-message-formats)
5. [State Machine Specification](#state-machine-specification)
6. [API Contracts](#api-contracts)
7. [File Formats](#file-formats)
8. [Error Handling](#error-handling)
9. [Threading Model](#threading-model)
10. [Performance Budgets](#performance-budgets)

---

## Data Models & Schemas

### Core Data Models

#### Session
```python
@dataclass
class Session:
    session_id: str                    # UUID v4
    started_at: datetime              # ISO 8601 UTC
    ended_at: Optional[datetime]      # ISO 8601 UTC
    task_name: str                    # User-provided task description
    quality_profile: QualityProfile   # Low | Std | High
    screen_enabled: bool              # Screen capture toggle
    status: SessionStatus             # Active | Paused | Completed | Failed

    # Paths
    cam_mp4_path: str                 # Relative: sessions/<id>/cam.mp4
    screen_mp4_path: Optional[str]    # Relative: sessions/<id>/screen.mp4
    snapshots_dir: str                # Relative: sessions/<id>/snapshots/
    vision_dir: str                   # Relative: sessions/<id>/vision/
    logs_dir: str                     # Relative: sessions/<id>/logs/

    # Statistics
    total_snapshots: int              # Count of captured snapshots
    uploaded_snapshots: int           # Count of successfully uploaded snapshots
    failed_snapshots: int             # Count of failed uploads
    total_events: int                 # Count of distraction events

class SessionStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class QualityProfile(Enum):
    LOW = "Low"      # 256p/10fps/200kbps
    STD = "Std"      # 480p/15fps/500kbps
    HIGH = "High"    # 720p/15fps/1000kbps
```

#### Snapshot
```python
@dataclass
class Snapshot:
    snapshot_id: str                  # UUID v4
    session_id: str                   # Foreign key to Session
    timestamp: datetime               # ISO 8601 UTC
    kind: SnapshotKind                # cam | screen

    # File references
    jpeg_path: str                    # Relative path to JPEG file
    jpeg_size_bytes: int              # File size in bytes

    # Vision API results (nullable until processed)
    vision_json_path: Optional[str]   # Relative path to vision/*.json
    vision_labels: Optional[Dict[str, float]]  # {label: confidence}
    processed_at: Optional[datetime]  # When OpenAI Vision API returned
    upload_status: UploadStatus       # Pending | Uploading | Success | Failed
    retry_count: int                  # Number of upload attempts
    error_message: Optional[str]      # Error details if failed

class SnapshotKind(Enum):
    CAM = "cam"
    SCREEN = "screen"

class UploadStatus(Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    SUCCESS = "success"
    FAILED = "failed"
```

#### DistractionEvent
```python
@dataclass
class DistractionEvent:
    event_id: str                     # UUID v4
    session_id: str                   # Foreign key to Session
    started_at: datetime              # ISO 8601 UTC
    ended_at: datetime                # ISO 8601 UTC
    duration_seconds: float           # Calculated duration

    # Classification
    event_type: DistractionType       # Type of distraction
    evidence: str                     # Human-readable explanation
    confidence: float                 # 0.0 - 1.0

    # Vision votes (snapshot hysteresis results)
    vision_votes: Dict[str, int]      # {label: count} e.g. {"HeadAway": 2, "EyesOffScreen": 1}
    snapshot_refs: List[str]          # List of snapshot_ids that contributed

    # User interaction
    acknowledged: bool                # User dismissed alert
    acknowledged_at: Optional[datetime]

class DistractionType(Enum):
    LOOK_AWAY = "LookAway"           # Head/eyes off screen
    PHONE = "Phone"                   # Phone detected in frame
    VIDEO = "Video"                   # Video content on screen
    SOCIAL = "Social"                 # Social media detected
    CHAT = "Chat"                     # Chat window open
    ABSENT = "Absent"                 # User not visible
    MICRO_SLEEP = "MicroSleep"        # Eyes closed/drowsy
    UNKNOWN = "Unknown"               # Could not classify
```

#### FocusState
```python
@dataclass
class FocusState:
    state: State                      # Current state
    entered_at: datetime              # When entered this state
    duration_seconds: float           # Time in current state
    snapshot_buffer: List[SnapshotResult]  # Last K snapshots for hysteresis
    confidence: float                 # State confidence 0.0-1.0

class State(Enum):
    FOCUSED = "focused"
    DISTRACTED = "distracted"
    BREAK = "break"
    ABSENT = "absent"

@dataclass
class SnapshotResult:
    timestamp: datetime
    cam_labels: Dict[str, float]      # {label: confidence}
    screen_labels: Dict[str, float]   # {label: confidence}
    span_minutes: float               # Time since first snapshot in buffer
```

### Session Report Schema v1.3

```python
@dataclass
class SessionReport:
    session_id: str
    meta: SessionMeta
    segments: List[Segment]
    kpis: KPIs
    recommendations: List[Recommendation]
    artifacts: Artifacts

@dataclass
class SessionMeta:
    started_at: str                   # ISO 8601
    ended_at: str                     # ISO 8601
    profile: str                      # Low | Std | High
    total_duration_minutes: float
    snapshot_interval_sec: int        # SNAPSHOT_INTERVAL_SEC used

@dataclass
class Segment:
    t0: float                         # Seconds from session start
    t1: float                         # Seconds from session start
    label: SegmentLabel               # Focus | Break | Admin | Setup
    task_hypothesis: str              # Inferred task description

    # App usage breakdown
    apps: List[AppUsage]              # Screen app classification

    # Distraction details
    distractions: List[DistractionDetail]

    # Posture analysis
    posture: PostureAnalysis

    # Emotion analysis (from Hume AI)
    expressions: ExpressionAnalysis

    # Snapshot references
    snapshot_refs: List[str]          # Paths to snapshots in this segment

class SegmentLabel(Enum):
    FOCUS = "Focus"
    BREAK = "Break"
    ADMIN = "Admin"
    SETUP = "Setup"

@dataclass
class AppUsage:
    app_class: str                    # IDE | Docs | Browser | Video | Social | Chat | Terminal | Unknown
    share: float                      # 0.0 - 1.0 (percentage of segment time)

@dataclass
class DistractionDetail:
    t0: float                         # Seconds from session start
    t1: float                         # Seconds from session start
    distraction_type: str             # LookAway | Phone | Video | Social | Chat
    evidence: str                     # Explanation
    vision_votes: Dict[str, int]      # Label vote counts from K snapshots

@dataclass
class PostureAnalysis:
    mode: str                         # Neutral | Slouch | HeadAway | Down | Absent
    pct: float                        # 0.0 - 1.0 (percentage of segment)

@dataclass
class ExpressionAnalysis:
    frustration_mean: float           # 0.0 - 1.0
    valence_mean: float               # -1.0 to 1.0
    arousal_mean: float               # 0.0 - 1.0

@dataclass
class KPIs:
    focus_ratio: float                # 0.0 - 1.0
    avg_focus_bout_min: float         # Average focused period duration
    num_alerts: int                   # Total distraction alerts
    top_triggers: List[str]           # Most common distraction types
    peak_distraction_hour: str        # e.g. "15:00-16:00"

@dataclass
class Recommendation:
    rec_type: str                     # BreakSchedule | AppBlock | TaskSplit | Ergonomics
    message: str                      # Human-readable recommendation
    priority: int                     # 1 (high) to 5 (low)

@dataclass
class Artifacts:
    memories_urls: Dict[str, str]     # {cam: url, screen: url}
    hume_job_id: Optional[str]        # Hume API job ID
```

---

## Module Interfaces

### 1. core/config.py

```python
class Config:
    """Configuration manager with developer settings"""

    def __init__(self, config_path: str = "config/default_config.json"):
        """Load configuration from multiple sources"""
        pass

    # Core settings
    def get_snapshot_interval_sec(self) -> int:
        """Default: 60, min: 10"""
        pass

    def get_video_bitrate_kbps_cam(self) -> int:
        """Get cam video bitrate based on profile"""
        pass

    def get_video_bitrate_kbps_screen(self) -> int:
        """Get screen video bitrate based on profile"""
        pass

    def get_video_res_profile(self) -> QualityProfile:
        """Get quality profile: Low | Std | High"""
        pass

    def get_max_parallel_uploads(self) -> int:
        """Default: 3"""
        pass

    def is_openai_vision_enabled(self) -> bool:
        """Default: True"""
        pass

    # API keys
    def get_openai_api_key(self) -> str:
        """Get encrypted OpenAI API key"""
        pass

    def get_hume_api_key(self) -> Optional[str]:
        """Get Hume AI API key if configured"""
        pass

    def get_memories_api_key(self) -> Optional[str]:
        """Get Memories.ai API key if configured"""
        pass

    # Paths
    def get_data_dir(self) -> Path:
        """Get data directory path"""
        pass

    def get_sessions_dir(self) -> Path:
        """Get sessions directory path"""
        pass

    # Save configuration
    def save_developer_settings(self, settings: Dict[str, Any]) -> None:
        """Save developer settings to config.yaml"""
        pass
```

### 2. core/database.py

```python
class Database:
    """SQLite database interface with schema v1.3"""

    def __init__(self, db_path: str):
        """Initialize database connection"""
        pass

    # Session operations
    def create_session(self, session: Session) -> str:
        """Create new session, return session_id"""
        pass

    def update_session_status(self, session_id: str, status: SessionStatus) -> None:
        """Update session status"""
        pass

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        pass

    def end_session(self, session_id: str, ended_at: datetime) -> None:
        """Mark session as completed"""
        pass

    # Snapshot operations
    def insert_snapshot(self, snapshot: Snapshot) -> str:
        """Insert snapshot record, return snapshot_id"""
        pass

    def update_snapshot_vision_results(
        self,
        snapshot_id: str,
        vision_labels: Dict[str, float],
        vision_json_path: str,
        processed_at: datetime
    ) -> None:
        """Update snapshot with vision API results"""
        pass

    def update_snapshot_upload_status(
        self,
        snapshot_id: str,
        status: UploadStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update snapshot upload status"""
        pass

    # Event operations
    def insert_distraction_event(self, event: DistractionEvent) -> str:
        """Insert distraction event, return event_id"""
        pass

    def acknowledge_event(self, event_id: str, acknowledged_at: datetime) -> None:
        """Mark event as acknowledged by user"""
        pass

    def get_session_events(self, session_id: str) -> List[DistractionEvent]:
        """Get all events for session"""
        pass

    # Report operations
    def store_session_report(self, session_id: str, report: SessionReport) -> None:
        """Store complete session report"""
        pass

    def get_session_report(self, session_id: str) -> Optional[SessionReport]:
        """Retrieve session report"""
        pass
```

### 3. core/state_machine.py

```python
class StateMachine:
    """Snapshot hysteresis fusion state machine"""

    def __init__(self, K: int = 3, min_span_minutes: float = 1.0):
        """
        Args:
            K: Number of snapshots for hysteresis voting
            min_span_minutes: Minimum time span across K snapshots for debounce
        """
        pass

    def update(self, snapshot_result: SnapshotResult) -> Optional[StateTransition]:
        """
        Process new snapshot result

        Returns:
            StateTransition if state changed, None otherwise
        """
        pass

    def get_current_state(self) -> FocusState:
        """Get current state with confidence"""
        pass

    def reset(self) -> None:
        """Reset state machine"""
        pass

@dataclass
class StateTransition:
    from_state: State
    to_state: State
    timestamp: datetime
    confidence: float
    evidence: Dict[str, Any]  # Vision votes and reasoning
```

### 4. capture/snapshot_scheduler.py

```python
class SnapshotScheduler:
    """Wall-clock based snapshot capture scheduler"""

    def __init__(
        self,
        session_id: str,
        interval_sec: int,
        snapshots_dir: Path,
        upload_queue: Queue[SnapshotPair]
    ):
        """
        Args:
            session_id: Current session ID
            interval_sec: Snapshot interval (default 60)
            snapshots_dir: Directory to save snapshots
            upload_queue: Queue to send snapshots for upload
        """
        pass

    def start(self) -> None:
        """Start scheduler in background thread"""
        pass

    def stop(self) -> None:
        """Stop scheduler and wait for completion"""
        pass

    def pause(self) -> None:
        """Pause snapshot capture"""
        pass

    def resume(self) -> None:
        """Resume snapshot capture"""
        pass

    def get_stats(self) -> SchedulerStats:
        """Get scheduler statistics"""
        pass

@dataclass
class SnapshotPair:
    cam_snapshot: Path       # Path to cam JPEG
    screen_snapshot: Optional[Path]  # Path to screen JPEG (if enabled)
    timestamp: datetime
    session_id: str

@dataclass
class SchedulerStats:
    total_captured: int
    last_capture_time: datetime
    next_capture_time: datetime
    is_running: bool
    is_paused: bool
```

### 5. capture/snapshot_uploader.py

```python
class SnapshotUploader:
    """Worker pool for uploading snapshots to OpenAI Vision API"""

    def __init__(
        self,
        num_workers: int,
        upload_queue: Queue[SnapshotPair],
        fusion_queue: Queue[FusionMessage],
        vision_client: OpenAIVisionClient,
        database: Database
    ):
        """
        Args:
            num_workers: Number of parallel upload workers
            upload_queue: Queue of snapshots to upload
            fusion_queue: Queue to send results to fusion engine
            vision_client: OpenAI Vision API client
            database: Database for logging results
        """
        pass

    def start(self) -> None:
        """Start worker pool"""
        pass

    def stop(self) -> None:
        """Stop workers and wait for completion"""
        pass

    def wait_for_completion(self) -> None:
        """Block until upload queue is empty"""
        pass

    def get_stats(self) -> UploaderStats:
        """Get uploader statistics"""
        pass

@dataclass
class UploaderStats:
    total_uploaded: int
    total_failed: int
    queue_size: int
    active_workers: int
```

### 6. integrations/openai_vision_client.py

```python
class OpenAIVisionClient:
    """OpenAI Vision API client for snapshot classification"""

    def __init__(self, api_key: str, timeout_sec: int = 30):
        """
        Args:
            api_key: OpenAI API key
            timeout_sec: Request timeout
        """
        pass

    def classify_cam_snapshot(
        self,
        image_path: Path
    ) -> VisionResult:
        """
        Classify webcam snapshot

        Returns:
            VisionResult with labels and confidences

        Raises:
            VisionAPIError: If API call fails
            RateLimitError: If rate limited (429)
        """
        pass

    def classify_screen_snapshot(
        self,
        image_path: Path
    ) -> VisionResult:
        """
        Classify screen snapshot

        Returns:
            VisionResult with labels and confidences

        Raises:
            VisionAPIError: If API call fails
            RateLimitError: If rate limited (429)
        """
        pass

    def batch_classify(
        self,
        cam_path: Path,
        screen_path: Optional[Path]
    ) -> Tuple[VisionResult, Optional[VisionResult]]:
        """Classify both snapshots (more efficient)"""
        pass

@dataclass
class VisionResult:
    labels: Dict[str, float]  # {label: confidence}
    raw_response: Dict[str, Any]  # Full API response
    processed_at: datetime
    latency_ms: float

# Detection classes - CANONICAL TAXONOMY (defined in prd.md)
# ALL code must use these exact labels
CAM_LABELS = {
    "HeadAway",        # Head turned >45° from screen
    "EyesOffScreen",   # Gaze not directed at screen
    "Absent",          # No person visible in frame
    "MicroSleep",      # Eyes closed, drowsy appearance
    "PhoneLikely",     # Phone visible in hand or being viewed
    "Focused"          # Engaged posture, eyes on screen (positive class)
}

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
```

### 7. analysis/fusion_engine.py

```python
class FusionEngine:
    """Snapshot hysteresis fusion engine"""

    def __init__(
        self,
        state_machine: StateMachine,
        fusion_queue: Queue[FusionMessage],
        event_queue: Queue[EventMessage],
        db_queue: Queue[DBMessage]
    ):
        pass

    def start(self) -> None:
        """Start fusion thread"""
        pass

    def stop(self) -> None:
        """Stop fusion thread"""
        pass

    def process_snapshot_result(
        self,
        snapshot_id: str,
        cam_result: VisionResult,
        screen_result: Optional[VisionResult]
    ) -> None:
        """
        Process snapshot classification results

        Applies hysteresis voting over last K snapshots
        Emits state transitions to event queue
        """
        pass

@dataclass
class FusionMessage:
    snapshot_id: str
    session_id: str
    timestamp: datetime
    cam_result: VisionResult
    screen_result: Optional[VisionResult]
```

### 8. analysis/distraction_detector.py

```python
class DistractionDetector:
    """Snapshot-based distraction detection with business rules"""

    def __init__(
        self,
        event_queue: Queue[EventMessage],
        db_queue: Queue[DBMessage],
        ui_queue: Queue[UIMessage]
    ):
        pass

    def on_state_transition(self, transition: StateTransition) -> None:
        """
        Handle state machine transition

        Applies business rules:
        - ≥N distract events in 20 min → micro-break alert
        - Screen ∈ {Video, Social, Games} ≥2 consecutive → prompt
        - Cam {HeadAway, MicroSleep} dominate → ergonomic alert
        """
        pass

    def on_distraction_confirmed(
        self,
        distraction_type: DistractionType,
        duration: timedelta,
        vision_votes: Dict[str, int],
        snapshot_refs: List[str]
    ) -> None:
        """Emit distraction event to UI and database"""
        pass
```

### 9. session/session_manager.py

```python
class SessionManager:
    """Orchestrates entire session lifecycle"""

    def __init__(
        self,
        config: Config,
        database: Database,
        queue_manager: QueueManager
    ):
        pass

    def start_session(
        self,
        task_name: str,
        quality_profile: QualityProfile,
        screen_enabled: bool
    ) -> str:
        """
        Start new session

        Returns:
            session_id

        Steps:
        1. Create session record in DB
        2. Create session folder structure
        3. Start video recorders (cam.mp4, screen.mp4)
        4. Start snapshot scheduler
        5. Start snapshot uploader worker pool
        6. Start fusion engine
        """
        pass

    def pause_session(self) -> None:
        """Pause current session"""
        pass

    def resume_session(self) -> None:
        """Resume paused session"""
        pass

    def end_session(self) -> SessionReport:
        """
        End current session and generate report

        Returns:
            SessionReport

        Steps:
        1. Stop snapshot scheduler
        2. Wait for all uploads to complete
        3. Stop video recorders
        4. Generate session report
        5. Trigger optional cloud upload
        6. Return final report
        """
        pass

    def get_current_session(self) -> Optional[Session]:
        """Get current active session"""
        pass
```

### 10. session/report_generator.py

```python
class ReportGenerator:
    """Generate session reports with schema v1.3"""

    def __init__(
        self,
        database: Database,
        memories_client: Optional[MemoriesClient],
        hume_client: Optional[HumeClient]
    ):
        pass

    def generate(self, session_id: str) -> SessionReport:
        """
        Generate session report from local data

        Steps:
        1. Query all snapshots and events from DB
        2. Compute segments based on state transitions
        3. Calculate KPIs
        4. Generate recommendations
        5. Return SessionReport
        """
        pass

    def merge_cloud_data(
        self,
        base_report: SessionReport,
        memories_data: Optional[Dict],
        hume_data: Optional[Dict]
    ) -> SessionReport:
        """
        Merge cloud analysis with local report

        Reconciles:
        - Realtime OpenAI Vision snapshot results
        - Post-hoc Memories.ai VLM analysis
        - Hume AI emotion timeline
        """
        pass

    def reconcile_multi_source_analysis(
        self,
        openai_results: List[SnapshotResult],
        memories_data: Optional[Dict],
        hume_data: Optional[Dict]
    ) -> ReconciledAnalysis:
        """
        Reconcile conflicting analyses from multiple sources

        Data sources priority:
        1. Realtime OpenAI Vision (70% weight) - ground truth at capture time
        2. Post-hoc Memories.ai VLM (20% weight) - holistic video understanding
        3. Hume AI emotions (10% weight) - affective context

        Returns:
            ReconciledAnalysis with merged labels and confidence
        """
        pass
```

### Post-Processing Reconciliation

**Purpose**: Merge realtime OpenAI Vision snapshot results with post-hoc Memories.ai and Hume AI analysis to improve report accuracy

#### Data Source Characteristics

| Source | Timing | Granularity | Strength | Weakness |
|--------|--------|-------------|----------|----------|
| OpenAI Vision | Realtime (60s) | Per-snapshot | Fast, low latency | No temporal context |
| Memories.ai VLM | Post-hoc (after session) | Full video | Temporal relationships, scene understanding | High latency, cost |
| Hume AI Expression | Post-hoc (after session) | Per-frame (1Hz+) | Emotion accuracy | No screen context |

#### Reconciliation Algorithm

```python
class ReconciliationEngine:
    """Merge analyses from OpenAI, Memories.ai, and Hume AI"""

    def __init__(
        self,
        openai_weight: float = 0.7,
        memories_weight: float = 0.2,
        hume_weight: float = 0.1
    ):
        """
        Args:
            openai_weight: Weight for realtime OpenAI results
            memories_weight: Weight for post-hoc Memories.ai analysis
            hume_weight: Weight for Hume AI emotions
        """
        self.weights = {
            "openai": openai_weight,
            "memories": memories_weight,
            "hume": hume_weight
        }

    def reconcile_segment(
        self,
        segment_start: float,  # Session-relative seconds
        segment_end: float,
        openai_snapshots: List[SnapshotResult],
        memories_segment: Optional[Dict],
        hume_segment: Optional[Dict]
    ) -> ReconciledSegment:
        """
        Reconcile single segment across all data sources

        Strategy:
        1. Start with OpenAI labels (70% baseline)
        2. Adjust based on Memories.ai temporal context
        3. Overlay Hume AI emotions
        4. Resolve conflicts with voting
        """

        # 1. Aggregate OpenAI labels across segment
        openai_labels = self._aggregate_snapshot_labels(openai_snapshots)

        # 2. Get Memories.ai labels (if available)
        memories_labels = {}
        if memories_segment:
            memories_labels = self._extract_memories_labels(memories_segment)

        # 3. Get Hume AI emotions (if available)
        hume_emotions = {}
        if hume_segment:
            hume_emotions = self._extract_hume_emotions(hume_segment)

        # 4. Weighted merge
        merged_labels = self._weighted_merge(
            openai_labels=openai_labels,
            memories_labels=memories_labels,
            hume_emotions=hume_emotions
        )

        # 5. Conflict resolution
        final_labels = self._resolve_conflicts(merged_labels)

        return ReconciledSegment(
            start_time=segment_start,
            end_time=segment_end,
            labels=final_labels,
            confidence=self._compute_confidence(merged_labels),
            sources_used=self._get_sources_used(openai_snapshots, memories_segment, hume_segment)
        )

    def _aggregate_snapshot_labels(
        self,
        snapshots: List[SnapshotResult]
    ) -> Dict[str, float]:
        """
        Aggregate OpenAI labels across multiple snapshots

        Returns:
            Dict[label, avg_confidence]
        """
        label_sums = {}
        label_counts = {}

        for snapshot in snapshots:
            for cam_label, conf in snapshot.cam_labels.items():
                label_sums[cam_label] = label_sums.get(cam_label, 0) + conf
                label_counts[cam_label] = label_counts.get(cam_label, 0) + 1

            for screen_label, conf in snapshot.screen_labels.items():
                label_sums[screen_label] = label_sums.get(screen_label, 0) + conf
                label_counts[screen_label] = label_counts.get(screen_label, 0) + 1

        # Average confidences
        return {
            label: label_sums[label] / label_counts[label]
            for label in label_sums
        }

    def _extract_memories_labels(self, memories_segment: Dict) -> Dict[str, float]:
        """
        Extract labels from Memories.ai VLM response

        Memories.ai provides:
        - Scene descriptions
        - Activity classifications
        - Temporal relationships
        """
        # Parse Memories.ai chat response
        # Example: "User was coding in VS Code, then switched to watching YouTube video"

        labels = {}

        description = memories_segment.get("description", "").lower()

        # Heuristic mapping from Memories.ai text to our labels
        if "coding" in description or "programming" in description:
            labels["Code"] = 0.9
        if "youtube" in description or "watching video" in description:
            labels["VideoOnScreen"] = 0.9
        if "distracted" in description:
            labels["HeadAway"] = 0.7
        # ... more mappings

        return labels

    def _extract_hume_emotions(self, hume_segment: Dict) -> Dict[str, float]:
        """
        Extract emotions from Hume AI Expression API

        Hume provides:
        - 53 emotion predictions
        - Valence/arousal scores
        - Facial expression analysis
        """
        emotions = {}

        # Map Hume emotions to our focus/distraction indicators
        frustration = hume_segment.get("frustration", 0.0)
        boredom = hume_segment.get("boredom", 0.0)
        concentration = hume_segment.get("concentration", 0.0)

        if frustration > 0.6:
            emotions["frustration_indicator"] = frustration
        if boredom > 0.5:
            emotions["boredom_indicator"] = boredom
        if concentration > 0.7:
            emotions["focus_indicator"] = concentration

        return emotions

    def _weighted_merge(
        self,
        openai_labels: Dict[str, float],
        memories_labels: Dict[str, float],
        hume_emotions: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Merge labels with weighted average

        Returns:
            Dict[label, weighted_confidence]
        """
        merged = {}

        # Start with OpenAI labels (highest weight)
        for label, conf in openai_labels.items():
            merged[label] = conf * self.weights["openai"]

        # Add Memories.ai labels
        for label, conf in memories_labels.items():
            existing = merged.get(label, 0.0)
            merged[label] = existing + (conf * self.weights["memories"])

        # Overlay Hume emotions (modify confidence)
        for emotion, value in hume_emotions.items():
            if emotion == "frustration_indicator":
                # Increase distraction confidence
                for distraction_label in ["HeadAway", "EyesOffScreen"]:
                    if distraction_label in merged:
                        merged[distraction_label] *= 1.2  # 20% boost
            elif emotion == "focus_indicator":
                # Increase focus confidence
                if "Focused" in merged:
                    merged["Focused"] *= 1.2

        # Normalize to 0-1 range
        for label in merged:
            merged[label] = min(1.0, merged[label])

        return merged

    def _resolve_conflicts(self, merged_labels: Dict[str, float]) -> Dict[str, float]:
        """
        Resolve conflicting labels

        Conflicts:
        - Focused + Distracted labels both high
        - Multiple distraction types competing
        """
        # Conflict 1: Focused vs Distracted
        focused_conf = merged_labels.get("Focused", 0.0)
        distraction_labels = ["HeadAway", "EyesOffScreen", "PhoneLikely", "VideoOnScreen"]
        max_distraction = max([merged_labels.get(l, 0.0) for l in distraction_labels])

        if focused_conf > 0.5 and max_distraction > 0.5:
            # Conflict: trust higher confidence
            if focused_conf > max_distraction:
                # Reduce distraction confidences
                for label in distraction_labels:
                    if label in merged_labels:
                        merged_labels[label] *= 0.5
            else:
                # Reduce focus confidence
                merged_labels["Focused"] *= 0.5

        return merged_labels

    def _compute_confidence(self, merged_labels: Dict[str, float]) -> float:
        """
        Compute overall confidence in reconciled result

        High confidence when:
        - All sources agree
        - High label confidences
        - No conflicts

        Low confidence when:
        - Sources disagree
        - Many conflicts resolved
        - Sparse data
        """
        if not merged_labels:
            return 0.0

        # Average of top 3 label confidences
        top_confs = sorted(merged_labels.values(), reverse=True)[:3]
        return sum(top_confs) / len(top_confs) if top_confs else 0.0

    def _get_sources_used(
        self,
        openai_snapshots: List,
        memories_segment: Optional[Dict],
        hume_segment: Optional[Dict]
    ) -> List[str]:
        """Track which data sources were used"""
        sources = []
        if openai_snapshots:
            sources.append("openai")
        if memories_segment:
            sources.append("memories")
        if hume_segment:
            sources.append("hume")
        return sources

@dataclass
class ReconciledSegment:
    start_time: float
    end_time: float
    labels: Dict[str, float]
    confidence: float
    sources_used: List[str]
```

#### Conflict Resolution Rules

**Rule 1: Temporal Context Beats Snapshots**
```python
# If Memories.ai indicates extended focused period
# but OpenAI snapshots show occasional distraction
# → Trust Memories.ai for segment label
# → Keep OpenAI for individual distraction events

if memories_says_focused and openai_shows_brief_distraction:
    segment_label = "Focus"
    include_brief_distraction_event = True
```

**Rule 2: Emotion Modulates Confidence**
```python
# Hume AI frustration increases distraction likelihood
# Hume AI concentration increases focus likelihood

if hume_frustration > 0.6:
    distraction_confidence *= 1.2

if hume_concentration > 0.7:
    focus_confidence *= 1.2
```

**Rule 3: Source Agreement Priority**
```python
# All 3 sources agree → High confidence (0.9)
# 2 sources agree → Medium confidence (0.7)
# No agreement → Low confidence (0.4), trust OpenAI (realtime)

confidence_map = {
    3: 0.9,  # All agree
    2: 0.7,  # Majority
    1: 0.4,  # Conflict
    0: 0.2   # No data
}
```

**Rule 4: Screen Takes Priority for Distraction Type**
```python
# If cam shows HeadAway
# but screen shows VideoOnScreen
# → Distraction type = VideoOnScreen (more specific)

if cam_distraction and screen_distraction:
    distraction_type = screen_distraction  # Screen more informative
```

---

## Configuration Specification

### config/default_config.json

```json
{
  "version": "1.3",
  "app": {
    "name": "Focus Guardian",
    "data_dir": "data",
    "log_level": "INFO"
  },
  "session": {
    "default_quality_profile": "Std",
    "default_screen_enabled": true,
    "auto_delete_recordings": false,
    "retention_days": 7
  },
  "snapshot": {
    "interval_sec": 60,
    "min_interval_sec": 10,
    "jpeg_quality": 85,
    "adaptive_quality": true
  },
  "video": {
    "profiles": {
      "Low": {
        "resolution": "256p",
        "fps": 10,
        "bitrate_kbps_cam": 200,
        "bitrate_kbps_screen": 300
      },
      "Std": {
        "resolution": "480p",
        "fps": 15,
        "bitrate_kbps_cam": 500,
        "bitrate_kbps_screen": 800
      },
      "High": {
        "resolution": "720p",
        "fps": 15,
        "bitrate_kbps_cam": 1000,
        "bitrate_kbps_screen": 1500
      }
    }
  },
  "fusion": {
    "K": 3,
    "min_span_minutes": 1.0,
    "confidence_threshold": 0.7
  },
  "upload": {
    "max_parallel_uploads": 3,
    "retry_max_attempts": 3,
    "retry_backoff_sec": [1, 5, 15],
    "timeout_sec": 30
  },
  "bandwidth": {
    "cap_mb_per_session": 500,
    "adaptive_jpeg_enabled": true
  }
}
```

### config.yaml (Developer Settings)

```yaml
# Developer-only settings (not exposed to end users)
developer:
  # Snapshot settings
  SNAPSHOT_INTERVAL_SEC: 60

  # Video encoding
  VIDEO_BITRATE_KBPS_CAM: 500
  VIDEO_BITRATE_KBPS_SCREEN: 800
  VIDEO_RES_PROFILE: "Std"  # Low | Std | High

  # API toggles
  OPENAI_VISION_ENABLED: true

  # Upload settings
  MAX_PARALLEL_UPLOADS: 3

  # Performance
  CPU_THROTTLE_THRESHOLD: 80
  DISK_SPACE_MIN_GB: 1.0

  # Debug
  DEBUG_MODE: false
  SAVE_RAW_API_RESPONSES: false
```

### .env (API Keys)

```bash
# OpenAI API
OPENAI_API_KEY=sk-...

# Hume AI (optional)
HUME_API_KEY=...

# Memories.ai (optional)
MEM_AI_API_KEY=...

# Optional backend
BACKEND_URL=https://api.focusguardian.com
BACKEND_API_KEY=...
```

### Configuration Precedence and Merging

#### Precedence Rules

**Configuration Source Priority (highest to lowest):**

| Priority | Source | Use Case | Modifiable at Runtime |
|----------|--------|----------|----------------------|
| 1 (Highest) | Runtime Overrides | Developer console, CLI flags | Yes |
| 2 | .env | API keys, secrets | No |
| 3 | config.yaml | Developer settings | Partial |
| 4 (Lowest) | default_config.json | Defaults | No |

```python
class ConfigManager:
    """
    Manage configuration from multiple sources with precedence

    Loading order:
    1. Load default_config.json (base)
    2. Merge config.yaml (developer overrides)
    3. Merge .env (API keys)
    4. Apply runtime overrides (if any)
    """

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config = {}
        self.runtime_overrides = {}
        self._load_all_sources()

    def _load_all_sources(self):
        """Load and merge all configuration sources"""

        # 1. Load defaults (base layer)
        default_path = self.config_dir / "default_config.json"
        with open(default_path, 'r') as f:
            self.config = json.load(f)

        # 2. Merge developer settings (if exists)
        yaml_path = self.config_dir / "config.yaml"
        if yaml_path.exists():
            with open(yaml_path, 'r') as f:
                dev_config = yaml.safe_load(f)

            # Deep merge developer settings
            if dev_config and 'developer' in dev_config:
                self._deep_merge(self.config, dev_config['developer'])

        # 3. Load environment variables (API keys)
        load_dotenv()
        env_overrides = {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'hume_api_key': os.getenv('HUME_API_KEY'),
            'memories_api_key': os.getenv('MEM_AI_API_KEY')
        }
        # Filter None values
        env_overrides = {k: v for k, v in env_overrides.items() if v is not None}
        self.config.update(env_overrides)

        # 4. Apply runtime overrides (initially empty)
        self.config.update(self.runtime_overrides)

    def _deep_merge(self, base: Dict, override: Dict):
        """
        Deep merge override dict into base dict

        Strategy:
        - Scalars: override replaces base
        - Lists: override replaces base (NOT append)
        - Dicts: recursive merge
        """
        for key, value in override.items():
            if key in base:
                if isinstance(base[key], dict) and isinstance(value, dict):
                    # Recursive merge for nested dicts
                    self._deep_merge(base[key], value)
                else:
                    # Override replaces base (scalars and lists)
                    base[key] = value
            else:
                # New key, add to base
                base[key] = value

    def set_runtime_override(self, key: str, value: Any):
        """
        Set runtime configuration override

        Overrides persist for session, NOT saved to disk

        Args:
            key: Configuration key (dot notation: snapshot.interval_sec)
            value: New value
        """
        # Parse dot notation
        keys = key.split('.')

        # Store in runtime overrides
        self.runtime_overrides[key] = value

        # Apply to config
        current = self.config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

        logging.info(f"Runtime override: {key} = {value}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with dot notation

        Args:
            key: Configuration key (dot notation: snapshot.interval_sec)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        current = self.config

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current
```

#### Merge Behavior Examples

**Example 1: Simple Override**
```python
# default_config.json
{
  "snapshot": {
    "interval_sec": 60,
    "jpeg_quality": 85
  }
}

# config.yaml
developer:
  snapshot:
    interval_sec: 30  # Override

# Result after merge:
{
  "snapshot": {
    "interval_sec": 30,      # From config.yaml
    "jpeg_quality": 85       # From default_config.json
  }
}
```

**Example 2: Nested Dict Merge**
```python
# default_config.json
{
  "video": {
    "profiles": {
      "Std": {
        "resolution": "480p",
        "fps": 15,
        "bitrate_kbps_cam": 500
      }
    }
  }
}

# config.yaml
developer:
  video:
    profiles:
      Std:
        fps: 10  # Override just FPS

# Result after merge:
{
  "video": {
    "profiles": {
      "Std": {
        "resolution": "480p",          # Preserved
        "fps": 10,                     # Overridden
        "bitrate_kbps_cam": 500        # Preserved
      }
    }
  }
}
```

**Example 3: List Replacement (NOT Append)**
```python
# default_config.json
{
  "upload": {
    "retry_backoff_sec": [1, 5, 15]
  }
}

# config.yaml
developer:
  upload:
    retry_backoff_sec: [2, 10]  # Replace entire list

# Result after merge:
{
  "upload": {
    "retry_backoff_sec": [2, 10]  # Replaced, not appended
  }
}
```

#### Runtime Modifiable Settings

**Settings that can be changed during session:**
```python
# Allow runtime modification for these settings
RUNTIME_MODIFIABLE = {
    "snapshot.interval_sec",           # Change snapshot frequency
    "snapshot.jpeg_quality",           # Adjust quality
    "upload.max_parallel_uploads",     # Scale workers
    "fusion.confidence_threshold",     # Tune sensitivity
    "developer.DEBUG_MODE",            # Toggle debugging
}

# Settings that CANNOT be changed at runtime (require restart)
RESTART_REQUIRED = {
    "video.profiles.Std.resolution",   # Video encoder config
    "app.data_dir",                    # Paths
    "openai_api_key",                  # API credentials
}

def validate_runtime_override(key: str) -> bool:
    """Check if setting can be changed at runtime"""
    if key in RUNTIME_MODIFIABLE:
        return True
    elif key in RESTART_REQUIRED:
        logging.error(
            f"Setting '{key}' requires application restart"
        )
        return False
    else:
        # Unknown setting, allow but warn
        logging.warning(
            f"Unknown setting '{key}', applying anyway"
        )
        return True
```

#### Validation and Conflicts

```python
class ConfigValidator:
    """Validate configuration for conflicts and invalid values"""

    @staticmethod
    def validate_all(config: Dict) -> List[str]:
        """
        Validate entire configuration

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate snapshot interval
        interval = config.get('snapshot', {}).get('interval_sec', 60)
        if interval < 10:
            errors.append(
                f"snapshot.interval_sec must be >= 10 (got {interval})"
            )

        # Validate worker count vs rate limit
        workers = config.get('upload', {}).get('max_parallel_uploads', 3)
        if workers > 10:
            errors.append(
                f"upload.max_parallel_uploads should be <= 10 "
                f"to avoid rate limits (got {workers})"
            )

        # Validate quality profiles
        profiles = config.get('video', {}).get('profiles', {})
        for name, profile in profiles.items():
            fps = profile.get('fps', 15)
            if fps < 5 or fps > 30:
                errors.append(
                    f"video.profiles.{name}.fps must be 5-30 (got {fps})"
                )

        # Validate API keys present
        if not config.get('openai_api_key'):
            errors.append("OPENAI_API_KEY not set in .env")

        return errors

    @staticmethod
    def check_conflicts(config: Dict) -> List[str]:
        """
        Check for conflicting settings

        Returns:
            List of conflict warnings
        """
        conflicts = []

        # Conflict: High worker count with low interval
        interval = config.get('snapshot', {}).get('interval_sec', 60)
        workers = config.get('upload', {}).get('max_parallel_uploads', 3)

        if interval < 30 and workers > 5:
            conflicts.append(
                f"High worker count ({workers}) with low interval ({interval}s) "
                f"may exceed API rate limits"
            )

        # Conflict: High JPEG quality with high FPS
        jpeg_quality = config.get('snapshot', {}).get('jpeg_quality', 85)
        fps = config.get('video', {}).get('profiles', {}).get('Std', {}).get('fps', 15)

        if jpeg_quality > 90 and fps > 20:
            conflicts.append(
                f"High JPEG quality ({jpeg_quality}) with high FPS ({fps}) "
                f"will consume excessive bandwidth"
            )

        return conflicts
```

---

## Queue Message Formats

### SnapshotUploadQueue

```python
@dataclass
class SnapshotUploadMessage:
    snapshot_pair: SnapshotPair
    priority: int = 0  # Higher = more urgent
```

### FusionQueue

```python
@dataclass
class FusionMessage:
    snapshot_id: str
    session_id: str
    timestamp: datetime
    cam_result: VisionResult
    screen_result: Optional[VisionResult]
```

### EventQueue (to UI)

```python
@dataclass
class EventMessage:
    event_type: EventType
    payload: Dict[str, Any]
    timestamp: datetime

class EventType(Enum):
    STATE_CHANGED = "state_changed"
    DISTRACTION_DETECTED = "distraction_detected"
    FOCUS_RESTORED = "focus_restored"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    SNAPSHOT_CAPTURED = "snapshot_captured"
    UPLOAD_PROGRESS = "upload_progress"
    ERROR = "error"
```

### DBQueue

```python
@dataclass
class DBMessage:
    operation: DBOperation
    payload: Dict[str, Any]

class DBOperation(Enum):
    INSERT_SNAPSHOT = "insert_snapshot"
    UPDATE_SNAPSHOT_VISION = "update_snapshot_vision"
    UPDATE_SNAPSHOT_STATUS = "update_snapshot_status"
    INSERT_EVENT = "insert_event"
    UPDATE_SESSION = "update_session"
```

### UIQueue

```python
@dataclass
class UIMessage:
    ui_action: UIAction
    data: Dict[str, Any]
    timestamp: datetime

class UIAction(Enum):
    SHOW_ALERT = "show_alert"
    UPDATE_STATUS = "update_status"
    UPDATE_PROGRESS = "update_progress"
    SHOW_NOTIFICATION = "show_notification"
    UPDATE_DASHBOARD = "update_dashboard"
```

---

## State Machine Specification

### State Definitions

```python
class State(Enum):
    FOCUSED = "focused"      # User actively working on task
    DISTRACTED = "distracted"  # User off-task or distracted
    BREAK = "break"          # Intentional break (paused)
    ABSENT = "absent"        # User not present
```

### Label Categories

```python
# Label taxonomy grouped by meaning (CANONICAL - from prd.md)
# These match the exact categories defined in the PRD Detection Label Taxonomy section

CAM_DISTRACTION_LABELS = {
    "HeadAway",      # Head turned >45° from screen
    "EyesOffScreen", # Gaze not directed at screen
    "MicroSleep",    # Eyes closed, drowsy appearance
    "PhoneLikely"    # Phone visible in hand or being viewed
}

CAM_FOCUS_LABELS = {
    "Focused"  # Engaged posture, eyes on screen
}

CAM_ABSENCE_LABELS = {
    "Absent"  # No person visible in frame
}

SCREEN_DISTRACTION_LABELS = {
    "VideoOnScreen",  # Video player or streaming content
    "SocialFeed",     # Social media feed scrolling
    "Games",          # Gaming applications
    "ChatWindow"      # Chat/messaging applications
}

SCREEN_FOCUS_LABELS = {
    "Code",      # Code editor or IDE
    "Docs",      # Documentation, technical reading
    "Reading",   # Long-form focused reading
    "Slides",    # Presentation software
    "Terminal"   # Command line terminal
}

SCREEN_BORDERLINE_LABELS = {
    # Context-dependent: could be work or distraction
    # Treat as neutral by default, let cam + context decide
    "Email",             # Inbox processing = focus, frequent checking = distraction
    "VideoCall",         # Work meeting = focus, social call = distraction
    "MultipleMonitors"   # Single focus window = acceptable, rapid switching = distraction
}

SCREEN_NEUTRAL_LABELS = {
    "Unknown"  # Cannot determine, maintain previous state
}

# Label hierarchy for disambiguation
LABEL_HIERARCHY = {
    # Child labels inherit parent category
    "Email": {
        "parent": "neutral",  # Default neutral
        "focus_keywords": ["inbox zero", "email processing", "compose"],
        "distraction_keywords": ["notification", "quick check"]
    },
    "VideoCall": {
        "parent": "neutral",  # Default neutral
        "focus_indicators": ["screen share", "presentation mode"],
        "distraction_indicators": ["social call", "casual chat"]
    },
    "MultipleMonitors": {
        "parent": "distraction",  # Default distraction
        "focus_exception": "If one window is Code/Docs/Terminal and others minimized"
    }
}
```

### Transition Rules

```python
# Hysteresis voting logic with detailed edge case handling
def compute_state_from_snapshots(
    buffer: List[SnapshotResult],
    current_state: State,
    K: int = 3,
    min_span_minutes: float = 1.0
) -> Tuple[State, float, Dict[str, int]]:
    """
    Vote across last K snapshots to determine state

    Args:
        buffer: Last K snapshot results (ordered oldest to newest)
        current_state: Previous state (used for tie-breaking)
        K: Number of snapshots to vote across (default 3)
        min_span_minutes: Minimum time span required (default 1.0)

    Returns:
        Tuple[State, confidence, vision_votes]
        - State: New state (or current_state if unchanged)
        - confidence: 0.0-1.0 confidence in decision
        - vision_votes: {label: count} across K snapshots

    Algorithm:
        1. Check buffer size: if len(buffer) < K, use partial buffer logic
        2. Check time span: if span < min_span_minutes, maintain current_state
        3. Aggregate label votes across snapshots (both cam and screen)
        4. Categorize votes into distraction/focus/absent groups
        5. Apply voting rules with tie-breaking

    Voting Rules (for K=3):
        - ABSENT: If ≥2 snapshots have cam "Absent" as primary → ABSENT
        - DISTRACTED: If ≥2 snapshots have distraction labels as primary → DISTRACTED
        - FOCUSED: If ≥2 snapshots have focus labels as primary → FOCUSED
        - Tie-breaking: If no category has ≥2 votes, maintain current_state

    Primary Label Selection (per snapshot):
        - Cam primary: Highest confidence cam label
        - Screen primary: Highest confidence screen label
        - If cam primary ∈ CAM_DISTRACTION_LABELS OR screen primary ∈ SCREEN_DISTRACTION_LABELS
          → snapshot votes for DISTRACTED
        - If cam primary ∈ CAM_ABSENCE_LABELS → snapshot votes for ABSENT
        - If cam primary ∈ CAM_FOCUS_LABELS AND screen primary ∈ SCREEN_FOCUS_LABELS
          → snapshot votes for FOCUSED
        - Otherwise: snapshot is neutral (maintain previous state)
    """

    # Edge case: empty buffer
    if not buffer:
        return current_state, 0.0, {}

    # Edge case: partial buffer (first K-1 snapshots)
    if len(buffer) < K:
        return compute_partial_buffer_state(buffer, current_state)

    # Check time span constraint
    span_minutes = (buffer[-1].timestamp - buffer[0].timestamp).total_seconds() / 60.0
    if span_minutes < min_span_minutes:
        # Insufficient time span, maintain current state with low confidence
        return current_state, 0.3, {}

    # Aggregate votes
    absent_votes = 0
    distracted_votes = 0
    focused_votes = 0
    neutral_votes = 0
    all_vision_votes = {}

    for snapshot in buffer:
        # Find primary labels
        cam_primary = get_primary_label(snapshot.cam_labels)
        screen_primary = get_primary_label(snapshot.screen_labels)

        # Count label occurrences for evidence
        if cam_primary:
            all_vision_votes[cam_primary] = all_vision_votes.get(cam_primary, 0) + 1
        if screen_primary:
            all_vision_votes[screen_primary] = all_vision_votes.get(screen_primary, 0) + 1

        # Categorize snapshot vote
        if cam_primary in CAM_ABSENCE_LABELS:
            absent_votes += 1
        elif (cam_primary in CAM_DISTRACTION_LABELS or
              screen_primary in SCREEN_DISTRACTION_LABELS):
            distracted_votes += 1
        elif (cam_primary in CAM_FOCUS_LABELS and
              (screen_primary in SCREEN_FOCUS_LABELS or screen_primary is None)):
            focused_votes += 1
        else:
            neutral_votes += 1

    # Apply voting rules (≥2 votes for K=3)
    threshold = (K + 1) // 2  # Ceiling of K/2

    if absent_votes >= threshold:
        return State.ABSENT, absent_votes / K, all_vision_votes
    elif distracted_votes >= threshold:
        return State.DISTRACTED, distracted_votes / K, all_vision_votes
    elif focused_votes >= threshold:
        return State.FOCUSED, focused_votes / K, all_vision_votes
    else:
        # Tie-breaking: no clear winner, maintain current state
        return current_state, 0.4, all_vision_votes


def compute_partial_buffer_state(
    buffer: List[SnapshotResult],
    current_state: State
) -> Tuple[State, float, Dict[str, int]]:
    """
    Handle partial buffer (first K-1 snapshots at session start)

    Strategy: Use simple majority voting across available snapshots
    but with lower confidence to reflect uncertainty

    Returns:
        Tuple[State, confidence, vision_votes]
        Confidence is reduced by factor of len(buffer)/K
    """
    if len(buffer) == 0:
        return current_state, 0.0, {}

    # Aggregate votes from partial buffer
    absent_count = 0
    distracted_count = 0
    focused_count = 0
    all_vision_votes = {}

    for snapshot in buffer:
        cam_primary = get_primary_label(snapshot.cam_labels)
        screen_primary = get_primary_label(snapshot.screen_labels)

        if cam_primary:
            all_vision_votes[cam_primary] = all_vision_votes.get(cam_primary, 0) + 1
        if screen_primary:
            all_vision_votes[screen_primary] = all_vision_votes.get(screen_primary, 0) + 1

        # Categorize
        if cam_primary in CAM_ABSENCE_LABELS:
            absent_count += 1
        elif (cam_primary in CAM_DISTRACTION_LABELS or
              screen_primary in SCREEN_DISTRACTION_LABELS):
            distracted_count += 1
        elif cam_primary in CAM_FOCUS_LABELS:
            focused_count += 1

    # Simple majority
    max_votes = max(absent_count, distracted_count, focused_count)

    if max_votes == 0:
        # No votes, assume focused start
        state = State.FOCUSED
        confidence = 0.2
    elif absent_count == max_votes:
        state = State.ABSENT
        confidence = absent_count / len(buffer) * 0.7  # Reduced confidence
    elif distracted_count == max_votes:
        state = State.DISTRACTED
        confidence = distracted_count / len(buffer) * 0.7
    elif focused_count == max_votes:
        state = State.FOCUSED
        confidence = focused_count / len(buffer) * 0.7
    else:
        # Tie, maintain current
        state = current_state
        confidence = 0.3

    return state, confidence, all_vision_votes


def get_primary_label(labels: Dict[str, float]) -> Optional[str]:
    """
    Get primary label (highest confidence) from label dict

    Args:
        labels: {label: confidence}

    Returns:
        Label with highest confidence, or None if empty
    """
    if not labels:
        return None
    return max(labels.items(), key=lambda x: x[1])[0]


# Debounce constraint
def validate_span(buffer: List[SnapshotResult], min_span_minutes: float = 1.0) -> bool:
    """
    Ensure snapshots span ≥ min_span_minutes

    Returns:
        True if span(buffer) ≥ min_span_minutes
    """
    if len(buffer) < 2:
        return False
    span = buffer[-1].timestamp - buffer[0].timestamp
    return span.total_seconds() / 60.0 >= min_span_minutes
```

### Voting Examples

**Example 1: Clear Distraction (All Same Label)**
```python
buffer = [
    SnapshotResult(
        timestamp=t0,
        cam_labels={"HeadAway": 0.9, "Focused": 0.1},
        screen_labels={"Code": 0.8}
    ),
    SnapshotResult(
        timestamp=t1,  # +60s
        cam_labels={"HeadAway": 0.85, "Focused": 0.15},
        screen_labels={"Code": 0.7}
    ),
    SnapshotResult(
        timestamp=t2,  # +120s
        cam_labels={"HeadAway": 0.8, "Focused": 0.2},
        screen_labels={"Code": 0.75}
    )
]

# Result:
# - Cam primary for all 3: HeadAway (distraction label)
# - Screen primary for all 3: Code (focus label)
# - Cam distraction overrides screen focus
# - distracted_votes = 3
# - State: DISTRACTED, confidence: 1.0
# - vision_votes: {"HeadAway": 3, "Code": 3}
```

**Example 2: Mixed Labels (Tie-Breaking)**
```python
buffer = [
    SnapshotResult(
        timestamp=t0,
        cam_labels={"HeadAway": 0.9},
        screen_labels={"Code": 0.8}
    ),
    SnapshotResult(
        timestamp=t1,  # +60s
        cam_labels={"EyesOffScreen": 0.7},
        screen_labels={"Code": 0.75}
    ),
    SnapshotResult(
        timestamp=t2,  # +120s
        cam_labels={"PhoneLikely": 0.85},
        screen_labels={"Code": 0.7}
    )
]

# Result:
# - Cam primaries: HeadAway, EyesOffScreen, PhoneLikely (all different distraction labels)
# - All 3 snapshots vote for DISTRACTED (different reasons)
# - distracted_votes = 3
# - State: DISTRACTED, confidence: 1.0
# - vision_votes: {"HeadAway": 1, "EyesOffScreen": 1, "PhoneLikely": 1, "Code": 3}
#
# Key insight: Don't need same label, just same category (distraction)
```

**Example 3: No Majority (Maintain Previous State)**
```python
buffer = [
    SnapshotResult(
        timestamp=t0,
        cam_labels={"Absent": 0.9},
        screen_labels={"Unknown": 0.5}
    ),
    SnapshotResult(
        timestamp=t1,  # +60s
        cam_labels={"HeadAway": 0.8},
        screen_labels={"Code": 0.7}
    ),
    SnapshotResult(
        timestamp=t2,  # +120s
        cam_labels={"Focused": 0.7},
        screen_labels={"Code": 0.8}
    )
]

# Result:
# - Snapshot 0: ABSENT (absent_votes = 1)
# - Snapshot 1: DISTRACTED (distracted_votes = 1)
# - Snapshot 2: FOCUSED (focused_votes = 1)
# - No category has ≥2 votes
# - State: current_state (unchanged), confidence: 0.4
# - vision_votes: {"Absent": 1, "HeadAway": 1, "Focused": 1, "Code": 2}
```

**Example 4: Partial Buffer (Session Start)**
```python
# Only 1 snapshot available (K=3 not yet reached)
buffer = [
    SnapshotResult(
        timestamp=t0,
        cam_labels={"Focused": 0.8},
        screen_labels={"Code": 0.9}
    )
]

# Result:
# - Use partial buffer logic
# - focused_count = 1
# - State: FOCUSED, confidence: 0.7 * (1/3) = 0.23
# - Low confidence due to insufficient data
```

### Edge Case Handling

#### Session Start State

```python
def initialize_state_machine() -> FocusState:
    """
    Initialize state machine at session start

    Returns:
        FocusState with FOCUSED as initial state, low confidence
    """
    return FocusState(
        state=State.FOCUSED,  # Assume user starts focused
        entered_at=datetime.now(timezone.utc),
        duration_seconds=0.0,
        snapshot_buffer=[],
        confidence=0.2  # Low confidence until first K snapshots
    )

# Rationale: Assume user starts focused when they explicitly start a session
# Low confidence reflects uncertainty until data collected
```

#### Pause/Resume Cycles

```python
class StateMachine:
    def pause_session(self):
        """
        Handle session pause

        Strategy:
        1. Transition to BREAK state immediately
        2. Clear snapshot buffer (paused snapshots invalid)
        3. Record pause timestamp
        """
        self.previous_state = self.current_state.state
        self.current_state = FocusState(
            state=State.BREAK,
            entered_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
            snapshot_buffer=[],  # Clear buffer
            confidence=1.0  # User explicitly paused
        )
        logging.info(f"Session paused, transitioned {self.previous_state} → BREAK")

    def resume_session(self):
        """
        Handle session resume

        Strategy:
        1. Transition to FOCUSED (assume user ready to work)
        2. Clear snapshot buffer (pre-resume snapshots stale)
        3. Low confidence until K new snapshots collected
        """
        self.current_state = FocusState(
            state=State.FOCUSED,
            entered_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
            snapshot_buffer=[],  # Fresh start
            confidence=0.3  # Moderate confidence
        )
        logging.info("Session resumed, transitioned BREAK → FOCUSED")

# Rapid pause/resume handling
def handle_rapid_pause_resume(pause_duration: timedelta) -> bool:
    """
    Detect and handle rapid pause/resume cycles

    Args:
        pause_duration: Time between pause and resume

    Returns:
        True if should suppress pause (too brief), False if valid pause
    """
    MIN_PAUSE_DURATION = 30  # seconds

    if pause_duration.total_seconds() < MIN_PAUSE_DURATION:
        logging.warning(
            f"Ignoring brief pause of {pause_duration.total_seconds():.0f}s "
            f"(minimum: {MIN_PAUSE_DURATION}s)"
        )
        return True  # Suppress
    else:
        return False  # Valid pause
```

#### Manual State Changes

```python
class StateMachine:
    def manual_state_override(
        self,
        new_state: State,
        reason: str
    ) -> StateTransition:
        """
        Handle user manual state override

        Use cases:
        - User marks themselves as "on break" during working period
        - User corrects false distraction alert
        - User indicates "focused" despite distraction detections

        Strategy:
        1. Apply override immediately
        2. Clear snapshot buffer (override invalidates recent data)
        3. High confidence (user knows their state)
        4. Resume normal voting after K new snapshots
        """
        old_state = self.current_state.state

        self.current_state = FocusState(
            state=new_state,
            entered_at=datetime.now(timezone.utc),
            duration_seconds=0.0,
            snapshot_buffer=[],  # Override invalidates buffer
            confidence=0.9  # High confidence in user input
        )

        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            timestamp=datetime.now(timezone.utc),
            confidence=0.9,
            evidence={"manual_override": True, "reason": reason}
        )

        logging.info(
            f"Manual state override: {old_state} → {new_state} "
            f"(reason: {reason})"
        )

        return transition
```

#### Concurrent Hysteresis and Manual Override

```python
# Scenario: User manually overrides state while hysteresis voting in progress

def update(self, snapshot_result: SnapshotResult) -> Optional[StateTransition]:
    """
    Process snapshot with manual override awareness

    Edge case: User overrode state recently, should we respect override
    or let voting take over?
    """
    # Check if manual override is recent (< 2 minutes)
    time_since_entry = (
        datetime.now(timezone.utc) - self.current_state.entered_at
    ).total_seconds()

    if (self.current_state.confidence > 0.8 and
        time_since_entry < 120):  # 2 minutes
        # Recent high-confidence state (likely manual override)
        # Add to buffer but don't transition yet
        self.current_state.snapshot_buffer.append(snapshot_result)

        # Trim buffer to K
        if len(self.current_state.snapshot_buffer) > self.K:
            self.current_state.snapshot_buffer.pop(0)

        # Don't transition until override "expires" (2 min) or buffer full
        if len(self.current_state.snapshot_buffer) < self.K:
            return None  # Respect override

    # Normal voting logic proceeds
    return self._compute_transition(snapshot_result)
```

#### Clock Skew/Time Travel

```python
def validate_snapshot_timestamp(
    snapshot_ts: datetime,
    last_snapshot_ts: Optional[datetime]
) -> bool:
    """
    Validate snapshot timestamp to detect clock skew

    Edge cases:
    - System clock adjusted backward (time travel to past)
    - System clock adjusted forward (jump to future)
    - Snapshots arriving out of order

    Strategy:
    - Reject snapshots with timestamp before last snapshot
    - Warn if timestamp too far in future (> 5 minutes)
    - Log clock skew events for debugging
    """
    now = datetime.now(timezone.utc)

    # Check 1: Future timestamp (clock skew or wrong timezone)
    if snapshot_ts > now + timedelta(minutes=5):
        logging.error(
            f"Snapshot timestamp in future: {snapshot_ts} "
            f"(now: {now}), rejecting"
        )
        return False

    # Check 2: Out of order (timestamp before last snapshot)
    if last_snapshot_ts and snapshot_ts < last_snapshot_ts:
        skew_seconds = (last_snapshot_ts - snapshot_ts).total_seconds()
        logging.error(
            f"Snapshot out of order: {snapshot_ts} < {last_snapshot_ts} "
            f"(skew: {skew_seconds:.0f}s), rejecting"
        )
        return False

    # Check 3: Very old snapshot (> 10 minutes delay)
    age_seconds = (now - snapshot_ts).total_seconds()
    if age_seconds > 600:
        logging.warning(
            f"Snapshot very old: {age_seconds:.0f}s delay, "
            f"accepting but may affect hysteresis"
        )

    return True
```

#### Empty/Partial Buffer Transitions

```python
def handle_empty_buffer_transition(
    current_state: State,
    requested_state: State
) -> StateTransition:
    """
    Handle state transition request when buffer is empty

    Occurs when:
    - Session just started
    - Buffer cleared due to pause/resume
    - Buffer cleared due to manual override

    Strategy:
    - Allow transition but with low confidence
    - Require user confirmation for DISTRACTED transitions
    """
    if requested_state == State.DISTRACTED:
        # Distraction without evidence requires confirmation
        confidence = 0.2
    elif requested_state == State.BREAK:
        # Breaks are usually intentional, higher confidence
        confidence = 0.7
    else:
        # FOCUSED or ABSENT
        confidence = 0.4

    return StateTransition(
        from_state=current_state,
        to_state=requested_state,
        timestamp=datetime.now(timezone.utc),
        confidence=confidence,
        evidence={"snapshot_buffer_size": 0}
    )
```

### State Transition Diagram

```
         [K snapshots with focus labels]
    ┌──────────────────────────────────┐
    │                                  │
    │  ┌──────────┐   [distraction]  ┌▼──────────┐
    └──┤ FOCUSED  ├───────────────────► DISTRACTED│
       └──────────┘                    └───────────┘
           ▲                                │
           │ [focus restored]               │
           └────────────────────────────────┘

       [absent ≥2/3]
    ┌──────────────────────────────────┐
    │                                  │
    │  ┌──────────┐   [user pauses]   ┌▼──────────┐
    └──┤ ABSENT   ├───────────────────►   BREAK   │
       └──────────┘                    └───────────┘
           ▲                                │
           │ [user resumes]                 │
           └────────────────────────────────┘
```

---

## API Contracts

### Internal Backend API (Optional)

#### POST /api/session/start
```json
Request:
{
  "quality": "Low|Std|High",
  "screen": true
}

Response:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### POST /api/session/end
```json
Request:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "metrics": {
    "total_snapshots": 120,
    "total_events": 5,
    "duration_minutes": 120
  }
}

Response:
{
  "status": "processing",
  "memories_job_id": "mem_abc123",
  "hume_job_id": "hume_xyz789"
}
```

#### POST /api/snapshot/log
```json
Request:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "kind": "cam",
  "ts": "2025-10-10T14:30:00Z",
  "openai_label_set": {
    "HeadAway": 0.85,
    "EyesOffScreen": 0.12
  },
  "file_ref": "snapshots/cam_20251010_143000.jpg"
}

Response:
{
  "ok": true
}
```

#### GET /api/report/:session_id
```json
Response:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "meta": {...},
  "segments": [...],
  "kpis": {...},
  "recommendations": [...],
  "artifacts": {...}
}
```

### OpenAI Vision API Integration

#### Model Selection

**Recommended Model:** `gpt-4o` (GPT-4 Omni)

**Rationale:**
- Optimized for vision tasks with lower latency than gpt-4-vision-preview
- Better structured output support
- Cost: ~$0.01-0.05 per image depending on resolution and detail level
- Alternative fallback: `gpt-4-turbo` (if rate limited)

**Configuration:**
```python
OPENAI_VISION_CONFIG = {
    "model": "gpt-4o",
    "max_tokens": 300,  # Structured labels don't need long responses
    "temperature": 0.3,  # Lower temperature for consistent classification
    "detail": "low"  # Use low detail for faster/cheaper processing
}
```

#### Prompt Templates

**CAM_PROMPT (Webcam Classification):**
```python
CAM_PROMPT = """Analyze this webcam image showing a person at their workspace.
Classify the person's attention state and return ONLY a JSON object.

Available labels:
- HeadAway: Head turned significantly away from screen (>45 degrees)
- EyesOffScreen: Eyes not looking at screen, gaze elsewhere
- Absent: No person visible in frame
- MicroSleep: Eyes closed or person appears drowsy/sleeping
- PhoneLikely: Person holding or looking at phone/mobile device
- Focused: Person actively working, eyes on screen, engaged posture

Return JSON format:
{
  "labels": {
    "HeadAway": 0.0-1.0,
    "EyesOffScreen": 0.0-1.0,
    "Absent": 0.0-1.0,
    "MicroSleep": 0.0-1.0,
    "PhoneLikely": 0.0-1.0,
    "Focused": 0.0-1.0
  },
  "primary": "most_confident_label",
  "reasoning": "brief explanation"
}

Confidence scale: 0.0 = not present, 0.5 = uncertain, 1.0 = definite
Multiple labels can be active if confidence > 0.3
"""
```

**SCREEN_PROMPT (Screen Classification):**
```python
SCREEN_PROMPT = """Analyze this screenshot and classify visible applications/content.
Return ONLY a JSON object.

Available labels:
- VideoOnScreen: Video player or streaming content visible (YouTube, Netflix, etc.)
- SocialFeed: Social media feed scrolling (Twitter, Instagram, Facebook, LinkedIn, TikTok)
- Code: Code editor or IDE (VS Code, PyCharm, Sublime, JetBrains)
- Docs: Documentation, technical reading, articles, wikis
- Email: Email client (Gmail, Outlook, Apple Mail, inbox view)
- VideoCall: Video conferencing (Zoom, Meet, Teams, FaceTime with call UI)
- Reading: Long-form reading (ebooks, PDFs, news articles, NOT code docs)
- Slides: Presentation software (PowerPoint, Google Slides, Keynote)
- Terminal: Command line terminal or shell
- ChatWindow: Chat/messaging applications (Slack, Discord, WhatsApp, iMessage)
- Games: Gaming applications or entertainment
- MultipleMonitors: Multiple unrelated windows visible (split screen, many tabs)
- Unknown: Cannot classify

Return JSON format:
{
  "labels": {
    "VideoOnScreen": 0.0-1.0,
    "SocialFeed": 0.0-1.0,
    "Code": 0.0-1.0,
    "Docs": 0.0-1.0,
    "Email": 0.0-1.0,
    "VideoCall": 0.0-1.0,
    "Reading": 0.0-1.0,
    "Slides": 0.0-1.0,
    "Terminal": 0.0-1.0,
    "ChatWindow": 0.0-1.0,
    "Games": 0.0-1.0,
    "MultipleMonitors": 0.0-1.0,
    "Unknown": 0.0-1.0
  },
  "primary": "most_confident_label",
  "reasoning": "brief explanation"
}

Confidence scale: 0.0 = not present, 0.5 = uncertain, 1.0 = definite
Multiple labels can be active if confidence > 0.3

Label priority when multiple present:
- If VideoCall with screen share → Code/Docs (work context)
- If Email with multiple tabs → Email (primary activity)
- If code visible among many windows → MultipleMonitors (context switching)
"""
```

#### Response Parsing Logic

```python
def parse_vision_response(
    raw_response: str,
    kind: SnapshotKind
) -> Dict[str, float]:
    """
    Parse OpenAI Vision API response with fallback handling

    Args:
        raw_response: Raw text response from GPT-4
        kind: cam or screen (determines expected label set)

    Returns:
        Dict[str, float]: {label: confidence}

    Fallback Strategy:
        1. Try to parse JSON from response
        2. If JSON malformed, extract using regex
        3. If extraction fails, return low-confidence Unknown/Focused default
        4. Validate all labels are in expected set (CAM_LABELS or SCREEN_LABELS)
        5. Filter out labels with confidence < 0.1
    """
    expected_labels = CAM_LABELS if kind == SnapshotKind.CAM else SCREEN_LABELS

    try:
        # Attempt JSON parse
        parsed = json.loads(raw_response)
        labels = parsed.get("labels", {})

        # Validate labels
        validated = {}
        for label, confidence in labels.items():
            if label in expected_labels:
                if 0.0 <= confidence <= 1.0:
                    if confidence >= 0.1:  # Filter low confidence
                        validated[label] = confidence
            else:
                logging.warning(f"Unknown label '{label}' returned by Vision API")

        # If no labels passed validation, use fallback
        if not validated:
            return get_fallback_labels(kind)

        return validated

    except json.JSONDecodeError:
        # Regex fallback
        logging.warning("Vision API response not valid JSON, attempting regex parse")
        labels = extract_labels_regex(raw_response, expected_labels)

        if labels:
            return labels
        else:
            return get_fallback_labels(kind)

def get_fallback_labels(kind: SnapshotKind) -> Dict[str, float]:
    """Return low-confidence default labels when parsing fails"""
    if kind == SnapshotKind.CAM:
        return {"Focused": 0.3, "Unknown": 0.7}
    else:
        return {"Unknown": 1.0}

def extract_labels_regex(text: str, expected_labels: Set[str]) -> Dict[str, float]:
    """Extract labels using regex patterns as fallback"""
    labels = {}
    for label in expected_labels:
        # Match patterns like: "HeadAway": 0.85 or HeadAway: 85%
        pattern = rf'"{label}":\s*(\d+\.?\d*)|{label}:\s*(\d+\.?\d*)%?'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            confidence = float(match.group(1) or match.group(2))
            # Normalize percentage to 0-1
            if confidence > 1.0:
                confidence /= 100.0
            labels[label] = confidence
    return labels
```

#### Cost Estimation

**Per-Snapshot Cost (2025 Q4 pricing):**
- Low detail (256p-480p): ~$0.001-0.003 per image
- High detail (720p): ~$0.005-0.010 per image

**Session Cost Estimates:**
```python
SESSION_COST_ESTIMATES = {
    "2hr_Std_profile": {
        "snapshots": 120,  # 60s interval * 2 hours
        "cost_per_snapshot": 0.002,  # $0.002 avg for low detail
        "total_cost": 0.24  # $0.24 per 2hr session
    },
    "8hr_Low_profile": {
        "snapshots": 480,  # 60s interval * 8 hours
        "cost_per_snapshot": 0.001,  # $0.001 for 256p low detail
        "total_cost": 0.48  # $0.48 per 8hr session
    },
    "8hr_High_profile": {
        "snapshots": 480,
        "cost_per_snapshot": 0.005,  # $0.005 for 720p high detail
        "total_cost": 2.40  # $2.40 per 8hr session
    }
}
```

**Monthly Cost (20 working days):**
- Low profile: ~$10/month
- Std profile: ~$50/month
- High profile: ~$100/month

#### Error Handling

```python
# Specific Vision API errors
class VisionAPIError(AppError):
    """Base class for Vision API errors"""
    pass

class VisionRateLimitError(VisionAPIError):
    """Rate limit exceeded (HTTP 429)"""
    code = ErrorCode.VISION_API_RATE_LIMIT
    recoverable = True

class VisionAuthError(VisionAPIError):
    """Authentication failed (HTTP 401)"""
    code = ErrorCode.UPLOAD_AUTH_FAILED
    recoverable = False

class VisionTimeoutError(VisionAPIError):
    """Request timeout"""
    code = ErrorCode.UPLOAD_TIMEOUT
    recoverable = True

class VisionParseError(VisionAPIError):
    """Failed to parse response"""
    code = ErrorCode.VISION_API_ERROR
    recoverable = True  # Can fallback to default labels

# Retry configuration
VISION_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    backoff_seconds=[1, 5, 15],
    retryable_errors={
        ErrorCode.VISION_API_ERROR,
        ErrorCode.UPLOAD_TIMEOUT,
        ErrorCode.VISION_API_RATE_LIMIT
    }
)
```

#### Rate Limiting Strategy

```python
class RateLimiter:
    """Token bucket rate limiter for Vision API calls"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_capacity: int = 10
    ):
        """
        Args:
            requests_per_minute: Sustained rate limit
            burst_capacity: Maximum burst size
        """
        self.rate = requests_per_minute / 60.0  # Requests per second
        self.capacity = burst_capacity
        self.tokens = burst_capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

    def acquire(self, timeout_sec: float = 10.0) -> bool:
        """
        Acquire permit to make API call

        Returns:
            True if acquired, False if timeout
        """
        deadline = time.time() + timeout_sec

        while time.time() < deadline:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_update

                # Refill tokens
                self.tokens = min(
                    self.capacity,
                    self.tokens + elapsed * self.rate
                )
                self.last_update = now

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True

            # Wait before retry
            time.sleep(0.1)

        return False

# Global rate limiter
vision_rate_limiter = RateLimiter(
    requests_per_minute=60,  # Conservative default
    burst_capacity=10
)
```

#### Local Fallback Classifier (Optional)

**Purpose**: Provide degraded but functional classification when OpenAI Vision API is unavailable

**Trigger Conditions:**
```python
class FallbackTrigger:
    """Determine when to switch to local fallback classifier"""

    def __init__(
        self,
        consecutive_failure_threshold: int = 5,
        error_rate_threshold: float = 0.5,  # 50% errors
        window_size: int = 10
    ):
        self.consecutive_failures = 0
        self.consecutive_threshold = consecutive_failure_threshold
        self.error_rate_threshold = error_rate_threshold
        self.recent_results = deque(maxlen=window_size)
        self.fallback_active = False

    def record_result(self, success: bool) -> bool:
        """
        Record API call result and check if fallback should activate

        Args:
            success: True if OpenAI Vision API succeeded

        Returns:
            True if should use fallback, False if continue with API
        """
        self.recent_results.append(success)

        if success:
            self.consecutive_failures = 0
            # Check if can exit fallback mode
            if self.fallback_active:
                error_rate = 1.0 - (sum(self.recent_results) / len(self.recent_results))
                if error_rate < 0.1:  # 90% success rate
                    self.fallback_active = False
                    logging.info("Exiting fallback mode, API recovered")
        else:
            self.consecutive_failures += 1

        # Trigger 1: Consecutive failures
        if self.consecutive_failures >= self.consecutive_threshold:
            if not self.fallback_active:
                logging.error(
                    f"OpenAI Vision API: {self.consecutive_failures} "
                    f"consecutive failures, activating fallback"
                )
                self.fallback_active = True

        # Trigger 2: High error rate
        if len(self.recent_results) >= self.window_size:
            error_rate = 1.0 - (sum(self.recent_results) / len(self.recent_results))
            if error_rate >= self.error_rate_threshold:
                if not self.fallback_active:
                    logging.error(
                        f"OpenAI Vision API: {error_rate:.1%} error rate, "
                        f"activating fallback"
                    )
                    self.fallback_active = True

        return self.fallback_active
```

**Fallback Implementation Options:**

**Option 1: Simple Rule-Based Classifier (Recommended for MVP)**
```python
class SimpleScreenClassifier:
    """
    Rule-based screen classifier using window titles and OCR

    Accuracy: ~60-70% (vs 85-90% for OpenAI Vision)
    Latency: <100ms
    Cost: Free
    """

    def classify_screen(self, screenshot_path: Path) -> Dict[str, float]:
        """
        Classify screen using simple heuristics

        Returns:
            Dict[str, float]: {label: confidence}
        """
        # Get active window title (platform-specific)
        window_title = self._get_active_window_title()

        labels = {}

        # Heuristic rules based on window title
        title_lower = window_title.lower()

        if any(x in title_lower for x in ['youtube', 'netflix', 'video', 'player']):
            labels['VideoOnScreen'] = 0.7

        if any(x in title_lower for x in ['twitter', 'facebook', 'instagram', 'reddit']):
            labels['SocialFeed'] = 0.7

        if any(x in title_lower for x in ['vscode', 'pycharm', 'sublime', 'vim', 'emacs']):
            labels['Code'] = 0.8

        if any(x in title_lower for x in ['chrome', 'firefox', 'safari', 'edge']) and 'docs' in title_lower:
            labels['Docs'] = 0.6

        if any(x in title_lower for x in ['slack', 'discord', 'whatsapp', 'telegram']):
            labels['ChatWindow'] = 0.8

        if any(x in title_lower for x in ['terminal', 'iterm', 'powershell', 'cmd']):
            labels['Terminal'] = 0.9

        if any(x in title_lower for x in ['steam', 'game', 'minecraft']):
            labels['Games'] = 0.7

        # Default if no match
        if not labels:
            labels['Unknown'] = 1.0

        return labels

    def _get_active_window_title(self) -> str:
        """Get active window title (platform-specific)"""
        import platform

        system = platform.system()

        if system == "Darwin":  # macOS
            # Use pyobjc to get active window
            from AppKit import NSWorkspace
            active_app = NSWorkspace.sharedWorkspace().activeApplication()
            return active_app['NSApplicationName']

        elif system == "Windows":
            # Use win32gui
            import win32gui
            window = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(window)

        elif system == "Linux":
            # Use xdotool
            import subprocess
            result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'],
                                  capture_output=True, text=True)
            return result.stdout.strip()

        return "Unknown"
```

**Option 2: Local CNN Model (Not Recommended for MVP)**
```python
class LocalCNNClassifier:
    """
    Local CNN for screen classification

    Pros:
    - Better accuracy than rule-based (~75-80%)
    - Works offline

    Cons:
    - Requires model training
    - Larger package size (~50-200MB)
    - Higher latency (~200-500ms on CPU)
    - Maintenance burden

    NOT RECOMMENDED for initial release
    Consider only if OpenAI API proves unreliable
    """
    pass
```

**Fallback Configuration:**
```python
# config.yaml
developer:
  # Fallback settings
  FALLBACK_ENABLED: true
  FALLBACK_CONSECUTIVE_FAILURES: 5
  FALLBACK_ERROR_RATE_THRESHOLD: 0.5
  FALLBACK_TYPE: "simple"  # simple | cnn | disabled
```

**Integration with Uploader:**
```python
class SnapshotUploader:
    def __init__(self, ...):
        self.vision_client = OpenAIVisionClient(...)
        self.fallback_classifier = SimpleScreenClassifier()
        self.fallback_trigger = FallbackTrigger()

    def classify_snapshot(self, image_path: Path, kind: SnapshotKind) -> VisionResult:
        """Classify with fallback support"""

        # Try OpenAI Vision API first
        use_fallback = self.fallback_trigger.fallback_active

        if not use_fallback:
            try:
                result = self.vision_client.classify_screen_snapshot(image_path)
                self.fallback_trigger.record_result(success=True)
                return result
            except VisionAPIError as e:
                self.fallback_trigger.record_result(success=False)
                logging.error(f"Vision API error: {e}")
                use_fallback = self.fallback_trigger.fallback_active

        # Use fallback if triggered
        if use_fallback and kind == SnapshotKind.SCREEN:
            labels = self.fallback_classifier.classify_screen(image_path)
            return VisionResult(
                labels=labels,
                raw_response={"fallback": True},
                processed_at=datetime.now(timezone.utc),
                latency_ms=50
            )
        else:
            # Cam fallback: assume focused
            return VisionResult(
                labels={"Focused": 0.5},
                raw_response={"fallback": True},
                processed_at=datetime.now(timezone.utc),
                latency_ms=10
            )
```

**Fallback Quality Expectations:**
- **Screen Classification**: 60-70% accuracy (vs 85-90% for OpenAI)
- **Cam Classification**: Not supported, defaults to Focused with low confidence
- **Acceptable degradation**: Users prefer partial functionality over complete failure

---

## File Formats

### Snapshot Naming Convention

```
sessions/<session_id>/snapshots/cam_YYYYMMDDHHmmss.jpg
sessions/<session_id>/snapshots/screen_YYYYMMDDHHmmss.jpg
```

Example:
```
sessions/550e8400-e29b/snapshots/cam_20251010143000.jpg
sessions/550e8400-e29b/snapshots/screen_20251010143000.jpg
```

### Vision JSON Response

```json
{
  "snapshot_id": "660e8400-e29b-41d4-a716-446655440000",
  "kind": "cam",
  "timestamp": "2025-10-10T14:30:00Z",
  "labels": {
    "HeadAway": 0.85,
    "EyesOffScreen": 0.12,
    "Focused": 0.03
  },
  "raw_response": {
    "model": "gpt-4-vision",
    "usage": {...}
  },
  "latency_ms": 1250
}
```

### Session Report JSON (v1.3)

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "meta": {
    "started_at": "2025-10-10T14:00:00Z",
    "ended_at": "2025-10-10T16:00:00Z",
    "profile": "Std",
    "total_duration_minutes": 120,
    "snapshot_interval_sec": 60
  },
  "segments": [
    {
      "t0": 0,
      "t1": 1800,
      "label": "Focus",
      "task_hypothesis": "Writing code",
      "apps": [
        {"class": "IDE", "share": 0.8},
        {"class": "Terminal", "share": 0.2}
      ],
      "distractions": [],
      "posture": {"mode": "Neutral", "pct": 0.95},
      "expressions": {
        "frustration_mean": 0.2,
        "valence_mean": 0.6,
        "arousal_mean": 0.7
      },
      "snapshot_refs": [
        "snapshots/cam_20251010140000.jpg",
        "snapshots/screen_20251010140000.jpg",
        "snapshots/cam_20251010141000.jpg",
        "snapshots/screen_20251010141000.jpg"
      ]
    }
  ],
  "kpis": {
    "focus_ratio": 0.85,
    "avg_focus_bout_min": 25.5,
    "num_alerts": 3,
    "top_triggers": ["VideoOnScreen", "HeadAway"],
    "peak_distraction_hour": "15:00-16:00"
  },
  "recommendations": [
    {
      "type": "BreakSchedule",
      "message": "Consider taking a 5-minute break every 25 minutes",
      "priority": 1
    }
  ],
  "artifacts": {
    "memories_urls": {
      "cam": "https://memories.ai/v/abc123",
      "screen": "https://memories.ai/v/def456"
    },
    "hume_job_id": "hume_xyz789"
  }
}
```

### SQLite Schema v1.3

```sql
-- sessions table
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    task_name TEXT NOT NULL,
    quality_profile TEXT NOT NULL,
    screen_enabled BOOLEAN NOT NULL,
    status TEXT NOT NULL,
    cam_mp4_path TEXT,
    screen_mp4_path TEXT,
    snapshots_dir TEXT,
    vision_dir TEXT,
    logs_dir TEXT,
    total_snapshots INTEGER DEFAULT 0,
    uploaded_snapshots INTEGER DEFAULT 0,
    failed_snapshots INTEGER DEFAULT 0,
    total_events INTEGER DEFAULT 0
);

-- snapshots table
CREATE TABLE snapshots (
    snapshot_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    kind TEXT NOT NULL,  -- cam | screen
    jpeg_path TEXT NOT NULL,
    jpeg_size_bytes INTEGER,
    vision_json_path TEXT,
    vision_labels TEXT,  -- JSON: {label: confidence}
    processed_at TIMESTAMP,
    upload_status TEXT NOT NULL,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- distraction_events table
CREATE TABLE distraction_events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP NOT NULL,
    duration_seconds REAL NOT NULL,
    event_type TEXT NOT NULL,
    evidence TEXT,
    confidence REAL,
    vision_votes TEXT,  -- JSON: {label: count}
    snapshot_refs TEXT,  -- JSON: [snapshot_id, ...]
    acknowledged BOOLEAN DEFAULT 0,
    acknowledged_at TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- session_reports table
CREATE TABLE session_reports (
    session_id TEXT PRIMARY KEY,
    report_json TEXT NOT NULL,  -- Full SessionReport as JSON
    generated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- indexes
CREATE INDEX idx_snapshots_session ON snapshots(session_id);
CREATE INDEX idx_snapshots_timestamp ON snapshots(timestamp);
CREATE INDEX idx_events_session ON distraction_events(session_id);
CREATE INDEX idx_events_timestamp ON distraction_events(started_at);
```

---

## Error Handling

### Error Code Definitions

```python
class ErrorCode(Enum):
    # Configuration errors (1xxx)
    CONFIG_LOAD_FAILED = 1001
    CONFIG_INVALID = 1002
    CONFIG_API_KEY_MISSING = 1003

    # Session errors (2xxx)
    SESSION_START_FAILED = 2001
    SESSION_ALREADY_ACTIVE = 2002
    SESSION_NOT_FOUND = 2003
    SESSION_DISK_SPACE_LOW = 2004

    # Capture errors (3xxx)
    CAMERA_ACCESS_DENIED = 3001
    CAMERA_NOT_FOUND = 3002
    SCREEN_CAPTURE_FAILED = 3003
    RECORDING_FAILED = 3004

    # Upload errors (4xxx)
    UPLOAD_FAILED = 4001
    UPLOAD_RATE_LIMITED = 4002
    UPLOAD_TIMEOUT = 4003
    UPLOAD_AUTH_FAILED = 4004

    # API errors (5xxx)
    VISION_API_ERROR = 5001
    VISION_API_RATE_LIMIT = 5002
    HUME_API_ERROR = 5003
    MEMORIES_API_ERROR = 5004

    # Database errors (6xxx)
    DB_CONNECTION_FAILED = 6001
    DB_QUERY_FAILED = 6002
    DB_WRITE_FAILED = 6003

    # Processing errors (7xxx)
    FUSION_ERROR = 7001
    REPORT_GENERATION_FAILED = 7002

    # System errors (9xxx)
    UNKNOWN_ERROR = 9999

@dataclass
class AppError(Exception):
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    recoverable: bool = True
```

### Retry Strategy

```python
@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_seconds: List[int] = field(default_factory=lambda: [1, 5, 15])
    retryable_errors: Set[ErrorCode] = field(default_factory=lambda: {
        ErrorCode.UPLOAD_FAILED,
        ErrorCode.UPLOAD_TIMEOUT,
        ErrorCode.VISION_API_ERROR,
    })

def retry_with_backoff(
    func: Callable,
    config: RetryConfig,
    *args,
    **kwargs
) -> Any:
    """
    Retry function with exponential backoff

    Raises:
        Last exception if all retries exhausted
    """
    pass
```

### Crash Recovery and System Safety

#### SQLite Database Safety

**WAL (Write-Ahead Logging) Mode:**
```python
# Enable WAL mode for crash safety
def initialize_database(db_path: str) -> sqlite3.Connection:
    """
    Initialize database with crash-safe configuration

    WAL Mode Benefits:
    - Atomic commits even if process crashes
    - Concurrent readers don't block writers
    - Automatic recovery on next connection
    - Database file remains consistent
    """
    conn = sqlite3.Connection(db_path)

    # Enable WAL mode
    conn.execute("PRAGMA journal_mode=WAL")

    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys=ON")

    # Set synchronous to NORMAL (balance safety/performance)
    # FULL = safest but slowest
    # NORMAL = safe with WAL, faster
    # OFF = fastest but unsafe
    conn.execute("PRAGMA synchronous=NORMAL")

    # Set busy timeout (wait 5s if database locked)
    conn.execute("PRAGMA busy_timeout=5000")

    return conn
```

**Transaction Safety:**
```python
class DatabaseWriter:
    """Thread-safe database writer with automatic rollback"""

    def __init__(self, db_path: str):
        self.conn = initialize_database(db_path)
        self.lock = threading.Lock()

    def execute_transaction(
        self,
        operations: List[Callable],
        rollback_on_error: bool = True
    ) -> bool:
        """
        Execute multiple operations in single transaction

        Args:
            operations: List of database operations
            rollback_on_error: Rollback if any operation fails

        Returns:
            True if successful, False if failed
        """
        with self.lock:
            try:
                self.conn.execute("BEGIN TRANSACTION")

                for operation in operations:
                    operation(self.conn)

                self.conn.commit()
                return True

            except Exception as e:
                if rollback_on_error:
                    self.conn.rollback()
                    logging.error(f"Transaction failed, rolled back: {e}")
                else:
                    # Try to salvage partial commit
                    try:
                        self.conn.commit()
                        logging.warning(f"Partial transaction committed: {e}")
                    except:
                        self.conn.rollback()

                return False

    def close(self):
        """Close connection with checkpoint"""
        # Force WAL checkpoint before closing
        self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        self.conn.close()
```

**Cascade Delete Rules:**
```sql
-- Foreign key constraints with cascade rules
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    -- ... other fields
);

CREATE TABLE snapshots (
    snapshot_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    -- ... other fields
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        ON DELETE CASCADE  -- Delete all snapshots if session deleted
);

CREATE TABLE distraction_events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    -- ... other fields
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        ON DELETE CASCADE  -- Delete all events if session deleted
);

-- Indexes for cascade performance
CREATE INDEX idx_snapshots_session_cascade ON snapshots(session_id);
CREATE INDEX idx_events_session_cascade ON distraction_events(session_id);
```

**Database Concurrency Conflict Handling:**
```python
class DatabaseConcurrency:
    """Handle SQLite concurrency with proper locking and retries"""

    @staticmethod
    def execute_with_retry(
        conn: sqlite3.Connection,
        operation: Callable,
        max_retries: int = 3,
        backoff_ms: List[int] = [10, 50, 100]
    ) -> Any:
        """
        Execute database operation with SQLITE_BUSY retry logic

        Args:
            conn: Database connection
            operation: Function that executes SQL
            max_retries: Maximum retry attempts
            backoff_ms: Backoff delays in milliseconds

        Returns:
            Operation result

        Raises:
            DatabaseBusyError: If all retries exhausted
        """
        for attempt in range(max_retries):
            try:
                return operation(conn)
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) or "SQLITE_BUSY" in str(e):
                    if attempt < max_retries - 1:
                        delay_ms = backoff_ms[min(attempt, len(backoff_ms) - 1)]
                        logging.warning(
                            f"Database locked, retry {attempt + 1}/{max_retries} "
                            f"after {delay_ms}ms"
                        )
                        time.sleep(delay_ms / 1000.0)
                    else:
                        raise DatabaseBusyError(
                            f"Database locked after {max_retries} retries"
                        )
                else:
                    # Other operational error, don't retry
                    raise

class DatabaseBusyError(Exception):
    """Database locked and retry limit exceeded"""
    pass

# Locking hierarchy to prevent deadlocks
LOCK_ORDER = {
    "session_lock": 1,    # Always acquire first
    "snapshot_lock": 2,   # Then snapshots
    "event_lock": 3,      # Then events
    "report_lock": 4      # Finally reports
}

class Database:
    """Database with proper locking discipline"""

    def __init__(self, db_path: str):
        self.conn = initialize_database(db_path)
        # Per-table locks for fine-grained concurrency
        self.session_lock = threading.RLock()
        self.snapshot_lock = threading.RLock()
        self.event_lock = threading.RLock()
        self.report_lock = threading.RLock()

    def insert_snapshot_safe(self, snapshot: Snapshot) -> str:
        """
        Insert snapshot with proper locking

        Lock order: session_lock → snapshot_lock
        """
        with self.session_lock:  # Acquire session lock first (order 1)
            # Verify session exists
            session = self.get_session(snapshot.session_id)
            if not session:
                raise ValueError(f"Session {snapshot.session_id} not found")

            with self.snapshot_lock:  # Then snapshot lock (order 2)
                # Execute with retry
                def insert_op(conn):
                    cursor = conn.execute("""
                        INSERT INTO snapshots (
                            snapshot_id, session_id, timestamp, kind,
                            jpeg_path, jpeg_size_bytes, upload_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        snapshot.snapshot_id,
                        snapshot.session_id,
                        snapshot.timestamp,
                        snapshot.kind.value,
                        snapshot.jpeg_path,
                        snapshot.jpeg_size_bytes,
                        snapshot.upload_status.value
                    ))
                    conn.commit()
                    return cursor.lastrowid

                return DatabaseConcurrency.execute_with_retry(
                    self.conn,
                    insert_op
                )

    def batch_insert_snapshots(self, snapshots: List[Snapshot]) -> int:
        """
        Batch insert snapshots in single transaction

        More efficient than individual inserts, reduces lock contention
        """
        with self.snapshot_lock:
            def batch_op(conn):
                conn.execute("BEGIN TRANSACTION")
                count = 0
                for snapshot in snapshots:
                    conn.execute("""
                        INSERT INTO snapshots (
                            snapshot_id, session_id, timestamp, kind,
                            jpeg_path, jpeg_size_bytes, upload_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        snapshot.snapshot_id,
                        snapshot.session_id,
                        snapshot.timestamp,
                        snapshot.kind.value,
                        snapshot.jpeg_path,
                        snapshot.jpeg_size_bytes,
                        snapshot.upload_status.value
                    ))
                    count += 1
                conn.commit()
                return count

            return DatabaseConcurrency.execute_with_retry(
                self.conn,
                batch_op
            )

# Transaction isolation level
def set_isolation_level(conn: sqlite3.Connection):
    """
    Set appropriate isolation level

    SQLite default: SERIALIZABLE (strictest)
    With WAL mode: Can use DEFERRED for better concurrency
    """
    # Use DEFERRED transactions for read-heavy workloads
    # Writers don't block readers with WAL mode
    conn.isolation_level = "DEFERRED"

# Deadlock prevention example
def update_session_and_event_safe(
    session_id: str,
    event: DistractionEvent,
    database: Database
):
    """
    Update session and insert event atomically

    Lock order: session_lock → event_lock (respects LOCK_ORDER)
    """
    with database.session_lock:  # Order 1
        session = database.get_session(session_id)

        with database.event_lock:  # Order 3
            # Both operations in single transaction
            def atomic_op(conn):
                conn.execute("BEGIN TRANSACTION")

                # Update session
                conn.execute(
                    "UPDATE sessions SET total_events = total_events + 1 WHERE session_id = ?",
                    (session_id,)
                )

                # Insert event
                conn.execute("""
                    INSERT INTO distraction_events (
                        event_id, session_id, started_at, ended_at, ...
                    ) VALUES (?, ?, ?, ?, ...)
                """, (...))

                conn.commit()

            DatabaseConcurrency.execute_with_retry(database.conn, atomic_op)

# Connection pooling (advanced, future consideration)
class DatabasePool:
    """
    Connection pool for multi-threaded access

    NOT RECOMMENDED for Phase 1:
    - Adds complexity
    - WAL mode + busy_timeout usually sufficient
    - Single connection with RLocks simpler

    Consider if profiling shows contention
    """
    pass
```

#### Crash Recovery Protocol

**Session Resume Strategy:**
```python
class SessionRecovery:
    """Handle recovery from crashes during active sessions"""

    def check_incomplete_sessions(self, database: Database) -> List[Session]:
        """
        Find sessions that were active when app crashed

        Returns:
            List of incomplete sessions
        """
        # Find sessions with status=ACTIVE but no ended_at timestamp
        incomplete = database.query(
            "SELECT * FROM sessions WHERE status = ? AND ended_at IS NULL",
            ("active",)
        )
        return [Session.from_row(row) for row in incomplete]

    def recover_session(
        self,
        session: Session,
        database: Database
    ) -> RecoveryAction:
        """
        Determine recovery action for incomplete session

        Strategy:
        1. Check if session is recent (< 5 minutes old)
           → Prompt user to resume
        2. Check if session has any data
           → If yes: mark as completed and generate report
           → If no: delete orphaned session
        3. Close video files properly
        4. Clean up temporary snapshots
        """
        now = datetime.now(timezone.utc)
        session_age = (now - session.started_at).total_seconds() / 60.0

        # Recent session: offer resume
        if session_age < 5:
            return RecoveryAction.PROMPT_RESUME

        # Check if session has meaningful data
        snapshot_count = database.count_snapshots(session.session_id)
        event_count = database.count_events(session.session_id)

        if snapshot_count > 0 or event_count > 0:
            # Has data: finalize and generate report
            logging.info(f"Recovering session {session.session_id} with {snapshot_count} snapshots")

            # Mark as completed with current timestamp
            database.end_session(session.session_id, now)
            database.update_session_status(session.session_id, SessionStatus.COMPLETED)

            # Generate report from available data
            try:
                report_generator = ReportGenerator(database, None, None)
                report = report_generator.generate(session.session_id)
                database.store_session_report(session.session_id, report)
            except Exception as e:
                logging.error(f"Failed to generate recovery report: {e}")

            return RecoveryAction.RECOVERED
        else:
            # No data: clean up orphan
            logging.info(f"Deleting orphaned session {session.session_id}")
            database.delete_session(session.session_id)
            cleanup_session_files(session)
            return RecoveryAction.DELETED

class RecoveryAction(Enum):
    PROMPT_RESUME = "prompt_resume"  # Ask user if they want to continue
    RECOVERED = "recovered"          # Finalized and saved
    DELETED = "deleted"              # Removed orphan
```

**Application Startup Recovery:**
```python
def startup_recovery_check():
    """
    Run recovery checks on application startup

    Steps:
    1. Check for incomplete sessions
    2. Verify database integrity
    3. Clean up temporary files
    4. Restore persisted queues
    5. Check disk space
    """
    logging.info("Running startup recovery checks...")

    # 1. Database integrity
    database = Database("data/focus_guardian.db")
    if not database.verify_integrity():
        logging.critical("Database corruption detected!")
        # Attempt recovery from backup or prompt user
        return False

    # 2. Incomplete sessions
    recovery = SessionRecovery()
    incomplete = recovery.check_incomplete_sessions(database)

    if incomplete:
        logging.warning(f"Found {len(incomplete)} incomplete sessions")
        for session in incomplete:
            action = recovery.recover_session(session, database)
            logging.info(f"Session {session.session_id}: {action.value}")

    # 3. Clean temporary files
    cleanup_temp_files()

    # 4. Restore persisted queues
    restore_upload_queue()

    # 5. Check disk space
    free_space_gb = get_free_disk_space()
    if free_space_gb < 1.0:
        logging.error(f"Low disk space: {free_space_gb:.2f} GB")
        return False

    logging.info("Startup recovery complete")
    return True
```

#### Queue Persistence

**Snapshot Upload Queue Persistence:**
```python
class PersistentUploadQueue:
    """
    Persist upload queue to disk to survive crashes

    Strategy:
    - Periodically save queue state to JSON file
    - On startup, restore pending uploads
    - Use atomic file writes (write to temp, then rename)
    """

    def __init__(self, queue_file: Path):
        self.queue_file = queue_file
        self.queue = Queue()
        self.lock = threading.Lock()
        self._restore_from_disk()

    def _restore_from_disk(self):
        """Restore queue from persisted state"""
        if not self.queue_file.exists():
            return

        try:
            with open(self.queue_file, 'r') as f:
                data = json.load(f)

            for item in data.get("pending_uploads", []):
                snapshot_pair = SnapshotPair(
                    cam_snapshot=Path(item["cam_snapshot"]),
                    screen_snapshot=Path(item["screen_snapshot"]) if item.get("screen_snapshot") else None,
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    session_id=item["session_id"]
                )
                self.queue.put(snapshot_pair)

            logging.info(f"Restored {self.queue.qsize()} pending uploads from disk")

        except Exception as e:
            logging.error(f"Failed to restore upload queue: {e}")
            # Continue with empty queue

    def persist_to_disk(self):
        """Save current queue state to disk atomically"""
        with self.lock:
            # Extract all items without removing from queue
            items = []
            temp_list = []

            # Drain queue into temp list
            while not self.queue.empty():
                try:
                    item = self.queue.get_nowait()
                    temp_list.append(item)
                except Empty:
                    break

            # Re-add items to queue and serialize
            for item in temp_list:
                self.queue.put(item)
                items.append({
                    "cam_snapshot": str(item.cam_snapshot),
                    "screen_snapshot": str(item.screen_snapshot) if item.screen_snapshot else None,
                    "timestamp": item.timestamp.isoformat(),
                    "session_id": item.session_id
                })

            data = {
                "version": "1.3",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pending_uploads": items
            }

            # Atomic write: write to temp file, then rename
            temp_file = self.queue_file.with_suffix(".tmp")
            try:
                with open(temp_file, 'w') as f:
                    json.dump(data, f, indent=2)

                # Atomic rename
                temp_file.replace(self.queue_file)

            except Exception as e:
                logging.error(f"Failed to persist queue: {e}")
                if temp_file.exists():
                    temp_file.unlink()

    def start_periodic_persistence(self, interval_sec: int = 30):
        """Start background thread to periodically save queue"""
        def persist_loop():
            while not shutdown_event.is_set():
                time.sleep(interval_sec)
                self.persist_to_disk()

        thread = threading.Thread(target=persist_loop, daemon=True, name="QueuePersister")
        thread.start()
```

**Graceful Shutdown Protocol:**
```python
class ShutdownManager:
    """Coordinate graceful shutdown across all threads"""

    def __init__(
        self,
        session_manager: SessionManager,
        upload_queue: PersistentUploadQueue,
        database: Database
    ):
        self.session_manager = session_manager
        self.upload_queue = upload_queue
        self.database = database

    def initiate_shutdown(self, timeout_sec: int = 30):
        """
        Graceful shutdown with timeout

        Steps:
        1. Signal all threads to stop
        2. Wait for upload queue to drain (with timeout)
        3. Persist remaining queue items
        4. Stop video recorders
        5. Close database with checkpoint
        6. Save logs
        """
        logging.info("Initiating graceful shutdown...")

        # 1. Signal shutdown
        shutdown_event.set()

        # 2. Wait for uploads to complete
        deadline = time.time() + timeout_sec
        while not self.upload_queue.empty() and time.time() < deadline:
            remaining = self.upload_queue.qsize()
            logging.info(f"Waiting for {remaining} uploads to complete...")
            time.sleep(1)

        # 3. Persist remaining items
        if not self.upload_queue.empty():
            logging.warning(f"Timeout reached, persisting {self.upload_queue.qsize()} pending uploads")
            self.upload_queue.persist_to_disk()

        # 4. Stop session (finalizes recordings)
        if self.session_manager.get_current_session():
            try:
                self.session_manager.end_session()
            except Exception as e:
                logging.error(f"Error ending session during shutdown: {e}")

        # 5. Close database
        try:
            self.database.close()
        except Exception as e:
            logging.error(f"Error closing database: {e}")

        logging.info("Shutdown complete")
```

#### Error Recovery Best Practices

**Defensive Programming:**
```python
# Always use context managers for resources
with Database(db_path) as db:
    # Operations automatically rolled back on exception
    db.insert_snapshot(snapshot)

# Always validate data before writes
def insert_snapshot_safe(snapshot: Snapshot):
    if not snapshot.session_id:
        raise ValueError("Snapshot missing session_id")
    if not snapshot.jpeg_path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {snapshot.jpeg_path}")

    # Proceed with insert
    database.insert_snapshot(snapshot)

# Always log errors with context
try:
    process_snapshot(snapshot)
except Exception as e:
    logging.error(
        f"Failed to process snapshot {snapshot.snapshot_id} "
        f"for session {snapshot.session_id}: {e}",
        exc_info=True  # Include stack trace
    )
```

**Health Checks:**
```python
class HealthMonitor:
    """Monitor system health and trigger recovery actions"""

    def check_system_health(self) -> HealthStatus:
        """
        Periodic health check

        Returns:
            HealthStatus with any detected issues
        """
        issues = []

        # Check disk space
        free_gb = get_free_disk_space()
        if free_gb < 1.0:
            issues.append(f"Low disk space: {free_gb:.2f} GB")

        # Check database connectivity
        try:
            database.execute("SELECT 1")
        except Exception as e:
            issues.append(f"Database connection failed: {e}")

        # Check thread health
        if not snapshot_scheduler.is_alive():
            issues.append("Snapshot scheduler thread died")

        # Check memory usage
        memory_mb = get_process_memory_mb()
        if memory_mb > 500:
            issues.append(f"High memory usage: {memory_mb} MB")

        if issues:
            return HealthStatus(healthy=False, issues=issues)
        else:
            return HealthStatus(healthy=True, issues=[])
```

---

## Threading Model

### Thread Pool Overview

```
Main Thread (UI)
  - CustomTkinter/PyQt6 event loop
  - Consumes: event_queue, ui_queue
  - Produces: user actions

Snapshot Scheduler Thread
  - Timer-based snapshot capture
  - Produces: snapshot_upload_queue

Snapshot Uploader Workers (Pool of N threads)
  - Consumes: snapshot_upload_queue
  - Produces: fusion_queue, db_queue

Fusion Engine Thread
  - Consumes: fusion_queue
  - Produces: event_queue, db_queue

Database Writer Thread
  - Consumes: db_queue
  - Performs: all DB writes

Recording Threads (2x)
  - Cam recorder thread
  - Screen recorder thread

Post-Processing Thread (optional)
  - Hume/Memories API uploads
  - Spawned after session ends
```

### Timing and Scheduling

#### Snapshot Timestamp Strategy

**Absolute Wall-Clock Timestamps:**
```python
# All timestamps use absolute wall-clock time (UTC)
# NOT session-relative seconds

snapshot_timestamp = datetime.now(timezone.utc)  # ISO 8601 UTC

# Reasons for absolute timestamps:
# 1. Easier correlation with external events (system logs, calendar)
# 2. Simpler debugging (no need to compute session start offset)
# 3. Consistent with database timestamp columns
# 4. Handles clock adjustments gracefully
```

**Session-Relative Time (for reports only):**
```python
# Session reports use relative seconds for segments
# Computed from absolute timestamps at report generation

def to_session_relative(absolute_ts: datetime, session_start: datetime) -> float:
    """Convert absolute timestamp to session-relative seconds"""
    return (absolute_ts - session_start).total_seconds()

# Example:
# Session starts: 2025-10-10T14:00:00Z
# Snapshot at:    2025-10-10T14:01:30Z
# Relative time:  90.0 seconds
```

#### Snapshot Scheduler Behavior

**Strict Cadence Mode (Default):**
```python
class SnapshotScheduler:
    """
    Maintains strict interval cadence regardless of processing delays

    Strategy: Schedule next capture based on session start time, not last capture

    Example with 60s interval:
    - Session start: T=0
    - Snapshot 1: T=60  (scheduled)
    - Snapshot 2: T=120 (scheduled, even if #1 still uploading)
    - Snapshot 3: T=180 (scheduled)

    Benefits:
    - Predictable snapshot times
    - No drift accumulation
    - Consistent time spans for hysteresis

    Drawback:
    - Upload queue can grow if processing slower than capture rate
    """

    def __init__(self, interval_sec: int, strict_cadence: bool = True):
        self.interval_sec = interval_sec
        self.strict_cadence = strict_cadence
        self.session_start = None
        self.next_snapshot_num = 0

    def calculate_next_capture_time(self) -> datetime:
        """Calculate next snapshot time using strict cadence"""
        if self.strict_cadence:
            # Absolute: start + (N * interval)
            next_time = self.session_start + timedelta(
                seconds=self.next_snapshot_num * self.interval_sec
            )
            self.next_snapshot_num += 1
            return next_time
        else:
            # Relative: last_capture + interval (drifts over time)
            return datetime.now(timezone.utc) + timedelta(seconds=self.interval_sec)

    def run(self):
        """Scheduler main loop"""
        self.session_start = datetime.now(timezone.utc)
        self.next_snapshot_num = 1  # First snapshot at T=interval

        while not shutdown_event.is_set():
            next_capture = self.calculate_next_capture_time()
            now = datetime.now(timezone.utc)

            # Wait until next scheduled time
            wait_seconds = (next_capture - now).total_seconds()

            if wait_seconds > 0:
                time.sleep(min(wait_seconds, 1.0))  # Check shutdown every 1s
            else:
                # Missed schedule (processing too slow)
                logging.warning(
                    f"Snapshot scheduler behind by {-wait_seconds:.1f}s, "
                    f"capturing immediately"
                )

            # Capture snapshot
            self.capture_and_enqueue()
```

**Handling Upload Delays:**
```python
# Queue Overflow Protection
SNAPSHOT_UPLOAD_QUEUE_SIZE = 100  # Hard limit

def capture_and_enqueue(self):
    """Capture snapshot and add to upload queue"""
    timestamp = datetime.now(timezone.utc)

    # Capture images (non-blocking, fast operation ~50-200ms)
    cam_snapshot = capture_cam_image()
    screen_snapshot = capture_screen_image() if self.screen_enabled else None

    # Check queue capacity before enqueueing
    if self.upload_queue.qsize() >= SNAPSHOT_UPLOAD_QUEUE_SIZE:
        # Queue full: drop oldest item
        dropped = self.upload_queue.get_nowait()
        logging.error(
            f"Upload queue full ({SNAPSHOT_UPLOAD_QUEUE_SIZE}), "
            f"dropped snapshot from {dropped.timestamp}"
        )
        self.stats.dropped_snapshots += 1

    # Enqueue new snapshot
    snapshot_pair = SnapshotPair(
        cam_snapshot=cam_snapshot,
        screen_snapshot=screen_snapshot,
        timestamp=timestamp,
        session_id=self.session_id
    )
    self.upload_queue.put(snapshot_pair)
```

**Timing Diagram (60s interval, 3s upload latency):**
```
Time    Scheduler              Upload Queue       Vision API
─────────────────────────────────────────────────────────────
0s      Session start          []
60s     Capture #1 → enqueue   [#1]
61s                            [#1]               ← #1 uploading
64s                            []                 #1 complete ✓
120s    Capture #2 → enqueue   [#2]
121s                           [#2]               ← #2 uploading
124s                           []                 #2 complete ✓
180s    Capture #3 → enqueue   [#3]
181s                           [#3]               ← #3 uploading
184s                           []                 #3 complete ✓

Observation: Queue stays small (≤1 item) when upload faster than capture
```

**Timing Diagram (60s interval, 90s upload latency - slow network):**
```
Time    Scheduler              Upload Queue       Vision API
─────────────────────────────────────────────────────────────
0s      Session start          []
60s     Capture #1 → enqueue   [#1]
61s                            [#1]               ← #1 uploading
120s    Capture #2 → enqueue   [#1, #2]
150s                           [#2]               #1 complete ✓
151s                           [#2]               ← #2 uploading
180s    Capture #3 → enqueue   [#2, #3]
240s    Capture #4 → enqueue   [#2, #3, #4]
241s                           [#3, #4]           #2 complete ✓
242s                           [#3, #4]           ← #3 uploading

Observation: Queue grows when upload slower than capture
Risk: Eventually hits 100-item limit, drops oldest
```

**Adaptive Throttling (Optional):**
```python
# If queue depth exceeds threshold, dynamically increase interval
QUEUE_DEPTH_THRESHOLD = 10

def adaptive_interval(self) -> int:
    """Adjust interval based on queue depth"""
    queue_depth = self.upload_queue.qsize()

    if queue_depth > QUEUE_DEPTH_THRESHOLD:
        # Double interval to let queue drain
        throttled = self.interval_sec * 2
        logging.warning(
            f"Queue depth {queue_depth} > {QUEUE_DEPTH_THRESHOLD}, "
            f"throttling to {throttled}s interval"
        )
        return throttled
    else:
        return self.interval_sec
```

### Thread Synchronization

```python
# Queue sizes with overflow handling
SNAPSHOT_UPLOAD_QUEUE_SIZE = 100  # Up to 100 pending uploads (drops oldest)
FUSION_QUEUE_SIZE = 50            # Vision results (drops oldest)
EVENT_QUEUE_SIZE = 100            # State transitions (drops oldest)
DB_QUEUE_SIZE = 200               # Database operations (blocks, never drops)
UI_QUEUE_SIZE = 100               # UI updates (drops oldest)

# Thread-safe primitives
session_lock = threading.RLock()      # Protects session state
state_lock = threading.RLock()        # Protects state machine
stats_lock = threading.RLock()        # Protects statistics

# Shutdown coordination
shutdown_event = threading.Event()    # Global shutdown signal
upload_complete_event = threading.Event()  # All uploads done
```

### Queue Overflow Handling

#### Queue Overflow Policies

**Policy Summary Table:**

| Queue | Size | Overflow Policy | Rationale |
|-------|------|----------------|-----------|
| Snapshot Upload | 100 | Drop oldest | Prefer recent data over old |
| Fusion | 50 | Drop oldest | Recent vision results more important |
| Event | 100 | Drop oldest | UI can miss intermediate states |
| Database | 200 | **Block** | Never lose data writes |
| UI | 100 | Drop oldest | UI can skip intermediate updates |

#### Snapshot Upload Queue

```python
class BoundedQueue(Queue):
    """Queue with drop-oldest overflow policy"""

    def __init__(self, maxsize: int, name: str):
        super().__init__(maxsize=maxsize)
        self.name = name
        self.dropped_count = 0
        self.lock = threading.Lock()

    def put_drop_oldest(self, item: Any, block: bool = False) -> bool:
        """
        Put item in queue, dropping oldest if full

        Returns:
            True if item added, False if dropped current item
        """
        try:
            # Try non-blocking put first
            self.put_nowait(item)
            return True
        except Full:
            with self.lock:
                # Queue full: drop oldest
                try:
                    dropped = self.get_nowait()
                    self.dropped_count += 1
                    logging.warning(
                        f"{self.name} queue full ({self.maxsize}), "
                        f"dropped item (total dropped: {self.dropped_count})"
                    )
                except Empty:
                    pass  # Race condition, queue drained

                # Add new item
                try:
                    self.put_nowait(item)
                    return True
                except Full:
                    # Still full (race), drop new item
                    self.dropped_count += 1
                    logging.error(
                        f"{self.name} queue still full, "
                        f"dropping new item"
                    )
                    return False

# Queue initialization
snapshot_upload_queue = BoundedQueue(
    maxsize=SNAPSHOT_UPLOAD_QUEUE_SIZE,
    name="SnapshotUpload"
)

fusion_queue = BoundedQueue(
    maxsize=FUSION_QUEUE_SIZE,
    name="Fusion"
)

event_queue = BoundedQueue(
    maxsize=EVENT_QUEUE_SIZE,
    name="Event"
)

ui_queue = BoundedQueue(
    maxsize=UI_QUEUE_SIZE,
    name="UI"
)

# Database queue BLOCKS (never drops)
db_queue = Queue(maxsize=DB_QUEUE_SIZE)  # Standard blocking queue
```

#### Database Queue (Blocking Policy)

```python
class DatabaseQueue:
    """
    Blocking queue for database operations

    Never drops writes - blocks producer if full
    Ensures all data persisted to database
    """

    def __init__(self, maxsize: int = 200):
        self.queue = Queue(maxsize=maxsize)
        self.blocked_count = 0

    def put(self, operation: DBMessage, timeout: float = 10.0) -> bool:
        """
        Put database operation in queue (blocks if full)

        Args:
            operation: Database operation to execute
            timeout: Max time to wait if queue full

        Returns:
            True if added, False if timeout

        Raises:
            DatabaseQueueFull: If timeout exceeded
        """
        try:
            self.queue.put(operation, block=True, timeout=timeout)
            return True
        except Full:
            self.blocked_count += 1
            logging.critical(
                f"Database queue blocked for {timeout}s "
                f"(blocked count: {self.blocked_count})"
            )
            raise DatabaseQueueFull(
                f"Database queue full, waited {timeout}s"
            )

class DatabaseQueueFull(Exception):
    """Database queue full and blocking timeout exceeded"""
    pass
```

#### Queue Monitoring

```python
class QueueMonitor:
    """Monitor queue depths and trigger alerts"""

    def __init__(
        self,
        queues: Dict[str, BoundedQueue],
        alert_threshold: float = 0.8  # 80% full
    ):
        self.queues = queues
        self.alert_threshold = alert_threshold

    def check_depths(self) -> Dict[str, QueueMetrics]:
        """
        Check all queue depths and return metrics

        Returns:
            Dict mapping queue name to metrics
        """
        metrics = {}

        for name, queue in self.queues.items():
            size = queue.qsize()
            capacity = queue.maxsize
            utilization = size / capacity if capacity > 0 else 0.0

            metrics[name] = QueueMetrics(
                name=name,
                size=size,
                capacity=capacity,
                utilization=utilization,
                dropped_count=getattr(queue, 'dropped_count', 0)
            )

            # Alert if over threshold
            if utilization >= self.alert_threshold:
                logging.warning(
                    f"Queue {name} at {utilization:.1%} capacity "
                    f"({size}/{capacity})"
                )

        return metrics

    def start_monitoring(self, interval_sec: int = 10):
        """Start background monitoring thread"""
        def monitor_loop():
            while not shutdown_event.is_set():
                self.check_depths()
                time.sleep(interval_sec)

        thread = threading.Thread(
            target=monitor_loop,
            daemon=True,
            name="QueueMonitor"
        )
        thread.start()

@dataclass
class QueueMetrics:
    name: str
    size: int
    capacity: int
    utilization: float  # 0.0 - 1.0
    dropped_count: int
```

#### Dropped Item Logging

```python
class DroppedItemLogger:
    """Log dropped items for debugging and analysis"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.lock = threading.Lock()

    def log_dropped_snapshot(
        self,
        snapshot: SnapshotPair,
        queue_name: str,
        queue_size: int
    ):
        """Log dropped snapshot for post-session analysis"""
        with self.lock:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "queue": queue_name,
                "queue_size": queue_size,
                "snapshot": {
                    "session_id": snapshot.session_id,
                    "timestamp": snapshot.timestamp.isoformat(),
                    "cam_path": str(snapshot.cam_snapshot),
                    "screen_path": str(snapshot.screen_snapshot) if snapshot.screen_snapshot else None
                }
            }

            # Append to log file
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')

# Global dropped item logger
dropped_logger = DroppedItemLogger(
    log_file=Path("logs/dropped_items.jsonl")
)
```

#### Queue Overflow Recovery Strategies

**Strategy 1: Automatic Throttling**
```python
# Already covered in adaptive_interval() above
# Reduces snapshot frequency when queue backs up
```

**Strategy 2: Worker Pool Scaling (Advanced)**
```python
class DynamicWorkerPool:
    """
    Scale worker pool size based on queue depth

    NOT RECOMMENDED for Phase 1 due to:
    - OpenAI API rate limits
    - Cost implications
    - Complexity

    Consider for future if upload latency is bottleneck
    """

    def scale_workers(self, queue_depth: int):
        """Add workers if queue backing up"""
        if queue_depth > 20 and self.num_workers < self.max_workers:
            self.add_worker()
            logging.info(f"Scaled workers to {self.num_workers}")
```

**Strategy 3: Quality Degradation**
```python
# Reduce JPEG quality when queue backing up
def adaptive_jpeg_quality(queue_depth: int, base_quality: int = 85) -> int:
    """
    Reduce JPEG quality to speed up uploads

    Args:
        queue_depth: Current upload queue size
        base_quality: Normal quality setting

    Returns:
        Adjusted quality (60-85)
    """
    if queue_depth > 50:
        return 60  # Low quality
    elif queue_depth > 20:
        return 70  # Medium quality
    else:
        return base_quality  # Normal quality
```

---

## Performance Budgets (Revised for Snapshot Architecture)

### CPU Usage

**Realistic Targets for Snapshot-Based Architecture:**

```python
TARGET_CPU_USAGE = {
    # Base application (idle, no session)
    "idle_avg": 2,          # ~2% CPU when idle

    # Active session (recording + snapshot upload)
    "session_avg": 15,      # Average CPU % achieved (PRD requirement: <30% max)
    "session_p95": 35,      # 95th percentile (PRD allows bursts within <30% avg)
    "session_max": 60,      # Maximum burst (PRD allows bursts within <30% avg)

    # Per-component breakdown (2hr session, Std profile)
    "video_recording": 5,   # ffmpeg H.264 encoding
    "snapshot_capture": 3,  # OpenCV JPEG capture @ 60s interval
    "upload_workers": 4,    # 3 parallel upload threads
    "fusion_engine": 1,     # Hysteresis voting logic
    "ui_updates": 1,        # CustomTkinter/PyQt6
    "database_writes": 1,   # SQLite writes
}

# Throttle trigger
CPU_THROTTLE_THRESHOLD = 60  # Reduce snapshot frequency if sustained >60%
```

**Rationale**: Snapshot architecture (60s interval) is much lighter than continuous CV processing. Original 30% avg target was based on continuous MediaPipe processing.

### Memory Usage

**Realistic Targets:**

```python
TARGET_MEMORY_USAGE = {
    # Base application
    "base_app_mb": 80,                  # Python + GUI framework

    # Per-session overhead
    "per_session_mb": 150,              # Video buffers + snapshot queue (REVISED from 200)

    # Component breakdown (during session)
    "video_buffers_mb": 50,             # ffmpeg video encoding buffers
    "snapshot_queue_mb": 30,            # 100 snapshots @ ~300KB each
    "database_cache_mb": 20,            # SQLite page cache
    "thread_stacks_mb": 10,             # 7 threads @ ~1.5MB each
    "gui_framework_mb": 40,             # CustomTkinter/PyQt6

    # Absolute maximum
    "max_mb": 400,                      # Hard limit (REVISED from 500)

    # Per quality profile
    "Low_profile_mb": 250,              # 256p @ 10fps
    "Std_profile_mb": 350,              # 480p @ 15fps (default)
    "High_profile_mb": 450,             # 720p @ 15fps
}

# Memory leak detection
MEMORY_LEAK_THRESHOLD_MB_PER_HOUR = 20  # Flag if growth >20MB/hr
```

**Rationale**: Snapshot architecture doesn't hold video frames in memory continuously, only during encoding buffer. Revised down from original targets.

### Latency Budgets

**Achievable Latencies:**

```python
TARGET_LATENCY = {
    # Snapshot capture (local operations)
    "snapshot_capture_ms": 150,         # OpenCV JPEG encode (REVISED from 200)
    "snapshot_save_disk_ms": 20,        # Write JPEG to SSD

    # Upload + inference (network + API)
    "snapshot_upload_p50_ms": 1500,     # Median upload+infer (NEW)
    "snapshot_upload_p95_ms": 3500,     # 95th percentile (REVISED from 2500)
    "snapshot_upload_p99_ms": 8000,     # 99th percentile (NEW)
    "snapshot_upload_timeout_ms": 30000,  # Hard timeout

    # Fusion and state machine
    "fusion_processing_ms": 50,         # Hysteresis voting (REVISED from 100)
    "state_transition_ms": 30,          # State machine update (NEW)

    # UI responsiveness
    "ui_update_ms": 33,                 # 30fps UI refresh (REVISED from 50)
    "alert_display_ms": 200,            # From event to UI (REVISED from 500)
    "button_click_response_ms": 100,    # User interaction latency (NEW)
}

# Latency percentile validation
def validate_latency_percentiles():
    """Ensure p50 < p95 < p99 < timeout"""
    assert 1500 < 3500 < 8000 < 30000  # Upload latencies
```

**Rationale**: Original 2.5s p95 for upload+inference was too optimistic for OpenAI API. Revised based on typical GPT-4 Vision latencies (1-4s median, 3-8s p95).

### Storage Budgets

**Revised for Snapshot Architecture:**

```python
STORAGE_BUDGET = {
    # Snapshot storage
    "snapshot_jpeg_kb": 100,            # Average JPEG size @ 85 quality (REVISED from 50)
    "snapshot_jpeg_max_kb": 300,        # Maximum per snapshot

    # Video recording (H.264)
    "video_bitrate_cam_kbps": 500,      # Std profile cam
    "video_bitrate_screen_kbps": 800,   # Std profile screen

    # Per-session totals (2hr session, Std profile)
    "session_2hr_snapshots_mb": 24,     # 120 snapshots @ 200KB each (REVISED from 6)
    "session_2hr_cam_video_mb": 440,    # 2hr @ 500kbps
    "session_2hr_screen_video_mb": 700, # 2hr @ 800kbps
    "session_2hr_database_mb": 5,       # SQLite database
    "session_2hr_logs_mb": 10,          # Application logs
    "session_2hr_total_mb": 1179,       # Total for 2hr (REVISED from 350)

    # Disk space requirements
    "disk_space_min_gb": 2.0,           # Minimum free space (REVISED from 1.0)
    "disk_space_warn_gb": 5.0,          # Warning threshold (NEW)

    # Per quality profile (2hr session)
    "Low_2hr_mb": 600,                  # 256p @ 10fps
    "Std_2hr_mb": 1179,                 # 480p @ 15fps (default)
    "High_2hr_mb": 2200,                # 720p @ 15fps
}
```

**Rationale**: Original 350MB for 2hr session only counted snapshots, not video recordings. Revised to include all storage (video, snapshots, database, logs).

### Network Budgets

**Realistic Network Usage:**

```python
NETWORK_BUDGET = {
    # Realtime snapshot uploads
    "snapshot_upload_kb": 100,          # Per snapshot JPEG (REVISED from 50)
    "session_2hr_snapshots": 120,       # 60s interval * 2 hours
    "session_2hr_realtime_mb": 12,      # Snapshot uploads (REVISED from 6)

    # Post-session uploads (optional)
    "post_session_cam_mb": 440,         # 2hr cam video @ 500kbps
    "post_session_screen_mb": 700,      # 2hr screen video @ 800kbps
    "post_session_total_mb": 1140,      # Optional video uploads (REVISED from 350)

    # Bandwidth caps
    "realtime_bandwidth_cap_mbps": 0.5, # Max sustained upload (NEW)
    "burst_bandwidth_cap_mbps": 2.0,    # Short burst (NEW)

    # Per quality profile (realtime uploads only)
    "Low_realtime_mbps": 0.03,          # ~30KB/s average
    "Std_realtime_mbps": 0.05,          # ~50KB/s average (default)
    "High_realtime_mbps": 0.10,         # ~100KB/s average
}

# Bandwidth validation
def validate_bandwidth_achievable():
    """
    Ensure bandwidth caps are achievable with 3 parallel uploads

    Worst case: 3 snapshots uploading simultaneously
    3 * 100KB = 300KB = 2.4Mbps burst
    """
    max_burst_mb = 3 * 0.1  # 3 snapshots * 100KB
    assert max_burst_mb < 2.0  # Under burst cap
```

**Rationale**: Added realtime vs post-session distinction. Original budgets didn't account for parallel uploads. Revised to ensure achievable targets.

### Validation and Trade-offs

```python
class PerformanceBudgetValidator:
    """Validate performance budgets are internally consistent"""

    @staticmethod
    def validate_cpu_memory_tradeoff():
        """
        CPU and memory have inverse relationship

        Higher snapshot frequency:
        - Increases CPU (more captures, uploads)
        - Decreases memory (queue drains faster)

        Lower snapshot frequency:
        - Decreases CPU (fewer operations)
        - Increases memory (queue can grow)
        """
        intervals = [30, 60, 120]  # seconds
        for interval in intervals:
            cpu_factor = 60 / interval  # Relative to 60s baseline
            memory_factor = interval / 60

            expected_cpu = 15 * cpu_factor  # Scale from baseline
            expected_memory = 350 * memory_factor  # Scale from baseline

            logging.info(
                f"Interval={interval}s: CPU={expected_cpu:.0f}%, "
                f"Memory={expected_memory:.0f}MB"
            )

    @staticmethod
    def validate_storage_vs_quality():
        """Storage increases quadratically with resolution"""
        profiles = {
            "Low": {"res": 256, "fps": 10, "bitrate": 200},
            "Std": {"res": 480, "fps": 15, "bitrate": 500},
            "High": {"res": 720, "fps": 15, "bitrate": 1000}
        }

        for name, config in profiles.items():
            # Storage = bitrate * duration
            storage_2hr_mb = config["bitrate"] * 7200 / 8 / 1024
            logging.info(
                f"{name}: {config['res']}p @ {config['fps']}fps "
                f"= {storage_2hr_mb:.0f}MB per 2hr"
            )

    @staticmethod
    def validate_network_vs_latency():
        """Network latency affects effective upload throughput"""
        # If upload latency = 3.5s (p95)
        # and snapshot interval = 60s
        # then effective parallelism = 60 / 3.5 = ~17 uploads in flight

        latency_p95 = 3.5  # seconds
        interval = 60  # seconds
        parallelism = interval / latency_p95

        if parallelism > 3:  # MAX_PARALLEL_UPLOADS
            logging.warning(
                f"Upload latency {latency_p95}s with {interval}s interval "
                f"suggests {parallelism:.0f} parallel uploads needed, "
                f"but only 3 configured. Queue will grow."
            )
```

---

## Validation & Testing

### Unit Test Coverage Requirements

```python
COVERAGE_TARGETS = {
    "core": 90,           # core/ modules
    "capture": 85,        # capture/ modules
    "analysis": 85,       # analysis/ modules
    "integrations": 75,   # integrations/ modules (mocked)
    "session": 90,        # session/ modules
    "ui": 60,             # ui/ modules (harder to test)
    "utils": 95           # utils/ modules
}
```

### Integration Test Scenarios

```python
INTEGRATION_TESTS = [
    "test_full_session_lifecycle",
    "test_snapshot_upload_retry",
    "test_fusion_hysteresis",
    "test_state_transitions",
    "test_report_generation",
    "test_cloud_upload_failure_recovery",
    "test_disk_space_low_handling",
    "test_api_rate_limit_backoff",
]
```

### Performance Test Requirements

```python
PERFORMANCE_TESTS = {
    "test_2hr_session_std_profile": {
        "duration_minutes": 120,
        "profile": "Std",
        "max_cpu_avg": 30,
        "max_memory_mb": 300,
        "max_disk_mb": 400
    },
    "test_8hr_session_low_profile": {
        "duration_minutes": 480,
        "profile": "Low",
        "max_cpu_avg": 20,
        "max_memory_mb": 250,
        "max_disk_mb": 800
    }
}
```

---

## Appendix: Constants

```python
# Application
APP_NAME = "Focus Guardian"
APP_VERSION = "1.3.0"
SCHEMA_VERSION = "1.3"

# Defaults
DEFAULT_SNAPSHOT_INTERVAL_SEC = 60
DEFAULT_MIN_SNAPSHOT_INTERVAL_SEC = 10
DEFAULT_QUALITY_PROFILE = QualityProfile.STD
DEFAULT_MAX_PARALLEL_UPLOADS = 3
DEFAULT_HYSTERESIS_K = 3
DEFAULT_MIN_SPAN_MINUTES = 1.0

# Limits
MAX_SESSION_DURATION_HOURS = 12
MAX_SNAPSHOT_RETRY_ATTEMPTS = 3
MAX_UPLOAD_QUEUE_SIZE = 100
MAX_RECORDING_FILE_SIZE_GB = 5

# Timeouts
API_REQUEST_TIMEOUT_SEC = 30
DATABASE_QUERY_TIMEOUT_SEC = 10
SHUTDOWN_GRACE_PERIOD_SEC = 30

# File paths
SESSIONS_DIR = "data/sessions"
REPORTS_DIR = "data/reports"
CONFIG_DIR = "config"
LOGS_DIR = "logs"
```

---

**End of Specification**

This specification serves as the single source of truth for implementation. All module interfaces, data structures, and behaviors should conform to these definitions.

**Version History:**
- v1.3 (2025-10-10): Initial specification for snapshot-based architecture
