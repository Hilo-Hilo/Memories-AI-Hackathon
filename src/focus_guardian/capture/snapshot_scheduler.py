"""
Wall-clock based snapshot capture scheduler.

Captures camera and screen snapshots at regular intervals (default 60s)
independent of video frame rate. Uses threading.Timer for wall-clock accuracy.
"""

import threading
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime
from dataclasses import dataclass
from queue import Queue

from ..core.models import Snapshot, SnapshotKind, UploadStatus
from ..capture.screen_capture import ScreenCapture, WebcamCapture
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SnapshotPair:
    """Pair of snapshots captured at the same time."""
    cam_snapshot: Snapshot          # Camera snapshot
    screen_snapshot: Optional[Snapshot]  # Screen snapshot (if enabled)
    timestamp: datetime
    session_id: str


@dataclass
class SchedulerStats:
    """Snapshot scheduler statistics."""
    total_captured: int
    last_capture_time: Optional[datetime]
    next_capture_time: Optional[datetime]
    is_running: bool
    is_paused: bool


class SnapshotScheduler:
    """Wall-clock based snapshot capture scheduler."""
    
    def __init__(
        self,
        session_id: str,
        interval_sec: int,
        snapshots_dir: Path,
        upload_queue: Queue,
        screen_enabled: bool = True,
        jpeg_quality: int = 85
    ):
        """
        Initialize snapshot scheduler.
        
        Args:
            session_id: Current session ID
            interval_sec: Snapshot interval in seconds (default 60)
            snapshots_dir: Directory to save snapshots
            upload_queue: Queue to send snapshot pairs for upload
            screen_enabled: Whether to capture screen snapshots
            jpeg_quality: JPEG compression quality (0-100)
        """
        self.session_id = session_id
        self.interval_sec = interval_sec
        self.snapshots_dir = snapshots_dir
        self.upload_queue = upload_queue
        self.screen_enabled = screen_enabled
        self.jpeg_quality = jpeg_quality
        
        # Ensure snapshot directory exists
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize capture devices
        try:
            self.webcam = WebcamCapture(camera_index=0, jpeg_quality=jpeg_quality)
            logger.info("Webcam capture initialized")
        except Exception as e:
            logger.error(f"Failed to initialize webcam: {e}")
            raise
        
        if screen_enabled:
            try:
                self.screen_capture = ScreenCapture(monitor_index=0, jpeg_quality=jpeg_quality)
                logger.info("Screen capture initialized")
            except Exception as e:
                logger.error(f"Failed to initialize screen capture: {e}")
                raise
        else:
            self.screen_capture = None
        
        # State
        self._running = False
        self._paused = False
        self._timer: Optional[threading.Timer] = None
        self._total_captured = 0
        self._last_capture_time: Optional[datetime] = None
        self._next_capture_time: Optional[datetime] = None
        
        logger.info(
            f"Snapshot scheduler initialized: interval={interval_sec}s, "
            f"screen_enabled={screen_enabled}"
        )
    
    def start(self) -> None:
        """Start scheduler in background thread."""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._paused = False
        self._schedule_next_capture()
        
        logger.info("Snapshot scheduler started")
    
    def stop(self) -> None:
        """Stop scheduler and wait for completion."""
        if not self._running:
            return
        
        logger.info("Stopping snapshot scheduler...")
        self._running = False
        
        # Cancel pending timer
        if self._timer:
            self._timer.cancel()
            self._timer = None
        
        # Cleanup capture devices
        if self.webcam:
            self.webcam.close()
        if self.screen_capture:
            self.screen_capture.close()
        
        logger.info(f"Snapshot scheduler stopped (total captured: {self._total_captured})")
    
    def pause(self) -> None:
        """Pause snapshot capture."""
        if not self._running or self._paused:
            return
        
        self._paused = True
        
        # Cancel pending timer
        if self._timer:
            self._timer.cancel()
            self._timer = None
        
        logger.info("Snapshot scheduler paused")
    
    def resume(self) -> None:
        """Resume snapshot capture."""
        if not self._running or not self._paused:
            return
        
        self._paused = False
        self._schedule_next_capture()
        
        logger.info("Snapshot scheduler resumed")
    
    def _schedule_next_capture(self) -> None:
        """Schedule next snapshot capture."""
        if not self._running or self._paused:
            return
        
        self._timer = threading.Timer(self.interval_sec, self._capture_snapshots)
        self._timer.daemon = True
        self._timer.start()
        
        from datetime import timedelta
        self._next_capture_time = datetime.now() + timedelta(seconds=self.interval_sec)
    
    def _capture_snapshots(self) -> None:
        """Capture camera and screen snapshots."""
        if not self._running or self._paused:
            return
        
        try:
            timestamp = datetime.now()
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
            
            # Capture camera snapshot
            cam_snapshot_id = str(uuid.uuid4())
            cam_path = self.snapshots_dir / f"cam_{timestamp_str}.jpg"
            cam_success, cam_size = self.webcam.capture_to_file(cam_path)
            
            if not cam_success:
                logger.error("Failed to capture camera snapshot")
                self._schedule_next_capture()  # Continue even if capture fails
                return
            
            cam_snapshot = Snapshot(
                snapshot_id=cam_snapshot_id,
                session_id=self.session_id,
                timestamp=timestamp,
                kind=SnapshotKind.CAM,
                jpeg_path=str(cam_path),  # Store absolute path
                jpeg_size_bytes=cam_size,
                upload_status=UploadStatus.PENDING
            )
            
            # Capture screen snapshot (if enabled)
            screen_snapshot = None
            if self.screen_enabled and self.screen_capture:
                screen_snapshot_id = str(uuid.uuid4())
                screen_path = self.snapshots_dir / f"screen_{timestamp_str}.jpg"
                screen_success, screen_size = self.screen_capture.capture_to_file(screen_path)
                
                if screen_success:
                    screen_snapshot = Snapshot(
                        snapshot_id=screen_snapshot_id,
                        session_id=self.session_id,
                        timestamp=timestamp,
                        kind=SnapshotKind.SCREEN,
                        jpeg_path=str(screen_path),  # Store absolute path
                        jpeg_size_bytes=screen_size,
                        upload_status=UploadStatus.PENDING
                    )
                else:
                    logger.warning("Failed to capture screen snapshot")
            
            # Create snapshot pair
            snapshot_pair = SnapshotPair(
                cam_snapshot=cam_snapshot,
                screen_snapshot=screen_snapshot,
                timestamp=timestamp,
                session_id=self.session_id
            )
            
            # Queue for upload
            self.upload_queue.put(snapshot_pair, block=False)
            
            # Update stats
            self._total_captured += 1
            self._last_capture_time = timestamp
            
            logger.info(
                f"Captured snapshot pair #{self._total_captured} "
                f"(cam: {cam_size} bytes, screen: {screen_size if screen_snapshot else 'N/A'})"
            )
        
        except Exception as e:
            logger.error(f"Error capturing snapshots: {e}", exc_info=True)
        
        finally:
            # Schedule next capture
            self._schedule_next_capture()
    
    def get_stats(self) -> SchedulerStats:
        """Get scheduler statistics."""
        return SchedulerStats(
            total_captured=self._total_captured,
            last_capture_time=self._last_capture_time,
            next_capture_time=self._next_capture_time,
            is_running=self._running,
            is_paused=self._paused
        )

