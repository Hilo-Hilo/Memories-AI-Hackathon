"""
Worker pool for uploading snapshots to OpenAI Vision API.

Implements a multi-threaded worker pool pattern with MAX_PARALLEL_UPLOADS workers
that process snapshots from the upload queue, call OpenAI Vision API, save results,
and forward to the fusion engine.
"""

import threading
import time
import json
from pathlib import Path
from typing import Optional
from queue import Queue, Empty
from dataclasses import dataclass
from datetime import datetime

from ..core.models import UploadStatus, Snapshot
from ..core.database import Database
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class UploaderStats:
    """Snapshot uploader statistics."""
    total_uploaded: int
    total_failed: int
    queue_size: int
    active_workers: int


class SnapshotUploader:
    """Worker pool for uploading snapshots to OpenAI Vision API."""
    
    def __init__(
        self,
        num_workers: int,
        upload_queue: Queue,
        fusion_queue: Queue,
        database: Database,
        vision_client,  # Type: OpenAIVisionClient (will be imported in Phase 3)
        max_retries: int = 3,
        retry_backoff: float = 2.0
    ):
        """
        Initialize snapshot uploader worker pool.
        
        Args:
            num_workers: Number of parallel upload workers
            upload_queue: Queue of SnapshotPair objects to upload
            fusion_queue: Queue to send results to fusion engine
            database: Database for logging results
            vision_client: OpenAI Vision API client
            max_retries: Maximum retry attempts per snapshot
            retry_backoff: Exponential backoff factor for retries
        """
        self.num_workers = num_workers
        self.upload_queue = upload_queue
        self.fusion_queue = fusion_queue
        self.database = database
        self.vision_client = vision_client
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        
        # State
        self._running = False
        self._workers: list[threading.Thread] = []
        self._stop_event = threading.Event()
        
        # Stats
        self._total_uploaded = 0
        self._total_failed = 0
        self._stats_lock = threading.Lock()
        
        logger.info(f"Snapshot uploader initialized with {num_workers} workers")
    
    def start(self) -> None:
        """Start worker pool."""
        if self._running:
            logger.warning("Uploader already running")
            return
        
        self._running = True
        self._stop_event.clear()
        
        # Start worker threads
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"uploader-worker-{i}",
                daemon=True,
                args=(i,)
            )
            worker.start()
            self._workers.append(worker)
        
        logger.info(f"Started {self.num_workers} uploader workers")
    
    def stop(self, timeout: float = 10.0) -> None:
        """Stop workers and wait for completion."""
        if not self._running:
            return
        
        logger.info("Stopping snapshot uploader...")
        self._running = False
        self._stop_event.set()
        
        # Wait for workers to finish
        for worker in self._workers:
            worker.join(timeout=timeout / self.num_workers)
            if worker.is_alive():
                logger.warning(f"Worker {worker.name} did not stop within timeout")
        
        self._workers.clear()
        logger.info(
            f"Snapshot uploader stopped "
            f"(uploaded: {self._total_uploaded}, failed: {self._total_failed})"
        )
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Block until upload queue is empty.
        
        Args:
            timeout: Maximum time to wait (None = wait forever)
            
        Returns:
            True if queue is empty, False if timeout
        """
        start_time = time.time()
        
        while not self.upload_queue.empty():
            if timeout and (time.time() - start_time) > timeout:
                logger.warning("Timeout waiting for upload queue to empty")
                return False
            time.sleep(0.1)
        
        logger.info("Upload queue is empty")
        return True
    
    def _worker_loop(self, worker_id: int) -> None:
        """Main worker loop."""
        logger.debug(f"Worker {worker_id} started")
        
        while not self._stop_event.is_set():
            try:
                # Get snapshot pair from queue (with timeout)
                try:
                    snapshot_pair = self.upload_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Check if we're still running before processing
                if not self._running:
                    logger.debug(f"Worker {worker_id} stopping, skipping snapshot")
                    self.upload_queue.task_done()
                    break
                
                # Process snapshot pair
                self._process_snapshot_pair(snapshot_pair, worker_id)
                
                # Mark task as done
                self.upload_queue.task_done()
            
            except Exception as e:
                # Only log errors if we're still supposed to be running
                if self._running:
                    logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                else:
                    logger.debug(f"Worker {worker_id} error during shutdown (ignored): {e}")
                
                # Make sure to mark task as done even on error
                try:
                    self.upload_queue.task_done()
                except:
                    pass
        
        logger.debug(f"Worker {worker_id} stopped")
    
    def _process_snapshot_pair(self, snapshot_pair, worker_id: int) -> None:
        """
        Process a snapshot pair (upload to Vision API and save results).
        
        Args:
            snapshot_pair: SnapshotPair object
            worker_id: Worker ID for logging
        """
        from ..capture.snapshot_scheduler import SnapshotPair
        
        session_id = snapshot_pair.session_id
        timestamp = snapshot_pair.timestamp
        
        # Insert snapshots into database
        self.database.insert_snapshot(snapshot_pair.cam_snapshot)
        if snapshot_pair.screen_snapshot:
            self.database.insert_snapshot(snapshot_pair.screen_snapshot)
        
        # Process camera snapshot
        cam_result = self._upload_snapshot(
            snapshot_pair.cam_snapshot,
            "cam",
            worker_id
        )
        
        # Process screen snapshot (if present)
        screen_result = None
        if snapshot_pair.screen_snapshot:
            screen_result = self._upload_snapshot(
                snapshot_pair.screen_snapshot,
                "screen",
                worker_id
            )
        
        # If both uploads successful, send to fusion queue
        if cam_result and (screen_result or not snapshot_pair.screen_snapshot):
            fusion_message = {
                "snapshot_id": snapshot_pair.cam_snapshot.snapshot_id,
                "session_id": session_id,
                "timestamp": timestamp,
                "cam_result": cam_result,
                "screen_result": screen_result
            }
            
            try:
                self.fusion_queue.put(fusion_message, block=False)
            except Exception as e:
                logger.error(f"Failed to queue fusion message: {e}")
    
    def _upload_snapshot(
        self,
        snapshot: Snapshot,
        kind: str,
        worker_id: int
    ) -> Optional[dict]:
        """
        Upload single snapshot to OpenAI Vision API with retry logic.
        
        Args:
            snapshot: Snapshot object
            kind: "cam" or "screen"
            worker_id: Worker ID for logging
            
        Returns:
            VisionResult dict or None if all retries failed
        """
        snapshot_id = snapshot.snapshot_id
        jpeg_path = Path(snapshot.jpeg_path)
        
        # Path should already be absolute from scheduler
        if not jpeg_path.exists():
            logger.error(f"Snapshot file not found: {jpeg_path}")
            return None
        
        for attempt in range(self.max_retries):
            try:
                # Update status to uploading
                self.database.update_snapshot_upload_status(
                    snapshot_id,
                    UploadStatus.UPLOADING
                )
                
                # Call OpenAI Vision API
                if kind == "cam":
                    vision_result = self.vision_client.classify_cam_snapshot(jpeg_path)
                else:
                    vision_result = self.vision_client.classify_screen_snapshot(jpeg_path)
                
                # Save vision result to JSON file
                vision_dir = jpeg_path.parent.parent / "vision"
                vision_dir.mkdir(parents=True, exist_ok=True)
                vision_json_path = vision_dir / f"{jpeg_path.stem}.json"
                
                with open(vision_json_path, 'w') as f:
                    json.dump(vision_result.raw_response, f, indent=2)
                
                # Update database with results
                self.database.update_snapshot_vision_results(
                    snapshot_id,
                    vision_result.labels,
                    str(vision_json_path.relative_to(vision_json_path.parent.parent.parent)),
                    datetime.now()
                )
                
                # Update stats
                with self._stats_lock:
                    self._total_uploaded += 1
                
                logger.debug(
                    f"Worker {worker_id} uploaded {kind} snapshot {snapshot_id[:8]} "
                    f"(latency: {vision_result.latency_ms:.0f}ms)"
                )
                
                return {
                    "labels": vision_result.labels,
                    "latency_ms": vision_result.latency_ms,
                    "processed_at": vision_result.processed_at
                }
            
            except Exception as e:
                logger.warning(
                    f"Worker {worker_id} upload attempt {attempt + 1}/{self.max_retries} "
                    f"failed for {kind} snapshot {snapshot_id[:8]}: {e}"
                )
                
                # Update retry count in database
                self.database.update_snapshot_upload_status(
                    snapshot_id,
                    UploadStatus.FAILED,
                    error_message=str(e),
                    increment_retry=True
                )
                
                # Exponential backoff before retry
                if attempt < self.max_retries - 1:
                    backoff_time = self.retry_backoff ** attempt
                    time.sleep(backoff_time)
                else:
                    # Final failure
                    with self._stats_lock:
                        self._total_failed += 1
                    logger.error(
                        f"Worker {worker_id} permanently failed to upload {kind} "
                        f"snapshot {snapshot_id[:8]} after {self.max_retries} attempts"
                    )
        
        return None
    
    def get_stats(self) -> UploaderStats:
        """Get uploader statistics."""
        with self._stats_lock:
            return UploaderStats(
                total_uploaded=self._total_uploaded,
                total_failed=self._total_failed,
                queue_size=self.upload_queue.qsize(),
                active_workers=len([w for w in self._workers if w.is_alive()])
            )

