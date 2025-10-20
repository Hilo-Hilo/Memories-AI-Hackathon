"""
Cloud analysis manager for orchestrating video uploads and result retrieval.

Handles the lifecycle of cloud analysis jobs:
1. Upload videos to Hume AI and Memories.ai
2. Track processing status
3. Retrieve results when complete
4. Validate and store structured data
5. Delete cloud videos after successful retrieval
"""

import uuid
import json
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime

from ..core.config import Config
from ..core.database import Database
from ..core.models import (
    CloudAnalysisJob, CloudProvider, CloudJobStatus, VideoType
)
from ..integrations.hume_client import HumeExpressionClient
from ..integrations.memories_client import MemoriesClient
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CloudAnalysisManager:
    """Manages cloud analysis job lifecycle."""

    def __init__(
        self,
        config: Config,
        database: Database,
        hume_client: Optional[HumeExpressionClient] = None,
        memories_client: Optional[MemoriesClient] = None
    ):
        """
        Initialize cloud analysis manager.

        Args:
            config: Configuration manager
            database: Database interface
            hume_client: Optional Hume AI client
            memories_client: Optional Memories.ai client
        """
        self.config = config
        self.database = database
        self.hume_client = hume_client
        self.memories_client = memories_client

        logger.info("Cloud analysis manager initialized")

    def upload_session_for_analysis(
        self,
        session_id: str,
        cam_video_path: Path,
        screen_video_path: Optional[Path] = None,
        run_hume: bool = True,
        run_memories: bool = True
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Upload session videos for cloud analysis.

        This method BLOCKS until uploads are complete. User should see
        a progress dialog during this operation.

        Args:
            session_id: Session ID
            cam_video_path: Path to webcam video
            screen_video_path: Path to screen video (optional)
            run_hume: Whether to upload to Hume AI
            run_memories: Whether to upload to Memories.ai

        Returns:
            Tuple of (hume_job_id, memories_job_id), either may be None
        """
        hume_job_id = None
        memories_job_id = None

        # Upload to Hume AI
        if run_hume and self.hume_client:
            logger.info("Uploading to Hume AI...")
            hume_job_id = self._upload_to_hume(session_id, cam_video_path)

        # Upload to Memories.ai
        if run_memories and self.memories_client:
            logger.info("Uploading to Memories.ai...")
            memories_job_id = self._upload_to_memories(session_id, cam_video_path, screen_video_path)

        return hume_job_id, memories_job_id

    def _upload_to_hume(self, session_id: str, cam_video_path: Path) -> Optional[str]:
        """
        Upload webcam video to Hume AI.

        Args:
            session_id: Session ID
            cam_video_path: Path to webcam video

        Returns:
            job_id (UUID) or None if failed
        """
        job_id = str(uuid.uuid4())

        # Create database record
        job = CloudAnalysisJob(
            job_id=job_id,
            session_id=session_id,
            provider=CloudProvider.HUME_AI,
            provider_job_id=None,
            status=CloudJobStatus.UPLOADING,
            video_type=VideoType.WEBCAM,
            video_path=str(cam_video_path),
            upload_started_at=datetime.now()
        )
        self.database.create_cloud_job(job)

        try:
            # Submit video to Hume AI Batch API
            provider_job_id = self.hume_client.analyze_video(
                video_path=cam_video_path,
                include_face=True,
                include_prosody=False,
                include_language=False
            )

            if not provider_job_id:
                raise Exception("Hume AI upload failed - no job ID returned")

            # Update job record with provider_job_id
            self.database.update_cloud_job_status(
                job_id=job_id,
                status=CloudJobStatus.PROCESSING,
                provider_job_id=provider_job_id
            )
            self.database.mark_cloud_job_upload_complete(job_id)

            logger.info(f"Hume AI upload complete: {provider_job_id}")
            return job_id

        except Exception as e:
            logger.error(f"Hume AI upload failed: {e}", exc_info=True)
            self.database.update_cloud_job_status(
                job_id=job_id,
                status=CloudJobStatus.FAILED,
                error_message=str(e)
            )
            return None

    def _upload_to_memories(
        self,
        session_id: str,
        cam_video_path: Path,
        screen_video_path: Optional[Path]
    ) -> Optional[str]:
        """
        Upload videos to Memories.ai, or reuse existing videos if already uploaded.

        Checks if videos for this session already exist in the cloud:
        - If videos exist and are processed (PARSE): reuse them
        - If videos exist but still processing: return existing job
        - If videos don't exist: upload new videos

        Args:
            session_id: Session ID
            cam_video_path: Path to webcam video
            screen_video_path: Path to screen video (optional)

        Returns:
            job_id (UUID) or None if failed
        """
        unique_id = f"focus_session_{session_id}"

        # Check for existing Memories.ai job for this session
        existing_jobs = self.database.get_cloud_jobs_for_session(session_id)
        existing_memories_job = None
        for job in existing_jobs:
            if job.provider == CloudProvider.MEMORIES_AI and job.provider_job_id:
                existing_memories_job = job
                break

        # If we have an existing job, check if videos still exist in cloud
        if existing_memories_job and existing_memories_job.provider_job_id:
            try:
                job_data = json.loads(existing_memories_job.provider_job_id)
                cam_video_no = job_data.get("cam_video_no")
                screen_video_no = job_data.get("screen_video_no")
                
                if cam_video_no:
                    # Check if videos still exist in cloud
                    cam_status = self.memories_client.get_video_status(cam_video_no, unique_id)
                    screen_status = None
                    if screen_video_no:
                        import time
                        time.sleep(1.0)  # Small delay to avoid rate limits
                        screen_status = self.memories_client.get_video_status(screen_video_no, unique_id)
                    
                    # Determine overall status
                    cam_exists = cam_status is not None
                    screen_exists = (screen_status is not None) if screen_video_no else True
                    
                    if cam_exists and screen_exists:
                        cam_processed = cam_status.get('status') == 'PARSE'
                        screen_processed = (screen_status.get('status') == 'PARSE') if screen_video_no else True
                        
                        if cam_processed and screen_processed:
                            # Videos exist and are processed - reuse them!
                            logger.info(f"Reusing existing processed videos: {cam_video_no}, {screen_video_no}")
                            # Return existing job ID so it can be queried again
                            return existing_memories_job.job_id
                        else:
                            # Videos exist but still processing
                            logger.info(f"Videos still processing: cam={cam_status.get('status')}, screen={screen_status.get('status') if screen_status else 'N/A'}")
                            # Update job status to PROCESSING if not already
                            if existing_memories_job.status != CloudJobStatus.PROCESSING:
                                self.database.update_cloud_job_status(
                                    existing_memories_job.job_id,
                                    CloudJobStatus.PROCESSING
                                )
                            return existing_memories_job.job_id
                    else:
                        logger.info(f"Previous videos not found in cloud (cam={cam_exists}, screen={screen_exists}), will upload new ones")
            except Exception as e:
                logger.warning(f"Error checking existing videos: {e}, will upload new ones")

        # No existing videos or they were deleted - create new job and upload
        job_id = str(uuid.uuid4())
        video_type = VideoType.BOTH if screen_video_path else VideoType.WEBCAM
        job = CloudAnalysisJob(
            job_id=job_id,
            session_id=session_id,
            provider=CloudProvider.MEMORIES_AI,
            provider_job_id=None,
            status=CloudJobStatus.UPLOADING,
            video_type=video_type,
            video_path=f"{cam_video_path},{screen_video_path}" if screen_video_path else str(cam_video_path),
            upload_started_at=datetime.now()
        )
        self.database.create_cloud_job(job)

        try:
            # Upload webcam video
            cam_video_no = self.memories_client.upload_video(
                video_path=cam_video_path,
                unique_id=unique_id
            )

            if not cam_video_no:
                raise Exception("Memories.ai webcam upload failed")

            # Upload screen video if available
            screen_video_no = None
            if screen_video_path and screen_video_path.exists():
                # Add delay between uploads to avoid rate limits
                import time
                time.sleep(3.0)
                logger.info("Waiting 3 seconds before uploading screen video...")

                screen_video_no = self.memories_client.upload_video(
                    video_path=screen_video_path,
                    unique_id=unique_id
                )

                if not screen_video_no:
                    raise Exception("Memories.ai screen upload failed")

            # Store both video_nos as JSON in provider_job_id
            provider_job_id = json.dumps({
                "unique_id": unique_id,
                "cam_video_no": cam_video_no,
                "screen_video_no": screen_video_no
            })

            # Update job record
            self.database.update_cloud_job_status(
                job_id=job_id,
                status=CloudJobStatus.PROCESSING,
                provider_job_id=provider_job_id
            )
            self.database.mark_cloud_job_upload_complete(job_id)

            logger.info(f"Memories.ai upload complete: {cam_video_no}, {screen_video_no}")
            return job_id

        except Exception as e:
            logger.error(f"Memories.ai upload failed: {e}", exc_info=True)
            self.database.update_cloud_job_status(
                job_id=job_id,
                status=CloudJobStatus.FAILED,
                error_message=str(e)
            )
            return None

    def check_job_status(self, job_id: str) -> CloudJobStatus:
        """
        Check if cloud job processing is complete.

        This polls the cloud provider API to check processing status.

        Args:
            job_id: Job ID

        Returns:
            Current CloudJobStatus
        """
        job = self.database.get_cloud_job(job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return CloudJobStatus.FAILED

        # If already completed or failed, return current status
        if job.status in [CloudJobStatus.COMPLETED, CloudJobStatus.FAILED]:
            return job.status

        # Poll provider API
        if job.provider == CloudProvider.HUME_AI:
            return self._check_hume_status(job)
        elif job.provider == CloudProvider.MEMORIES_AI:
            return self._check_memories_status(job)
        else:
            return job.status

    def _check_hume_status(self, job: CloudAnalysisJob) -> CloudJobStatus:
        """Check Hume AI job status."""
        if not self.hume_client or not job.provider_job_id:
            return CloudJobStatus.FAILED

        try:
            # Poll job status (non-blocking, single check)
            status = self.hume_client.poll_job(job.provider_job_id, timeout=1)

            if status == "COMPLETED":
                self.database.update_cloud_job_status(
                    job_id=job.job_id,
                    status=CloudJobStatus.COMPLETED
                )
                return CloudJobStatus.COMPLETED
            elif status == "FAILED":
                self.database.update_cloud_job_status(
                    job_id=job.job_id,
                    status=CloudJobStatus.FAILED,
                    error_message="Hume AI processing failed"
                )
                return CloudJobStatus.FAILED
            else:
                return CloudJobStatus.PROCESSING

        except Exception as e:
            logger.error(f"Error checking Hume AI status: {e}")
            return CloudJobStatus.PROCESSING

    def _check_memories_status(self, job: CloudAnalysisJob) -> CloudJobStatus:
        """Check Memories.ai job status."""
        if not self.memories_client or not job.provider_job_id:
            return CloudJobStatus.FAILED

        try:
            # Parse provider_job_id JSON
            job_data = json.loads(job.provider_job_id)
            unique_id = job_data["unique_id"]
            cam_video_no = job_data["cam_video_no"]

            # Check if cam video is processed (non-blocking, single check)
            processed = self.memories_client.wait_for_processing(
                video_no=cam_video_no,
                unique_id=unique_id,
                max_wait=1  # Just one quick check
            )

            if processed:
                self.database.update_cloud_job_status(
                    job_id=job.job_id,
                    status=CloudJobStatus.COMPLETED
                )
                return CloudJobStatus.COMPLETED
            else:
                return CloudJobStatus.PROCESSING

        except Exception as e:
            logger.error(f"Error checking Memories.ai status: {e}")
            return CloudJobStatus.PROCESSING

    def retrieve_and_store_results(self, job_id: str) -> Optional[Path]:
        """
        Retrieve results from cloud provider and store locally.

        After successful retrieval and validation, this method marks
        the job as safe for cloud video deletion.

        Args:
            job_id: Job ID

        Returns:
            Path to stored results JSON file, or None if failed
        """
        job = self.database.get_cloud_job(job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return None

        if job.status != CloudJobStatus.COMPLETED:
            logger.warning(f"Job not completed: {job_id} (status: {job.status.value})")
            return None

        # Retrieve results based on provider
        if job.provider == CloudProvider.HUME_AI:
            return self._retrieve_hume_results(job)
        elif job.provider == CloudProvider.MEMORIES_AI:
            return self._retrieve_memories_results(job)
        else:
            return None

    def _retrieve_hume_results(self, job: CloudAnalysisJob) -> Optional[Path]:
        """Retrieve Hume AI results and store locally."""
        if not self.hume_client or not job.provider_job_id:
            return None

        try:
            # Fetch results from Hume AI
            results = self.hume_client.fetch_results(job.provider_job_id)

            if not results:
                raise Exception("Failed to fetch Hume AI results")

            # Validate results structure
            if not self._validate_hume_results(results):
                raise Exception("Hume AI results validation failed")

            # Store results locally
            results_dir = self.config.get_data_dir() / "cloud_results" / job.session_id
            results_dir.mkdir(parents=True, exist_ok=True)
            results_path = results_dir / f"hume_{job.job_id}.json"

            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)

            # Update database
            self.database.mark_cloud_job_results_fetched(
                job_id=job.job_id,
                results_file_path=str(results_path)
            )

            logger.info(f"Hume AI results stored: {results_path}")
            return results_path

        except Exception as e:
            logger.error(f"Failed to retrieve Hume AI results: {e}", exc_info=True)
            return None

    def _retrieve_memories_results(self, job: CloudAnalysisJob) -> Optional[Path]:
        """Retrieve Memories.ai results and store locally."""
        if not self.memories_client or not job.provider_job_id:
            return None

        try:
            # Parse provider_job_id JSON
            job_data = json.loads(job.provider_job_id)
            unique_id = job_data["unique_id"]
            cam_video_no = job_data["cam_video_no"]
            screen_video_no = job_data.get("screen_video_no")

            # Build video list for chat
            video_nos = [cam_video_no]
            if screen_video_no:
                video_nos.append(screen_video_no)

            # Chat with videos to get structured analysis
            prompt = self._build_memories_analysis_prompt()
            analysis_text = self.memories_client.chat_with_video(
                video_nos=video_nos,
                prompt=prompt,
                unique_id=unique_id,
                stream=True
            )

            if not analysis_text:
                raise Exception("Failed to get Memories.ai analysis")

            # Parse and validate structured response
            results = self._parse_memories_response(analysis_text)

            if not self._validate_memories_results(results):
                raise Exception("Memories.ai results validation failed")

            # Store results locally
            results_dir = self.config.get_data_dir() / "cloud_results" / job.session_id
            results_dir.mkdir(parents=True, exist_ok=True)
            results_path = results_dir / f"memories_{job.job_id}.json"

            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)

            # Update database
            self.database.mark_cloud_job_results_fetched(
                job_id=job.job_id,
                results_file_path=str(results_path)
            )

            logger.info(f"Memories.ai results stored: {results_path}")
            return results_path

        except Exception as e:
            logger.error(f"Failed to retrieve Memories.ai results: {e}", exc_info=True)
            return None

    def delete_cloud_videos(self, job_id: str) -> bool:
        """
        Delete videos from cloud provider.

        Only deletes if can_delete_remote flag is True (i.e., results
        have been successfully retrieved and stored locally).

        Args:
            job_id: Job ID

        Returns:
            True if deleted successfully, False otherwise
        """
        job = self.database.get_cloud_job(job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return False

        if not job.can_delete_remote:
            logger.warning(f"Job not safe to delete: {job_id} (results not fetched)")
            return False

        if job.remote_deleted_at:
            logger.info(f"Job already deleted: {job_id}")
            return True

        # Delete based on provider
        try:
            if job.provider == CloudProvider.HUME_AI:
                # Hume AI doesn't provide delete API - jobs expire automatically
                logger.info(f"Hume AI jobs expire automatically: {job.provider_job_id}")
                success = True

            elif job.provider == CloudProvider.MEMORIES_AI:
                success = self._delete_memories_videos(job)

            else:
                success = False

            if success:
                self.database.mark_cloud_video_deleted(job_id)
                logger.info(f"Cloud videos deleted for job: {job_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to delete cloud videos: {e}", exc_info=True)
            return False

    def _delete_memories_videos(self, job: CloudAnalysisJob) -> bool:
        """Delete Memories.ai videos with delays to avoid rate limits."""
        if not self.memories_client or not job.provider_job_id:
            return False

        try:
            # Parse provider_job_id JSON
            job_data = json.loads(job.provider_job_id)
            unique_id = job_data["unique_id"]
            cam_video_no = job_data["cam_video_no"]
            screen_video_no = job_data.get("screen_video_no")

            # Delete cam video with retry logic
            cam_deleted = self.memories_client.delete_video(cam_video_no, unique_id)

            # Delete screen video if exists
            screen_deleted = True
            if screen_video_no:
                # Add delay between deletions to avoid rate limits
                import time
                time.sleep(3.0)
                logger.info("Waiting 3 seconds before deleting screen video...")
                screen_deleted = self.memories_client.delete_video(screen_video_no, unique_id)

            return cam_deleted and screen_deleted

        except Exception as e:
            logger.error(f"Failed to delete Memories.ai videos: {e}")
            return False

    def _build_memories_analysis_prompt(self) -> str:
        """Build comprehensive Markdown report prompt for Memories.ai."""
        # Check for custom prompt first
        if self.config:
            custom = self.config.get_custom_prompt("memories_analysis")
            if custom:
                return custom
        
        # Default prompt
        return """Analyze this focus session by examining both the webcam and screen recordings.

Generate a comprehensive productivity report in Markdown format with the following sections:

# Focus Session Productivity Report

## Executive Summary
Provide a 2-3 sentence overview of the session quality, primary activities, and overall productivity assessment.

## Time-Based Activity Breakdown
Create a chronological timeline showing:
- Time segments with start/end timestamps (MM:SS format)
- Activity classification (Focus/Break/Distraction)
- Task hypothesis (what you observed the user doing)
- Confidence level and evidence from both webcam and screen

Use a table or structured list format for readability.

## Application Usage Analysis
Analyze screen content to identify:
- Applications/tools used with time spent in each
- Productivity classification (Productive/Neutral/Distraction)
- Context switches and multitasking patterns
- Percentage breakdown of time allocation

## Distraction Analysis
Detail distraction events including:
- Timestamp and duration of each distraction
- Distraction triggers (social media, phone, web browsing, etc.)
- Correlation between webcam behavior (head movement, gaze) and screen content
- Total distraction time and frequency

## Behavioral Insights
Correlate webcam and screen observations:
- Focus patterns (when user was most engaged)
- Attention quality indicators (posture, gaze consistency, head position)
- Break patterns and their relationship to productivity
- Signs of fatigue or frustration
- Phone usage detection and impact

## Productivity Metrics
Calculate and present:
- Focus ratio (focused time / total session time)
- Average focus bout duration
- Distraction frequency (events per hour)
- Overall productivity score (0-100)
- Context switch frequency

## Actionable Recommendations
Provide 3-5 specific, evidence-based recommendations to improve focus and productivity based on observed patterns.

---

**Instructions:**
- Use clear Markdown formatting with headers, lists, tables, and emphasis
- Include specific timestamps and evidence from the videos
- Be objective and analytical
- Provide quantitative metrics wherever possible
- Make recommendations actionable and personalized to observed behavior
- Do NOT wrap the output in code blocks - return raw Markdown text"""

    def _parse_memories_response(self, response_text: str) -> Dict[str, Any]:
        """
        Store Memories.ai Markdown response without parsing.

        Args:
            response_text: Raw Markdown report from Memories.ai

        Returns:
            Dictionary with markdown_report field containing raw text
        """
        # Clean up code blocks if VLM wrapped response despite instructions
        clean_text = response_text.strip()
        if clean_text.startswith("```"):
            # Extract content between ``` markers
            lines = clean_text.split('\n')
            content_lines = []
            in_code_block = False
            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    content_lines.append(line)
            if content_lines:
                clean_text = '\n'.join(content_lines)

        # Return raw Markdown text without parsing
        return {
            "markdown_report": clean_text,
            "report_generated_at": datetime.now().isoformat()
        }

    def _validate_hume_results(self, results: Dict[str, Any]) -> bool:
        """Validate Hume AI results structure."""
        required_fields = ["job_id", "timeline", "summary", "frame_count"]
        return all(field in results for field in required_fields)

    def _validate_memories_results(self, results: Dict[str, Any]) -> bool:
        """Validate Memories.ai results structure."""
        # Check for markdown_report field and ensure it's non-empty
        if "markdown_report" not in results:
            return False
        report = results["markdown_report"]
        return isinstance(report, str) and len(report.strip()) > 0

    def get_storage_summary(self) -> Dict[str, Any]:
        """
        Get summary of cloud storage usage by querying cloud APIs.

        IMPORTANT: Queries actual cloud APIs (Hume AI, Memories.ai) to get
        the real list of stored videos, not just database records.

        Returns:
            Dictionary with storage summary:
            {
                "hume_ai": {
                    "count": 3,
                    "oldest_days": 5,
                    "newest_days": 1,
                    "jobs": [list of job dicts with id, status, created_timestamp_ms]
                },
                "memories_ai": {
                    "count": 5,
                    "oldest_days": 10,
                    "newest_days": 2,
                    "videos": [list of video dicts with video_no, video_name, status, etc.]
                },
                "total_count": 8,
                "error": None or error message
            }
        """
        hume_jobs = []
        memories_videos = []
        error_msg = None

        # Query Hume AI API for all jobs
        if self.hume_client:
            try:
                logger.info("Querying Hume AI for stored jobs...")
                api_jobs = self.hume_client.list_jobs(status=None, limit=100)
                if api_jobs:
                    hume_jobs = api_jobs
                    logger.info(f"Found {len(hume_jobs)} Hume AI jobs in cloud")
            except Exception as e:
                logger.error(f"Failed to query Hume AI: {e}", exc_info=True)
                error_msg = f"Hume AI: {str(e)}"

        # Query Memories.ai API for all videos
        if self.memories_client:
            try:
                logger.info("Querying Memories.ai for stored videos...")
                # List all videos across all unique_ids by using "default" or iterating known session IDs
                # For simplicity, query with unique_id pattern "focus_session_*"
                # NOTE: Memories.ai API doesn't support wildcard queries, so we need to query each session

                # Alternative approach: Get all sessions from database and query each unique_id
                all_sessions = self.database.get_all_sessions()
                all_videos = []

                for session in all_sessions:
                    unique_id = f"focus_session_{session.session_id}"
                    try:
                        videos = self.memories_client.list_videos(unique_id=unique_id, page=1, size=200)
                        if videos:
                            # Add session_id to each video for cross-referencing
                            for video in videos:
                                video["focus_guardian_session_id"] = session.session_id
                            all_videos.extend(videos)
                    except Exception as e:
                        logger.debug(f"No videos found for session {session.session_id}: {e}")
                        continue

                memories_videos = all_videos
                logger.info(f"Found {len(memories_videos)} Memories.ai videos in cloud")

            except Exception as e:
                logger.error(f"Failed to query Memories.ai: {e}", exc_info=True)
                if error_msg:
                    error_msg += f"; Memories.ai: {str(e)}"
                else:
                    error_msg = f"Memories.ai: {str(e)}"

        def calculate_age_days(timestamp_ms: Optional[int]) -> int:
            """Calculate days since timestamp (milliseconds)."""
            if not timestamp_ms:
                return 0
            timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
            delta = datetime.now() - timestamp_dt
            return delta.days

        # Calculate Hume AI stats
        hume_stats = {"count": 0, "oldest_days": 0, "newest_days": 0, "jobs": []}
        if hume_jobs:
            ages = [calculate_age_days(j.get("created_timestamp_ms")) for j in hume_jobs]
            hume_stats = {
                "count": len(hume_jobs),
                "oldest_days": max(ages) if ages else 0,
                "newest_days": min(ages) if ages else 0,
                "jobs": hume_jobs  # Include full job list for detailed view
            }

        # Calculate Memories.ai stats
        memories_stats = {"count": 0, "oldest_days": 0, "newest_days": 0, "videos": []}
        if memories_videos:
            ages = [calculate_age_days(int(v.get("create_time", 0))) for v in memories_videos if v.get("create_time")]
            memories_stats = {
                "count": len(memories_videos),
                "oldest_days": max(ages) if ages else 0,
                "newest_days": min(ages) if ages else 0,
                "videos": memories_videos  # Include full video list for detailed view
            }

        return {
            "hume_ai": hume_stats,
            "memories_ai": memories_stats,
            "total_count": len(hume_jobs) + len(memories_videos),
            "error": error_msg
        }
