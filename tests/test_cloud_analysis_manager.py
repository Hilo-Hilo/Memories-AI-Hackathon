"""
Test suite for CloudAnalysisManager with mock cloud providers.

Run with: python tests/test_cloud_analysis_manager.py
"""

import sys
from pathlib import Path
from datetime import datetime
import uuid
import tempfile
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from focus_guardian.core.config import Config
from focus_guardian.core.database import Database
from focus_guardian.core.models import CloudProvider, CloudJobStatus, VideoType
from focus_guardian.session.cloud_analysis_manager import CloudAnalysisManager


class MockHumeClient:
    """Mock Hume AI client for testing."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.uploaded_videos = []

    def analyze_video(self, video_path, include_face=True, include_prosody=False, include_language=False):
        """Mock video analysis - returns job ID."""
        job_id = f"mock_hume_{uuid.uuid4().hex[:8]}"
        self.uploaded_videos.append((str(video_path), job_id))
        return job_id

    def poll_job(self, job_id, timeout=1):
        """Mock poll - returns COMPLETED immediately."""
        if "mock_hume" in job_id:
            return "COMPLETED"
        return "IN_PROGRESS"

    def fetch_results(self, job_id):
        """Mock results fetch."""
        return {
            "job_id": job_id,
            "timeline": [
                {
                    "timestamp": 0.0,
                    "frame": 0,
                    "emotions": {
                        "Concentration": 0.7,
                        "Frustration": 0.3,
                        "Boredom": 0.2
                    }
                }
            ],
            "summary": {
                "avg_concentration": 0.7,
                "avg_frustration": 0.3,
                "avg_boredom": 0.2
            },
            "frame_count": 100
        }


class MockMemoriesClient:
    """Mock Memories.ai client for testing."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.uploaded_videos = []

    def upload_video(self, video_path, unique_id=None):
        """Mock video upload - returns video_no."""
        video_no = f"mock_video_{uuid.uuid4().hex[:8]}"
        self.uploaded_videos.append((str(video_path), video_no))
        return video_no

    def wait_for_processing(self, video_no, unique_id, max_wait=1):
        """Mock wait - returns True immediately."""
        if "mock_video" in video_no:
            return True
        return False

    def chat_with_video(self, video_nos, prompt, unique_id, stream=False):
        """Mock chat - returns JSON response."""
        response = {
            "time_segmentation": [
                {
                    "start_time": 0.0,
                    "end_time": 120.0,
                    "label": "Focus",
                    "task_hypothesis": "Coding in IDE",
                    "confidence": 0.85
                }
            ],
            "app_usage": [
                {
                    "app_class": "IDE",
                    "total_seconds": 100.0,
                    "percentage": 0.83,
                    "is_productive": True
                }
            ],
            "distraction_analysis": {
                "total_distraction_time": 20.0,
                "distraction_events": []
            },
            "insights": {
                "focus_ratio": 0.83,
                "avg_focus_bout_minutes": 25.0,
                "primary_distractor": "None",
                "productivity_score": 0.85,
                "recommendations": ["Keep up the good work"]
            }
        }
        return json.dumps(response)

    def delete_video(self, video_no, unique_id="default"):
        """Mock delete - returns True."""
        return True


def setup_test_environment():
    """Setup test database and temp directory."""
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test_cloud_manager.db"
    schema_path = Path(__file__).parent.parent / "config" / "schema.sql"

    database = Database(db_path=db_path, schema_path=schema_path)
    config = Config()

    return database, config, temp_dir


def cleanup_test_environment(temp_dir):
    """Cleanup test environment."""
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


def test_upload_to_hume():
    """Test uploading session to Hume AI."""
    print("\n=== Testing Hume AI Upload ===")

    database, config, temp_dir = setup_test_environment()

    try:
        # Create mock Hume client
        hume_client = MockHumeClient(api_key="test_key")

        # Create manager
        manager = CloudAnalysisManager(
            config=config,
            database=database,
            hume_client=hume_client,
            memories_client=None
        )

        # Create test video file
        session_id = str(uuid.uuid4())
        cam_video = temp_dir / "cam.mp4"
        cam_video.write_text("fake video content")

        # Upload
        hume_job_id, memories_job_id = manager.upload_session_for_analysis(
            session_id=session_id,
            cam_video_path=cam_video,
            screen_video_path=None,
            run_hume=True,
            run_memories=False
        )

        assert hume_job_id is not None
        assert memories_job_id is None
        print(f"✓ Hume job created: {hume_job_id}")

        # Verify database record
        job = database.get_cloud_job(hume_job_id)
        assert job is not None
        assert job.provider == CloudProvider.HUME_AI
        assert job.status == CloudJobStatus.PROCESSING
        assert job.provider_job_id is not None
        print(f"✓ Database record created with status: {job.status.value}")
        print(f"✓ Provider job ID: {job.provider_job_id}")

        # Verify mock client called
        assert len(hume_client.uploaded_videos) == 1
        print("✓ Mock Hume client received upload request")

        print("✓ Hume AI upload test passed")

    finally:
        cleanup_test_environment(temp_dir)


