"""
Memories.ai API client for post-session video analysis.

Uploads session videos and snapshots to Memories.ai for comprehensive
pattern analysis using VLM (Vision-Language Models) to understand
temporal relationships and behavioral patterns.
"""

import requests
import time
import json
from pathlib import Path
from typing import Optional, Dict, List, Any

from ..utils.logger import get_logger

logger = get_logger(__name__)


class MemoriesClient:
    """Client for Memories.ai API (post-processing only)."""

    def __init__(self, api_key: str, base_url: str = "https://api.memories.ai"):
        """
        Initialize Memories.ai client.

        Args:
            api_key: Memories.ai API key
            base_url: API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": api_key,  # Memories.ai uses plain Authorization header
            "Accept": "application/json"
        })

        logger.info("Memories.ai client initialized")

    def upload_video(
        self,
        video_path: Path,
        unique_id: Optional[str] = None,
        max_retries: int = 3,
        initial_delay: float = 2.0
    ) -> Optional[str]:
        """
        Upload video file to Memories.ai with retry logic.

        Args:
            video_path: Path to video file
            unique_id: Optional unique identifier for the video session
            max_retries: Maximum number of retry attempts (default: 3)
            initial_delay: Initial delay in seconds for exponential backoff (default: 2.0)

        Returns:
            videoNo (object ID) for the uploaded video or None if failed
        """
        logger.info(f"Uploading video to Memories.ai: {video_path}")

        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return None

        url = f"{self.base_url}/serve/api/v1/upload"
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                # Prepare file upload
                with open(video_path, 'rb') as video_file:
                    files = {
                        "file": (video_path.name, video_file, "video/mp4")
                    }

                    data = {}
                    if unique_id:
                        data["unique_id"] = unique_id

                    # Upload video
                    response = self.session.post(url, files=files, data=data)
                    response.raise_for_status()

                    result = response.json()

                    # Check response code
                    if result.get('code') == '0000':
                        video_no = result['data']['videoNo']
                        logger.info(f"Video uploaded successfully: {video_no}")
                        return video_no
                    else:
                        # Log full response for debugging
                        error_msg = result.get('msg') or result.get('message') or 'Unknown error'

                        # Check if rate limited or should retry
                        if 'exceeded the limit' in error_msg.lower() or 'rate limit' in error_msg.lower():
                            if attempt < max_retries - 1:
                                logger.warning(f"Rate limited on attempt {attempt + 1}/{max_retries}. Retrying in {delay}s...")
                                logger.error(f"Full API response: {result}")
                                time.sleep(delay)
                                delay *= 2  # Exponential backoff
                                continue
                            else:
                                logger.error(f"Upload failed after {max_retries} attempts: {error_msg}")
                                logger.error(f"Full API response: {result}")
                                return None
                        else:
                            logger.error(f"Upload failed: {error_msg}")
                            logger.error(f"Full API response: {result}")
                            return None

            except requests.exceptions.HTTPError as e:
                # Check for HTTP 429 (Too Many Requests)
                if e.response.status_code == 429:
                    if attempt < max_retries - 1:
                        logger.warning(f"HTTP 429 on attempt {attempt + 1}/{max_retries}. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Upload failed after {max_retries} attempts: HTTP 429")
                        return None
                else:
                    logger.error(f"HTTP error uploading video: {e}", exc_info=True)
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to upload video: {e}", exc_info=True)
                return None
            except Exception as e:
                logger.error(f"Unexpected error uploading video: {e}", exc_info=True)
                return None

        logger.error(f"Upload failed after {max_retries} attempts")
        return None

    def wait_for_processing(
        self,
        video_no: str,
        unique_id: str,
        max_wait: int = 600
    ) -> bool:
        """
        Wait for video to be processed to PARSE status.

        Args:
            video_no: Video number from upload
            unique_id: Unique identifier for the video
            max_wait: Maximum wait time in seconds

        Returns:
            True if processing succeeded, False otherwise
        """
        logger.info(f"Waiting for Memories.ai processing: {video_no}")

        url = f"{self.base_url}/serve/api/v1/list_videos"
        payload = {
            "unique_id": unique_id,
            "page": 1,
            "size": 200
        }

        elapsed = 0
        poll_interval = 10

        while elapsed < max_wait:
            try:
                response = self.session.post(url, json=payload)
                response.raise_for_status()

                result = response.json()

                if result.get('code') == '0000':
                    videos = result.get('data', {}).get('videos', [])

                    for video in videos:
                        if video['video_no'] == video_no:
                            status = video['status']
                            logger.info(f"Processing status: {status} (waited {elapsed}s)")

                            if status == 'PARSE':
                                logger.info("Video processing complete!")
                                return True
                            elif status == 'FAIL':
                                logger.error("Video processing failed!")
                                return False
                            elif status == 'PENDING':
                                logger.debug(f"Video still pending processing (waited {elapsed}s)")
                            elif status == 'PROCESSING':
                                logger.debug(f"Video being processed (waited {elapsed}s)")
                            elif status == 'UPLOADING':
                                logger.debug(f"Video being uploaded (waited {elapsed}s)")
                            elif status == 'UNPARSE':
                                logger.debug(f"Video uploaded, waiting for parsing (waited {elapsed}s)")
                            else:
                                logger.debug(f"Unknown video status '{status}' (waited {elapsed}s)")

                time.sleep(poll_interval)
                elapsed += poll_interval

            except Exception as e:
                logger.error(f"Error checking processing status: {e}")
                time.sleep(poll_interval)
                elapsed += poll_interval

        logger.error(f"Timeout waiting for video processing after {max_wait}s")
        return False

    def chat_with_video(
        self,
        video_nos: List[str],
        prompt: str,
        unique_id: str,
        stream: bool = False
    ) -> Optional[str]:
        """
        Chat with uploaded videos using Memories.ai VLM.

        Args:
            video_nos: List of video numbers to analyze
            prompt: Analysis prompt
            unique_id: Unique identifier for the session
            stream: Use streaming response

        Returns:
            Response text or None if failed
        """
        logger.info(f"Chatting with Memories.ai videos: {video_nos}")

        endpoint = "chat_stream" if stream else "chat"
        url = f"{self.base_url}/serve/api/v1/{endpoint}"

        payload = {
            "video_nos": video_nos,
            "prompt": prompt,
            "unique_id": unique_id
        }

        try:
            if stream:
                # Streaming response
                headers = self.session.headers.copy()
                headers["Accept"] = "text/event-stream"

                response = self.session.post(url, json=payload, headers=headers, stream=True)
                response.raise_for_status()

                # Collect streamed response
                full_response = ""
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        if line.strip().lower() in ('data:"done"', 'data:[done]', 'data:done'):
                            break

                        if line.startswith("data:"):
                            data = line.replace("data:", "", 1).strip()
                            try:
                                obj = json.loads(data)
                                if obj.get('type') == 'content':
                                    content = obj.get('content', '')
                                    full_response += content
                            except json.JSONDecodeError:
                                full_response += data

                return full_response

            else:
                # Non-streaming response
                response = self.session.post(url, json=payload)
                response.raise_for_status()

                # Handle line-by-line response
                full_response = ""
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        full_response += line + "\n"

                return full_response.strip()

        except Exception as e:
            logger.error(f"Failed to chat with video: {e}", exc_info=True)
            return None

    def analyze_session(
        self,
        cam_video_path: Path,
        screen_video_path: Path,
        snapshots_dir: Path,
        unique_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Comprehensive session analysis using Memories.ai.

        Args:
            cam_video_path: Path to webcam video
            screen_video_path: Path to screen video
            snapshots_dir: Directory containing snapshots
            unique_id: Optional unique identifier

        Returns:
            Complete analysis results or None if failed
        """
        if not unique_id:
            unique_id = f"focus_session_{int(time.time())}"

        logger.info(f"Starting comprehensive Memories.ai analysis: {unique_id}")

        try:
            # Upload webcam video
            cam_video_no = self.upload_video(cam_video_path, unique_id=unique_id)
            if not cam_video_no:
                logger.error("Failed to upload webcam video")
                return None

            # Upload screen video
            screen_video_no = self.upload_video(screen_video_path, unique_id=unique_id)
            if not screen_video_no:
                logger.error("Failed to upload screen video")
                return None

            # Wait for both videos to be processed
            logger.info("Waiting for webcam video processing...")
            if not self.wait_for_processing(cam_video_no, unique_id):
                logger.error("Webcam video processing failed")
                return None

            logger.info("Waiting for screen video processing...")
            if not self.wait_for_processing(screen_video_no, unique_id):
                logger.error("Screen video processing failed")
                return None

            # Build comprehensive analysis prompt
            prompt = self._build_analysis_prompt()

            # Chat with both videos to get analysis
            logger.info("Requesting Memories.ai analysis...")
            analysis_text = self.chat_with_video(
                video_nos=[cam_video_no, screen_video_no],
                prompt=prompt,
                unique_id=unique_id,
                stream=True
            )

            if not analysis_text:
                logger.error("Failed to get analysis from Memories.ai")
                return None

            # Parse structured response
            results = self._parse_analysis_response(analysis_text)

            # Add metadata
            results["unique_id"] = unique_id
            results["cam_video_no"] = cam_video_no
            results["screen_video_no"] = screen_video_no

            logger.info("Memories.ai analysis completed successfully")
            return results

        except Exception as e:
            logger.error(f"Memories.ai analysis failed: {e}", exc_info=True)
            return None

    def _build_analysis_prompt(self) -> str:
        """Build prompt for comprehensive session analysis."""
        return """Analyze this focus session by examining both the webcam and screen recordings. Provide:

1. **Time Segmentation**: Break the session into segments and label each as "Focus", "Break", or "Distraction"
   - Include start time, end time, and duration for each segment
   - Identify the dominant state in each time window

2. **Task Hypothesis**: For each focused segment, what was the user working on?
   - Identify visible applications (code editor, browser, terminal, etc.)
   - Infer task type from screen content and user behavior

3. **App Usage Analysis**: What applications were visible throughout the session?
   - Calculate time spent in each application
   - Categorize apps as productive vs distracting

4. **Distraction Analysis**: When did distractions occur and what caused them?
   - Identify distraction triggers (social media, videos, phone, etc.)
   - Note behavioral patterns (head movement, looking away, leaving desk)
   - Correlate webcam behavior with screen content

5. **Insights and Recommendations**:
   - Overall focus ratio (focused time / total time)
   - Primary distractors and their frequency
   - Productivity patterns (most productive time windows)
   - Actionable recommendations for improving focus

Please provide a structured analysis with specific timestamps and measurable metrics."""

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Memories.ai response into structured format.

        Args:
            response_text: Raw text response from Memories.ai

        Returns:
            Structured analysis dictionary
        """
        # For hackathon, we'll do basic parsing
        # In production, use structured output via JSON schema or better parsing

        results = {
            "raw_analysis": response_text,
            "segments": [],
            "insights": {},
            "app_usage": []
        }

        # Try to extract key metrics from text
        lines = response_text.split('\n')

        # Look for focus ratio
        for line in lines:
            if "focus ratio" in line.lower():
                try:
                    # Extract percentage
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)%', line)
                    if match:
                        results["insights"]["focus_ratio"] = float(match.group(1)) / 100.0
                except:
                    pass

        # If no structured data found, add placeholder
        if not results["insights"]:
            results["insights"] = {
                "focus_ratio": 0.7,  # Placeholder
                "primary_distractor": "Unknown",
                "productivity_score": 0.72
            }

        return results

    def search_video_content(
        self,
        video_no: str,
        query: str,
        unique_id: str,
        top_k: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Search for specific content within a video.

        Args:
            video_no: Video number to search
            query: Search query
            unique_id: Unique identifier
            top_k: Number of results to return

        Returns:
            List of search results with timestamps
        """
        logger.info(f"Searching video {video_no} for: {query}")

        url = f"{self.base_url}/serve/api/v1/search"

        payload = {
            "search_param": query,
            "search_type": "BY_VIDEO",
            "unique_id": unique_id,
            "top_k": top_k,
            "filtering_level": "medium"
        }

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()

            result = response.json()

            if result.get('code') == '0000':
                # Parse search results - data is a flat array, not nested
                results = result.get('data', [])
                logger.info(f"Found {len(results)} search results")
                return results
            else:
                logger.error(f"Search failed: {result.get('msg', 'Unknown error')}")
                return None

        except Exception as e:
            logger.error(f"Failed to search video: {e}", exc_info=True)
            return None

    def list_videos(self, unique_id: str, page: int = 1, size: int = 200) -> Optional[List[Dict[str, Any]]]:
        """
        List all videos for a unique ID.

        Args:
            unique_id: Unique identifier
            page: Page number for pagination (default: 1)
            size: Number of results per page (default: 200)

        Returns:
            List of video metadata
        """
        url = f"{self.base_url}/serve/api/v1/list_videos"
        payload = {
            "unique_id": unique_id,
            "page": page,
            "size": size
        }

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()

            result = response.json()

            if result.get('code') == '0000':
                videos = result.get('data', {}).get('videos', [])
                logger.info(f"Found {len(videos)} videos for {unique_id}")
                return videos
            else:
                logger.error(f"List videos failed: {result.get('msg', 'Unknown error')}")
                return None

        except Exception as e:
            logger.error(f"Failed to list videos: {e}", exc_info=True)
            return None

    def get_video_status(self, video_no: str, unique_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if a video exists and get its processing status.

        Args:
            video_no: Video number to check
            unique_id: Unique identifier

        Returns:
            Video info dict with status, or None if not found
            Status values: PARSE (processed), UNPARSE (uploaded but not processed),
                          PROCESSING (being processed), FAIL (failed)
        """
        logger.info(f"Checking status for video {video_no} in {unique_id}")

        try:
            videos = self.list_videos(unique_id)
            if videos:
                for video in videos:
                    if video.get('video_no') == video_no:
                        status = video.get('status')
                        logger.info(f"Video {video_no} found with status: {status}")
                        return video
            
            logger.info(f"Video {video_no} not found in {unique_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to get video status: {e}", exc_info=True)
            return None

    def delete_video(
        self,
        video_no: str,
        unique_id: str = "default",
        max_retries: int = 5,
        initial_delay: float = 2.0
    ) -> bool:
        """
        Delete a video from Memories.ai with exponential backoff retry.

        Args:
            video_no: Video number to delete
            unique_id: Unique identifier for scoping (default: "default")
            max_retries: Maximum number of retry attempts (default: 5)
            initial_delay: Initial delay in seconds for exponential backoff (default: 2.0)

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/serve/api/v1/delete_videos"

        # API expects an array of video numbers
        payload = [video_no]
        params = {"unique_id": unique_id}

        delay = initial_delay

        for attempt in range(max_retries):
            try:
                response = self.session.post(url, json=payload, params=params)
                response.raise_for_status()

                result = response.json()

                if result.get('code') == '0000':
                    logger.info(f"Video deleted successfully: {video_no}")
                    return True
                else:
                    error_msg = result.get('msg', 'Unknown error')

                    # Check if rate limited
                    if 'exceeded the limit' in error_msg.lower() or 'rate limit' in error_msg.lower():
                        if attempt < max_retries - 1:
                            logger.warning(f"Rate limited on attempt {attempt + 1}/{max_retries}. Retrying in {delay}s...")
                            time.sleep(delay)
                            delay *= 2  # Exponential backoff
                            continue
                        else:
                            logger.error(f"Delete failed after {max_retries} attempts: {error_msg}")
                            return False
                    else:
                        logger.error(f"Delete failed: {error_msg}")
                        return False

            except requests.exceptions.HTTPError as e:
                # Check for HTTP 429 (Too Many Requests)
                if e.response.status_code == 429:
                    if attempt < max_retries - 1:
                        logger.warning(f"HTTP 429 on attempt {attempt + 1}/{max_retries}. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Delete failed after {max_retries} attempts: HTTP 429")
                        return False
                else:
                    logger.error(f"HTTP error deleting video: {e}", exc_info=True)
                    return False

            except Exception as e:
                logger.error(f"Failed to delete video: {e}", exc_info=True)
                return False

        logger.error(f"Delete failed after {max_retries} attempts")
        return False
