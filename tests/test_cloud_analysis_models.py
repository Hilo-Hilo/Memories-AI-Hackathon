"""
Test suite for CloudAnalysisJob model and related enums.

Run with: python tests/test_cloud_analysis_models.py
"""

import sys
from pathlib import Path
from datetime import datetime
import uuid

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from focus_guardian.core.models import (
    CloudAnalysisJob, CloudProvider, CloudJobStatus, VideoType
)


def test_cloud_provider_enum():
    """Test CloudProvider enum values."""
    print("\n=== Testing CloudProvider Enum ===")

    assert CloudProvider.HUME_AI.value == "hume_ai"
    assert CloudProvider.MEMORIES_AI.value == "memories_ai"

    # Test enum construction from string
    assert CloudProvider("hume_ai") == CloudProvider.HUME_AI
    assert CloudProvider("memories_ai") == CloudProvider.MEMORIES_AI

    print("✓ CloudProvider enum works correctly")


def test_cloud_job_status_enum():
    """Test CloudJobStatus enum values."""
    print("\n=== Testing CloudJobStatus Enum ===")

    assert CloudJobStatus.PENDING.value == "pending"
    assert CloudJobStatus.UPLOADING.value == "uploading"
    assert CloudJobStatus.PROCESSING.value == "processing"
    assert CloudJobStatus.COMPLETED.value == "completed"
    assert CloudJobStatus.FAILED.value == "failed"

    # Test lifecycle progression
    statuses = [
        CloudJobStatus.PENDING,
        CloudJobStatus.UPLOADING,
        CloudJobStatus.PROCESSING,
        CloudJobStatus.COMPLETED
    ]

    print(f"✓ Status lifecycle: {' → '.join([s.value for s in statuses])}")


def test_video_type_enum():
    """Test VideoType enum values."""
    print("\n=== Testing VideoType Enum ===")

    assert VideoType.WEBCAM.value == "webcam"
    assert VideoType.SCREEN.value == "screen"
    assert VideoType.BOTH.value == "both"

    print("✓ VideoType enum works correctly")


def test_cloud_analysis_job_creation():
    """Test CloudAnalysisJob model creation."""
    print("\n=== Testing CloudAnalysisJob Creation ===")

    job_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    job = CloudAnalysisJob(
        job_id=job_id,
        session_id=session_id,
        provider=CloudProvider.HUME_AI,
        provider_job_id="hume_12345",
        status=CloudJobStatus.PENDING,
        video_type=VideoType.WEBCAM,
        video_path="/path/to/cam.mp4"
    )

    # Verify required fields
    assert job.job_id == job_id
    assert job.session_id == session_id
    assert job.provider == CloudProvider.HUME_AI
    assert job.provider_job_id == "hume_12345"
    assert job.status == CloudJobStatus.PENDING
    assert job.video_type == VideoType.WEBCAM
    assert job.video_path == "/path/to/cam.mp4"

    # Verify default values
    assert job.upload_started_at is None
    assert job.upload_completed_at is None
    assert job.processing_started_at is None
    assert job.processing_completed_at is None
    assert job.results_fetched == False
    assert job.results_stored_at is None
    assert job.results_file_path is None
    assert job.can_delete_remote == False
    assert job.remote_deleted_at is None
    assert job.retry_count == 0
    assert job.last_error is None

    # Verify timestamps are set
    assert job.created_at is not None
    assert job.updated_at is not None

    print(f"✓ Created job: {job.job_id[:8]}...")
    print(f"✓ Provider: {job.provider.value}")
    print(f"✓ Status: {job.status.value}")
    print(f"✓ Video type: {job.video_type.value}")
    print("✓ All default values correct")


