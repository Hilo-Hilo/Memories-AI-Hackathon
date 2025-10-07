#!/usr/bin/env python3
"""
Live Webcam Expression Measurement using Hume AI
Captures frames at 1Hz and analyzes facial expressions in real-time
"""

import os
import time
import cv2
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from hume import HumeClient
from hume.expression_measurement.batch.types import InferenceBaseRequest, Models, Face
import subprocess
import sys
import warnings

# Suppress OpenCV warnings
os.environ['OPENCV_LOG_LEVEL'] = 'SILENT'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
warnings.filterwarnings('ignore')

# Redirect stderr to suppress OpenCV errors temporarily
import contextlib

@contextlib.contextmanager
def suppress_opencv_errors():
    """Context manager to suppress OpenCV error messages"""
    stderr_backup = sys.stderr
    try:
        sys.stderr = open(os.devnull, 'w')
        yield
    finally:
        sys.stderr.close()
        sys.stderr = stderr_backup

# Load environment variables
load_dotenv()

API_KEY = os.getenv('HUME_API_KEY')
if not API_KEY:
    raise ValueError("HUME_API_KEY not found in .env file")

# Initialize Hume client
client = HumeClient(api_key=API_KEY)

def get_camera_name_for_index(index, cap):
    """Get the actual camera name for a specific OpenCV index"""
    try:
        # Get camera description using OpenCV properties
        # Try to get the device description
        camera_name = None

        # For macOS, use AVFoundation to list devices
        try:
            # Use ffmpeg or system_profiler to map devices
            result = subprocess.run(
                ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '""'],
                capture_output=True,
                text=True,
                stderr=subprocess.STDOUT,
                timeout=3
            )

            # Parse ffmpeg output to find device at index
            lines = result.stdout.split('\n')
            device_count = 0
            for line in lines:
                if 'AVFoundation video devices:' in line:
                    continue
                if '[AVFoundation' in line and '] [' in line:
                    # Extract device name
                    parts = line.split('] [')
                    if len(parts) >= 2:
                        if device_count == index:
                            camera_name = parts[1].rstrip(']').strip()
                            break
                        device_count += 1
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback: use backend name
        if not camera_name:
            backend = cap.getBackendName()
            camera_name = f"Camera {index} ({backend})"

        return camera_name
    except Exception as e:
        return f"Camera {index}"

def list_available_cameras(max_cameras=10):
    """List all available camera devices with their names"""
    available_cameras = []

    print("Detecting cameras...\n")

    consecutive_failures = 0
    max_consecutive_failures = 3  # Stop after 3 consecutive failed attempts

    # Scan for all cameras, but stop early if we hit too many failures
    for i in range(max_cameras):
        with suppress_opencv_errors():
            cap = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)

            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    name = get_camera_name_for_index(i, cap)
                    available_cameras.append({'id': i, 'name': name})
                    print(f"  Found: [{i}] {name}")
                    consecutive_failures = 0  # Reset failure counter
                else:
                    consecutive_failures += 1
                cap.release()
            else:
                consecutive_failures += 1

            # Stop scanning if we've had too many consecutive failures
            if consecutive_failures >= max_consecutive_failures:
                break

    print()
    return available_cameras

def select_camera():
    """Prompt user to select a camera"""
    print("="*70)
    print("  CAMERA SELECTION")
    print("="*70)
    print()

    cameras = list_available_cameras()

    if not cameras:
        print("No cameras found!")
        return None, None

    print("-"*70)

    camera_ids = [cam['id'] for cam in cameras]

    while True:
        try:
            default_id = camera_ids[0]
            choice = input(f"\nSelect camera [{min(camera_ids)}-{max(camera_ids)}] (or press Enter for {default_id}): ").strip()

            if choice == "":
                selected_cam = cameras[0]
                return selected_cam['id'], selected_cam['name']

            camera_id = int(choice)
            if camera_id in camera_ids:
                selected_cam = next(cam for cam in cameras if cam['id'] == camera_id)
                return selected_cam['id'], selected_cam['name']
            else:
                print(f"Invalid choice. Please select from: {camera_ids}")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            return None, None

