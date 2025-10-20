"""
Real API Integration Test Suite for Cloud Analysis Workflow.

Tests the complete workflow with actual Hume AI and Memories.ai APIs:
1. Hume AI: Upload → Poll → Fetch → Validate → Store
2. Memories.ai: Upload → Process → Chat → Parse → Validate → Store → Delete
3. CloudAnalysisManager: Full integrated workflow with database tracking

IMPORTANT: This test makes real API calls and incurs costs (~$1.50 per run).
Requires API keys in .env file:
- HUME_API_KEY
- MEM_AI_API_KEY

Run with: python tests/test_real_api_integration.py
Expected duration: 15-20 minutes
"""

import sys
import os
import time
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from focus_guardian.core.config import Config
from focus_guardian.core.database import Database
from focus_guardian.core.models import (
    CloudAnalysisJob, CloudProvider, CloudJobStatus, VideoType,
    Session, SessionStatus, QualityProfile
)
from focus_guardian.integrations.hume_client import HumeExpressionClient
from focus_guardian.integrations.memories_client import MemoriesClient
from focus_guardian.session.cloud_analysis_manager import CloudAnalysisManager


# Test session details
TEST_SESSION_ID = "ce08da15-986c-4c63-8788-bd851a94b130"
TEST_CAM_VIDEO = Path(f"data/sessions/{TEST_SESSION_ID}/cam.mp4")
TEST_SCREEN_VIDEO = Path(f"data/sessions/{TEST_SESSION_ID}/screen.mp4")


