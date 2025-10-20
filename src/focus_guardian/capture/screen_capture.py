"""
Screen snapshot capture using mss library.

Provides fast, cross-platform screen capture for snapshot analysis.
mss is ~3x faster than PIL/Pillow for screenshots.
"""

import mss
import mss.tools
from pathlib import Path
from PIL import Image
from typing import Optional, Tuple
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ScreenCapture:
    """Captures screen snapshots using mss."""
    
    def __init__(self, monitor_index: int = 0, jpeg_quality: int = 85):
        """
        Initialize screen capture.
        
        Args:
            monitor_index: Monitor to capture (0 = primary, -1 = all monitors)
            jpeg_quality: JPEG compression quality (0-100, 85 recommended)
        """
        self.monitor_index = monitor_index
        self.jpeg_quality = jpeg_quality
        self._sct = mss.mss()
        
        # Get monitor info
        monitors = self._sct.monitors
        if monitor_index == -1:
            self.monitor = monitors[0]  # All monitors combined
            logger.info("Screen capture initialized for all monitors")
        elif 0 <= monitor_index + 1 < len(monitors):  # Fixed: check bounds after +1 offset
            self.monitor = monitors[monitor_index + 1]  # +1 because monitors[0] is "all monitors"
            logger.info(f"Screen capture initialized for monitor {monitor_index}")
        else:
            self.monitor = monitors[1]  # Default to primary monitor
            logger.warning(f"Invalid monitor index {monitor_index}, using primary monitor")
        
        logger.debug(f"Monitor dimensions: {self.monitor}")
    
    def capture_to_file(self, output_path: Path) -> Tuple[bool, Optional[int]]:
        """
        Capture screen and save as JPEG.
        
        Args:
            output_path: Path to save JPEG file
            
        Returns:
            Tuple of (success, file_size_bytes)
        """
        try:
            # Capture screenshot
            screenshot = self._sct.grab(self.monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Save as JPEG with specified quality
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "JPEG", quality=self.jpeg_quality, optimize=True)
            
            # Get file size
            file_size = output_path.stat().st_size
            
            logger.debug(f"Captured screen snapshot: {output_path.name} ({file_size} bytes)")
            return True, file_size
        
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return False, None
    
    def capture_to_bytes(self) -> Optional[bytes]:
        """
        Capture screen and return as JPEG bytes.
        
        Returns:
            JPEG bytes or None if capture failed
        """
        try:
            import io
            
            # Capture screenshot
            screenshot = self._sct.grab(self.monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Convert to JPEG bytes
            buffer = io.BytesIO()
            img.save(buffer, "JPEG", quality=self.jpeg_quality, optimize=True)
            return buffer.getvalue()
        
        except Exception as e:
            logger.error(f"Failed to capture screen to bytes: {e}")
            return None
    
    def get_screen_resolution(self) -> Tuple[int, int]:
        """Get current screen resolution (width, height)."""
        return (self.monitor["width"], self.monitor["height"])
    
    def close(self) -> None:
        """Close screen capture resources."""
        if self._sct:
            self._sct.close()
            logger.debug("Screen capture closed")


class WebcamCapture:
    """Captures webcam snapshots using OpenCV."""

    def __init__(self, camera_index: int = 0, jpeg_quality: int = 85, prefer_builtin: bool = True):
        """
        Initialize webcam capture.

        Args:
            camera_index: Camera device index (-1 = auto-detect, 0+ = specific camera)
            jpeg_quality: JPEG compression quality (0-100, 85 recommended)
            prefer_builtin: ONLY used when camera_index == -1 (auto-detect mode)
        """
        import cv2

        self.jpeg_quality = jpeg_quality
        self.cv2 = cv2

        # CRITICAL: Only auto-detect if camera_index is -1
        # If user selected a specific camera (index >= 0), use it exactly
        if camera_index == -1:
            if prefer_builtin:
                camera_index = self._find_builtin_camera()
            else:
                camera_index = 0  # Default to first camera
            logger.info(f"Auto-detected camera index: {camera_index}")
        else:
            logger.info(f"Using user-selected camera index: {camera_index}")

        self.camera_index = camera_index

        # Open camera
        self._camera = cv2.VideoCapture(camera_index)

        if not self._camera.isOpened():
            raise RuntimeError(f"Failed to open camera at index {camera_index}")

        # Set camera properties for better quality
        self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self._camera.set(cv2.CAP_PROP_FPS, 30)

        # Get actual resolution and camera name
        width = int(self._camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logger.info(f"Webcam capture initialized: {width}x{height} at index {camera_index}")

    @staticmethod
    def _enumerate_cameras_opencv() -> list[dict]:
        """
        Enumerate cameras using OpenCV (activates cameras briefly).

        IMPORTANT: Cannot reliably map camera names to OpenCV indices without device-specific APIs.
        Returns generic "Camera {index} - {resolution}" names. Users must use preview to identify.

        Returns:
            List of dicts with 'index' and 'name' keys
        """
        import cv2
        import sys

        cameras = []

        # Get camera names from AVFoundation (for reference)
        av_camera_names = []
        if sys.platform == 'darwin':
            av_cameras = WebcamCapture._enumerate_cameras_avfoundation()
            if av_cameras:
                av_camera_names = [cam['name'] for cam in av_cameras]
                logger.info(f"AVFoundation cameras: {', '.join(av_camera_names)}")

        # Test each OpenCV index
        for idx in range(5):  # Check first 5 camera devices
            try:
                cap = cv2.VideoCapture(idx)
                if not cap.isOpened():
                    continue

                # Read a test frame to verify it works
                ret, frame = cap.read()
                cap.release()

                if not ret or frame is None:
                    continue

                # Get frame properties
                h, w = frame.shape[:2]

                # Use generic name with resolution
                camera_name = f"Camera {idx} ({w}x{h})"
                logger.info(f"OpenCV[{idx}]: {w}x{h}")

                cameras.append({
                    "index": idx,
                    "name": camera_name
                })

            except Exception as e:
                logger.debug(f"Camera index {idx} not available: {e}")
                continue

        # EMPIRICAL FINDING: On macOS, the HIGHEST working camera index is usually the built-in FaceTime camera
        # Reverse the list so built-in camera appears first in UI
        if sys.platform == 'darwin' and cameras:
            logger.info(f"Reversing camera order (empirical: highest index = built-in camera)")
            cameras.reverse()
            camera_names = [cam['name'] for cam in cameras]
            logger.info(f"Reordered cameras: {camera_names}")

        return cameras

    @staticmethod
    def enumerate_cameras() -> list[dict]:
        """
        Enumerate all available cameras.

        NOTE: On macOS, cameras will be briefly activated to accurately map names to indices.
        This is unavoidable because system_profiler order doesn't match OpenCV index order.

        Returns:
            List of dicts with 'index' and 'name' keys
            Example: [{"index": 0, "name": "FaceTime HD Camera"}, {"index": 1, "name": "Continuity Camera"}]
        """
        import sys

        # Always use OpenCV enumeration - it's the only reliable way to map names to indices
        logger.info("Enumerating cameras (will activate briefly to identify them)...")
        return WebcamCapture._enumerate_cameras_opencv()

    @staticmethod
    def _enumerate_cameras_avfoundation() -> list[dict]:
        """
        Enumerate cameras using AVFoundation (macOS only) WITHOUT activating them.

        This method uses AVCaptureDevice.DiscoverySession which queries available
        devices without opening or starting capture sessions.

        Returns:
            List of dicts with 'index', 'name', 'unique_id' keys
        """
        try:
            import AVFoundation
            import objc

            # Create discovery session for video devices
            # This discovers devices WITHOUT activating them
            device_types = [
                AVFoundation.AVCaptureDeviceTypeBuiltInWideAngleCamera,
                AVFoundation.AVCaptureDeviceTypeExternalUnknown,
            ]

            # Add Continuity Camera type if available (macOS 13+)
            if hasattr(AVFoundation, 'AVCaptureDeviceTypeContinuityCamera'):
                device_types.append(AVFoundation.AVCaptureDeviceTypeContinuityCamera)

            discovery_session = AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(
                device_types,
                AVFoundation.AVMediaTypeVideo,
                AVFoundation.AVCaptureDevicePositionUnspecified
            )

            cameras = []
            for device in discovery_session.devices():
                camera_info = {
                    'name': str(device.localizedName()),
                    'unique_id': str(device.uniqueID()),
                    'model_id': str(device.modelID()) if hasattr(device, 'modelID') else None,
                }
                cameras.append(camera_info)
                logger.debug(f"AVFoundation found camera: {camera_info['name']} (ID: {camera_info['unique_id']})")

            return cameras

        except ImportError:
            logger.debug("AVFoundation not available - falling back to OpenCV enumeration")
            return []
        except Exception as e:
            logger.debug(f"AVFoundation enumeration failed: {e}")
            return []

    @staticmethod
    def _get_macos_camera_names() -> list[str]:
        """
        Get camera names from macOS system_profiler in the order OpenCV sees them.

        Returns:
            List of camera names in OpenCV enumeration order
        """
        import subprocess

        try:
            # Use system_profiler to get actual camera names
            result = subprocess.run(
                ['system_profiler', 'SPCameraDataType'],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                # Parse camera names from output
                # Format: "    CameraName:\n      Model ID: ...\n"
                cameras_found = []
                lines = result.stdout.split('\n')

                for i, line in enumerate(lines):
                    # Skip the main "Camera:" line
                    if line.strip() == "Camera:":
                        continue

                    # Look for camera names (indented lines ending with :)
                    if line.startswith('    ') and line.strip().endswith(':'):
                        camera_name = line.strip().rstrip(':')

                        # Skip sub-fields (Model ID, Unique ID)
                        if camera_name not in ['Model ID', 'Unique ID']:
                            cameras_found.append(camera_name)

                logger.debug(f"system_profiler found cameras: {cameras_found}")
                return cameras_found

        except Exception as e:
            logger.debug(f"Could not get camera names from system_profiler: {e}")

        # Fallback: empty list
        return []

    @staticmethod
    def _get_camera_name(index: int, cap=None) -> str:
        """
        Get human-readable camera name.

        Args:
            index: Camera index
            cap: Optional open VideoCapture object

        Returns:
            Camera name (falls back to "Camera {index}")
        """
        import sys

        # Try to get actual device name from system
        if sys.platform == 'darwin':
            camera_names = WebcamCapture._get_macos_camera_names()
            if index < len(camera_names):
                return camera_names[index]

            # Fallback if system query failed
            return f"Camera {index}"

        # On other platforms, use generic names
        return f"Camera {index}"
    
    def _find_builtin_camera(self) -> int:
        """
        Find a working webcam, preferring built-in over Continuity Camera.

        Uses the first working camera index from enumeration.

        Returns:
            Camera index for working webcam
        """
        import cv2

        # EMPIRICAL FINDING: On macOS, the HIGHEST working index is usually the built-in FaceTime camera
        # Find all working cameras and prefer the highest index
        import sys

        working_cameras = []
        max_test_index = 5  # Test up to index 5

        for idx in range(max_test_index):
            try:
                cap = cv2.VideoCapture(idx)
                if cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()
                    if ret and frame is not None:
                        working_cameras.append(idx)
                        logger.debug(f"Found working camera at index {idx}")
            except:
                continue

        if not working_cameras:
            logger.warning("No working cameras found, defaulting to index 0")
            return 0

        # On macOS, prefer the HIGHEST index (empirically the built-in camera)
        # On other platforms, prefer the LOWEST index
        if sys.platform == 'darwin':
            selected = max(working_cameras)
            logger.info(f"Auto-detect selected camera at index {selected} (highest of {working_cameras})")
        else:
            selected = min(working_cameras)
            logger.info(f"Auto-detect selected camera at index {selected} (lowest of {working_cameras})")

        return selected
    
    def capture_to_file(self, output_path: Path) -> Tuple[bool, Optional[int]]:
        """
        Capture frame from webcam and save as JPEG.
        
        Args:
            output_path: Path to save JPEG file
            
        Returns:
            Tuple of (success, file_size_bytes)
        """
        try:
            # Read frame
            ret, frame = self._camera.read()
            
            if not ret or frame is None:
                logger.error("Failed to read frame from camera")
                return False, None
            
            # Save as JPEG
            output_path.parent.mkdir(parents=True, exist_ok=True)
            encode_params = [self.cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
            self.cv2.imwrite(str(output_path), frame, encode_params)
            
            # Get file size
            file_size = output_path.stat().st_size
            
            logger.debug(f"Captured webcam snapshot: {output_path.name} ({file_size} bytes)")
            return True, file_size
        
        except Exception as e:
            logger.error(f"Failed to capture webcam: {e}")
            return False, None
    
    def is_opened(self) -> bool:
        """Check if camera is opened."""
        return self._camera.isOpened()
    
    def release(self) -> None:
        """Release camera resources."""
        if self._camera:
            self._camera.release()
            logger.debug("Webcam capture released")
    
    def close(self) -> None:
        """Alias for release()."""
        self.release()

