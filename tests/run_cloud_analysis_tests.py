"""
Master test runner for all cloud analysis tests.

Run with: python tests/run_cloud_analysis_tests.py
"""

import sys
import subprocess
from pathlib import Path


def run_test(test_file, description):
    """Run a single test file and return success status."""
    print("\n" + "="*70)
    print(f"RUNNING: {description}")
    print("="*70)

    test_path = Path(__file__).parent / test_file

    try:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print(f"\n✓ {description} - PASSED")
            return True
        else:
            print(f"\n✗ {description} - FAILED")
            return False

    except Exception as e:
        print(f"\n✗ {description} - ERROR: {e}")
        return False


def main():
    """Run all cloud analysis tests in order."""
    print("\n" + "#"*70)
    print("#" + " "*68 + "#")
    print("#" + "  FOCUS GUARDIAN - CLOUD ANALYSIS TEST SUITE".center(68) + "#")
    print("#" + " "*68 + "#")
    print("#"*70)

    tests = [
        ("test_cloud_analysis_models.py", "Cloud Analysis Models (CloudAnalysisJob)"),
        ("test_cloud_analysis_database.py", "Cloud Analysis Database Operations"),
        ("test_memories_parsing.py", "Memories.ai JSON Parsing & Validation"),
        ("test_cloud_analysis_manager.py", "Cloud Analysis Manager (with mocks)"),
    ]

    results = []
    passed = 0
    failed = 0

    for test_file, description in tests:
        success = run_test(test_file, description)
        results.append((description, success))

        if success:
            passed += 1
        else:
            failed += 1

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for description, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status:12} - {description}")

    print("\n" + "="*70)
    print(f"Total: {len(tests)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("="*70)

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nCloud analysis implementation is ready for production.")
        print("\nNext steps:")
        print("1. Configure API keys in .env file")
        print("2. Test with real Hume AI and Memories.ai APIs")
        print("3. Run end-to-end integration test with GUI")
        print()
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