def print_header(title):
    """Print formatted test header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_step(step_num, total_steps, message):
    """Print formatted test step."""
    print(f"\n[{step_num}/{total_steps}] {message}")


def print_success(message):
    """Print success message."""
    print(f"  ✓ {message}")


def print_error(message):
    """Print error message."""
    print(f"  ✗ {message}")


def print_info(message):
    """Print info message."""
    print(f"    {message}")


def test_hume_ai_workflow():
    """
    Test complete Hume AI workflow with real API.

    Steps:
    1. Initialize client
    2. Upload video
    3. Poll for completion
    4. Fetch results
    5. Validate structure
    6. Store locally
    """
    print_header("TEST 1/3: Hume AI Workflow")

    try:
        # Step 1: Initialize client
        print_step(1, 6, "Initializing Hume AI client")
        config = Config()
        api_key = config.get_config_value("hume_api_key")

        if not api_key:
            print_error("HUME_API_KEY not found in .env")
            return False

        client = HumeExpressionClient(api_key=api_key)
        print_success("Client initialized")
        print_info(f"API Key: {api_key[:8]}...")

        # Step 2: Upload video
        print_step(2, 6, f"Uploading video: {TEST_CAM_VIDEO.name}")

        if not TEST_CAM_VIDEO.exists():
            print_error(f"Video file not found: {TEST_CAM_VIDEO}")
            return False

        print_info(f"File size: {TEST_CAM_VIDEO.stat().st_size / (1024*1024):.1f} MB")

        start_time = time.time()
        job_id = client.analyze_video(
            video_path=TEST_CAM_VIDEO,
            include_face=True,
            include_prosody=False,
            include_language=False
        )

        if not job_id:
            print_error("Video upload failed")
            return False

        upload_time = time.time() - start_time
        print_success(f"Video uploaded in {upload_time:.1f}s")
        print_info(f"Job ID: {job_id}")

        # Step 3: Poll for completion
        print_step(3, 6, "Polling for job completion (this may take 5-10 minutes)")
        print_info("Checking status every 10 seconds...")

        poll_start = time.time()
        status = client.poll_job(job_id, timeout=600)  # 10 minute timeout
        poll_duration = time.time() - poll_start

        if status != "COMPLETED":
            print_error(f"Job did not complete. Status: {status}")
            return False

        print_success(f"Job completed after {poll_duration/60:.1f} minutes")

        # Step 4: Fetch results
        print_step(4, 6, "Fetching emotion analysis results")

        results = client.fetch_results(job_id)

        if not results:
            print_error("Failed to fetch results")
            return False

        print_success(f"Results fetched")
        print_info(f"Timeline frames: {len(results.get('timeline', []))}")
        print_info(f"Total frames analyzed: {results.get('frame_count', 0)}")

        # Step 5: Validate structure
        print_step(5, 6, "Validating results structure")

        required_fields = ["job_id", "timeline", "summary", "frame_count"]
        missing_fields = [f for f in required_fields if f not in results]

        if missing_fields:
            print_error(f"Missing fields: {missing_fields}")
            return False

        print_success("All required fields present")

        # Check summary emotions
        summary = results.get("summary", {})
        emotions = ["avg_concentration", "avg_frustration", "avg_boredom", "avg_stress"]
        found_emotions = [e for e in emotions if e in summary]

        print_info(f"Emotions found: {', '.join(found_emotions)}")

        for emotion in found_emotions:
            value = summary[emotion]
            print_info(f"  - {emotion}: {value:.3f}")

        # Step 6: Store locally
        print_step(6, 6, "Storing results locally")

        results_dir = Path("data/cloud_results") / TEST_SESSION_ID
        results_dir.mkdir(parents=True, exist_ok=True)

        results_file = results_dir / f"hume_{job_id}.json"

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        print_success(f"Results stored: {results_file}")
        print_info(f"File size: {results_file.stat().st_size / 1024:.1f} KB")

        print("\n" + "✓" * 70)
        print("HUME AI TEST PASSED")
        print("✓" * 70)

        return True

    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memories_ai_workflow():
    """
    Test complete Memories.ai workflow with real API.

    Steps:
    1. Initialize client
    2. Upload videos
    3. Wait for processing
    4. Chat for analysis
    5. Parse JSON response
    6. Validate structure
    7. Store locally
    8. Delete from cloud
    """
    print_header("TEST 2/3: Memories.ai Workflow")

    try:
        # Step 1: Initialize client
        print_step(1, 8, "Initializing Memories.ai client")
        config = Config()
        api_key = config.get_config_value("mem_ai_api_key")

        if not api_key:
            print_error("MEM_AI_API_KEY not found in .env")
            return False

        client = MemoriesClient(api_key=api_key)
        print_success("Client initialized")
        print_info(f"API Key: {api_key[:8]}...")

        # Step 2: Upload videos
        print_step(2, 8, "Uploading videos to Memories.ai")

        unique_id = f"test_session_{int(time.time())}"
        print_info(f"Unique ID: {unique_id}")

        # Upload cam video
        print_info(f"Uploading cam video: {TEST_CAM_VIDEO.name} ({TEST_CAM_VIDEO.stat().st_size / (1024*1024):.1f} MB)")
        cam_start = time.time()
        cam_video_no = client.upload_video(TEST_CAM_VIDEO, unique_id=unique_id)

        if not cam_video_no:
            print_error("Cam video upload failed")
            return False

        cam_time = time.time() - cam_start
        print_success(f"Cam video uploaded in {cam_time:.1f}s (video_no: {cam_video_no})")

        # Upload screen video
        print_info(f"Uploading screen video: {TEST_SCREEN_VIDEO.name} ({TEST_SCREEN_VIDEO.stat().st_size / (1024*1024):.1f} MB)")
        screen_start = time.time()
        screen_video_no = client.upload_video(TEST_SCREEN_VIDEO, unique_id=unique_id)

        if not screen_video_no:
            print_error("Screen video upload failed")
            return False

        screen_time = time.time() - screen_start
        print_success(f"Screen video uploaded in {screen_time:.1f}s (video_no: {screen_video_no})")

        # Step 3: Wait for processing
        print_step(3, 8, "Waiting for video processing (2-5 minutes)")

        # Wait for cam video
        print_info("Waiting for cam video processing...")
        process_start = time.time()
        if not client.wait_for_processing(cam_video_no, unique_id, max_wait=300):
            print_error("Cam video processing timed out")
            return False

        print_success(f"Cam video processed in {(time.time() - process_start)/60:.1f} minutes")

        # Wait for screen video
        print_info("Waiting for screen video processing...")
        process_start = time.time()
        if not client.wait_for_processing(screen_video_no, unique_id, max_wait=300):
            print_error("Screen video processing timed out")
            return False

        print_success(f"Screen video processed in {(time.time() - process_start)/60:.1f} minutes")

        # Step 4: Chat for analysis
        print_step(4, 8, "Requesting analysis via chat")

        prompt = """Analyze this focus session by examining both the webcam and screen recordings.