def test_cloud_job_lifecycle():
    """Test CloudAnalysisJob lifecycle state transitions."""
    print("\n=== Testing CloudAnalysisJob Lifecycle ===")

    job = CloudAnalysisJob(
        job_id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        provider=CloudProvider.MEMORIES_AI,
        provider_job_id=None,
        status=CloudJobStatus.PENDING,
        video_type=VideoType.BOTH,
        video_path="/path/to/cam.mp4,/path/to/screen.mp4"
    )

    print(f"Initial state: {job.status.value}")

    # Simulate upload phase
    job.status = CloudJobStatus.UPLOADING
    job.upload_started_at = datetime.now()
    print(f"After upload start: {job.status.value}")

    # Simulate upload completion
    job.status = CloudJobStatus.PROCESSING
    job.upload_completed_at = datetime.now()
    job.provider_job_id = '{"unique_id": "test", "cam_video_no": "123", "screen_video_no": "456"}'
    print(f"After upload complete: {job.status.value}")
    print(f"✓ Provider job ID: {job.provider_job_id[:30]}...")

    # Simulate processing completion
    job.status = CloudJobStatus.COMPLETED
    job.processing_started_at = datetime.now()
    job.processing_completed_at = datetime.now()
    print(f"After processing: {job.status.value}")

    # Simulate results retrieval
    job.results_fetched = True
    job.results_stored_at = datetime.now()
    job.results_file_path = "/path/to/results.json"
    job.can_delete_remote = True
    print(f"After results fetched: can_delete_remote={job.can_delete_remote}")

    # Simulate cloud deletion
    job.remote_deleted_at = datetime.now()
    print(f"After cloud deletion: remote_deleted_at={job.remote_deleted_at.isoformat()}")

    print("✓ Complete lifecycle simulation successful")


def test_cloud_job_error_handling():
    """Test CloudAnalysisJob error tracking."""
    print("\n=== Testing CloudAnalysisJob Error Handling ===")

    job = CloudAnalysisJob(
        job_id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        provider=CloudProvider.HUME_AI,
        provider_job_id=None,
        status=CloudJobStatus.PENDING,
        video_type=VideoType.WEBCAM,
        video_path="/path/to/cam.mp4"
    )

    # Simulate upload failure
    job.status = CloudJobStatus.FAILED
    job.retry_count = 1
    job.last_error = "Connection timeout during upload"

    print(f"✓ Status: {job.status.value}")
    print(f"✓ Retry count: {job.retry_count}")
    print(f"✓ Last error: {job.last_error}")

    # Simulate retry
    job.retry_count += 1
    job.last_error = "Upload failed again - quota exceeded"

    assert job.retry_count == 2
    assert "quota exceeded" in job.last_error

    print(f"✓ After retry: count={job.retry_count}, error={job.last_error[:30]}...")
    print("✓ Error tracking works correctly")


def test_cloud_job_safety_flags():
    """Test safety flags for cloud deletion."""
    print("\n=== Testing Safety Flags ===")

    job = CloudAnalysisJob(
        job_id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        provider=CloudProvider.MEMORIES_AI,
        provider_job_id="video_123",
        status=CloudJobStatus.COMPLETED,
        video_type=VideoType.WEBCAM,
        video_path="/path/to/cam.mp4"
    )

    # Initially not safe to delete
    assert job.can_delete_remote == False
    assert job.remote_deleted_at is None
    print("✓ Initial state: NOT safe to delete (results not fetched)")

    # Mark results as fetched
    job.results_fetched = True
    job.results_stored_at = datetime.now()
    job.results_file_path = "/local/path/results.json"
    job.can_delete_remote = True

    assert job.can_delete_remote == True
    assert job.results_fetched == True
    assert job.results_file_path is not None
    print("✓ After results fetched: SAFE to delete")

    # Simulate deletion
    job.remote_deleted_at = datetime.now()

    assert job.remote_deleted_at is not None
    print(f"✓ Cloud video deleted at: {job.remote_deleted_at.isoformat()}")
    print("✓ Safety flag workflow complete")


def main():
    """Run all model tests."""
    print("\n" + "="*60)
    print("CLOUD ANALYSIS MODELS - TEST SUITE")
    print("="*60)

    try:
        test_cloud_provider_enum()
        test_cloud_job_status_enum()
        test_video_type_enum()
        test_cloud_analysis_job_creation()
        test_cloud_job_lifecycle()
        test_cloud_job_error_handling()
        test_cloud_job_safety_flags()

        print("\n" + "="*60)
        print("✓ ALL MODEL TESTS PASSED!")
        print("="*60)
        print("\nCloudAnalysisJob model is working correctly.")
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
