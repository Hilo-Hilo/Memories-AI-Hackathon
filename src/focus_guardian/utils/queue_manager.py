"""
Inter-thread communication queue management for Focus Guardian.

Provides thread-safe queues for communication between different modules:
- snapshot_upload_queue: scheduler → uploader workers
- fusion_queue: uploader → fusion_engine
- event_queue: fusion_engine → UI
- db_queue: events → database writer thread
"""

from queue import Queue, Empty, Full
from typing import Any, Optional
from dataclasses import dataclass

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QueueConfig:
    """Configuration for a queue."""
    name: str
    maxsize: int = 100
    timeout: float = 1.0


class QueueManager:
    """Manages all inter-thread communication queues."""
    
    def __init__(self, max_queue_size: int = 100):
        """
        Initialize queue manager with all required queues.
        
        Args:
            max_queue_size: Maximum size for each queue (prevents memory overflow)
        """
        self.max_queue_size = max_queue_size
        
        # Create all queues
        self.snapshot_upload_queue: Queue = Queue(maxsize=max_queue_size)
        self.fusion_queue: Queue = Queue(maxsize=max_queue_size)
        self.event_queue: Queue = Queue(maxsize=max_queue_size)
        self.db_queue: Queue = Queue(maxsize=max_queue_size)
        self.ui_queue: Queue = Queue(maxsize=max_queue_size)
        
        # Shutdown flag
        self._shutdown = False
        
        logger.info(f"QueueManager initialized with max_size={max_queue_size}")
    
    def put(self, queue: Queue, item: Any, timeout: Optional[float] = 1.0) -> bool:
        """
        Put item into queue with timeout.
        
        Args:
            queue: Queue to put item into
            item: Item to add
            timeout: Timeout in seconds (None = block forever)
            
        Returns:
            True if successful, False if timeout or shutdown
        """
        if self._shutdown:
            logger.warning("Attempted to put item into queue after shutdown")
            return False
        
        try:
            queue.put(item, block=True, timeout=timeout)
            return True
        except Full:
            logger.warning(f"Queue full, dropped item: {type(item).__name__}")
            return False
        except Exception as e:
            logger.error(f"Error putting item into queue: {e}")
            return False
    
    def get(self, queue: Queue, timeout: Optional[float] = 1.0) -> Optional[Any]:
        """
        Get item from queue with timeout.
        
        Args:
            queue: Queue to get item from
            timeout: Timeout in seconds (None = block forever)
            
        Returns:
            Item from queue or None if timeout or shutdown
        """
        if self._shutdown:
            return None
        
        try:
            return queue.get(block=True, timeout=timeout)
        except Empty:
            return None
        except Exception as e:
            logger.error(f"Error getting item from queue: {e}")
            return None
    
    def get_nowait(self, queue: Queue) -> Optional[Any]:
        """
        Get item from queue without blocking.
        
        Args:
            queue: Queue to get item from
            
        Returns:
            Item from queue or None if empty
        """
        try:
            return queue.get_nowait()
        except Empty:
            return None
        except Exception as e:
            logger.error(f"Error getting item from queue: {e}")
            return None
    
    def qsize(self, queue: Queue) -> int:
        """Get approximate queue size."""
        try:
            return queue.qsize()
        except Exception:
            return 0
    
    def shutdown(self) -> None:
        """Signal shutdown to all queues."""
        self._shutdown = True
        logger.info("QueueManager shutdown initiated")
    
    def is_shutdown(self) -> bool:
        """Check if shutdown has been initiated."""
        return self._shutdown
    
    def clear_all(self) -> None:
        """Clear all queues (useful for testing or reset)."""
        for queue in [
            self.snapshot_upload_queue,
            self.fusion_queue,
            self.event_queue,
            self.db_queue,
            self.ui_queue
        ]:
            while not queue.empty():
                try:
                    queue.get_nowait()
                except Empty:
                    break
        
        logger.debug("All queues cleared")
    
    def get_stats(self) -> dict:
        """Get statistics for all queues."""
        return {
            "snapshot_upload_queue": self.qsize(self.snapshot_upload_queue),
            "fusion_queue": self.qsize(self.fusion_queue),
            "event_queue": self.qsize(self.event_queue),
            "db_queue": self.qsize(self.db_queue),
            "ui_queue": self.qsize(self.ui_queue),
            "max_size": self.max_queue_size,
            "shutdown": self._shutdown
        }

