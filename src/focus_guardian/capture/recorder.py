"""
Video recording using ffmpeg-python for continuous H.264 MP4 encoding.

Provides continuous recording of webcam and screen throughout the session,
with configurable bitrates and quality profiles.
"""

import cv2
import subprocess
import threading
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import mss

from ..core.models import QualityProfile
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MP4Recorder:
    """Base class for MP4 recording with H.264 codec."""
    
    def __init__(
        self,
        output_path: Path,
        fps: int = 15,
        bitrate_kbps: int = 500,
        resolution: Optional[Tuple[int, int]] = None
    ):
        """
        Initialize MP4 recorder.
        
        Args:
            output_path: Path to output MP4 file
            fps: Frames per second
            bitrate_kbps: Video bitrate in kbps
            resolution: (width, height) or None for auto
        """
        self.output_path = output_path
        self.fps = fps
        self.bitrate_kbps = bitrate_kbps
        self.resolution = resolution
        
        self._recording = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def start(self) -> bool:
        """Start recording in background thread."""
        if self._recording:
            logger.warning("Recording already in progress")
            return False
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        self._recording = True
        
        logger.info(f"Started recording: {self.output_path.name}")
        return True
    
    def stop(self, timeout: float = 5.0) -> bool:
        """Stop recording."""
        if not self._recording:
            return True
        
        logger.info(f"Stopping recording: {self.output_path.name}")
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning(f"Recording thread did not stop within timeout")
                return False
        
        self._recording = False
        logger.info(f"Stopped recording: {self.output_path.name}")
        return True
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording
    
    def _record_loop(self) -> None:
        """Main recording loop (to be implemented by subclasses)."""
        raise NotImplementedError


