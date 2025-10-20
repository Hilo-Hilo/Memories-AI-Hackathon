"""
State machine for focus state tracking with K=3 hysteresis voting.

Implements the core pattern detection logic: requires K consecutive snapshots
spanning ≥1 minute to confirm a state transition, eliminating false positives.

Now supports dynamic label profiles for customizable detection.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Set
from collections import deque

from ..core.models import (
    State, FocusState, SnapshotResult, StateTransition,
    CAM_DISTRACTION_LABELS, CAM_FOCUS_LABELS, CAM_ABSENCE_LABELS,
    SCREEN_DISTRACTION_LABELS, SCREEN_FOCUS_LABELS
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StateMachine:
    """State machine with K-snapshot hysteresis voting."""
    
    def __init__(
        self,
        K: int = 3,
        min_span_minutes: float = 1.0,
        label_profile=None  # Optional LabelProfile instance
    ):
        """
        Initialize state machine.
        
        Args:
            K: Number of snapshots for hysteresis voting (default 3)
            min_span_minutes: Minimum time span across K snapshots (default 1.0)
            label_profile: Optional LabelProfile for custom labels (uses hardcoded if None)
        """
        self.K = K
        self.min_span_minutes = min_span_minutes
        self.min_span_seconds = min_span_minutes * 60
        
        # Label sets for voting (dynamic or hardcoded fallback)
        if label_profile:
            self.cam_distraction_labels = label_profile.get_cam_labels_by_category("distraction")
            self.cam_focus_labels = label_profile.get_cam_labels_by_category("focus")
            self.cam_absence_labels = label_profile.get_cam_labels_by_category("absence")
            self.screen_distraction_labels = label_profile.get_screen_labels_by_category("distraction")
            self.screen_focus_labels = label_profile.get_screen_labels_by_category("focus")
            logger.info(f"State machine using custom label profile: {label_profile.name}")
        else:
            # Fallback to hardcoded labels
            self.cam_distraction_labels = CAM_DISTRACTION_LABELS
            self.cam_focus_labels = CAM_FOCUS_LABELS
            self.cam_absence_labels = CAM_ABSENCE_LABELS
            self.screen_distraction_labels = SCREEN_DISTRACTION_LABELS
            self.screen_focus_labels = SCREEN_FOCUS_LABELS
            logger.info("State machine using hardcoded labels (no profile specified)")
        
        # Current state
        self._current_state = State.FOCUSED
        self._entered_at = datetime.now()
        self._confidence = 0.5
        
        # Rolling buffer of last K snapshots
        self._snapshot_buffer: deque[SnapshotResult] = deque(maxlen=K)
        
        logger.info(
            f"State machine initialized: K={K}, min_span={min_span_minutes} min"
        )
    
    def update(self, snapshot_result: SnapshotResult) -> Optional[StateTransition]:
        """
        Process new snapshot result and determine if state transition occurs.
        
        Args:
            snapshot_result: SnapshotResult with cam/screen labels
            
        Returns:
            StateTransition if state changed, None otherwise
        """
        # Add to buffer
        self._snapshot_buffer.append(snapshot_result)
        
        # Need at least K snapshots to make decision
        if len(self._snapshot_buffer) < self.K:
            logger.debug(
                f"Insufficient snapshots for voting: {len(self._snapshot_buffer)}/{self.K}"
            )
            return None
        
        # Check if span requirement is met
        span_seconds = self._get_buffer_span_seconds()
        if span_seconds < self.min_span_seconds:
            logger.debug(
                f"Insufficient span for debounce: {span_seconds:.1f}s < "
                f"{self.min_span_seconds:.1f}s"
            )
            return None
        
        # Perform voting across K snapshots
        new_state, confidence, evidence = self._vote_on_state()
        
        # Check if state changed
        if new_state != self._current_state:
            transition = StateTransition(
                from_state=self._current_state,
                to_state=new_state,
                timestamp=datetime.now(),
                confidence=confidence,
                evidence=evidence
            )
            
            logger.info(
                f"State transition: {self._current_state.value} → {new_state.value} "
                f"(confidence: {confidence:.2f}, span: {span_seconds:.1f}s)"
            )
            
            # Update state
            self._current_state = new_state
            self._entered_at = datetime.now()
            self._confidence = confidence
            
            return transition
        
        # No state change, but update confidence
        self._confidence = confidence
        return None
    
    def _vote_on_state(self) -> tuple[State, float, dict]:
        """
        Vote on state across K snapshots using hysteresis logic.
        
        Returns:
            Tuple of (new_state, confidence, evidence_dict)
        """
        # Aggregate labels across all snapshots
        cam_label_counts = {}
        screen_label_counts = {}
        
        for snapshot in self._snapshot_buffer:
            # Count camera labels
            for label, conf in snapshot.cam_labels.items():
                if label not in cam_label_counts:
                    cam_label_counts[label] = {"count": 0, "total_conf": 0.0}
                cam_label_counts[label]["count"] += 1
                cam_label_counts[label]["total_conf"] += conf
            
            # Count screen labels
            for label, conf in snapshot.screen_labels.items():
                if label not in screen_label_counts:
                    screen_label_counts[label] = {"count": 0, "total_conf": 0.0}
                screen_label_counts[label]["count"] += 1
                screen_label_counts[label]["total_conf"] += conf
        
        # Determine dominant patterns (≥2 of K snapshots)
        majority_threshold = max(2, self.K // 2 + 1)  # At least 2, or majority
        
        # Check for absence (highest priority)
        if self._has_majority(cam_label_counts, self.cam_absence_labels, majority_threshold):
            avg_conf = self._get_average_confidence(cam_label_counts, self.cam_absence_labels)
            return State.ABSENT, avg_conf, {
                "cam_labels": cam_label_counts,
                "screen_labels": screen_label_counts,
                "reason": "User absent from desk"
            }
        
        # Check for distraction
        cam_distracted = self._has_majority(
            cam_label_counts, self.cam_distraction_labels, majority_threshold
        )
        screen_distracted = self._has_majority(
            screen_label_counts, self.screen_distraction_labels, majority_threshold
        )
        
        if cam_distracted or screen_distracted:
            # Calculate combined confidence
            cam_conf = self._get_average_confidence(
                cam_label_counts, self.cam_distraction_labels
            ) if cam_distracted else 0.0
            
            screen_conf = self._get_average_confidence(
                screen_label_counts, self.screen_distraction_labels
            ) if screen_distracted else 0.0
            
            # Weight: camera evidence slightly higher (70% cam, 30% screen)
            combined_conf = 0.7 * cam_conf + 0.3 * screen_conf
            
            return State.DISTRACTED, combined_conf, {
                "cam_labels": cam_label_counts,
                "screen_labels": screen_label_counts,
                "reason": "Distraction pattern detected",
                "cam_distracted": cam_distracted,
                "screen_distracted": screen_distracted
            }
        
        # Check for focus
        cam_focused = self._has_majority(
            cam_label_counts, self.cam_focus_labels, majority_threshold
        )
        screen_focused = self._has_majority(
            screen_label_counts, self.screen_focus_labels, majority_threshold
        )
        
        if cam_focused or screen_focused:
            cam_conf = self._get_average_confidence(
                cam_label_counts, self.cam_focus_labels
            ) if cam_focused else 0.0
            
            screen_conf = self._get_average_confidence(
                screen_label_counts, self.screen_focus_labels
            ) if screen_focused else 0.0
            
            # Weight: camera evidence slightly higher
            combined_conf = 0.6 * cam_conf + 0.4 * screen_conf
            
            return State.FOCUSED, combined_conf, {
                "cam_labels": cam_label_counts,
                "screen_labels": screen_label_counts,
                "reason": "Focus pattern confirmed",
                "cam_focused": cam_focused,
                "screen_focused": screen_focused
            }
        
        # Default: maintain current state with lower confidence
        return self._current_state, 0.3, {
            "cam_labels": cam_label_counts,
            "screen_labels": screen_label_counts,
            "reason": "Ambiguous pattern, maintaining current state"
        }
    
    def _has_majority(
        self,
        label_counts: dict,
        label_set: set,
        threshold: int
    ) -> bool:
        """Check if any label from label_set appears in ≥threshold snapshots."""
        for label in label_set:
            if label in label_counts and label_counts[label]["count"] >= threshold:
                return True
        return False
    
    def _get_average_confidence(
        self,
        label_counts: dict,
        label_set: set
    ) -> float:
        """Get average confidence for labels in label_set."""
        total_conf = 0.0
        total_count = 0
        
        for label in label_set:
            if label in label_counts:
                total_conf += label_counts[label]["total_conf"]
                total_count += label_counts[label]["count"]
        
        if total_count == 0:
            return 0.0
        
        return total_conf / total_count
    
    def _get_buffer_span_seconds(self) -> float:
        """Get time span of snapshots in buffer (in seconds)."""
        if len(self._snapshot_buffer) < 2:
            return 0.0
        
        first_ts = self._snapshot_buffer[0].timestamp
        last_ts = self._snapshot_buffer[-1].timestamp
        span = (last_ts - first_ts).total_seconds()
        
        # Return minimum 0.01 seconds to prevent division by zero
        return max(span, 0.01)
    
    def get_current_state(self) -> FocusState:
        """Get current state with details."""
        duration = (datetime.now() - self._entered_at).total_seconds()
        
        return FocusState(
            state=self._current_state,
            entered_at=self._entered_at,
            duration_seconds=duration,
            snapshot_buffer=list(self._snapshot_buffer),
            confidence=self._confidence
        )
    
    def reset(self) -> None:
        """Reset state machine to initial state."""
        self._current_state = State.FOCUSED
        self._entered_at = datetime.now()
        self._confidence = 0.5
        self._snapshot_buffer.clear()
        logger.info("State machine reset")