Provide a JSON response with the following EXACT structure:

{
  "time_segmentation": [
    {
      "start_time": 0.0,
      "end_time": 120.5,
      "label": "Focus",
      "task_hypothesis": "Coding in IDE",
      "confidence": 0.85
    }
  ],
  "app_usage": [
    {
      "app_class": "IDE",
      "total_seconds": 450.2,
      "percentage": 0.62,
      "is_productive": true
    }
  ],
  "distraction_analysis": {
    "total_distraction_time": 125.3,
    "distraction_events": [
      {
        "start_time": 200.0,
        "end_time": 215.5,
        "trigger": "Social media",
        "evidence": "Opened Instagram on screen"
      }
    ]
  },
  "insights": {
    "focus_ratio": 0.72,
    "avg_focus_bout_minutes": 15.3,
    "primary_distractor": "Social media",
    "productivity_score": 0.68,
    "recommendations": [
      "Block social media during focus sessions"
    ]
  }
}

IMPORTANT: Respond ONLY with valid JSON. Do not include any markdown formatting or explanatory text."""

        print_info("Sending chat request...")
        chat_start = time.time()
        analysis_text = client.chat_with_video(
            video_nos=[cam_video_no, screen_video_no],
            prompt=prompt,
            unique_id=unique_id,
            stream=True
        )

        if not analysis_text:
            print_error("Chat failed to return analysis")
            return False

        chat_time = time.time() - chat_start
        print_success(f"Analysis received in {chat_time:.1f}s")
        print_info(f"Response length: {len(analysis_text)} characters")

        # Step 5: Parse JSON response
        print_step(5, 8, "Parsing JSON response")

        # Try to parse JSON (handle markdown blocks)
        clean_text = analysis_text.strip()
        if clean_text.startswith("```"):
            print_info("Detected markdown code blocks, extracting JSON...")
            lines = clean_text.split('\n')
            json_lines = []
            in_code_block = False
            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    json_lines.append(line)
            clean_text = '\n'.join(json_lines)

        try:
            results = json.loads(clean_text)
            print_success("JSON parsed successfully")
        except json.JSONDecodeError as e:
            print_error(f"JSON parsing failed: {e}")
            print_info("Raw response (first 500 chars):")
            print_info(analysis_text[:500])
            return False

        # Step 6: Validate structure
        print_step(6, 8, "Validating results structure")

        required_fields = ["time_segmentation", "app_usage", "distraction_analysis", "insights"]
        missing_fields = [f for f in required_fields if f not in results]

        if missing_fields:
            print_error(f"Missing fields: {missing_fields}")
            print_info(f"Found fields: {list(results.keys())}")
            return False

        print_success("All required fields present")

        # Print insights
        insights = results.get("insights", {})
        if "focus_ratio" in insights:
            print_info(f"Focus ratio: {insights['focus_ratio']:.2%}")
        if "primary_distractor" in insights:
            print_info(f"Primary distractor: {insights['primary_distractor']}")
        if "productivity_score" in insights:
            print_info(f"Productivity score: {insights['productivity_score']:.2f}")

        # Step 7: Store locally
        print_step(7, 8, "Storing results locally")

        results_dir = Path("data/cloud_results") / TEST_SESSION_ID
        results_dir.mkdir(parents=True, exist_ok=True)

        results_file = results_dir / f"memories_{unique_id}.json"

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        print_success(f"Results stored: {results_file}")
        print_info(f"File size: {results_file.stat().st_size / 1024:.1f} KB")

        # Step 8: Delete from cloud
        print_step(8, 8, "Deleting videos from cloud")

        cam_deleted = client.delete_video(cam_video_no, unique_id)
        screen_deleted = client.delete_video(screen_video_no, unique_id)

        if cam_deleted and screen_deleted:
            print_success("Videos deleted from cloud")
        else:
            print_error("Failed to delete some videos")
            print_info(f"Cam deleted: {cam_deleted}, Screen deleted: {screen_deleted}")

        print("\n" + "✓" * 70)
        print("MEMORIES.AI TEST PASSED")
        print("✓" * 70)

        return True

    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cloud_analysis_manager_workflow():
    """
    Test CloudAnalysisManager with full integrated workflow.

    Steps:
    1. Initialize CloudAnalysisManager
    2. Upload session to both providers
    3. Monitor job status
    4. Retrieve results
    5. Verify safety flags
    6. Delete cloud videos
    7. Verify local storage
    """
    print_header("TEST 3/3: CloudAnalysisManager Full Workflow")

    try:
        # Step 1: Initialize CloudAnalysisManager
        print_step(1, 7, "Initializing CloudAnalysisManager")

        config = Config()

        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_path = Path(temp_db.name)
        temp_db.close()

        schema_path = Path("config/schema.sql")
        database = Database(db_path, schema_path)

        # Initialize clients
        hume_key = config.get_config_value("hume_api_key")
        mem_key = config.get_config_value("mem_ai_api_key")

        hume_client = HumeExpressionClient(api_key=hume_key) if hume_key else None
        memories_client = MemoriesClient(api_key=mem_key) if mem_key else None

        manager = CloudAnalysisManager(
            config=config,
            database=database,
            hume_client=hume_client,
            memories_client=memories_client
        )

        print_success("CloudAnalysisManager initialized")
        print_info(f"Hume client: {'✓' if hume_client else '✗'}")
        print_info(f"Memories client: {'✓' if memories_client else '✗'}")

        # Step 2: Upload session
        print_step(2, 7, "Uploading session to both providers (BLOCKING)")

        upload_start = time.time()
        hume_job_id, memories_job_id = manager.upload_session_for_analysis(
            session_id=TEST_SESSION_ID,
            cam_video_path=TEST_CAM_VIDEO,
            screen_video_path=TEST_SCREEN_VIDEO,
            run_hume=True,
            run_memories=True
        )
        upload_time = time.time() - upload_start

        if not hume_job_id or not memories_job_id:
            print_error("Upload failed")
            print_info(f"Hume job: {hume_job_id}")
            print_info(f"Memories job: {memories_job_id}")
            return False

        print_success(f"Upload completed in {upload_time/60:.1f} minutes")
        print_info(f"Hume job ID: {hume_job_id}")
        print_info(f"Memories job ID: {memories_job_id}")

        # Verify database records
        hume_job = database.get_cloud_job(hume_job_id)
        memories_job = database.get_cloud_job(memories_job_id)

        print_info(f"Hume status: {hume_job.status.value}")
        print_info(f"Memories status: {memories_job.status.value}")
        print_info(f"Hume can_delete: {hume_job.can_delete_remote}")
        print_info(f"Memories can_delete: {memories_job.can_delete_remote}")

        # Step 3: Monitor job status
        print_step(3, 7, "Monitoring job status (polling every 30s)")

        poll_start = time.time()
        max_wait = 600  # 10 minutes
        poll_interval = 30

        hume_completed = False
        memories_completed = False

        while (time.time() - poll_start) < max_wait:
            if not hume_completed:
                hume_status = manager.check_job_status(hume_job_id)
                if hume_status == CloudJobStatus.COMPLETED:
                    hume_completed = True
                    print_success(f"Hume AI completed after {(time.time() - poll_start)/60:.1f} minutes")

            if not memories_completed:
                memories_status = manager.check_job_status(memories_job_id)
                if memories_status == CloudJobStatus.COMPLETED:
                    memories_completed = True
                    print_success(f"Memories.ai completed after {(time.time() - poll_start)/60:.1f} minutes")

            if hume_completed and memories_completed:
                break

            if (time.time() - poll_start) < max_wait:
                print_info(f"Waiting... (elapsed: {(time.time() - poll_start)/60:.1f}min)")
                time.sleep(poll_interval)

        if not (hume_completed and memories_completed):
            print_error("Jobs did not complete in time")
            return False

        # Step 4: Retrieve results
        print_step(4, 7, "Retrieving and storing results")

        hume_results_path = manager.retrieve_and_store_results(hume_job_id)
        memories_results_path = manager.retrieve_and_store_results(memories_job_id)

        if not hume_results_path or not memories_results_path:
            print_error("Failed to retrieve results")
            return False

        print_success(f"Hume results: {hume_results_path}")
        print_success(f"Memories results: {memories_results_path}")

        # Step 5: Verify safety flags
        print_step(5, 7, "Verifying safety flags")

        hume_job = database.get_cloud_job(hume_job_id)
        memories_job = database.get_cloud_job(memories_job_id)

        if not hume_job.can_delete_remote:
            print_error("Hume can_delete_remote should be True after results fetched")
            return False

        if not memories_job.can_delete_remote:
            print_error("Memories can_delete_remote should be True after results fetched")
            return False

        print_success("Safety flags verified (can_delete_remote = True)")

        # Step 6: Delete cloud videos
        print_step(6, 7, "Deleting cloud videos")

        hume_deleted = manager.delete_cloud_videos(hume_job_id)
        memories_deleted = manager.delete_cloud_videos(memories_job_id)

        if not (hume_deleted and memories_deleted):
            print_error("Failed to delete cloud videos")
            return False

        print_success("Cloud videos deleted")

        # Verify deletion timestamps
        hume_job = database.get_cloud_job(hume_job_id)
        memories_job = database.get_cloud_job(memories_job_id)

        print_info(f"Hume deleted at: {hume_job.remote_deleted_at}")
        print_info(f"Memories deleted at: {memories_job.remote_deleted_at}")

        # Step 7: Verify local storage
        print_step(7, 7, "Verifying local storage")

        if not Path(hume_results_path).exists():
            print_error(f"Hume results file not found: {hume_results_path}")
            return False

        if not Path(memories_results_path).exists():
            print_error(f"Memories results file not found: {memories_results_path}")
            return False

        print_success("Local results files verified")
        print_info(f"Hume file size: {Path(hume_results_path).stat().st_size / 1024:.1f} KB")
        print_info(f"Memories file size: {Path(memories_results_path).stat().st_size / 1024:.1f} KB")

        # Cleanup temp database
        db_path.unlink()

        print("\n" + "✓" * 70)
        print("CLOUD ANALYSIS MANAGER TEST PASSED")
        print("✓" * 70)

        return True

    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all real API integration tests."""
    print("\n" + "=" * 70)
    print("  REAL API INTEGRATION TEST SUITE")
    print("  " + "-" * 66)
    print(f"  Test Session: {TEST_SESSION_ID}")
    print(f"  Cam Video: {TEST_CAM_VIDEO}")
    print(f"  Screen Video: {TEST_SCREEN_VIDEO}")
    print("=" * 70)

    # Verify test files exist
    if not TEST_CAM_VIDEO.exists():
        print_error(f"Cam video not found: {TEST_CAM_VIDEO}")
        return 1

    if not TEST_SCREEN_VIDEO.exists():
        print_error(f"Screen video not found: {TEST_SCREEN_VIDEO}")
        return 1

    print_success(f"Test videos found")
    print_info(f"Cam: {TEST_CAM_VIDEO.stat().st_size / (1024*1024):.1f} MB")
    print_info(f"Screen: {TEST_SCREEN_VIDEO.stat().st_size / (1024*1024):.1f} MB")

    # Track results
    results = []
    start_time = time.time()

    # Run tests
    print_info("\nStarting tests... (estimated 15-20 minutes)")
    print_info("⚠️  This will incur API costs (~$1.50)\n")

    time.sleep(2)  # Give user a moment to cancel

    # Test 1: Hume AI
    test1_result = test_hume_ai_workflow()
    results.append(("Hume AI Workflow", test1_result))

    # Test 2: Memories.ai
    test2_result = test_memories_ai_workflow()
    results.append(("Memories.ai Workflow", test2_result))

    # Test 3: CloudAnalysisManager
    test3_result = test_cloud_analysis_manager_workflow()
    results.append(("CloudAnalysisManager Workflow", test3_result))

    # Summary
    total_time = time.time() - start_time

    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {status:12} | {test_name}")

    print("=" * 70)
    print(f"  Total time: {total_time/60:.1f} minutes")
    print("=" * 70)

    # Final verdict
    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nCloud analysis implementation is verified and ready for production.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nPlease review the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
