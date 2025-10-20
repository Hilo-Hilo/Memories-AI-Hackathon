"""
Test suite for cloud analysis database operations.

Run with: python tests/test_cloud_analysis_database.py
"""

import sys
from pathlib import Path
from datetime import datetime
import uuid
import tempfile
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from focus_guardian.core.database import Database
from focus_guardian.core.models import (
    CloudAnalysisJob, CloudProvider, CloudJobStatus, VideoType
)


def setup_test_database():
    """Create temporary test database."""
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test_cloud.db"
    schema_path = Path(__file__).parent.parent / "config" / "schema.sql"

    database = Database(db_path=db_path, schema_path=schema_path)
    return database, temp_dir


def cleanup_test_database(temp_dir):
    """Cleanup temporary test database."""
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


def test_create_cloud_job():
    """Test creating cloud analysis job in database."""
    print("\n=== Testing Create Cloud Job ===")

    database, temp_dir = setup_test_database()

    try:
        job = CloudAnalysisJob(
            job_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            provider=CloudProvider.HUME_AI,
            provider_job_id="hume_test_123",
            status=CloudJobStatus.PENDING,
            video_type=VideoType.WEBCAM,
            video_path="/test/cam.mp4"
        )

        # Create job in database
        job_id = database.create_cloud_job(job)

        assert job_id == job.job_id
        print(f"✓ Created cloud job: {job_id[:8]}...")

        # Retrieve and verify
        retrieved = database.get_cloud_job(job_id)

        assert retrieved is not None
        assert retrieved.job_id == job.job_id
        assert retrieved.session_id == job.session_id
        assert retrieved.provider == CloudProvider.HUME_AI
        assert retrieved.provider_job_id == "hume_test_123"
        assert retrieved.status == CloudJobStatus.PENDING
        assert retrieved.video_type == VideoType.WEBCAM
        assert retrieved.video_path == "/test/cam.mp4"

        print("✓ Retrieved job matches created job")
        print("✓ Create cloud job test passed")

    finally:
        cleanup_test_database(temp_dir)


def test_update_cloud_job_status():
    """Test updating cloud job status."""
    print("\n=== Testing Update Cloud Job Status ===")

    database, temp_dir = setup_test_database()

    try:
        job = CloudAnalysisJob(
            job_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            provider=CloudProvider.MEMORIES_AI,
            provider_job_id=None,
            status=CloudJobStatus.PENDING,
            video_type=VideoType.BOTH,
            video_path="/test/cam.mp4,/test/screen.mp4"
        )

        database.create_cloud_job(job)

        # Update to uploading
        database.update_cloud_job_status(
            job_id=job.job_id,
            status=CloudJobStatus.UPLOADING
        )

        retrieved = database.get_cloud_job(job.job_id)
        assert retrieved.status == CloudJobStatus.UPLOADING
        assert retrieved.upload_started_at is not None
        print(f"✓ Status updated to UPLOADING, timestamp: {retrieved.upload_started_at}")

        # Update to processing with provider_job_id
        database.update_cloud_job_status(
            job_id=job.job_id,
            status=CloudJobStatus.PROCESSING,
            provider_job_id='{"cam": "123", "screen": "456"}'
        )

        retrieved = database.get_cloud_job(job.job_id)
        assert retrieved.status == CloudJobStatus.PROCESSING
        assert retrieved.provider_job_id == '{"cam": "123", "screen": "456"}'
        assert retrieved.processing_started_at is not None
        print(f"✓ Status updated to PROCESSING with provider_job_id")

        # Update to completed
        database.update_cloud_job_status(
            job_id=job.job_id,
            status=CloudJobStatus.COMPLETED
        )

        retrieved = database.get_cloud_job(job.job_id)
        assert retrieved.status == CloudJobStatus.COMPLETED
        assert retrieved.processing_completed_at is not None
        print(f"✓ Status updated to COMPLETED")

        print("✓ Update cloud job status test passed")

    finally:
        cleanup_test_database(temp_dir)


