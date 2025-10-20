"""
Hume AI Expression API client for post-session emotion analysis.

Provides emotion timeline analysis from recorded webcam video,
detecting frustration, boredom, stress, and other emotional states
that correlate with distraction patterns.
"""

import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

try:
    from hume import HumeClient as HumeSDKClient
    from hume.core import ApiError
    HUME_SDK_AVAILABLE = True
except ImportError:
    HUME_SDK_AVAILABLE = False
    HumeSDKClient = None
    ApiError = Exception

from ..utils.logger import get_logger

logger = get_logger(__name__)


class HumeExpressionClient:
    """Client for Hume AI Expression API (post-processing only)."""

    def __init__(self, api_key: str):
        """
        Initialize Hume AI client.

        Args:
            api_key: Hume AI API key
        """
        self.api_key = api_key

        # Initialize client if SDK available
        if not HUME_SDK_AVAILABLE:
            logger.error("Hume SDK not installed. Install with: pip install hume")
            self.client = None
            return

        try:
            self.client = HumeSDKClient(api_key=api_key)
            logger.info("Hume AI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Hume SDK: {e}")
            self.client = None

    def analyze_video(
        self,
        video_path: Path,
        include_face: bool = True,
        include_prosody: bool = False,
        include_language: bool = False
    ) -> Optional[str]:
        """
        Submit video for expression analysis using Hume AI Batch API.

        Args:
            video_path: Path to video file (cam.mp4)
            include_face: Include facial expression analysis
            include_prosody: Include voice prosody (audio) analysis
            include_language: Include emotional language analysis

        Returns:
            job_id for polling, or None if failed

        Raises:
            Exception if submission fails
        """
        if not self.client:
            logger.error("Hume AI client not initialized")
            return None

        logger.info(f"Submitting video for Hume AI analysis: {video_path}")

        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        try:
            # Configure models to run
            models_config = {}
            if include_face:
                models_config["face"] = {}
            if include_prosody:
                models_config["prosody"] = {}
            if include_language:
                models_config["language"] = {}

            # Upload file using Hume SDK's local file upload method
            logger.info("Uploading video file to Hume AI...")

            with open(video_path, 'rb') as video_file:
                # Use start_inference_job_from_local_file for direct upload
                job_id = self.client.expression_measurement.batch.start_inference_job_from_local_file(
                    file=[video_file],
                    json={
                        "models": models_config
                    }
                )

            logger.info(f"Hume AI job submitted successfully: {job_id}")
            return job_id

        except ApiError as e:
            logger.error(f"Hume API error submitting job: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to submit Hume AI job: {e}", exc_info=True)
            raise

    def poll_job(self, job_id: str, timeout: int = 600) -> str:
        """
        Poll job status until completion.

        Args:
            job_id: Job ID from analyze_video
            timeout: Maximum time to wait in seconds

        Returns:
            Job status ("COMPLETED", "FAILED", "QUEUED", "IN_PROGRESS")
        """
        if not self.client:
            logger.error("Hume AI client not initialized")
            return "FAILED"

        logger.info(f"Polling Hume AI job: {job_id}")

        start_time = time.time()
        poll_interval = 5  # Start with 5 second intervals

        while (time.time() - start_time) < timeout:
            try:
                # Get job details from Hume API
                job_details = self.client.expression_measurement.batch.get_job_details(id=job_id)
                status = job_details.state.status

                logger.info(f"Hume AI job {job_id}: {status}")

                if status in ["COMPLETED", "FAILED"]:
                    return status

                # Exponential backoff
                time.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.5, 30)  # Max 30s

            except ApiError as e:
                logger.error(f"API error polling Hume AI job: {e}")
                time.sleep(poll_interval)
            except Exception as e:
                logger.error(f"Error polling Hume AI job: {e}")
                time.sleep(poll_interval)

        logger.warning(f"Hume AI job {job_id} timed out after {timeout}s")
        return "TIMEOUT"

    def fetch_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch emotion analysis results.

        Args:
            job_id: Job ID from analyze_video

        Returns:
            Emotion timeline data or None if failed
        """
        if not self.client:
            logger.error("Hume AI client not initialized")
            return None

        logger.info(f"Fetching Hume AI results for job: {job_id}")

        try:
            # Fetch predictions from Hume API
            predictions = self.client.expression_measurement.batch.get_job_predictions(id=job_id)

            # Parse predictions into our format
            results = self._parse_predictions(predictions, job_id)

            logger.info(f"Fetched Hume AI results: {len(results.get('timeline', []))} frames")
            return results

        except ApiError as e:
            logger.error(f"API error fetching Hume AI results: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch Hume AI results: {e}", exc_info=True)
            return None

    def _parse_predictions(self, predictions, job_id: str) -> Dict[str, Any]:
        """
        Parse Hume API predictions into our timeline format.

        Args:
            predictions: Raw predictions from Hume API
            job_id: Job ID

        Returns:
            Structured emotion timeline
        """
        timeline = []
        emotion_sums = {}
        frame_count = 0

        # Process each source prediction
        for source_prediction in predictions:
            # Process each file prediction
            for file_prediction in source_prediction.results.predictions:
                # Process face predictions
                if hasattr(file_prediction.models, 'face') and file_prediction.models.face:
                    for group in file_prediction.models.face.grouped_predictions:
                        for pred in group.predictions:
                            frame_count += 1

                            # Convert frame number to timestamp (assuming 1 fps)
                            timestamp = pred.frame

                            # Extract emotions as dict
                            emotions_dict = {}
                            for emotion in pred.emotions:
                                emotions_dict[emotion.name] = emotion.score

                                # Accumulate for summary
                                if emotion.name not in emotion_sums:
                                    emotion_sums[emotion.name] = 0.0
                                emotion_sums[emotion.name] += emotion.score

                            # Add to timeline
                            timeline.append({
                                "timestamp": timestamp,
                                "frame": pred.frame,
                                "emotions": emotions_dict
                            })

        # Calculate summary statistics
        summary = {}
        if frame_count > 0:
            for emotion_name, total_score in emotion_sums.items():
                summary[f"avg_{emotion_name.lower()}"] = total_score / frame_count

        # Add key metrics
        key_emotions = ["Concentration", "Frustration", "Boredom", "Stress", "Confusion"]
        for emotion in key_emotions:
            key = f"avg_{emotion.lower()}"
            if key not in summary:
                summary[key] = 0.0

        return {
            "job_id": job_id,
            "timeline": timeline,
            "summary": summary,
            "frame_count": frame_count
        }

    def _generate_mock_results(self, job_id: str) -> Dict[str, Any]:
        """
        Generate mock emotion timeline for testing.

        This is used when Hume SDK is not available or for placeholder jobs.
        """
        return {
            "job_id": job_id,
            "timeline": [
                {
                    "timestamp": 0.0,
                    "frame": 0,
                    "emotions": {
                        "Concentration": 0.7,
                        "Frustration": 0.3,
                        "Boredom": 0.2,
                        "Stress": 0.4,
                        "Confusion": 0.25
                    }
                },
                {
                    "timestamp": 30.0,
                    "frame": 30,
                    "emotions": {
                        "Concentration": 0.5,
                        "Frustration": 0.5,
                        "Boredom": 0.3,
                        "Stress": 0.6,
                        "Confusion": 0.4
                    }
                },
                {
                    "timestamp": 60.0,
                    "frame": 60,
                    "emotions": {
                        "Concentration": 0.6,
                        "Frustration": 0.4,
                        "Boredom": 0.35,
                        "Stress": 0.5,
                        "Confusion": 0.3
                    }
                }
            ],
            "summary": {
                "avg_concentration": 0.6,
                "avg_frustration": 0.4,
                "avg_boredom": 0.28,
                "avg_stress": 0.5,
                "avg_confusion": 0.32
            },
            "frame_count": 3,
            "_mock": True
        }

    def analyze_video_sync(
        self,
        video_path: Path,
        timeout: int = 600
    ) -> Optional[Dict[str, Any]]:
        """
        Synchronously analyze video and return results.

        Convenience method that submits, polls, and fetches in one call.

        Args:
            video_path: Path to video file
            timeout: Maximum time to wait

        Returns:
            Emotion timeline data or None if failed
        """
        try:
            # Submit job
            job_id = self.analyze_video(video_path)

            if not job_id:
                logger.error("Failed to submit Hume AI job")
                return None

            # Poll until complete
            status = self.poll_job(job_id, timeout=timeout)

            if status != "COMPLETED":
                logger.error(f"Hume AI job failed or timed out: {status}")
                return None

            # Fetch results
            return self.fetch_results(job_id)

        except Exception as e:
            logger.error(f"Synchronous Hume AI analysis failed: {e}")
            return None

    def extract_emotion_summary(self, results: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract simplified emotion summary from Hume results.

        Args:
            results: Full Hume AI results

        Returns:
            Dict with key emotions (frustration, boredom, stress, concentration)
        """
        summary = results.get("summary", {})

        return {
            "frustration_mean": summary.get("avg_frustration", 0.0),
            "boredom_mean": summary.get("avg_boredom", 0.0),
            "concentration_mean": summary.get("avg_concentration", 0.0),
            "stress_mean": summary.get("avg_stress", 0.0),
            "confusion_mean": summary.get("avg_confusion", 0.0)
        }

    def correlate_with_distractions(
        self,
        emotion_timeline: List[Dict],
        distraction_events: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Correlate emotion spikes with distraction events.

        Args:
            emotion_timeline: Timeline from Hume AI results
            distraction_events: Distraction events from database

        Returns:
            List of correlations with insights
        """
        correlations = []

        # For each distraction event
        for event in distraction_events:
            event_time = event.get("started_at")
            if not event_time:
                continue

            # Find emotion data around the distraction (±5 minutes)
            window_start = event_time - 300  # 5 minutes before
            window_end = event_time + 300   # 5 minutes after

            # Get emotions in this window
            window_emotions = [
                frame for frame in emotion_timeline
                if window_start <= frame.get("timestamp", 0) <= window_end
            ]

            if not window_emotions:
                continue

            # Calculate average emotions before distraction
            pre_distraction = [
                frame for frame in window_emotions
                if frame.get("timestamp", 0) < event_time
            ]

            # Calculate emotion changes
            if pre_distraction:
                avg_emotions = {}
                for emotion_name in ["Frustration", "Boredom", "Stress", "Concentration"]:
                    scores = [
                        frame.get("emotions", {}).get(emotion_name, 0.0)
                        for frame in pre_distraction
                    ]
                    avg_emotions[emotion_name.lower()] = sum(scores) / len(scores) if scores else 0.0

                # Add correlation
                correlations.append({
                    "event_id": event.get("event_id"),
                    "event_time": event_time,
                    "pre_distraction_emotions": avg_emotions,
                    "dominant_emotion": max(avg_emotions.items(), key=lambda x: x[1])[0],
                    "insight": self._generate_insight(avg_emotions)
                })

        return correlations

    def _generate_insight(self, emotions: Dict[str, float]) -> str:
        """Generate human-readable insight from emotion data."""
        dominant = max(emotions.items(), key=lambda x: x[1])
        emotion_name, score = dominant

        if emotion_name == "frustration" and score > 0.5:
            return "High frustration detected before distraction. Consider taking a short break when frustrated."
        elif emotion_name == "boredom" and score > 0.5:
            return "Boredom preceded distraction. Try varying task types or using Pomodoro technique."
        elif emotion_name == "stress" and score > 0.5:
            return "Elevated stress before distraction. Practice stress-reduction techniques."
        elif emotions.get("concentration", 0) < 0.3:
            return "Low concentration detected. This task may be too difficult or unclear."
        else:
            return "Emotions stable before distraction. May be external trigger."

    def list_jobs(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        List all batch jobs from Hume AI.

        Queries the Hume AI API to get the actual list of stored jobs.

        Args:
            status: Filter by status (QUEUED, IN_PROGRESS, COMPLETED, FAILED)
            limit: Maximum number of jobs to return

        Returns:
            List of job dictionaries with id, status, created_timestamp_ms, etc.
            Returns None if client not initialized or query fails.
        """
        if not self.client:
            logger.error("Hume AI client not initialized")
            return None

        try:
            logger.info(f"Listing Hume AI jobs (status={status}, limit={limit})")

            # Query Hume API for job list
            jobs = self.client.expression_measurement.batch.list_jobs(
                status=status,
                limit=limit
            )

            # Convert to list of dicts for easier processing
            job_list = []
            for job in jobs:
                job_dict = {
                    "id": job.id if hasattr(job, 'id') else str(job),
                    "status": job.state.status if hasattr(job, 'state') else "UNKNOWN",
                    "created_timestamp_ms": job.state.created_timestamp_ms if hasattr(job, 'state') else None,
                    "started_timestamp_ms": job.state.started_timestamp_ms if hasattr(job, 'state') and hasattr(job.state, 'started_timestamp_ms') else None,
                    "ended_timestamp_ms": job.state.ended_timestamp_ms if hasattr(job, 'state') and hasattr(job.state, 'ended_timestamp_ms') else None,
                }
                job_list.append(job_dict)

            logger.info(f"Found {len(job_list)} Hume AI jobs")
            return job_list

        except ApiError as e:
            logger.error(f"Hume API error listing jobs: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to list Hume AI jobs: {e}", exc_info=True)
            return None
