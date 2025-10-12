"""
Threading utilities for Focus Guardian.

Provides helpers for managing background threads with proper lifecycle
management and error handling.
"""

import threading
from typing import Callable, Optional, Any
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ManagedThread:
    """Managed thread with lifecycle controls."""
    
    def __init__(self, name: str, target: Callable, daemon: bool = True):
        """
        Initialize managed thread.
        
        Args:
            name: Thread name for logging
            target: Target function to run
            daemon: Whether thread should be daemon
        """
        self.name = name
        self.target = target
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._daemon = daemon
        self._running = False
    
    def start(self) -> None:
        """Start the thread."""
        if self._running:
            logger.warning(f"Thread {self.name} already running")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_with_error_handling,
            name=self.name,
            daemon=self._daemon
        )
        self._thread.start()
        self._running = True
        logger.info(f"Started thread: {self.name}")
    
    def _run_with_error_handling(self) -> None:
        """Run target with error handling."""
        try:
            self.target()
        except Exception as e:
            logger.error(f"Thread {self.name} crashed: {e}", exc_info=True)
        finally:
            self._running = False
            logger.info(f"Thread {self.name} stopped")
    
    def stop(self, timeout: float = 5.0) -> bool:
        """
        Stop the thread.
        
        Args:
            timeout: Maximum time to wait for thread to stop
            
        Returns:
            True if stopped successfully, False if timeout
        """
        if not self._running:
            return True
        
        logger.debug(f"Stopping thread: {self.name}")
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning(f"Thread {self.name} did not stop within timeout")
                return False
        
        self._running = False
        logger.info(f"Stopped thread: {self.name}")
        return True
    
    def is_running(self) -> bool:
        """Check if thread is running."""
        return self._running
    
    def should_stop(self) -> bool:
        """Check if stop has been requested."""
        return self._stop_event.is_set()


class ThreadPool:
    """Simple thread pool for worker threads."""
    
    def __init__(self, name: str, num_workers: int, worker_func: Callable[[int], None]):
        """
        Initialize thread pool.
        
        Args:
            name: Pool name for logging
            num_workers: Number of worker threads
            worker_func: Worker function (receives worker_id as argument)
        """
        self.name = name
        self.num_workers = num_workers
        self.worker_func = worker_func
        self.workers: list[ManagedThread] = []
    
    def start(self) -> None:
        """Start all worker threads."""
        for i in range(self.num_workers):
            worker = ManagedThread(
                name=f"{self.name}-worker-{i}",
                target=lambda worker_id=i: self.worker_func(worker_id),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started thread pool: {self.name} with {self.num_workers} workers")
    
    def stop(self, timeout: float = 5.0) -> None:
        """Stop all worker threads."""
        logger.info(f"Stopping thread pool: {self.name}")
        
        for worker in self.workers:
            worker.stop(timeout=timeout)
        
        self.workers.clear()
        logger.info(f"Stopped thread pool: {self.name}")
    
    def is_running(self) -> bool:
        """Check if any workers are running."""
        return any(worker.is_running() for worker in self.workers)

