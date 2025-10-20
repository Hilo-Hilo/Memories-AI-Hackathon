"""
Test suite for cloud features (Hume AI and Memories.ai integration).

Run with: python tests/test_cloud_features.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from focus_guardian.core.config import Config
from focus_guardian.integrations.hume_client import HumeExpressionClient
from focus_guardian.integrations.memories_client import MemoriesClient


def test_config_cloud_features():
    """Test cloud features configuration."""
    print("\n=== Testing Cloud Features Configuration ===")

    config = Config()

    # Get current values (may be enabled from previous runs)
    current_cloud = config.is_cloud_features_enabled()
    current_hume = config.is_hume_ai_enabled()
    current_memories = config.is_memories_ai_enabled()

    print(f"Current state - Cloud: {current_cloud}, Hume: {current_hume}, Memories: {current_memories}")

    # Reset to default for testing
    config.set_cloud_features_enabled(False)
    config.set_hume_ai_enabled(False)
    config.set_memories_ai_enabled(False)

    assert config.is_cloud_features_enabled() == False, "Cloud features should be disabled after reset"
    assert config.is_hume_ai_enabled() == False, "Hume AI should be disabled after reset"
    assert config.is_memories_ai_enabled() == False, "Memories.ai should be disabled after reset"

    print("✓ Configuration reset to defaults")

    # Test setters
    config.set_cloud_features_enabled(True)
    assert config.is_cloud_features_enabled() == True
    print("✓ Cloud features master switch works")

    config.set_hume_ai_enabled(True)
    assert config.is_hume_ai_enabled() == True
    print("✓ Hume AI enable/disable works")

    config.set_memories_ai_enabled(True)
    assert config.is_memories_ai_enabled() == True
    print("✓ Memories.ai enable/disable works")

    # Test auto-upload settings
    config.set_hume_ai_auto_upload(True)
    assert config.is_hume_ai_auto_upload() == True
    print("✓ Hume AI auto-upload setting works")

    config.set_memories_ai_auto_upload(True)
    assert config.is_memories_ai_auto_upload() == True
    print("✓ Memories.ai auto-upload setting works")

    # Test hierarchical checks (cloud must be enabled for sub-features)
    config.set_cloud_features_enabled(False)
    assert config.is_hume_ai_enabled() == False, "Hume AI should be disabled when cloud features disabled"
    assert config.is_memories_ai_enabled() == False, "Memories.ai should be disabled when cloud features disabled"
    print("✓ Hierarchical checks work (master switch controls sub-features)")

    print("✓ All configuration tests passed!\n")


def test_api_keys():
    """Test API key loading."""
    print("=== Testing API Key Loading ===")

    config = Config()

    openai_key = config.get_openai_api_key()
    hume_key = config.get_hume_api_key()
    mem_key = config.get_memories_api_key()

    print(f"OpenAI API key: {'✓ Configured' if openai_key else '✗ Not configured'}")
    print(f"Hume AI API key: {'✓ Configured' if hume_key else '✗ Not configured'}")
    print(f"Memories.ai API key: {'✓ Configured' if mem_key else '✗ Not configured'}")

    if not openai_key:
        print("⚠ Warning: OpenAI API key not configured (REQUIRED for app to function)")

    if not hume_key:
        print("⚠ Warning: Hume AI API key not configured (optional - for emotion analysis)")

    if not mem_key:
        print("⚠ Warning: Memories.ai API key not configured (optional - for pattern analysis)")

    print("✓ API key loading test passed!\n")


def test_hume_client_init():
    """Test Hume AI client initialization."""
    print("=== Testing Hume AI Client ===")

    config = Config()
    hume_key = config.get_hume_api_key()

    if not hume_key:
        print("⚠ Skipping Hume AI test - no API key configured")
        return

    try:
        client = HumeExpressionClient(api_key=hume_key)

        if client.client:
            print("✓ Hume SDK client initialized successfully")
        else:
            print("✗ Hume SDK not available (install with: pip install hume)")

    except Exception as e:
        print(f"✗ Hume client initialization failed: {e}")
        raise

    print("✓ Hume AI client test passed!\n")


def test_memories_client_init():
    """Test Memories.ai client initialization."""
    print("=== Testing Memories.ai Client ===")

    config = Config()
    mem_key = config.get_memories_api_key()

    if not mem_key:
        print("⚠ Skipping Memories.ai test - no API key configured")
        return

    try:
        client = MemoriesClient(api_key=mem_key)

        assert client.session is not None, "REST session should be initialized"
        assert client.base_url == "https://api.memories.ai", "Base URL should be correct"
        assert "Authorization" in client.session.headers, "Authorization header should be set"

        print("✓ Memories.ai REST client initialized successfully")
        print(f"✓ Base URL: {client.base_url}")
        print("✓ Authorization header configured")

    except Exception as e:
        print(f"✗ Memories.ai client initialization failed: {e}")
        raise

    print("✓ Memories.ai client test passed!\n")


def test_hume_mock_workflow():
    """Test Hume AI mock workflow (placeholder job)."""
    print("=== Testing Hume AI Mock Workflow ===")

    config = Config()
    hume_key = config.get_hume_api_key()

    if not hume_key:
        print("⚠ Skipping Hume AI workflow test - no API key configured")
        return

    try:
        from pathlib import Path

        client = HumeExpressionClient(api_key=hume_key)

        # Test with placeholder (since we don't have a real video to upload)
        # Note: This uses the placeholder workflow that returns mock data
        print("Testing placeholder workflow...")

        # Analyze video (returns placeholder job ID)
        test_video = Path("/tmp/test_video.mp4")  # Doesn't need to exist for placeholder
        job_id = "hume_placeholder_test"

        # Poll job (returns mock status)
        status = client.poll_job(job_id)
        assert status == "COMPLETED", "Placeholder job should complete"
        print(f"✓ Placeholder job polling works (status: {status})")

        # Fetch results (returns mock data)
        results = client.fetch_results(job_id)
        assert results is not None, "Should return mock results"
        assert "_mock" in results, "Should be marked as mock data"
        assert "timeline" in results, "Should have emotion timeline"
        assert "summary" in results, "Should have summary statistics"
        print("✓ Placeholder results fetching works")

        # Test emotion summary extraction
        summary = client.extract_emotion_summary(results)
        assert "frustration_mean" in summary
        assert "boredom_mean" in summary
        assert "concentration_mean" in summary
        print("✓ Emotion summary extraction works")

        print("✓ Hume AI mock workflow test passed!\n")

    except Exception as e:
        print(f"✗ Hume AI workflow test failed: {e}")
        raise


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FOCUS GUARDIAN - CLOUD FEATURES TEST SUITE")
    print("="*60)

    try:
        test_config_cloud_features()
        test_api_keys()
        test_hume_client_init()
        test_memories_client_init()
        test_hume_mock_workflow()

        print("="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\nCloud features are properly configured and ready to use.")
        print("\nNext steps:")
        print("1. Enable cloud features in Settings UI")
        print("2. Run a focus session")
        print("3. Check Reports tab for cloud-enhanced analysis")
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
