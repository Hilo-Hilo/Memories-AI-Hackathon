"""
Fusion engine for snapshot hysteresis voting.

Receives snapshot classification results from uploader, maintains rolling buffer,
and uses state machine to detect patterns. Emits events when state transitions occur.
"""

import threading
from queue import Queue
from typing import Optional
from datetime import datetime

from ..core.state_machine import StateMachine
from ..core.models import SnapshotResult, StateTransition, State
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FusionEngine:
    """Processes snapshot results and performs hysteresis voting."""
    
    def __init__(
        self,
        state_machine: StateMachine,
        fusion_queue: Queue,
        event_queue: Queue,
        K: int = 3,
        min_span_minutes: float = 1.0
    ):
        """
        Initialize fusion engine.
        
        Args:
            state_machine: StateMachine instance for state tracking
            fusion_queue: Queue to receive snapshot results from uploader
            event_queue: Queue to send state transitions to detector
            K: Number of snapshots for hysteresis (default 3)
            min_span_minutes: Minimum span for debounce (default 1.0)
        """
        self.state_machine = state_machine
        self.fusion_queue = fusion_queue
        self.event_queue = event_queue
        self.K = K
        self.min_span_minutes = min_span_minutes
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        logger.info(f"Fusion engine initialized (K={K}, min_span={min_span_minutes} min)")
    
    def start(self) -> None:
        """Start fusion thread."""
        if self._running:
            logger.warning("Fusion engine already running")
            return
        
        self._running = True
        self._stop_event.clear()
        
        self._thread = threading.Thread(
            target=self._fusion_loop,
            name="fusion-engine",
            daemon=True
        )
        self._thread.start()
        
        logger.info("Fusion engine started")
    
    def stop(self, timeout: float = 5.0) -> None:
        """Stop fusion thread."""
        if not self._running:
            return
        
        logger.info("Stopping fusion engine...")
        self._running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning("Fusion thread did not stop within timeout")
        
        logger.info("Fusion engine stopped")
    
    def _fusion_loop(self) -> None:
        """Main fusion processing loop."""
        logger.debug("Fusion loop started")
        
        while not self._stop_event.is_set():
            try:
                # Get snapshot result from queue (with timeout)
                fusion_message = None
                try:
                    fusion_message = self.fusion_queue.get(timeout=1.0)
                except:
                    continue
                
                if not fusion_message:
                    continue
                
                # Process snapshot result
                self._process_snapshot_result(fusion_message)
                
                # Mark task as done
                self.fusion_queue.task_done()
            
            except Exception as e:
                logger.error(f"Fusion loop error: {e}", exc_info=True)
        
        logger.debug("Fusion loop stopped")
    
    def _process_snapshot_result(self, fusion_message: dict) -> None:
        """
        Process snapshot result through state machine.
        
        Args:
            fusion_message: Dict with cam_result and screen_result
        """
        try:
            # Extract data from message
            snapshot_id = fusion_message.get("snapshot_id")
            timestamp = fusion_message.get("timestamp")
            cam_result = fusion_message.get("cam_result")
            screen_result = fusion_message.get("screen_result")
            
            if not cam_result:
                logger.warning(f"No cam result for snapshot {snapshot_id}")
                return
            
            # Calculate span from first snapshot (will be set by state machine)
            # For now, just pass 0, state machine will calculate actual span
            span_minutes = 0.0
            
            # Create SnapshotResult for state machine
            snapshot_result = SnapshotResult(
                timestamp=timestamp,
                cam_labels=cam_result.get("labels", {}),
                screen_labels=screen_result.get("labels", {}) if screen_result else {},
                span_minutes=span_minutes
            )
            
            # Update state machine
            transition = self.state_machine.update(snapshot_result)

            # If state transition occurred, emit event
            if transition:
                logger.info(
                    f"🔄 STATE TRANSITION DETECTED: {transition.from_state.value} → "
                    f"{transition.to_state.value} (confidence: {transition.confidence:.2f})"
                )
                logger.info(f"Transition evidence: {transition.evidence}")

                # Send transition to event queue for distraction detector
                try:
                    self.event_queue.put({
                        "type": "state_transition",
                        "transition": transition,
                        "snapshot_id": snapshot_id,
                        "timestamp": timestamp
                    }, block=False)
                    logger.info(f"📤 Sent transition to distraction detector queue")
                except Exception as e:
                    logger.error(f"❌ Failed to queue state transition: {e}", exc_info=True)
            else:
                logger.debug(
                    f"No state transition (current: {self.state_machine._current_state.value})"
                )
        
        except Exception as e:
            logger.error(f"Error processing snapshot result: {e}", exc_info=True)
    
    def get_current_state(self):
        """Get current focus state from state machine."""
        return self.state_machine.get_current_state()

