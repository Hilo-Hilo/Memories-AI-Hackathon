"""
Test suite for Memories.ai JSON response parsing and validation.

Run with: python tests/test_memories_parsing.py
"""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from focus_guardian.session.cloud_analysis_manager import CloudAnalysisManager
from focus_guardian.core.config import Config
from focus_guardian.core.database import Database


def test_parse_valid_json():
    """Test parsing valid Memories.ai JSON response."""
    print("\n=== Testing Parse Valid JSON ===")

    manager = CloudAnalysisManager(Config(), None, None, None)

    valid_json = """{
  "time_segmentation": [
    {
      "start_time": 0.0,
      "end_time": 120.5,
      "label": "Focus",
      "task_hypothesis": "Coding in IDE",
      "confidence": 0.85
    },
    {
      "start_time": 120.5,
      "end_time": 135.0,
      "label": "Distraction",
      "task_hypothesis": "Checking social media",
      "confidence": 0.92
    }
  ],
  "app_usage": [
    {
      "app_class": "IDE",
      "total_seconds": 450.2,
      "percentage": 0.62,
      "is_productive": true
    },
    {
      "app_class": "Social",
      "total_seconds": 75.5,
      "percentage": 0.10,
      "is_productive": false
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
      "Block social media during focus sessions",
      "Take scheduled breaks every 25 minutes"
    ]
  }
}"""

    result = manager._parse_memories_response(valid_json)

    assert "time_segmentation" in result
    assert "app_usage" in result
    assert "distraction_analysis" in result
    assert "insights" in result

    assert len(result["time_segmentation"]) == 2
    assert len(result["app_usage"]) == 2
    assert result["insights"]["focus_ratio"] == 0.72
    assert result["insights"]["productivity_score"] == 0.68

    print("✓ Parsed valid JSON successfully")
    print(f"✓ Time segments: {len(result['time_segmentation'])}")
    print(f"✓ App usage entries: {len(result['app_usage'])}")
    print(f"✓ Focus ratio: {result['insights']['focus_ratio']}")
    print("✓ Valid JSON parsing test passed")


def test_parse_json_with_markdown():
    """Test parsing JSON wrapped in markdown code blocks."""
    print("\n=== Testing Parse JSON with Markdown ===")

    manager = CloudAnalysisManager(Config(), None, None, None)

    markdown_json = """```json
{
  "time_segmentation": [
    {
      "start_time": 0.0,
      "end_time": 100.0,
      "label": "Focus",
      "task_hypothesis": "Writing code",
      "confidence": 0.90
    }
  ],
  "app_usage": [
    {
      "app_class": "IDE",
      "total_seconds": 100.0,
      "percentage": 1.0,
      "is_productive": true
    }
  ],
  "distraction_analysis": {
    "total_distraction_time": 0.0,
    "distraction_events": []
  },
  "insights": {
    "focus_ratio": 1.0,
    "avg_focus_bout_minutes": 100.0,
    "primary_distractor": "None",
    "productivity_score": 1.0,
    "recommendations": ["Keep up the great work!"]
  }
}
```"""

    result = manager._parse_memories_response(markdown_json)

    assert "time_segmentation" in result
    assert len(result["time_segmentation"]) == 1
    assert result["insights"]["focus_ratio"] == 1.0

    print("✓ Parsed JSON from markdown code blocks")
    print(f"✓ Focus ratio: {result['insights']['focus_ratio']}")
    print("✓ Markdown parsing test passed")


def test_parse_invalid_json():
    """Test parsing invalid JSON (should return fallback structure)."""
    print("\n=== Testing Parse Invalid JSON ===")

    manager = CloudAnalysisManager(Config(), None, None, None)

    invalid_json = "This is not JSON at all. It's just text explaining the analysis."

    result = manager._parse_memories_response(invalid_json)

    # Should return fallback structure
    assert "time_segmentation" in result
    assert "app_usage" in result
    assert "distraction_analysis" in result
    assert "insights" in result
    assert "_raw_text" in result

    # Fallback values should be present
    assert isinstance(result["time_segmentation"], list)
    assert isinstance(result["app_usage"], list)
    assert "focus_ratio" in result["insights"]

    print("✓ Invalid JSON handled gracefully")
    print(f"✓ Fallback focus_ratio: {result['insights']['focus_ratio']}")
    print("✓ Raw text preserved in _raw_text field")
    print("✓ Invalid JSON parsing test passed")


def test_validate_hume_results():
    """Test Hume AI results validation."""
    print("\n=== Testing Validate Hume Results ===")

    manager = CloudAnalysisManager(Config(), None, None, None)

    # Valid Hume results
    valid_hume = {
        "job_id": "test_123",
        "timeline": [{"timestamp": 0.0, "emotions": {}}],
        "summary": {"avg_concentration": 0.7},
        "frame_count": 100
    }

    assert manager._validate_hume_results(valid_hume) == True
    print("✓ Valid Hume results passed validation")

    # Invalid Hume results (missing required field)
    invalid_hume = {
        "job_id": "test_123",
        "timeline": [],
        # Missing summary and frame_count
    }

    assert manager._validate_hume_results(invalid_hume) == False
    print("✓ Invalid Hume results failed validation (as expected)")

    print("✓ Hume results validation test passed")


