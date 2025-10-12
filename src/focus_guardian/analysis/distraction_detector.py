"""
Distraction detector with business rules.

Processes state transitions from fusion engine and applies business logic
to determine when to emit distraction alerts. Tracks patterns over time.
"""

import uuid
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from queue import Queue, Empty
from collections import deque

from ..core.models import (
    DistractionEvent, DistractionType, State, StateTransition
)
from ..core.database import Database
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DistractionDetector:
    """Detects and emits distraction events based on state transitions."""
    
    def __init__(
        self,
        event_queue: Queue,
        ui_queue: Queue,
        database: Database,
        session_id: str,
        alert_threshold_minutes: float = 0.5  # Min duration to trigger alert
    ):
        """
        Initialize distraction detector.
        
        Args:
            event_queue: Queue to receive state transitions
            ui_queue: Queue to send UI notifications
            database: Database for persisting events
            session_id: Current session ID
            alert_threshold_minutes: Minimum distraction duration for alert
        """
        self.event_queue = event_queue
        self.ui_queue = ui_queue
        self.database = database
        self.session_id = session_id
        self.alert_threshold_minutes = alert_threshold_minutes
        
        # Track current distraction
        self._current_distraction_start: Optional[datetime] = None
        self._current_distraction_state: Optional[State] = None
        self._current_distraction_evidence: Dict = {}
        
        # Track recent alerts (for micro-break suggestions)
        self._recent_alerts: deque = deque(maxlen=20)  # Last 20 alerts
        
        # Thread control
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        logger.info(
            f"Distraction detector initialized (threshold: {alert_threshold_minutes} min)"
        )
    
    def start(self) -> None:
        """Start detector thread."""
        if self._running:
            return
        
        self._running = True
        self._stop_event.clear()
        
        self._thread = threading.Thread(
            target=self._detector_loop,
            name="distraction-detector",
            daemon=True
        )
        self._thread.start()
        
        logger.info("Distraction detector started")
    
    def stop(self, timeout: float = 5.0) -> None:
        """Stop detector thread."""
        if not self._running:
            return
        
        logger.info("Stopping distraction detector...")
        self._running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=timeout)
        
        logger.info("Distraction detector stopped")
    
    def _detector_loop(self) -> None:
        """Main detector loop processing events from queue."""
        logger.debug("Detector loop started")
        
        while not self._stop_event.is_set():
            try:
                # Get event from queue
                try:
                    message = self.event_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                if not message:
                    continue
                
                # Process message
                msg_type = message.get("type")
                
                if msg_type == "state_transition":
                    transition = message.get("transition")
                    if transition:
                        self.process_transition(transition)
                
                # Mark task done
                self.event_queue.task_done()
            
            except Exception as e:
                logger.error(f"Detector loop error: {e}", exc_info=True)
        
        logger.debug("Detector loop stopped")
    
    def process_transition(self, transition: StateTransition) -> None:
        """
        Process state transition and apply business rules.
        
        Args:
            transition: StateTransition from fusion engine
        """
        from_state = transition.from_state
        to_state = transition.to_state
        
        # Handle transition TO distracted/absent state
        if to_state in [State.DISTRACTED, State.ABSENT]:
            self._start_distraction(to_state, transition)
        
        # Handle transition FROM distracted/absent TO focused
        elif from_state in [State.DISTRACTED, State.ABSENT] and to_state == State.FOCUSED:
            self._end_distraction(transition)
        
        # Check for micro-break suggestion
        self._check_micro_break_needed()
    
    def _start_distraction(self, state: State, transition: StateTransition) -> None:
        """Start tracking a distraction episode and emit immediate alert."""
        if self._current_distraction_start is not None:
            # Already tracking a distraction
            logger.debug("Already tracking distraction, updating evidence")
            self._current_distraction_evidence = transition.evidence
            return
        
        self._current_distraction_start = transition.timestamp
        self._current_distraction_state = state
        self._current_distraction_evidence = transition.evidence
        
        logger.info(f"Started tracking distraction: {state.value}")
        
        # Emit IMMEDIATE alert when distraction detected (don't wait for it to end)
        self._emit_immediate_alert(
            state=state,
            started_at=transition.timestamp,
            evidence=transition.evidence,
            confidence=transition.confidence
        )
    
    def _end_distraction(self, transition: StateTransition) -> None:
        """End distraction tracking and emit event if threshold met."""
        if self._current_distraction_start is None:
            logger.debug("No distraction to end")
            return
        
        # Calculate duration
        duration = (transition.timestamp - self._current_distraction_start).total_seconds()
        duration_minutes = duration / 60.0
        
        # Only emit event if duration exceeds threshold
        if duration_minutes >= self.alert_threshold_minutes:
            self._emit_distraction_event(
                started_at=self._current_distraction_start,
                ended_at=transition.timestamp,
                duration_seconds=duration,
                evidence=self._current_distraction_evidence,
                confidence=transition.confidence
            )
        else:
            logger.debug(
                f"Distraction too brief ({duration_minutes:.2f} min), "
                f"not emitting event"
            )
        
        # Reset tracking
        self._current_distraction_start = None
        self._current_distraction_state = None
        self._current_distraction_evidence = {}
    
    def _emit_distraction_event(
        self,
        started_at: datetime,
        ended_at: datetime,
        duration_seconds: float,
        evidence: Dict,
        confidence: float
    ) -> None:
        """Emit distraction event to database and UI."""
        # Determine distraction type from evidence
        distraction_type = self._classify_distraction_type(evidence)
        
        # Extract vision votes from evidence
        cam_labels = evidence.get("cam_labels", {})
        screen_labels = evidence.get("screen_labels", {})
        
        # Build vision votes dict (label -> count across K snapshots)
        vision_votes = {}
        for label, data in cam_labels.items():
            if isinstance(data, dict) and "count" in data:
                vision_votes[label] = data["count"]
        for label, data in screen_labels.items():
            if isinstance(data, dict) and "count" in data:
                vision_votes[label] = data["count"]
        
        # Create evidence string
        evidence_str = self._build_evidence_string(evidence)
        
        # Create distraction event
        event = DistractionEvent(
            event_id=str(uuid.uuid4()),
            session_id=self.session_id,
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration_seconds,
            event_type=distraction_type,
            evidence=evidence_str,
            confidence=confidence,
            vision_votes=vision_votes,
            snapshot_refs=[],  # Will be populated if needed
            acknowledged=False
        )
        
        # Save to database
        try:
            self.database.insert_distraction_event(event)
            logger.info(
                f"Distraction event created: {distraction_type.value} "
                f"({duration_seconds:.1f}s, confidence: {confidence:.2f})"
            )
        except Exception as e:
            logger.error(f"Failed to save distraction event: {e}")
        
        # Send UI notification
        self._send_ui_notification(event)
        
        # Track for micro-break suggestions
        self._recent_alerts.append({
            "timestamp": ended_at,
            "type": distraction_type,
            "duration": duration_seconds
        })
    
    def _classify_distraction_type(self, evidence: Dict) -> DistractionType:
        """Classify distraction type from evidence."""
        cam_labels = evidence.get("cam_labels", {})
        screen_labels = evidence.get("screen_labels", {})
        
        # Check camera labels first (higher priority)
        if "Absent" in cam_labels:
            return DistractionType.ABSENT
        if "PhoneLikely" in cam_labels:
            return DistractionType.PHONE
        if "MicroSleep" in cam_labels:
            return DistractionType.MICRO_SLEEP
        if "HeadAway" in cam_labels or "EyesOffScreen" in cam_labels:
            # Check screen for more specific type
            if "VideoOnScreen" in screen_labels:
                return DistractionType.VIDEO
            if "SocialFeed" in screen_labels:
                return DistractionType.SOCIAL
            if "ChatWindow" in screen_labels:
                return DistractionType.CHAT
            return DistractionType.LOOK_AWAY
        
        # Check screen labels
        if "VideoOnScreen" in screen_labels:
            return DistractionType.VIDEO
        if "SocialFeed" in screen_labels:
            return DistractionType.SOCIAL
        if "ChatWindow" in screen_labels:
            return DistractionType.CHAT
        if "Games" in screen_labels:
            return DistractionType.SOCIAL  # Using SOCIAL as proxy for Games
        
        return DistractionType.UNKNOWN
    
    def _build_evidence_string(self, evidence: Dict) -> str:
        """Build human-readable evidence string."""
        parts = []
        
        reason = evidence.get("reason", "")
        if reason:
            parts.append(reason)
        
        cam_distracted = evidence.get("cam_distracted", False)
        screen_distracted = evidence.get("screen_distracted", False)
        
        if cam_distracted:
            parts.append("Camera detected inattention")
        if screen_distracted:
            parts.append("Screen showed distracting content")
        
        if not parts:
            parts.append("Pattern-confirmed distraction")
        
        return "; ".join(parts)
    
    def _emit_immediate_alert(
        self,
        state: State,
        started_at: datetime,
        evidence: Dict,
        confidence: float
    ) -> None:
        """Emit immediate alert when distraction starts (don't wait for it to end)."""
        # Determine distraction type
        distraction_type = self._classify_distraction_type(evidence)
        
        # Extract vision votes
        cam_labels = evidence.get("cam_labels", {})
        screen_labels = evidence.get("screen_labels", {})
        
        vision_votes = {}
        for label, data in cam_labels.items():
            if isinstance(data, dict) and "count" in data:
                vision_votes[label] = data["count"]
        for label, data in screen_labels.items():
            if isinstance(data, dict) and "count" in data:
                vision_votes[label] = data["count"]
        
        # Send IMMEDIATE UI alert (before creating the full event)
        logger.info(f"🔔 IMMEDIATE ALERT: {distraction_type.value} detected!")
        
        try:
            self.ui_queue.put({
                "type": "distraction_alert",
                "event": None,  # No event yet, just alerting
                "message": f"🔔 {distraction_type.value} detected!",
                "distraction_type": distraction_type.value,
                "confidence": confidence,
                "vision_votes": vision_votes
            }, block=False)
            logger.info("Alert sent to UI queue")
        except Exception as e:
            logger.error(f"Failed to send immediate alert: {e}")
    
    def _send_ui_notification(self, event: DistractionEvent) -> None:
        """Send notification to UI queue."""
        try:
            self.ui_queue.put({
                "type": "distraction_alert",
                "event": event,
                "message": f"{event.event_type.value} detected ({event.duration_seconds:.0f}s)"
            }, block=False)
        except Exception as e:
            logger.error(f"Failed to send UI notification: {e}")
    
    def _check_micro_break_needed(self) -> None:
        """Check if user needs a micro-break based on recent alerts."""
        if len(self._recent_alerts) < 3:
            return
        
        # Check if ≥3 distractions in last 20 minutes
        now = datetime.now()
        recent = [
            a for a in self._recent_alerts
            if (now - a["timestamp"]).total_seconds() < 1200  # 20 minutes
        ]
        
        if len(recent) >= 3:
            logger.info(
                f"Detected {len(recent)} distractions in 20 minutes, "
                f"suggesting micro-break"
            )
            
            # Send micro-break suggestion to UI
            try:
                self.ui_queue.put({
                    "type": "micro_break_suggestion",
                    "message": "You've been distracted frequently. Consider a 5-minute break.",
                    "distraction_count": len(recent)
                }, block=False)
            except Exception as e:
                logger.error(f"Failed to send micro-break suggestion: {e}")