def test_get_cloud_jobs_for_session():
    """Test retrieving all cloud jobs for a session."""
    print("\n=== Testing Get Cloud Jobs for Session ===")

    database, temp_dir = setup_test_database()

    try:
        session_id = str(uuid.uuid4())

        # Create multiple jobs for same session
        job1 = CloudAnalysisJob(
            job_id=str(uuid.uuid4()),
            session_id=session_id,
            provider=CloudProvider.HUME_AI,
            provider_job_id="hume_123",
            status=CloudJobStatus.PROCESSING,
            video_type=VideoType.WEBCAM,
            video_path="/test/cam.mp4"
        )

        job2 = CloudAnalysisJob(
            job_id=str(uuid.uuid4()),
            session_id=session_id,
            provider=CloudProvider.MEMORIES_AI,
            provider_job_id='{"cam": "456"}',
            status=CloudJobStatus.COMPLETED,
            video_type=VideoType.BOTH,
            video_path="/test/cam.mp4,/test/screen.mp4"
        )

        database.create_cloud_job(job1)
        database.create_cloud_job(job2)

        # Retrieve all jobs for session
        jobs = database.get_cloud_jobs_for_session(session_id)

        assert len(jobs) == 2
        print(f"✓ Found {len(jobs)} jobs for session")

        # Verify both providers present
        providers = [j.provider for j in jobs]
        assert CloudProvider.HUME_AI in providers
        assert CloudProvider.MEMORIES_AI in providers
        print("✓ Both Hume AI and Memories.ai jobs retrieved")

        # Verify statuses
        statuses = [j.status for j in jobs]
        assert CloudJobStatus.PROCESSING in statuses
        assert CloudJobStatus.COMPLETED in statuses
        print("✓ Job statuses correct")

        print("✓ Get cloud jobs for session test passed")

    finally:
        cleanup_test_database(temp_dir)


def test_get_cloud_jobs_by_status():
    """Test retrieving cloud jobs by status."""
    print("\n=== Testing Get Cloud Jobs by Status ===")

    database, temp_dir = setup_test_database()

    try:
        # Create jobs with different statuses
        for i in range(3):
            job = CloudAnalysisJob(
                job_id=str(uuid.uuid4()),
                session_id=str(uuid.uuid4()),
                provider=CloudProvider.HUME_AI,
                provider_job_id=f"job_{i}",
                status=CloudJobStatus.PROCESSING,
                video_type=VideoType.WEBCAM,
                video_path=f"/test/cam_{i}.mp4"
            )
            database.create_cloud_job(job)

        # Create one completed job
        completed_job = CloudAnalysisJob(
            job_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            provider=CloudProvider.MEMORIES_AI,
            provider_job_id="completed_job",
            status=CloudJobStatus.COMPLETED,
            video_type=VideoType.WEBCAM,
            video_path="/test/cam_done.mp4"
        )
        database.create_cloud_job(completed_job)

        # Query by status
        processing_jobs = database.get_cloud_jobs_by_status(CloudJobStatus.PROCESSING)
        completed_jobs = database.get_cloud_jobs_by_status(CloudJobStatus.COMPLETED)

        assert len(processing_jobs) == 3
        assert len(completed_jobs) == 1
        print(f"✓ Found {len(processing_jobs)} PROCESSING jobs")
        print(f"✓ Found {len(completed_jobs)} COMPLETED jobs")

        print("✓ Get cloud jobs by status test passed")

    finally:
        cleanup_test_database(temp_dir)


def test_mark_cloud_job_upload_complete():
    """Test marking upload phase complete."""
    print("\n=== Testing Mark Upload Complete ===")

    database, temp_dir = setup_test_database()

    try:
        job = CloudAnalysisJob(
            job_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            provider=CloudProvider.HUME_AI,
            provider_job_id=None,
            status=CloudJobStatus.UPLOADING,
            video_type=VideoType.WEBCAM,
            video_path="/test/cam.mp4"
        )

        database.create_cloud_job(job)

        # Mark upload complete
        database.mark_cloud_job_upload_complete(job.job_id)

        retrieved = database.get_cloud_job(job.job_id)
        assert retrieved.upload_completed_at is not None
        assert retrieved.status == CloudJobStatus.PROCESSING
        print(f"✓ Upload marked complete, status: {retrieved.status.value}")
        print(f"✓ Upload completed at: {retrieved.upload_completed_at}")

        print("✓ Mark upload complete test passed")

    finally:
        cleanup_test_database(temp_dir)