def print_header(camera_id, camera_name):
    """Print script header"""
    print("\n" + "="*70)
    print("  LIVE WEBCAM EXPRESSION MEASUREMENT - HUME AI")
    print("="*70)
    print(f"Camera: {camera_name}")
    print(f"Capture Rate: 1 frame per second")
    print(f"Press Ctrl+C to exit")
    print("="*70 + "\n")

def capture_frame(cap):
    """Capture a single frame from webcam"""
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame from webcam")
        return None
    return frame

def save_temp_image(frame):
    """Save frame to temporary file"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    cv2.imwrite(temp_file.name, frame)
    return temp_file.name

def analyze_expression(image_path):
    """Send image to Hume API for expression analysis"""
    try:
        # Start batch job with face model
        with open(image_path, 'rb') as f:
            job_id = client.expression_measurement.batch.start_inference_job_from_local_file(
                file=[f],
                json=InferenceBaseRequest(
                    models=Models(
                        face=Face()
                    )
                )
            )

        # Poll for completion (with timeout)
        max_wait = 30  # 30 seconds timeout
        start_time = time.time()

        while time.time() - start_time < max_wait:
            job_details = client.expression_measurement.batch.get_job_details(id=job_id)
            status = job_details.state.status

            if status == "COMPLETED":
                # Get predictions
                predictions = client.expression_measurement.batch.get_job_predictions(id=job_id)
                return predictions
            elif status == "FAILED":
                print(f"  [ERROR] Job failed")
                return None

            time.sleep(1)

        print(f"  [TIMEOUT] Analysis took too long")
        return None

    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return None

def display_results(predictions, frame_num):
    """Display emotion analysis results"""
    if not predictions:
        return

    timestamp = datetime.now().strftime("%H:%M:%S")

    try:
        for source_prediction in predictions:
            for file_prediction in source_prediction.results.predictions:
                # Check if face predictions exist
                if hasattr(file_prediction.models, 'face') and file_prediction.models.face:
                    face_predictions = file_prediction.models.face.grouped_predictions

                    if not face_predictions or len(face_predictions) == 0:
                        print(f"[{timestamp}] Frame #{frame_num}: No faces detected")
                        return

                    # Process first face detected
                    for group_idx, group in enumerate(face_predictions):
                        if group.predictions and len(group.predictions) > 0:
                            pred = group.predictions[0]

                            print(f"\n[{timestamp}] Frame #{frame_num} - Face #{group_idx + 1}")
                            print("-" * 70)

                            # Sort emotions by score
                            sorted_emotions = sorted(
                                pred.emotions,
                                key=lambda x: x.score,
                                reverse=True
                            )

                            # Display top 5 emotions
                            print("Top 5 Emotions:")
                            for i, emotion in enumerate(sorted_emotions[:5], 1):
                                bar_length = int(emotion.score * 50)
                                bar = "█" * bar_length + "░" * (50 - bar_length)
                                print(f"  {i}. {emotion.name:15s} {bar} {emotion.score:.3f}")

                            return

                    print(f"[{timestamp}] Frame #{frame_num}: Face detected but no predictions")
                else:
                    print(f"[{timestamp}] Frame #{frame_num}: No face model results")

    except Exception as e:
        print(f"[{timestamp}] Frame #{frame_num}: Error processing results - {str(e)}")

def main():
    """Main loop for live expression measurement"""
    # Select camera
    camera_id, camera_name = select_camera()

    if camera_id is None:
        return

    print_header(camera_id, camera_name)

    # Initialize webcam with AVFoundation backend to avoid deprecation warnings
    print("Initializing camera...")
    cap = cv2.VideoCapture(camera_id, cv2.CAP_AVFOUNDATION)

    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_id}")
        return

    print(f"{camera_name} initialized successfully!\n")

    frame_num = 0

    try:
        while True:
            frame_num += 1

            # Capture frame
            frame = capture_frame(cap)
            if frame is None:
                continue

            # Save to temporary file
            temp_path = save_temp_image(frame)

            print(f"\nProcessing frame #{frame_num}...")

            # Analyze expression
            predictions = analyze_expression(temp_path)

            # Display results
            display_results(predictions, frame_num)

            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass

            # Wait for 1 second (1Hz)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("  Shutting down gracefully...")
        print(f"  Total frames processed: {frame_num}")
        print("="*70)

    finally:
        # Release webcam
        cap.release()
        print("\nWebcam released. Goodbye!")

if __name__ == "__main__":
    main()