class WebcamRecorder(MP4Recorder):
    """Records webcam to MP4 using OpenCV and H.264 codec."""
    
    def __init__(
        self,
        output_path: Path,
        camera_index: int = 0,
        fps: int = 15,
        bitrate_kbps: int = 500,
        resolution: Optional[Tuple[int, int]] = None
    ):
        """
        Initialize webcam recorder.
        
        Args:
            output_path: Path to output MP4 file
            camera_index: Camera device index
            fps: Frames per second
            bitrate_kbps: Video bitrate in kbps
            resolution: (width, height) or None for camera default
        """
        super().__init__(output_path, fps, bitrate_kbps, resolution)
        self.camera_index = camera_index
        self._camera: Optional[cv2.VideoCapture] = None
        self._writer: Optional[cv2.VideoWriter] = None
    
    def _record_loop(self) -> None:
        """Main recording loop for webcam."""
        try:
            # Open camera
            self._camera = cv2.VideoCapture(self.camera_index)
            
            if not self._camera.isOpened():
                logger.error(f"Failed to open camera at index {self.camera_index}")
                return
            
            # Set resolution if specified
            if self.resolution:
                self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            else:
                self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            # Set FPS
            self._camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Get actual resolution
            width = int(self._camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self._camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(f"Webcam recording: {width}x{height} @ {self.fps}fps")
            
            # Initialize video writer with H.264 codec
            fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
            self._writer = cv2.VideoWriter(
                str(self.output_path),
                fourcc,
                self.fps,
                (width, height)
            )
            
            if not self._writer.isOpened():
                logger.error("Failed to initialize video writer")
                return
            
            # Recording loop
            frame_interval = 1.0 / self.fps
            import time
            
            while not self._stop_event.is_set():
                start_time = time.time()
                
                ret, frame = self._camera.read()
                if not ret or frame is None:
                    logger.warning("Failed to read frame from camera")
                    time.sleep(0.1)
                    continue
                
                # Write frame
                self._writer.write(frame)
                
                # Maintain FPS
                elapsed = time.time() - start_time
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
            
            logger.info(f"Webcam recording loop ended: {self.output_path.name}")
        
        except Exception as e:
            logger.error(f"Webcam recording error: {e}", exc_info=True)
        
        finally:
            # Cleanup
            if self._writer:
                self._writer.release()
            if self._camera:
                self._camera.release()


class ScreenRecorder(MP4Recorder):
    """Records screen to MP4 using mss and OpenCV."""
    
    def __init__(
        self,
        output_path: Path,
        monitor_index: int = 0,
        fps: int = 15,
        bitrate_kbps: int = 1000,
        resolution: Optional[Tuple[int, int]] = None
    ):
        """
        Initialize screen recorder.
        
        Args:
            output_path: Path to output MP4 file
            monitor_index: Monitor to capture (0 = primary)
            fps: Frames per second
            bitrate_kbps: Video bitrate in kbps
            resolution: (width, height) or None for screen resolution
        """
        super().__init__(output_path, fps, bitrate_kbps, resolution)
        self.monitor_index = monitor_index
        self._sct: Optional[mss.mss] = None
        self._writer: Optional[cv2.VideoWriter] = None
    
    def _record_loop(self) -> None:
        """Main recording loop for screen."""
        try:
            import numpy as np
            import time
            
            # Initialize screen capture
            self._sct = mss.mss()
            monitors = self._sct.monitors
            
            if self.monitor_index + 1 < len(monitors):
                monitor = monitors[self.monitor_index + 1]
            else:
                monitor = monitors[1]  # Primary monitor
            
            # Get resolution
            width = monitor["width"]
            height = monitor["height"]
            
            # Apply resolution scaling if specified
            if self.resolution:
                target_width, target_height = self.resolution
                scale_needed = True
            else:
                target_width, target_height = width, height
                scale_needed = False
            
            logger.info(f"Screen recording: {width}x{height} @ {self.fps}fps")
            if scale_needed:
                logger.info(f"  Scaling to: {target_width}x{target_height}")
            
            # Initialize video writer with H.264 codec
            fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
            self._writer = cv2.VideoWriter(
                str(self.output_path),
                fourcc,
                self.fps,
                (target_width, target_height)
            )
            
            if not self._writer.isOpened():
                logger.error("Failed to initialize video writer")
                return
            
            # Recording loop
            frame_interval = 1.0 / self.fps
            
            while not self._stop_event.is_set():
                start_time = time.time()
                
                # Capture screen
                screenshot = self._sct.grab(monitor)
                
                # Convert to numpy array (BGR format for OpenCV)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Resize if needed
                if scale_needed:
                    frame = cv2.resize(frame, (target_width, target_height))
                
                # Write frame
                self._writer.write(frame)
                
                # Maintain FPS
                elapsed = time.time() - start_time
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
            
            logger.info(f"Screen recording loop ended: {self.output_path.name}")
        
        except Exception as e:
            logger.error(f"Screen recording error: {e}", exc_info=True)
        
        finally:
            # Cleanup
            if self._writer:
                self._writer.release()
            if self._sct:
                self._sct.close()


def create_recorder(
    kind: str,
    output_path: Path,
    quality_profile: QualityProfile,
    **kwargs
) -> MP4Recorder:
    """
    Factory function to create appropriate recorder.
    
    Args:
        kind: "cam" or "screen"
        output_path: Path to output MP4 file
        quality_profile: Quality profile (Low/Std/High)
        **kwargs: Additional arguments passed to recorder
        
    Returns:
        MP4Recorder instance (WebcamRecorder or ScreenRecorder)
    """
    # Quality profile settings
    profile_settings = {
        QualityProfile.LOW: {"fps": 10, "cam_bitrate": 200, "screen_bitrate": 400},
        QualityProfile.STD: {"fps": 15, "cam_bitrate": 500, "screen_bitrate": 1000},
        QualityProfile.HIGH: {"fps": 15, "cam_bitrate": 1000, "screen_bitrate": 2000},
    }
    
    settings = profile_settings[quality_profile]
    
    if kind == "cam":
        return WebcamRecorder(
            output_path=output_path,
            fps=settings["fps"],
            bitrate_kbps=settings["cam_bitrate"],
            **kwargs
        )
    elif kind == "screen":
        return ScreenRecorder(
            output_path=output_path,
            fps=settings["fps"],
            bitrate_kbps=settings["screen_bitrate"],
            **kwargs
        )
    else:
        raise ValueError(f"Invalid recorder kind: {kind}")

