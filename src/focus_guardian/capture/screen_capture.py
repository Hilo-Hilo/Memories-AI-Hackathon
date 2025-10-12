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
        elif 0 <= monitor_index < len(monitors):
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
            camera_index: Camera device index (0 = default camera)
            jpeg_quality: JPEG compression quality (0-100, 85 recommended)
            prefer_builtin: Try to find built-in webcam instead of Continuity Camera
        """
        import cv2
        
        self.jpeg_quality = jpeg_quality
        self.cv2 = cv2
        
        # If prefer_builtin, try to find the actual built-in webcam
        if prefer_builtin:
            camera_index = self._find_builtin_camera()
        
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
    
    def _find_builtin_camera(self) -> int:
        """
        Find a working webcam, preferring built-in over Continuity Camera.
        
        On macOS, tries to find built-in FaceTime camera, but falls back
        to any working camera if not found.
        
        Returns:
            Camera index for working webcam
        """
        import cv2
        import sys
        
        working_cameras = []
        
        # Try different camera indices
        for idx in range(5):  # Check first 5 camera devices
            try:
                cap = cv2.VideoCapture(idx)
                if cap.isOpened():
                    # Read a test frame to verify it works
                    ret, frame = cap.read()
                    cap.release()
                    
                    if ret and frame is not None:
                        working_cameras.append(idx)
                        logger.debug(f"Camera index {idx} is available")
            except Exception as e:
                logger.debug(f"Camera index {idx} not available: {e}")
                continue
        
        if not working_cameras:
            logger.error("No working cameras found!")
            return 0  # Fallback to 0, will fail gracefully later
        
        # On macOS, prefer index 1 if available (usually built-in FaceTime)
        # Otherwise use the first working camera
        if sys.platform == 'darwin' and 1 in working_cameras:
            logger.info(f"Using built-in camera at index 1")
            return 1
        else:
            camera_idx = working_cameras[0]
            logger.info(f"Using camera at index {camera_idx}")
            return camera_idx
    
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

