"""
Test camera selection consistency between preview, snapshots, and recording.

This test verifies that the camera selected in Settings UI is used consistently
across all three capture mechanisms:
1. Live preview (UI)
2. Snapshot capture (scheduler)
3. Video recording (recorder)

Critical bug fix: Previously, video recorder would auto-detect camera even when
user selected a specific camera index, causing preview and recording to use
different cameras.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from focus_guardian.capture.screen_capture import WebcamCapture
from focus_guardian.capture.recorder import create_recorder
from focus_guardian.core.models import QualityProfile


class TestCameraSelectionConsistency:
    """Test that camera selection is consistent across all components."""

    def test_webcam_capture_respects_user_selection(self):
        """WebcamCapture should use exact camera_index when specified (not auto-detect)."""

        with patch('cv2.VideoCapture') as mock_capture:
            mock_camera = MagicMock()
            mock_camera.isOpened.return_value = True
            mock_camera.get.return_value = 1280  # Width
            mock_capture.return_value = mock_camera

            # User selects camera index 0
            capture = WebcamCapture(camera_index=0, prefer_builtin=False)

            # Should use index 0 exactly (NOT auto-detect to different camera)
            assert capture.camera_index == 0
            mock_capture.assert_called_once_with(0)

    def test_webcam_capture_auto_detect_when_minus_one(self):
        """WebcamCapture should auto-detect when camera_index is -1."""

        with patch('cv2.VideoCapture') as mock_capture:
            mock_camera = MagicMock()
            mock_camera.isOpened.return_value = True
            mock_camera.get.return_value = 1280
            mock_capture.return_value = mock_camera

            with patch.object(WebcamCapture, '_find_builtin_camera', return_value=2):
                # Auto-detect mode
                capture = WebcamCapture(camera_index=-1, prefer_builtin=True)

                # Should auto-detect to index 2
                assert capture.camera_index == 2
                mock_capture.assert_called_once_with(2)

    def test_recorder_uses_specified_camera_index(self):
        """Video recorder should use the camera_index passed to it."""

        output_path = Path("/tmp/test_cam.mp4")

        # Create recorder with camera_index=1
        recorder = create_recorder(
            kind="cam",
            output_path=output_path,
            quality_profile=QualityProfile.STD,
            camera_index=1
        )

        # Should store camera_index=1
        assert recorder.camera_index == 1

    def test_recorder_defaults_to_zero_if_not_specified(self):
        """Video recorder should default to camera 0 if no camera_index provided."""

        output_path = Path("/tmp/test_cam.mp4")

        # Create recorder without camera_index
        recorder = create_recorder(
            kind="cam",
            output_path=output_path,
            quality_profile=QualityProfile.STD
        )

        # Should default to 0
        assert recorder.camera_index == 0


class TestCameraIndexFlow:
    """Test the complete flow from config → session_manager → components."""

    def test_config_camera_index_flows_to_all_components(self):
        """Camera index from config should reach both recorder and scheduler."""
        from focus_guardian.core.config import Config
        from focus_guardian.session.session_manager import SessionManager
        from focus_guardian.core.database import Database
        from queue import Queue

        # Mock config to return camera_index=1
        config = Mock(spec=Config)
        config.get_camera_index.return_value = 1
        config.get_snapshot_interval_sec.return_value = 60
        config.get_config_value.return_value = 3
        config.get_openai_api_key.return_value = "test-key"
        config.get_max_parallel_uploads.return_value = 3

        # Mock database
        database = Mock(spec=Database)
        database.get_active_session.return_value = None

        ui_queue = Queue()

        with patch('focus_guardian.session.session_manager.create_recorder') as mock_create_recorder, \
             patch('focus_guardian.session.session_manager.SnapshotScheduler') as mock_scheduler, \
             patch('focus_guardian.session.session_manager.OpenAIVisionClient'), \
             patch('focus_guardian.session.session_manager.SnapshotUploader'), \
             patch('focus_guardian.session.session_manager.FusionEngine'), \
             patch('focus_guardian.session.session_manager.DistractionDetector'):

            session_manager = SessionManager(config, database, ui_queue)

            # Start a session
            try:
                session_manager.start_session("Test task", QualityProfile.STD, screen_enabled=False)
            except Exception:
                pass  # Expected to fail due to mocking, but we can still check calls

            # Verify camera_index=1 was passed to BOTH recorder and scheduler
            # Recorder call
            recorder_calls = mock_create_recorder.call_args_list
            cam_recorder_call = [call for call in recorder_calls if call[1].get('kind') == 'cam'][0]
            assert cam_recorder_call[1]['camera_index'] == 1, \
                "Recorder should receive camera_index=1 from config"

            # Scheduler call
            scheduler_call = mock_scheduler.call_args
            assert scheduler_call[1]['camera_index'] == 1, \
                "Scheduler should receive camera_index=1 from config"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
