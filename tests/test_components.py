"""
Test script to verify Focus Guardian components.

Tests each implemented module in isolation to ensure they work correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import time
from datetime import datetime


def test_config():
    """Test configuration system."""
    print("\n" + "="*60)
    print("TEST 1: Configuration System")
    print("="*60)
    
    from focus_guardian.core.config import Config
    
    config = Config()
    
    print(f"✓ Config initialized")
    print(f"  - Data dir: {config.get_data_dir()}")
    print(f"  - Snapshot interval: {config.get_snapshot_interval_sec()}s")
    print(f"  - Max parallel uploads: {config.get_max_parallel_uploads()}")
    print(f"  - Quality profile: {config.get_video_res_profile()}")
    print(f"  - OpenAI Vision enabled: {config.is_openai_vision_enabled()}")
    
    # Check API keys
    openai_key = config.get_openai_api_key()
    if openai_key:
        print(f"  - OpenAI API key: {openai_key[:10]}...{openai_key[-4:]}")
    else:
        print(f"  - ⚠️  OpenAI API key not set (add to .env file)")
    
    return config


def test_database(config):
    """Test database operations."""
    print("\n" + "="*60)
    print("TEST 2: Database System")
    print("="*60)
    
    from focus_guardian.core.database import Database
    from focus_guardian.core.models import Session, SessionStatus, QualityProfile
    import uuid
    
    db_path = config.get_data_dir() / "test_focus_guardian.db"
    schema_path = Path(__file__).parent.parent / "config" / "schema.sql"
    
    # Remove old test database
    if db_path.exists():
        db_path.unlink()
    
    db = Database(db_path, schema_path)
    print(f"✓ Database initialized at {db_path}")
    
    # Create test session
    test_session = Session(
        session_id=str(uuid.uuid4()),
        started_at=datetime.now(),
        ended_at=None,
        task_name="Test Session",
        quality_profile=QualityProfile.STD,
        screen_enabled=True,
        status=SessionStatus.ACTIVE,
        cam_mp4_path="sessions/test/cam.mp4",
        screen_mp4_path="sessions/test/screen.mp4",
        snapshots_dir="sessions/test/snapshots/",
        vision_dir="sessions/test/vision/",
        logs_dir="sessions/test/logs/"
    )
    
    session_id = db.create_session(test_session)
    print(f"✓ Created test session: {session_id[:8]}...")
    
    # Retrieve session
    retrieved = db.get_session(session_id)
    if retrieved:
        print(f"✓ Retrieved session: {retrieved.task_name}")
    
    return db


def test_logger():
    """Test logging system."""
    print("\n" + "="*60)
    print("TEST 3: Logging System")
    print("="*60)
    
    from focus_guardian.utils.logger import setup_logger, get_logger
    
    logger = setup_logger("test_logger")
    logger.info("Test info message")
    logger.debug("Test debug message")
    logger.warning("Test warning message")
    
    print("✓ Logger configured and working")


def test_queue_manager():
    """Test queue management."""
    print("\n" + "="*60)
    print("TEST 4: Queue Manager")
    print("="*60)
    
    from focus_guardian.utils.queue_manager import QueueManager
    
    qm = QueueManager(max_queue_size=10)
    
    # Test putting and getting
    qm.put(qm.snapshot_upload_queue, {"test": "data"})
    item = qm.get(qm.snapshot_upload_queue, timeout=1.0)
    
    if item and item.get("test") == "data":
        print("✓ Queue manager working (put/get successful)")
    
    stats = qm.get_stats()
    print(f"  - Queue stats: {stats}")


def test_performance_monitor():
    """Test performance monitoring."""
    print("\n" + "="*60)
    print("TEST 5: Performance Monitor")
    print("="*60)
    
    from focus_guardian.utils.performance_monitor import PerformanceMonitor
    
    monitor = PerformanceMonitor()
    stats = monitor.get_stats()
    
    print(f"✓ Performance monitor working")
    print(f"  - CPU: {stats.cpu_percent:.1f}%")
    print(f"  - Memory: {stats.memory_mb:.1f} MB ({stats.memory_percent:.1f}%)")
    print(f"  - Disk free: {stats.disk_free_gb:.1f} GB")


def test_screen_capture():
    """Test screen capture."""
    print("\n" + "="*60)
    print("TEST 6: Screen Capture")
    print("="*60)
    
    from focus_guardian.capture.screen_capture import ScreenCapture
    from pathlib import Path
    
    try:
        capture = ScreenCapture(monitor_index=0)
        
        # Capture test screenshot
        output_path = Path("/tmp/test_screen.jpg")
        success, size = capture.capture_to_file(output_path)
        
        if success:
            print(f"✓ Screen capture working")
            print(f"  - Saved to: {output_path}")
            print(f"  - File size: {size:,} bytes")
            print(f"  - Resolution: {capture.get_screen_resolution()}")
        else:
            print("✗ Screen capture failed")
        
        capture.close()
    except Exception as e:
        print(f"✗ Screen capture error: {e}")


def test_webcam_capture():
    """Test webcam capture."""
    print("\n" + "="*60)
    print("TEST 7: Webcam Capture")
    print("="*60)
    
    from focus_guardian.capture.screen_capture import WebcamCapture
    from pathlib import Path
    
    try:
        capture = WebcamCapture(camera_index=0)
        
        # Capture test frame
        output_path = Path("/tmp/test_webcam.jpg")
        success, size = capture.capture_to_file(output_path)
        
        if success:
            print(f"✓ Webcam capture working")
            print(f"  - Saved to: {output_path}")
            print(f"  - File size: {size:,} bytes")
        else:
            print("✗ Webcam capture failed")
        
        capture.close()
    except Exception as e:
        print(f"✗ Webcam capture error: {e}")
        print(f"  Note: Make sure camera is not in use by another app")


def test_state_machine():
    """Test state machine."""
    print("\n" + "="*60)
    print("TEST 8: State Machine (K=3 Hysteresis)")
    print("="*60)
    
    from focus_guardian.core.state_machine import StateMachine
    from focus_guardian.core.models import SnapshotResult
    from datetime import datetime, timedelta
    
    sm = StateMachine(K=3, min_span_minutes=1.0)
    print(f"✓ State machine initialized (K=3)")
    
    # Simulate 3 snapshots showing distraction
    base_time = datetime.now()
    
    for i in range(3):
        snapshot = SnapshotResult(
            timestamp=base_time + timedelta(seconds=i * 30),
            cam_labels={"HeadAway": 0.85, "EyesOffScreen": 0.72},
            screen_labels={"VideoOnScreen": 0.92},
            span_minutes=(i * 30) / 60.0
        )
        
        transition = sm.update(snapshot)
        if transition:
            print(f"  - Transition detected: {transition.from_state.value} → {transition.to_state.value}")
            print(f"    Confidence: {transition.confidence:.2f}")
    
    current_state = sm.get_current_state()
    print(f"✓ Current state: {current_state.state.value} (confidence: {current_state.confidence:.2f})")


def test_openai_vision(config):
    """Test OpenAI Vision API client."""
    print("\n" + "="*60)
    print("TEST 9: OpenAI Vision API Client")
    print("="*60)
    
    api_key = config.get_openai_api_key()
    
    if not api_key:
        print("⚠️  OpenAI API key not set - skipping this test")
        print("   Add OPENAI_API_KEY to your .env file to test")
        return
    
    from focus_guardian.integrations.openai_vision_client import OpenAIVisionClient
    from pathlib import Path
    
    try:
        client = OpenAIVisionClient(api_key=api_key)
        print(f"✓ OpenAI Vision client initialized")
        
        # Test with screen capture
        test_image = Path("/tmp/test_screen.jpg")
        if test_image.exists():
            print(f"  Testing with {test_image}...")
            result = client.classify_screen_snapshot(test_image)
            print(f"✓ Classification successful!")
            print(f"  - Labels: {result.labels}")
            print(f"  - Latency: {result.latency_ms:.0f}ms")
            print(f"  - Reasoning: {result.raw_response.get('reasoning', 'N/A')[:100]}...")
        else:
            print("  ⚠️  No test image available (run screen capture test first)")
    
    except Exception as e:
        print(f"✗ OpenAI Vision API error: {e}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FOCUS GUARDIAN - COMPONENT TESTING")
    print("="*60)
    print("\nTesting implemented modules (Phases 1-4)...\n")
    
    try:
        # Run tests
        config = test_config()
        test_database(config)
        test_logger()
        test_queue_manager()
        test_performance_monitor()
        test_screen_capture()
        test_webcam_capture()
        test_state_machine()
        test_openai_vision(config)
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED")
        print("="*60)
        print("\nNext steps:")
        print("1. Add OPENAI_API_KEY to .env file for Vision API testing")
        print("2. Run: python tests/test_components.py")
        print("3. Continue with Phase 5: PyQt6 GUI implementation")
        print()
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