def test_validate_memories_results():
    """Test Memories.ai results validation."""
    print("\n=== Testing Validate Memories Results ===")

    manager = CloudAnalysisManager(Config(), None, None, None)

    # Valid Memories results
    valid_memories = {
        "time_segmentation": [],
        "app_usage": [],
        "distraction_analysis": {},
        "insights": {}
    }

    assert manager._validate_memories_results(valid_memories) == True
    print("✓ Valid Memories results passed validation")

    # Invalid Memories results (missing required field)
    invalid_memories = {
        "time_segmentation": [],
        "app_usage": [],
        # Missing distraction_analysis and insights
    }

    assert manager._validate_memories_results(invalid_memories) == False
    print("✓ Invalid Memories results failed validation (as expected)")

    print("✓ Memories results validation test passed")


def test_parse_complex_memories_response():
    """Test parsing complex Memories.ai response with all fields."""
    print("\n=== Testing Parse Complex Response ===")

    manager = CloudAnalysisManager(Config(), None, None, None)

    complex_json = """{
  "time_segmentation": [
    {
      "start_time": 0.0,
      "end_time": 300.0,
      "label": "Focus",
      "task_hypothesis": "Implementing authentication module",
      "confidence": 0.88
    },
    {
      "start_time": 300.0,
      "end_time": 320.0,
      "label": "Break",
      "task_hypothesis": "Getting coffee",
      "confidence": 0.75
    },
    {
      "start_time": 320.0,
      "end_time": 350.0,
      "label": "Distraction",
      "task_hypothesis": "Browsing social media",
      "confidence": 0.92
    },
    {
      "start_time": 350.0,
      "end_time": 650.0,
      "label": "Focus",
      "task_hypothesis": "Writing unit tests",
      "confidence": 0.85
    }
  ],
  "app_usage": [
    {
      "app_class": "IDE",
      "total_seconds": 520.0,
      "percentage": 0.80,
      "is_productive": true
    },
    {
      "app_class": "Terminal",
      "total_seconds": 80.0,
      "percentage": 0.12,
      "is_productive": true
    },
    {
      "app_class": "Social",
      "total_seconds": 30.0,
      "percentage": 0.05,
      "is_productive": false
    },
    {
      "app_class": "Browser",
      "total_seconds": 20.0,
      "percentage": 0.03,
      "is_productive": false
    }
  ],
  "distraction_analysis": {
    "total_distraction_time": 50.0,
    "distraction_events": [
      {
        "start_time": 320.0,
        "end_time": 350.0,
        "trigger": "Social media notification",
        "evidence": "Head turned to phone, then opened Instagram on screen"
      },
      {
        "start_time": 550.0,
        "end_time": 565.0,
        "trigger": "Checking email",
        "evidence": "Opened Gmail tab, briefly scanned inbox"
      }
    ]
  },
  "insights": {
    "focus_ratio": 0.85,
    "avg_focus_bout_minutes": 25.0,
    "primary_distractor": "Social media",
    "productivity_score": 0.82,
    "recommendations": [
      "Enable Do Not Disturb on phone during focus sessions",
      "Close social media tabs before starting work",
      "Schedule email checking for breaks only",
      "Consider using Pomodoro technique (25 min focus + 5 min break)"
    ]
  }
}"""

    result = manager._parse_memories_response(complex_json)

    # Verify structure
    assert len(result["time_segmentation"]) == 4
    assert len(result["app_usage"]) == 4
    assert len(result["distraction_analysis"]["distraction_events"]) == 2
    assert len(result["insights"]["recommendations"]) == 4

    # Verify specific values
    assert result["insights"]["focus_ratio"] == 0.85
    assert result["insights"]["productivity_score"] == 0.82
    assert result["distraction_analysis"]["total_distraction_time"] == 50.0

    # Verify segment labels
    labels = [seg["label"] for seg in result["time_segmentation"]]
    assert "Focus" in labels
    assert "Break" in labels
    assert "Distraction" in labels

    # Verify app classifications
    productive_apps = [app for app in result["app_usage"] if app["is_productive"]]
    distracting_apps = [app for app in result["app_usage"] if not app["is_productive"]]

    assert len(productive_apps) == 2  # IDE, Terminal
    assert len(distracting_apps) == 2  # Social, Browser

    print("✓ Parsed complex response successfully")
    print(f"✓ Time segments: {len(result['time_segmentation'])}")
    print(f"✓ App usage entries: {len(result['app_usage'])}")
    print(f"✓ Distraction events: {len(result['distraction_analysis']['distraction_events'])}")
    print(f"✓ Recommendations: {len(result['insights']['recommendations'])}")
    print(f"✓ Focus ratio: {result['insights']['focus_ratio']}")
    print(f"✓ Productivity score: {result['insights']['productivity_score']}")
    print("✓ Complex parsing test passed")


def main():
    """Run all Memories.ai parsing tests."""
    print("\n" + "="*60)
    print("MEMORIES.AI JSON PARSING - TEST SUITE")
    print("="*60)

    try:
        test_parse_valid_json()
        test_parse_json_with_markdown()
        test_parse_invalid_json()
        test_validate_hume_results()
        test_validate_memories_results()
        test_parse_complex_memories_response()

        print("\n" + "="*60)
        print("✓ ALL PARSING TESTS PASSED!")
        print("="*60)
        print("\nMemories.ai JSON parsing and validation is working correctly.")
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