def test_mark_cloud_job_results_fetched():
    """Test marking results as fetched."""
    print("\n=== Testing Mark Results Fetched ===")

    database, temp_dir = setup_test_database()

    try:
        job = CloudAnalysisJob(
            job_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            provider=CloudProvider.MEMORIES_AI,
            provider_job_id='{"cam": "123"}',
            status=CloudJobStatus.PROCESSING,
            video_type=VideoType.WEBCAM,
            video_path="/test/cam.mp4"
        )

        database.create_cloud_job(job)

        # Mark results fetched
        results_path = "/local/path/results.json"
        database.mark_cloud_job_results_fetched(
            job_id=job.job_id,
            results_file_path=results_path
        )

        retrieved = database.get_cloud_job(job.job_id)
        assert retrieved.results_fetched == True
        assert retrieved.results_file_path == results_path
        assert retrieved.can_delete_remote == True
        assert retrieved.status == CloudJobStatus.COMPLETED
        assert retrieved.results_stored_at is not None
        print(f"✓ Results marked fetched")
        print(f"✓ Results path: {retrieved.results_file_path}")
        print(f"✓ Can delete remote: {retrieved.can_delete_remote}")
        print(f"✓ Status: {retrieved.status.value}")

        print("✓ Mark results fetched test passed")

    finally:
        cleanup_test_database(temp_dir)


def test_mark_cloud_video_deleted():
    """Test marking cloud video as deleted."""
    print("\n=== Testing Mark Cloud Video Deleted ===")

    database, temp_dir = setup_test_database()

    try:
        job = CloudAnalysisJob(
            job_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            provider=CloudProvider.HUME_AI,
            provider_job_id="hume_123",
            status=CloudJobStatus.COMPLETED,
            video_type=VideoType.WEBCAM,
            video_path="/test/cam.mp4",
            results_fetched=True,
            can_delete_remote=True
        )

        database.create_cloud_job(job)

        # Mark video deleted
        database.mark_cloud_video_deleted(job.job_id)

        retrieved = database.get_cloud_job(job.job_id)
        assert retrieved.remote_deleted_at is not None
        print(f"✓ Video marked deleted at: {retrieved.remote_deleted_at}")

        print("✓ Mark cloud video deleted test passed")

    finally:
        cleanup_test_database(temp_dir)


def test_increment_cloud_job_retry():
    """Test incrementing retry counter."""
    print("\n=== Testing Increment Retry Counter ===")

    database, temp_dir = setup_test_database()

    try:
        job = CloudAnalysisJob(
            job_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            provider=CloudProvider.MEMORIES_AI,
            provider_job_id=None,
            status=CloudJobStatus.UPLOADING,
            video_type=VideoType.WEBCAM,
            video_path="/test/cam.mp4"
        )

        database.create_cloud_job(job)

        # Increment retry
        error_msg = "Connection timeout"
        database.increment_cloud_job_retry(job.job_id, error_msg)

        retrieved = database.get_cloud_job(job.job_id)
        assert retrieved.retry_count == 1
        assert retrieved.last_error == error_msg
        print(f"✓ Retry count: {retrieved.retry_count}")
        print(f"✓ Last error: {retrieved.last_error}")

        # Increment again
        error_msg2 = "Quota exceeded"
        database.increment_cloud_job_retry(job.job_id, error_msg2)

        retrieved = database.get_cloud_job(job.job_id)
        assert retrieved.retry_count == 2
        assert retrieved.last_error == error_msg2
        print(f"✓ Retry count after 2nd failure: {retrieved.retry_count}")
        print(f"✓ Updated error: {retrieved.last_error}")

        print("✓ Increment retry counter test passed")

    finally:
        cleanup_test_database(temp_dir)


def main():
    """Run all database tests."""
    print("\n" + "="*60)
    print("CLOUD ANALYSIS DATABASE - TEST SUITE")
    print("="*60)

    try:
        test_create_cloud_job()
        test_update_cloud_job_status()
        test_get_cloud_jobs_for_session()
        test_get_cloud_jobs_by_status()
        test_mark_cloud_job_upload_complete()
        test_mark_cloud_job_results_fetched()
        test_mark_cloud_video_deleted()
        test_increment_cloud_job_retry()

        print("\n" + "="*60)
        print("✓ ALL DATABASE TESTS PASSED!")
        print("="*60)
        print("\nDatabase cloud job operations are working correctly.")
        print()

        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