def test_upload_to_memories():
    """Test uploading session to Memories.ai."""
    print("\n=== Testing Memories.ai Upload ===")

    database, config, temp_dir = setup_test_environment()

    try:
        # Create mock Memories client
        memories_client = MockMemoriesClient(api_key="test_key")

        # Create manager
        manager = CloudAnalysisManager(
            config=config,
            database=database,
            hume_client=None,
            memories_client=memories_client
        )

        # Create test video files
        session_id = str(uuid.uuid4())
        cam_video = temp_dir / "cam.mp4"
        screen_video = temp_dir / "screen.mp4"
        cam_video.write_text("fake cam video")
        screen_video.write_text("fake screen video")

        # Upload
        hume_job_id, memories_job_id = manager.upload_session_for_analysis(
            session_id=session_id,
            cam_video_path=cam_video,
            screen_video_path=screen_video,
            run_hume=False,
            run_memories=True
        )

        assert hume_job_id is None
        assert memories_job_id is not None
        print(f"✓ Memories job created: {memories_job_id}")

        # Verify database record
        job = database.get_cloud_job(memories_job_id)
        assert job is not None
        assert job.provider == CloudProvider.MEMORIES_AI
        assert job.status == CloudJobStatus.PROCESSING
        assert job.video_type == VideoType.BOTH
        print(f"✓ Database record created with status: {job.status.value}")
        print(f"✓ Video type: {job.video_type.value}")

        # Verify provider_job_id contains both video_nos
        provider_data = json.loads(job.provider_job_id)
        assert "cam_video_no" in provider_data
        assert "screen_video_no" in provider_data
        print(f"✓ Provider job ID contains both video_nos")

        # Verify mock client received both uploads
        assert len(memories_client.uploaded_videos) == 2
        print("✓ Mock Memories client received 2 upload requests")

        print("✓ Memories.ai upload test passed")

    finally:
        cleanup_test_environment(temp_dir)


def test_check_job_status():
    """Test checking job status."""
    print("\n=== Testing Check Job Status ===")

    database, config, temp_dir = setup_test_environment()

    try:
        # Create mock clients
        hume_client = MockHumeClient(api_key="test_key")

        # Create manager
        manager = CloudAnalysisManager(
            config=config,
            database=database,
            hume_client=hume_client,
            memories_client=None
        )

        # Create test video
        session_id = str(uuid.uuid4())
        cam_video = temp_dir / "cam.mp4"
        cam_video.write_text("fake video")

        # Upload
        hume_job_id, _ = manager.upload_session_for_analysis(
            session_id=session_id,
            cam_video_path=cam_video,
            screen_video_path=None,
            run_hume=True,
            run_memories=False
        )

        # Check status
        status = manager.check_job_status(hume_job_id)

        assert status == CloudJobStatus.COMPLETED
        print(f"✓ Status check returned: {status.value}")

        # Verify database updated
        job = database.get_cloud_job(hume_job_id)
        assert job.status == CloudJobStatus.COMPLETED
        print("✓ Database status updated to COMPLETED")

        print("✓ Check job status test passed")

    finally:
        cleanup_test_environment(temp_dir)


def test_retrieve_hume_results():
    """Test retrieving Hume AI results."""
    print("\n=== Testing Retrieve Hume Results ===")

    database, config, temp_dir = setup_test_environment()

    try:
        # Create mock client
        hume_client = MockHumeClient(api_key="test_key")

        # Create manager
        manager = CloudAnalysisManager(
            config=config,
            database=database,
            hume_client=hume_client,
            memories_client=None
        )

        # Create test video
        session_id = str(uuid.uuid4())
        cam_video = temp_dir / "cam.mp4"
        cam_video.write_text("fake video")

        # Upload
        hume_job_id, _ = manager.upload_session_for_analysis(
            session_id=session_id,
            cam_video_path=cam_video,
            screen_video_path=None,
            run_hume=True,
            run_memories=False
        )

        # Mark as completed
        database.update_cloud_job_status(hume_job_id, CloudJobStatus.COMPLETED)

        # Retrieve results
        results_path = manager.retrieve_and_store_results(hume_job_id)

        assert results_path is not None
        assert results_path.exists()
        print(f"✓ Results stored at: {results_path}")

        # Verify JSON content
        with open(results_path, 'r') as f:
            results = json.load(f)

        assert "timeline" in results
        assert "summary" in results
        assert "frame_count" in results
        print("✓ Results JSON has required fields")

        # Verify database updated
        job = database.get_cloud_job(hume_job_id)
        assert job.results_fetched == True
        assert job.can_delete_remote == True
        assert job.results_file_path == str(results_path)
        print("✓ Database marked results fetched and safe to delete")

        print("✓ Retrieve Hume results test passed")

    finally:
        cleanup_test_environment(temp_dir)


