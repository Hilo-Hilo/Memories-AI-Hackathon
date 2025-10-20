"""
SQLite database interface for Focus Guardian.

Provides a clean API for all database operations with proper error handling,
transaction management, and connection pooling.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from ..core.models import (
    Session, SessionStatus, QualityProfile,
    Snapshot, SnapshotKind, UploadStatus,
    DistractionEvent, DistractionType,
    SessionReport,
    CloudAnalysisJob, CloudProvider, CloudJobStatus, VideoType
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Database:
    """SQLite database interface with schema v1.3."""
    
    def __init__(self, db_path: Path, schema_path: Path):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
            schema_path: Path to schema.sql file
        """
        self.db_path = db_path
        self.schema_path = schema_path
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._initialize_schema()
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def _initialize_schema(self) -> None:
        """Initialize database schema from schema.sql."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        with open(self.schema_path, 'r') as f:
            schema_sql = f.read()
        
        with self._get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()
        
        logger.debug("Database schema initialized")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    # ========================================================================
    # Session Operations
    # ========================================================================
    
    def create_session(self, session: Session) -> str:
        """
        Create new session record.
        
        Args:
            session: Session object to insert
            
        Returns:
            session_id
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO sessions (
                    session_id, started_at, ended_at, task_name,
                    quality_profile, screen_enabled, status,
                    cam_mp4_path, screen_mp4_path, snapshots_dir,
                    vision_dir, logs_dir,
                    total_snapshots, uploaded_snapshots, failed_snapshots, total_events
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.started_at.isoformat(),
                session.ended_at.isoformat() if session.ended_at else None,
                session.task_name,
                session.quality_profile.value,
                1 if session.screen_enabled else 0,
                session.status.value,
                session.cam_mp4_path,
                session.screen_mp4_path,
                session.snapshots_dir,
                session.vision_dir,
                session.logs_dir,
                session.total_snapshots,
                session.uploaded_snapshots,
                session.failed_snapshots,
                session.total_events
            ))
            conn.commit()
        
        logger.info(f"Created session: {session.session_id}")
        return session.session_id
    
    def update_session_status(self, session_id: str, status: SessionStatus) -> None:
        """Update session status."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET status = ? WHERE session_id = ?",
                (status.value, session_id)
            )
            conn.commit()
        
        logger.debug(f"Updated session {session_id} status to {status.value}")
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()
        
        if not row:
            return None
        
        return Session(
            session_id=row['session_id'],
            started_at=datetime.fromisoformat(row['started_at']),
            ended_at=datetime.fromisoformat(row['ended_at']) if row['ended_at'] else None,
            task_name=row['task_name'],
            quality_profile=QualityProfile(row['quality_profile']),
            screen_enabled=bool(row['screen_enabled']),
            status=SessionStatus(row['status']),
            cam_mp4_path=row['cam_mp4_path'],
            screen_mp4_path=row['screen_mp4_path'],
            snapshots_dir=row['snapshots_dir'],
            vision_dir=row['vision_dir'],
            logs_dir=row['logs_dir'],
            total_snapshots=row['total_snapshots'],
            uploaded_snapshots=row['uploaded_snapshots'],
            failed_snapshots=row['failed_snapshots'],
            total_events=row['total_events']
        )

    def get_all_sessions(self, limit: int = 50) -> List[Session]:
        """
        Get all sessions sorted by started_at descending (most recent first).

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of Session objects
        """
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM sessions
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,)).fetchall()

        sessions = []
        for row in rows:
            sessions.append(Session(
                session_id=row['session_id'],
                started_at=datetime.fromisoformat(row['started_at']),
                ended_at=datetime.fromisoformat(row['ended_at']) if row['ended_at'] else None,
                task_name=row['task_name'],
                quality_profile=QualityProfile(row['quality_profile']),
                screen_enabled=bool(row['screen_enabled']),
                status=SessionStatus(row['status']),
                cam_mp4_path=row['cam_mp4_path'],
                screen_mp4_path=row['screen_mp4_path'],
                snapshots_dir=row['snapshots_dir'],
                vision_dir=row['vision_dir'],
                logs_dir=row['logs_dir'],
                total_snapshots=row['total_snapshots'],
                uploaded_snapshots=row['uploaded_snapshots'],
                failed_snapshots=row['failed_snapshots'],
                total_events=row['total_events']
            ))

        return sessions

    def end_session(self, session_id: str, ended_at: datetime) -> None:
        """Mark session as completed."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE sessions 
                SET ended_at = ?, status = ? 
                WHERE session_id = ?
            """, (ended_at.isoformat(), SessionStatus.COMPLETED.value, session_id))
            conn.commit()
        
        logger.info(f"Ended session: {session_id}")
    
    def update_session_stats(
        self,
        session_id: str,
        total_snapshots: Optional[int] = None,
        uploaded_snapshots: Optional[int] = None,
        failed_snapshots: Optional[int] = None,
        total_events: Optional[int] = None
    ) -> None:
        """Update session statistics."""
        updates = []
        params = []
        
        if total_snapshots is not None:
            updates.append("total_snapshots = ?")
            params.append(total_snapshots)
        if uploaded_snapshots is not None:
            updates.append("uploaded_snapshots = ?")
            params.append(uploaded_snapshots)
        if failed_snapshots is not None:
            updates.append("failed_snapshots = ?")
            params.append(failed_snapshots)
        if total_events is not None:
            updates.append("total_events = ?")
            params.append(total_events)
        
        if not updates:
            return
        
        params.append(session_id)
        sql = f"UPDATE sessions SET {', '.join(updates)} WHERE session_id = ?"
        
        with self._get_connection() as conn:
            conn.execute(sql, params)
            conn.commit()

    def delete_session(self, session_id: str) -> None:
        """
        Delete session and all related records.

        Deletes from all tables: session_reports, cloud_analysis_jobs,
        distraction_events, snapshots, and sessions.

        Args:
            session_id: Session ID to delete
        """
        with self._get_connection() as conn:
            # Delete in reverse dependency order
            conn.execute("DELETE FROM session_reports WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM cloud_analysis_jobs WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM distraction_events WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM snapshots WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()

        logger.info(f"Deleted session and all related records: {session_id}")

    # ========================================================================
    # Snapshot Operations
    # ========================================================================
    
    def insert_snapshot(self, snapshot: Snapshot) -> str:
        """Insert snapshot record."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO snapshots (
                    snapshot_id, session_id, timestamp, kind,
                    jpeg_path, jpeg_size_bytes,
                    vision_json_path, vision_labels, processed_at,
                    upload_status, retry_count, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.snapshot_id,
                snapshot.session_id,
                snapshot.timestamp.isoformat(),
                snapshot.kind.value,
                snapshot.jpeg_path,
                snapshot.jpeg_size_bytes,
                snapshot.vision_json_path,
                json.dumps(snapshot.vision_labels) if snapshot.vision_labels else None,
                snapshot.processed_at.isoformat() if snapshot.processed_at else None,
                snapshot.upload_status.value,
                snapshot.retry_count,
                snapshot.error_message
            ))
            conn.commit()
        
        logger.debug(f"Inserted snapshot: {snapshot.snapshot_id}")
        return snapshot.snapshot_id
    
    def update_snapshot_vision_results(
        self,
        snapshot_id: str,
        vision_labels: Dict[str, float],
        vision_json_path: str,
        processed_at: datetime
    ) -> None:
        """Update snapshot with vision API results."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE snapshots 
                SET vision_labels = ?, vision_json_path = ?, 
                    processed_at = ?, upload_status = ?
                WHERE snapshot_id = ?
            """, (
                json.dumps(vision_labels),
                vision_json_path,
                processed_at.isoformat(),
                UploadStatus.SUCCESS.value,
                snapshot_id
            ))
            conn.commit()
        
        logger.debug(f"Updated snapshot {snapshot_id} with vision results")
    
    def update_snapshot_upload_status(
        self,
        snapshot_id: str,
        status: UploadStatus,
        error_message: Optional[str] = None,
        increment_retry: bool = False
    ) -> None:
        """Update snapshot upload status."""
        with self._get_connection() as conn:
            if increment_retry:
                conn.execute("""
                    UPDATE snapshots 
                    SET upload_status = ?, error_message = ?, retry_count = retry_count + 1
                    WHERE snapshot_id = ?
                """, (status.value, error_message, snapshot_id))
            else:
                conn.execute("""
                    UPDATE snapshots 
                    SET upload_status = ?, error_message = ?
                    WHERE snapshot_id = ?
                """, (status.value, error_message, snapshot_id))
            conn.commit()
    
    def get_snapshots_for_session(self, session_id: str) -> List[Snapshot]:
        """Get all snapshots for a session."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM snapshots WHERE session_id = ? ORDER BY timestamp",
                (session_id,)
            ).fetchall()
        
        snapshots = []
        for row in rows:
            snapshots.append(Snapshot(
                snapshot_id=row['snapshot_id'],
                session_id=row['session_id'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                kind=SnapshotKind(row['kind']),
                jpeg_path=row['jpeg_path'],
                jpeg_size_bytes=row['jpeg_size_bytes'],
                vision_json_path=row['vision_json_path'],
                vision_labels=json.loads(row['vision_labels']) if row['vision_labels'] else None,
                processed_at=datetime.fromisoformat(row['processed_at']) if row['processed_at'] else None,
                upload_status=UploadStatus(row['upload_status']),
                retry_count=row['retry_count'],
                error_message=row['error_message']
            ))
        
        return snapshots
    
    # ========================================================================
    # Event Operations
    # ========================================================================
    
    def insert_distraction_event(self, event: DistractionEvent) -> str:
        """Insert distraction event."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO distraction_events (
                    event_id, session_id, started_at, ended_at, duration_seconds,
                    event_type, evidence, confidence,
                    vision_votes, snapshot_refs,
                    acknowledged, acknowledged_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.session_id,
                event.started_at.isoformat(),
                event.ended_at.isoformat(),
                event.duration_seconds,
                event.event_type.value,
                event.evidence,
                event.confidence,
                json.dumps(event.vision_votes),
                json.dumps(event.snapshot_refs),
                1 if event.acknowledged else 0,
                event.acknowledged_at.isoformat() if event.acknowledged_at else None
            ))
            conn.commit()
        
        logger.info(f"Inserted distraction event: {event.event_id} ({event.event_type.value})")
        return event.event_id
    
    def acknowledge_event(self, event_id: str, acknowledged_at: datetime) -> None:
        """Mark event as acknowledged by user."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE distraction_events 
                SET acknowledged = 1, acknowledged_at = ?
                WHERE event_id = ?
            """, (acknowledged_at.isoformat(), event_id))
            conn.commit()
        
        logger.debug(f"Acknowledged event: {event_id}")
    
    def get_session_events(self, session_id: str) -> List[DistractionEvent]:
        """Get all events for a session."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM distraction_events WHERE session_id = ? ORDER BY started_at",
                (session_id,)
            ).fetchall()
        
        events = []
        for row in rows:
            events.append(DistractionEvent(
                event_id=row['event_id'],
                session_id=row['session_id'],
                started_at=datetime.fromisoformat(row['started_at']),
                ended_at=datetime.fromisoformat(row['ended_at']),
                duration_seconds=row['duration_seconds'],
                event_type=DistractionType(row['event_type']),
                evidence=row['evidence'],
                confidence=row['confidence'],
                vision_votes=json.loads(row['vision_votes']),
                snapshot_refs=json.loads(row['snapshot_refs']),
                acknowledged=bool(row['acknowledged']),
                acknowledged_at=datetime.fromisoformat(row['acknowledged_at']) if row['acknowledged_at'] else None
            ))
        
        return events
    
    # ========================================================================
    # Report Operations
    # ========================================================================
    
    def store_session_report(self, session_id: str, report: SessionReport) -> None:
        """Store complete session report."""
        import uuid
        report_id = str(uuid.uuid4())
        report_json = json.dumps(self._serialize_report(report), indent=2)
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO session_reports (
                    report_id, session_id, report_json
                ) VALUES (?, ?, ?)
            """, (report_id, session_id, report_json))
            conn.commit()
        
        logger.info(f"Stored session report for {session_id}")
    
    def get_session_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session report as dictionary."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT report_json FROM session_reports WHERE session_id = ?",
                (session_id,)
            ).fetchone()
        
        if not row:
            return None
        
        return json.loads(row['report_json'])
    
    def _serialize_report(self, report: SessionReport) -> Dict[str, Any]:
        """Serialize SessionReport to dict for JSON storage."""
        # This will be a recursive serialization of all dataclasses
        # For now, return a placeholder - will implement full serialization later
        return {
            "session_id": report.session_id,
            "meta": {
                "started_at": report.meta.started_at,
                "ended_at": report.meta.ended_at,
                "profile": report.meta.profile,
                "total_duration_minutes": report.meta.total_duration_minutes,
                "snapshot_interval_sec": report.meta.snapshot_interval_sec
            },
            "segments": [],  # TODO: Serialize segments
            "kpis": {
                "focus_ratio": report.kpis.focus_ratio,
                "avg_focus_bout_min": report.kpis.avg_focus_bout_min,
                "num_alerts": report.kpis.num_alerts,
                "top_triggers": report.kpis.top_triggers,
                "peak_distraction_hour": report.kpis.peak_distraction_hour
            },
            "recommendations": [],  # TODO: Serialize recommendations
            "artifacts": {
                "memories_urls": report.artifacts.memories_urls,
                "hume_job_id": report.artifacts.hume_job_id
            }
        }

    # ========================================================================
    # Cloud Analysis Jobs Operations
    # ========================================================================

    def create_cloud_job(self, job: CloudAnalysisJob) -> str:
        """
        Create new cloud analysis job record.

        Args:
            job: CloudAnalysisJob object to insert

        Returns:
            job_id
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO cloud_analysis_jobs (
                    job_id, session_id, provider, provider_job_id,
                    status, upload_started_at, upload_completed_at,
                    processing_started_at, processing_completed_at,
                    results_fetched, results_stored_at, results_file_path,
                    video_type, video_path,
                    can_delete_remote, remote_deleted_at,
                    retry_count, last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id,
                job.session_id,
                job.provider.value,
                job.provider_job_id,
                job.status.value,
                job.upload_started_at.isoformat() if job.upload_started_at else None,
                job.upload_completed_at.isoformat() if job.upload_completed_at else None,
                job.processing_started_at.isoformat() if job.processing_started_at else None,
                job.processing_completed_at.isoformat() if job.processing_completed_at else None,
                1 if job.results_fetched else 0,
                job.results_stored_at.isoformat() if job.results_stored_at else None,
                job.results_file_path,
                job.video_type.value,
                job.video_path,
                1 if job.can_delete_remote else 0,
                job.remote_deleted_at.isoformat() if job.remote_deleted_at else None,
                job.retry_count,
                job.last_error
            ))
            conn.commit()

        logger.debug(f"Cloud job created: {job.job_id} ({job.provider.value})")
        return job.job_id

    def get_cloud_job(self, job_id: str) -> Optional[CloudAnalysisJob]:
        """Get cloud job by job_id."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM cloud_analysis_jobs WHERE job_id = ?
            """, (job_id,)).fetchone()

            if not row:
                return None

            return self._row_to_cloud_job(row)

    def get_cloud_jobs_for_session(self, session_id: str) -> List[CloudAnalysisJob]:
        """Get all cloud jobs for a session."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM cloud_analysis_jobs
                WHERE session_id = ?
                ORDER BY created_at DESC
            """, (session_id,)).fetchall()

            return [self._row_to_cloud_job(row) for row in rows]

    def get_cloud_jobs_by_status(self, status: CloudJobStatus) -> List[CloudAnalysisJob]:
        """Get all cloud jobs with given status."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM cloud_analysis_jobs
                WHERE status = ?
                ORDER BY created_at DESC
            """, (status.value,)).fetchall()

            return [self._row_to_cloud_job(row) for row in rows]

    def get_all_cloud_jobs_not_deleted(self) -> List[CloudAnalysisJob]:
        """
        Get all cloud jobs where videos are still stored in cloud.

        Returns only completed jobs that have not been deleted yet
        (remote_deleted_at IS NULL).

        Returns:
            List of CloudAnalysisJob objects still in cloud storage
        """
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM cloud_analysis_jobs
                WHERE remote_deleted_at IS NULL
                  AND status = 'completed'
                ORDER BY upload_completed_at DESC
            """).fetchall()

            return [self._row_to_cloud_job(row) for row in rows]

    def update_cloud_job_status(
        self,
        job_id: str,
        status: CloudJobStatus,
        provider_job_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update cloud job status and optionally provider_job_id."""
        timestamp_field = None
        timestamp_value = datetime.now().isoformat()

        if status == CloudJobStatus.UPLOADING:
            timestamp_field = "upload_started_at"
        elif status == CloudJobStatus.PROCESSING:
            timestamp_field = "processing_started_at"
        elif status == CloudJobStatus.COMPLETED:
            timestamp_field = "processing_completed_at"

        with self._get_connection() as conn:
            if timestamp_field:
                conn.execute(f"""
                    UPDATE cloud_analysis_jobs
                    SET status = ?,
                        provider_job_id = COALESCE(?, provider_job_id),
                        {timestamp_field} = ?,
                        last_error = ?
                    WHERE job_id = ?
                """, (status.value, provider_job_id, timestamp_value, error_message, job_id))
            else:
                conn.execute("""
                    UPDATE cloud_analysis_jobs
                    SET status = ?,
                        provider_job_id = COALESCE(?, provider_job_id),
                        last_error = ?
                    WHERE job_id = ?
                """, (status.value, provider_job_id, error_message, job_id))
            conn.commit()

        logger.debug(f"Cloud job status updated: {job_id} -> {status.value}")

    def mark_cloud_job_upload_complete(self, job_id: str) -> None:
        """Mark upload phase complete."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE cloud_analysis_jobs
                SET upload_completed_at = ?,
                    status = 'processing'
                WHERE job_id = ?
            """, (datetime.now().isoformat(), job_id))
            conn.commit()

    def mark_cloud_job_results_fetched(
        self,
        job_id: str,
        results_file_path: str
    ) -> None:
        """Mark results as fetched and stored locally."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE cloud_analysis_jobs
                SET results_fetched = 1,
                    results_stored_at = ?,
                    results_file_path = ?,
                    can_delete_remote = 1,
                    status = 'completed'
                WHERE job_id = ?
            """, (datetime.now().isoformat(), results_file_path, job_id))
            conn.commit()

        logger.debug(f"Cloud job results fetched: {job_id}")

    def mark_cloud_video_deleted(self, job_id: str) -> None:
        """Mark cloud video as deleted."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE cloud_analysis_jobs
                SET remote_deleted_at = ?
                WHERE job_id = ?
            """, (datetime.now().isoformat(), job_id))
            conn.commit()

        logger.debug(f"Cloud video marked deleted: {job_id}")

    def increment_cloud_job_retry(self, job_id: str, error: str) -> None:
        """Increment retry count and update error message."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE cloud_analysis_jobs
                SET retry_count = retry_count + 1,
                    last_error = ?
                WHERE job_id = ?
            """, (error, job_id))
            conn.commit()

    def _row_to_cloud_job(self, row: sqlite3.Row) -> CloudAnalysisJob:
        """Convert database row to CloudAnalysisJob object."""
        return CloudAnalysisJob(
            job_id=row['job_id'],
            session_id=row['session_id'],
            provider=CloudProvider(row['provider']),
            provider_job_id=row['provider_job_id'],
            status=CloudJobStatus(row['status']),
            upload_started_at=datetime.fromisoformat(row['upload_started_at']) if row['upload_started_at'] else None,
            upload_completed_at=datetime.fromisoformat(row['upload_completed_at']) if row['upload_completed_at'] else None,
            processing_started_at=datetime.fromisoformat(row['processing_started_at']) if row['processing_started_at'] else None,
            processing_completed_at=datetime.fromisoformat(row['processing_completed_at']) if row['processing_completed_at'] else None,
            results_fetched=bool(row['results_fetched']),
            results_stored_at=datetime.fromisoformat(row['results_stored_at']) if row['results_stored_at'] else None,
            results_file_path=row['results_file_path'],
            video_type=VideoType(row['video_type']),
            video_path=row['video_path'],
            can_delete_remote=bool(row['can_delete_remote']),
            remote_deleted_at=datetime.fromisoformat(row['remote_deleted_at']) if row['remote_deleted_at'] else None,
            retry_count=row['retry_count'],
            last_error=row['last_error'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )

