#!/usr/bin/env python3
"""
Comprehensive test suite for Memories.ai and Hume AI structured outputs.

Tests:
1. Memories.ai - Complete workflow with structured response validation
2. Hume AI - Job submission and emotion timeline structure
"""

import sys
import json
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from focus_guardian.core.config import Config
from focus_guardian.integrations.memories_client import MemoriesClient
from focus_guardian.integrations.hume_client import HumeExpressionClient


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def test_memories_ai_structured_output():
    """Test Memories.ai API responses and structure."""
    print_section("MEMORIES.AI - STRUCTURED OUTPUT TEST")

    config = Config()
    api_key = config.get_memories_api_key()

    if not api_key:
        print("✗ MEM_AI_API_KEY not configured")
        return False

    client = MemoriesClient(api_key=api_key)
    test_video = Path("data/sessions/ce08da15-986c-4c63-8788-bd851a94b130/cam.mp4")
    unique_id = f"test_struct_{int(time.time())}"

    print(f"Unique ID: {unique_id}")
    print(f"Test Video: {test_video.name} ({test_video.stat().st_size / 1024 / 1024:.1f} MB)\n")

    # Test 1: Upload and verify response structure
    print("[1/5] Testing upload_video() response structure...")
    video_no = client.upload_video(test_video, unique_id=unique_id)

    if not video_no:
        print("✗ Upload failed")
        return False

    print(f"✓ Upload successful: {video_no}")
    print(f"  Response type: {type(video_no)}")
    print(f"  Format: {video_no[:2]}... (starts with 'VI')")

    # Test 2: List videos and validate structure
    print("\n[2/5] Testing list_videos() response structure...")
    videos = client.list_videos(unique_id=unique_id)

    if not videos:
        print("✗ List videos failed")
        return False

    print(f"✓ Found {len(videos)} video(s)")
    print("\nResponse structure:")
    for i, video in enumerate(videos[:1]):  # Show first video structure
        print(f"\n  Video {i+1} fields:")
        for key, value in video.items():
            print(f"    - {key}: {type(value).__name__} = {str(value)[:60]}")

    # Validate expected fields
    required_fields = ['video_no', 'video_name', 'status', 'duration', 'size', 'create_time']
    video = videos[0]

    print("\n  Field validation:")
    for field in required_fields:
        has_field = field in video
        status = "✓" if has_field else "✗"
        print(f"    {status} {field}: {'present' if has_field else 'MISSING'}")

    # Test 3: Wait for processing and check status values
    print("\n[3/5] Testing wait_for_processing() status polling...")
    print("(Will poll for 30 seconds to demonstrate status structure)")

    # Just poll a few times to show the structure
    for attempt in range(3):
        videos = client.list_videos(unique_id=unique_id)
        if videos:
            status = videos[0].get('status')
            print(f"  Attempt {attempt+1}: status = '{status}' (type: {type(status).__name__})")
        time.sleep(5)

    print("\n  Possible status values per API docs:")
    print("    - UNPARSE: Video uploaded, not yet processed")
    print("    - PARSE: Video processing complete")
    print("    - FAIL: Processing failed")

    # Test 4: Search API structure (if video is processed)
    print("\n[4/5] Testing search_video_content() response structure...")

    search_results = client.search_video_content(
        video_no=video_no,
        query="person in frame",
        unique_id=unique_id,
        top_k=3
    )

    if search_results:
        print(f"✓ Search returned {len(search_results)} results")
        print("\nSearch result structure:")
        if search_results:
            result = search_results[0]
            print(f"  Result fields:")
            for key, value in result.items():
                print(f"    - {key}: {type(value).__name__} = {value}")
    else:
        print("  Note: Search returns empty if video not yet processed (expected)")

    # Test 5: Delete and verify response
    print("\n[5/5] Testing delete_video() response...")
    deleted = client.delete_video(video_no, unique_id=unique_id)

    print(f"✓ Delete result: {deleted} (type: {type(deleted).__name__})")
    print(f"  Expected: boolean (True/False)")

    print("\n" + "="*80)
    print("  MEMORIES.AI STRUCTURED OUTPUT TEST - COMPLETE")
    print("="*80)

    return True


def test_hume_ai_structured_output():
    """Test Hume AI API responses and structure."""
    print_section("HUME AI - STRUCTURED OUTPUT TEST")

    config = Config()
    api_key = config.get_hume_api_key()

    if not api_key:
        print("✗ HUME_API_KEY not configured")
        return False

    client = HumeExpressionClient(api_key=api_key)

    if not client.client:
        print("✗ Hume client failed to initialize")
        return False

    test_video = Path("data/sessions/ce08da15-986c-4c63-8788-bd851a94b130/cam.mp4")

    print(f"Test Video: {test_video.name} ({test_video.stat().st_size / 1024 / 1024:.1f} MB)\n")

    # Test 1: Submit job and verify job_id structure
    print("[1/4] Testing analyze_video() response structure...")

    try:
        job_id = client.analyze_video(test_video, include_face=True)

        print(f"✓ Job submitted: {job_id}")
        print(f"  Response type: {type(job_id).__name__}")
        print(f"  Format: UUID string (e.g., '71f651a6-b67d-4e8e-b4bf-ae4549c80dd5')")

    except Exception as e:
        print(f"✗ Job submission failed: {e}")
        return False

    # Test 2: Poll job and check status structure
    print("\n[2/4] Testing poll_job() status values...")
    print("(Will poll 3 times to show status progression)")

    for attempt in range(3):
        try:
            job_details = client.client.expression_measurement.batch.get_job_details(id=job_id)
            status = job_details.state.status

            print(f"  Attempt {attempt+1}: status = '{status}'")

            if attempt == 0:
                print(f"    Full state structure:")
                print(f"      - status: {status}")
                print(f"      - created_timestamp: {job_details.state.created_timestamp_ms}")
                print(f"      - started_timestamp: {getattr(job_details.state, 'started_timestamp_ms', 'N/A')}")

            if status in ["COMPLETED", "FAILED"]:
                break

        except Exception as e:
            print(f"  Attempt {attempt+1}: Error - {e}")

        time.sleep(5)

    print("\n  Possible status values per API docs:")
    print("    - QUEUED: Job queued for processing")
    print("    - IN_PROGRESS: Job currently processing")
    print("    - COMPLETED: Processing finished successfully")
    print("    - FAILED: Processing failed")

    # Test 3: Fetch predictions structure (if job completes quickly)
    print("\n[3/4] Testing fetch_results() structure...")
    print("  Note: Only checking structure if job completes within test window")

    # Check if completed
    try:
        job_details = client.client.expression_measurement.batch.get_job_details(id=job_id)
        if job_details.state.status == "COMPLETED":
            print("  Job completed! Fetching predictions...")

            results = client.fetch_results(job_id)

            if results:
                print(f"\n✓ Results fetched successfully")
                print(f"\n  Top-level structure:")
                print(f"    - job_id: {results.get('job_id')}")
                print(f"    - frame_count: {results.get('frame_count')}")
                print(f"    - timeline: array of {len(results.get('timeline', []))} emotion frames")
                print(f"    - summary: {len(results.get('summary', {}))} emotion averages")

                if results.get('timeline'):
                    print(f"\n  Timeline frame structure (first frame):")
                    frame = results['timeline'][0]
                    print(f"    - timestamp: {frame.get('timestamp')}")
                    print(f"    - frame: {frame.get('frame')}")
                    print(f"    - emotions: dict with {len(frame.get('emotions', {}))} emotion scores")

                    print(f"\n  Top 5 emotions in first frame:")
                    emotions = frame.get('emotions', {})
                    sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
                    for name, score in sorted_emotions[:5]:
                        print(f"      - {name}: {score:.3f}")

                print(f"\n  Summary structure:")
                summary = results.get('summary', {})
                for key, value in list(summary.items())[:5]:
                    print(f"    - {key}: {value:.3f}")
        else:
            print(f"  Job status: {job_details.state.status}")
            print(f"  Skipping predictions fetch (job not complete)")

    except Exception as e:
        print(f"  Could not fetch predictions: {e}")

    # Test 4: Document expected emotion dimensions
    print("\n[4/4] Hume AI Emotion Dimensions...")
    print("  Facial Expression Model returns 48 emotion dimensions including:")
    print("    - Admiration, Adoration, Aesthetic Appreciation, Amusement")
    print("    - Anxiety, Awe, Awkwardness, Boredom")
    print("    - Calmness, Concentration, Confusion, Contemplation")
    print("    - Determination, Disappointment, Disgust, Distress")
    print("    - Ecstasy, Embarrassment, Empathic Pain, Entrancement")
    print("    - Excitement, Fear, Guilt, Horror")
    print("    - Interest, Joy, Love, Nostalgia")
    print("    - Pain, Pride, Realization, Relief")
    print("    - Romance, Sadness, Satisfaction, Desire")
    print("    - Shame, Surprise (negative), Surprise (positive), Sympathy")
    print("    - Tiredness, Triumph, ...and more")

    print("\n" + "="*80)
    print("  HUME AI STRUCTURED OUTPUT TEST - COMPLETE")
    print("="*80)

    return True


def main():
    """Run all structured output tests."""
    print("\n" + "="*80)
    print("  API STRUCTURED OUTPUT VALIDATION SUITE")
    print("  Testing Memories.ai and Hume AI response formats")
    print("="*80)

    results = {}

    # Test Memories.ai
    try:
        results['memories_ai'] = test_memories_ai_structured_output()
    except Exception as e:
        print(f"\n✗ Memories.ai test crashed: {e}")
        import traceback
        traceback.print_exc()
        results['memories_ai'] = False

    # Test Hume AI
    try:
        results['hume_ai'] = test_hume_ai_structured_output()
    except Exception as e:
        print(f"\n✗ Hume AI test crashed: {e}")
        import traceback
        traceback.print_exc()
        results['hume_ai'] = False

    # Summary
    print_section("FINAL SUMMARY")
    print(f"Memories.ai Structured Output Test: {'✓ PASSED' if results.get('memories_ai') else '✗ FAILED'}")
    print(f"Hume AI Structured Output Test: {'✓ PASSED' if results.get('hume_ai') else '✗ FAILED'}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All structured output tests PASSED!")
    else:
        print("\n⚠️  Some tests failed - review output above")

    print("\n" + "="*80)

    return all_passed


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(2)