def test_retrieve_memories_results():
    """Test retrieving Memories.ai results."""
    print("\n=== Testing Retrieve Memories Results ===")

    database, config, temp_dir = setup_test_environment()

    try:
        # Create mock client
        memories_client = MockMemoriesClient(api_key="test_key")

        # Create manager
        manager = CloudAnalysisManager(
            config=config,
            database=database,
            hume_client=None,
            memories_client=memories_client
        )

        # Create test videos
        session_id = str(uuid.uuid4())
        cam_video = temp_dir / "cam.mp4"
        screen_video = temp_dir / "screen.mp4"
        cam_video.write_text("fake cam")
        screen_video.write_text("fake screen")

        # Upload
        _, memories_job_id = manager.upload_session_for_analysis(
            session_id=session_id,
            cam_video_path=cam_video,
            screen_video_path=screen_video,
            run_hume=False,
            run_memories=True
        )

        # Mark as completed
        database.update_cloud_job_status(memories_job_id, CloudJobStatus.COMPLETED)

        # Retrieve results
        results_path = manager.retrieve_and_store_results(memories_job_id)

        assert results_path is not None
        assert results_path.exists()
        print(f"✓ Results stored at: {results_path}")

        # Verify JSON content
        with open(results_path, 'r') as f:
            results = json.load(f)

        assert "time_segmentation" in results
        assert "app_usage" in results
        assert "distraction_analysis" in results
        assert "insights" in results
        print("✓ Results JSON has required Memories.ai fields")

        # Verify database updated
        job = database.get_cloud_job(memories_job_id)
        assert job.results_fetched == True
        assert job.can_delete_remote == True
        print("✓ Database marked results fetched")

        print("✓ Retrieve Memories results test passed")

    finally:
        cleanup_test_environment(temp_dir)


def test_delete_cloud_videos():
    """Test deleting cloud videos."""
    print("\n=== Testing Delete Cloud Videos ===")

    database, config, temp_dir = setup_test_environment()

    try:
        # Create mock client
        memories_client = MockMemoriesClient(api_key="test_key")

        # Create manager
        manager = CloudAnalysisManager(
            config=config,
            database=database,
            hume_client=None,
            memories_client=memories_client
        )

        # Create test video
        session_id = str(uuid.uuid4())
        cam_video = temp_dir / "cam.mp4"
        cam_video.write_text("fake video")

        # Upload
        _, memories_job_id = manager.upload_session_for_analysis(
            session_id=session_id,
            cam_video_path=cam_video,
            screen_video_path=None,
            run_hume=False,
            run_memories=True
        )

        # Complete and fetch results
        database.update_cloud_job_status(memories_job_id, CloudJobStatus.COMPLETED)
        manager.retrieve_and_store_results(memories_job_id)

        # Delete cloud videos
        success = manager.delete_cloud_videos(memories_job_id)

        assert success == True
        print("✓ Cloud videos deleted successfully")

        # Verify database updated
        job = database.get_cloud_job(memories_job_id)
        assert job.remote_deleted_at is not None
        print(f"✓ Database marked deleted at: {job.remote_deleted_at}")

        print("✓ Delete cloud videos test passed")

    finally:
        cleanup_test_environment(temp_dir)


def test_delete_safety():
    """Test that deletion fails if results not fetched."""
    print("\n=== Testing Delete Safety ===")

    database, config, temp_dir = setup_test_environment()

    try:
        # Create mock client
        memories_client = MockMemoriesClient(api_key="test_key")

        # Create manager
        manager = CloudAnalysisManager(
            config=config,
            database=database,
            hume_client=None,
            memories_client=memories_client
        )

        # Create test video
        session_id = str(uuid.uuid4())
        cam_video = temp_dir / "cam.mp4"
        cam_video.write_text("fake video")

        # Upload
        _, memories_job_id = manager.upload_session_for_analysis(
            session_id=session_id,
            cam_video_path=cam_video,
            screen_video_path=None,
            run_hume=False,
            run_memories=True
        )

        # Try to delete WITHOUT fetching results
        success = manager.delete_cloud_videos(memories_job_id)

        assert success == False
        print("✓ Deletion blocked (results not fetched)")

        # Verify database NOT updated
        job = database.get_cloud_job(memories_job_id)
        assert job.remote_deleted_at is None
        assert job.can_delete_remote == False
        print("✓ Database NOT marked as deleted (safety check passed)")

        print("✓ Delete safety test passed")

    finally:
        cleanup_test_environment(temp_dir)


def main():
    """Run all CloudAnalysisManager tests."""
    print("\n" + "="*60)
    print("CLOUD ANALYSIS MANAGER - TEST SUITE")
    print("="*60)

    try:
        test_upload_to_hume()
        test_upload_to_memories()
        test_check_job_status()
        test_retrieve_hume_results()
        test_retrieve_memories_results()
        test_delete_cloud_videos()
        test_delete_safety()

        print("\n" + "="*60)
        print("✓ ALL MANAGER TESTS PASSED!")
        print("="*60)
        print("\nCloudAnalysisManager is working correctly with mock providers.")
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
