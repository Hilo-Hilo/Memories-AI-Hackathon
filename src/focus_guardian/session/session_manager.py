"""
Session manager for Focus Guardian.

Orchestrates the entire session lifecycle: recording, snapshot capture,
upload, analysis, and event detection. This is the central coordinator
that brings all components together.
"""

import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..core.config import Config
from ..core.database import Database
from ..core.models import Session, SessionStatus, QualityProfile
from ..core.state_machine import StateMachine
from ..capture.recorder import WebcamRecorder, ScreenRecorder, create_recorder
from ..capture.snapshot_scheduler import SnapshotScheduler
from ..capture.snapshot_uploader import SnapshotUploader
from ..analysis.fusion_engine import FusionEngine
from ..analysis.distraction_detector import DistractionDetector
from ..integrations.openai_vision_client import OpenAIVisionClient
from ..integrations.hume_client import HumeExpressionClient
from ..integrations.memories_client import MemoriesClient
from ..session.report_generator import ReportGenerator
from ..utils.queue_manager import QueueManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Manages focus session lifecycle and coordinates all components."""
    
    def __init__(self, config: Config, database: Database, ui_queue):
        """
        Initialize session manager.
        
        Args:
            config: Configuration manager
            database: Database interface
            ui_queue: Queue for sending messages to UI
        """
        self.config = config
        self.database = database
        self.ui_queue = ui_queue
        
        # Session state
        self.current_session: Optional[Session] = None
        self.current_session_id: Optional[str] = None
        
        # Components (initialized per session)
        self.queue_manager: Optional[QueueManager] = None
        self.webcam_recorder: Optional[WebcamRecorder] = None
        self.screen_recorder: Optional[ScreenRecorder] = None
        self.snapshot_scheduler: Optional[SnapshotScheduler] = None
        self.snapshot_uploader: Optional[SnapshotUploader] = None
        self.state_machine: Optional[StateMachine] = None
        self.fusion_engine: Optional[FusionEngine] = None
        self.distraction_detector: Optional[DistractionDetector] = None
        self.vision_client: Optional[OpenAIVisionClient] = None
        
        # Post-processing clients (optional)
        self.hume_client: Optional[HumeExpressionClient] = None
        self.memories_client: Optional[MemoriesClient] = None
        self.report_generator: Optional[ReportGenerator] = None
        
        # Initialize post-processing clients if API keys available
        self._initialize_post_processing_clients()
        
        logger.info("Session manager initialized")
    
    def start_session(
        self,
        task_name: str,
        quality_profile: Optional[QualityProfile] = None,
        screen_enabled: bool = True
    ) -> str:
        """
        Start a new focus session.
        
        Args:
            task_name: Name/description of the task
            quality_profile: Video quality (Low/Std/High)
            screen_enabled: Whether to capture screen
            
        Returns:
            session_id
        """
        if self.current_session:
            raise RuntimeError("A session is already active")
        
        logger.info(f"Starting new session: {task_name}")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        
        # Use default quality profile if not specified
        if quality_profile is None:
            quality_profile = self.config.get_video_res_profile()
        
        # Create session directory structure
        sessions_dir = self.config.get_sessions_dir()
        session_dir = sessions_dir / session_id
        snapshots_dir = session_dir / "snapshots"
        vision_dir = session_dir / "vision"
        logs_dir = session_dir / "logs"
        
        for directory in [session_dir, snapshots_dir, vision_dir, logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Create session record
        self.current_session = Session(
            session_id=session_id,
            started_at=datetime.now(),
            ended_at=None,
            task_name=task_name,
            quality_profile=quality_profile,
            screen_enabled=screen_enabled,
            status=SessionStatus.ACTIVE,
            cam_mp4_path=str(session_dir / "cam.mp4"),
            screen_mp4_path=str(session_dir / "screen.mp4") if screen_enabled else None,
            snapshots_dir=str(snapshots_dir),
            vision_dir=str(vision_dir),
            logs_dir=str(logs_dir)
        )
        
        # Save to database
        self.database.create_session(self.current_session)
        logger.info(f"Session record created: {session_id}")
        
        # Initialize components
        self._initialize_components(session_dir, snapshots_dir, quality_profile, screen_enabled)
        
        # Start all components
        self._start_components()
        
        logger.info(f"Session started successfully: {session_id}")
        return session_id
    
    def _initialize_components(
        self,
        session_dir: Path,
        snapshots_dir: Path,
        quality_profile: QualityProfile,
        screen_enabled: bool
    ) -> None:
        """Initialize all session components."""
        logger.info("Initializing session components...")
        
        # Queue manager for inter-thread communication
        self.queue_manager = QueueManager(
            max_queue_size=self.config.get_config_value("queue_max_size", 100)
        )
        
        # OpenAI Vision client
        openai_key = self.config.get_openai_api_key()
        if not openai_key:
            raise RuntimeError("OpenAI API key not configured")

        vision_model = self.config.get_config_value("openai_vision_model", "gpt-5-nano")
        vision_detail = self.config.get_config_value("openai_vision_detail", "high")

        self.vision_client = OpenAIVisionClient(
            api_key=openai_key,
            model=vision_model,
            detail=vision_detail
        )
        
        # Get camera config (used by both recorder and scheduler)
        camera_index = self.config.get_camera_index()
        snapshot_interval = self.config.get_snapshot_interval_sec()

        # Video recorders
        self.webcam_recorder = create_recorder(
            kind="cam",
            output_path=Path(self.current_session.cam_mp4_path),
            quality_profile=quality_profile,
            camera_index=camera_index  # CRITICAL: Use same camera as snapshots
        )

        if screen_enabled:
            self.screen_recorder = create_recorder(
                kind="screen",
                output_path=Path(self.current_session.screen_mp4_path),
                quality_profile=quality_profile
            )

        # Snapshot scheduler
        self.snapshot_scheduler = SnapshotScheduler(
            session_id=self.current_session_id,
            interval_sec=snapshot_interval,
            snapshots_dir=snapshots_dir,
            upload_queue=self.queue_manager.snapshot_upload_queue,
            screen_enabled=screen_enabled,
            camera_index=camera_index
        )
        
        # Snapshot uploader worker pool
        num_workers = self.config.get_max_parallel_uploads()
        self.snapshot_uploader = SnapshotUploader(
            num_workers=num_workers,
            upload_queue=self.queue_manager.snapshot_upload_queue,
            fusion_queue=self.queue_manager.fusion_queue,
            vision_client=self.vision_client,
            database=self.database
        )
        
        # State machine
        K_hysteresis = self.config.get_K_hysteresis()
        min_span_minutes = self.config.get_min_span_minutes()
        self.state_machine = StateMachine(
            K=K_hysteresis,
            min_span_minutes=min_span_minutes
        )
        
        # Fusion engine
        self.fusion_engine = FusionEngine(
            state_machine=self.state_machine,
            fusion_queue=self.queue_manager.fusion_queue,
            event_queue=self.queue_manager.event_queue,
            K=K_hysteresis,
            min_span_minutes=min_span_minutes
        )
        
        # Distraction detector
        self.distraction_detector = DistractionDetector(
            event_queue=self.queue_manager.event_queue,
            ui_queue=self.ui_queue,
            database=self.database,
            session_id=self.current_session_id
        )
        
        logger.info("All components initialized")
    
    def _initialize_post_processing_clients(self) -> None:
        """Initialize optional post-processing clients."""
        # Hume AI client
        hume_key = self.config.get_hume_api_key()
        if hume_key:
            try:
                self.hume_client = HumeExpressionClient(api_key=hume_key)
                logger.info("Hume AI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Hume AI client: {e}")
        
        # Memories.ai client
        mem_key = self.config.get_memories_api_key()
        if mem_key:
            try:
                self.memories_client = MemoriesClient(api_key=mem_key)
                logger.info("Memories.ai client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Memories.ai client: {e}")
        
        # Report generator
        self.report_generator = ReportGenerator(
            database=self.database,
            hume_client=self.hume_client,
            memories_client=self.memories_client
        )
    
    def _start_components(self) -> None:
        """Start all session components in correct order."""
        logger.info("Starting session components...")
        
        # Start video recorders
        if self.webcam_recorder:
            self.webcam_recorder.start()
            logger.info("Webcam recorder started")
        
        if self.screen_recorder:
            self.screen_recorder.start()
            logger.info("Screen recorder started")
        
        # Start uploader worker pool
        if self.snapshot_uploader:
            self.snapshot_uploader.start()
            logger.info("Snapshot uploader started")
        
        # Start fusion engine
        if self.fusion_engine:
            self.fusion_engine.start()
            logger.info("Fusion engine started")
        
        # Start distraction detector
        if self.distraction_detector:
            self.distraction_detector.start()
            logger.info("Distraction detector started")
        
        # Start snapshot scheduler (last, so everything is ready)
        if self.snapshot_scheduler:
            self.snapshot_scheduler.start()
            logger.info("Snapshot scheduler started")
        
        logger.info("All components started")
    
    def pause_session(self) -> None:
        """Pause the current session."""
        if not self.current_session:
            raise RuntimeError("No active session to pause")
        
        logger.info("Pausing session...")
        
        # Pause snapshot scheduler
        if self.snapshot_scheduler:
            self.snapshot_scheduler.pause()
        
        # Update database
        self.database.update_session_status(
            self.current_session_id,
            SessionStatus.PAUSED
        )
        
        logger.info("Session paused")
    
    def resume_session(self) -> None:
        """Resume a paused session."""
        if not self.current_session:
            raise RuntimeError("No active session to resume")
        
        logger.info("Resuming session...")
        
        # Resume snapshot scheduler
        if self.snapshot_scheduler:
            self.snapshot_scheduler.resume()
        
        # Update database
        self.database.update_session_status(
            self.current_session_id,
            SessionStatus.ACTIVE
        )
        
        logger.info("Session resumed")
    
    def stop_session(self) -> Optional[str]:
        """
        Stop the current session and cleanup.
        
        Returns:
            Session ID of stopped session
        """
        if not self.current_session:
            raise RuntimeError("No active session to stop")
        
        logger.info(f"Stopping session: {self.current_session_id}")
        
        # Stop snapshot scheduler first (no more captures)
        if self.snapshot_scheduler:
            self.snapshot_scheduler.stop()
            logger.info("Snapshot scheduler stopped")
        
        # Wait for uploader to finish pending uploads
        if self.snapshot_uploader:
            logger.info("Waiting for uploads to complete...")
            self.snapshot_uploader.wait_for_completion(timeout=30.0)
            self.snapshot_uploader.stop()
            logger.info("Snapshot uploader stopped")
        
        # Stop fusion engine
        if self.fusion_engine:
            self.fusion_engine.stop()
            logger.info("Fusion engine stopped")
        
        # Stop distraction detector
        if self.distraction_detector:
            self.distraction_detector.stop()
            logger.info("Distraction detector stopped")
        
        # Stop video recorders
        if self.webcam_recorder:
            self.webcam_recorder.stop()
            logger.info("Webcam recorder stopped")
        
        if self.screen_recorder:
            self.screen_recorder.stop()
            logger.info("Screen recorder stopped")
        
        # Update session in database
        self.database.end_session(self.current_session_id, datetime.now())
        
        # Get final stats
        stats = self.get_session_stats()
        logger.info(
            f"Session ended: {stats['total_snapshots']} snapshots, "
            f"{stats['total_events']} distractions"
        )
        
        # Generate session report
        if self.report_generator:
            try:
                logger.info("Generating session report...")
                report = self.report_generator.generate(
                    session_id=self.current_session_id,
                    data_dir=self.config.get_data_dir()
                )
                
                # Export to JSON file
                reports_dir = self.config.get_reports_dir()
                report_path = reports_dir / f"{self.current_session_id}_report.json"
                self.report_generator.export_to_json(report, report_path)
                
                logger.info(f"Session report generated: {report_path}")
                
                # TODO: Optionally run cloud analysis (Hume AI, Memories.ai)
                # This could be done in background after session ends
                
            except Exception as e:
                logger.error(f"Failed to generate report: {e}", exc_info=True)
        
        # Cleanup
        session_id_for_return = self.current_session_id
        self.current_session = None
        self.current_session_id = None
        
        logger.info("Session stopped successfully")
        
        return session_id_for_return
    
    def get_session_stats(self) -> dict:
        """Get current session statistics."""
        if not self.current_session:
            return {
                "total_snapshots": 0,
                "uploaded_snapshots": 0,
                "failed_snapshots": 0,
                "total_events": 0,
                "focus_ratio": 0.0
            }
        
        # Update stats from live components
        self._update_session_stats()
        
        # Get updated session from database
        session = self.database.get_session(self.current_session_id)
        if not session:
            return {}
        
        # Calculate focus ratio
        events = self.database.get_session_events(self.current_session_id)
        total_distraction_time = sum(e.duration_seconds for e in events)
        
        if session.started_at:
            total_time = (datetime.now() - session.started_at).total_seconds()
            focus_ratio = max(0.0, (total_time - total_distraction_time) / total_time) if total_time > 0 else 0.0
        else:
            focus_ratio = 0.0
        
        return {
            "total_snapshots": session.total_snapshots,
            "uploaded_snapshots": session.uploaded_snapshots,
            "failed_snapshots": session.failed_snapshots,
            "total_events": session.total_events,
            "focus_ratio": focus_ratio
        }
    
    def _update_session_stats(self) -> None:
        """Update session statistics in database from live components."""
        if not self.current_session_id:
            return
        
        # Get stats from components
        total_snapshots = 0
        uploaded_snapshots = 0
        failed_snapshots = 0
        
        if self.snapshot_scheduler:
            scheduler_stats = self.snapshot_scheduler.get_stats()
            total_snapshots = scheduler_stats.total_captured
        
        if self.snapshot_uploader:
            uploader_stats = self.snapshot_uploader.get_stats()
            uploaded_snapshots = uploader_stats.total_uploaded
            failed_snapshots = uploader_stats.total_failed
        
        # Count events from database
        events = self.database.get_session_events(self.current_session_id)
        total_events = len(events)
        
        # Update database
        self.database.update_session_stats(
            self.current_session_id,
            total_snapshots=total_snapshots,
            uploaded_snapshots=uploaded_snapshots,
            failed_snapshots=failed_snapshots,
            total_events=total_events
        )
    
    def is_session_active(self) -> bool:
        """Check if a session is currently active."""
        return self.current_session is not None
    
    def get_current_session_id(self) -> Optional[str]:
        """Get current session ID if active."""
        return self.current_session_id

