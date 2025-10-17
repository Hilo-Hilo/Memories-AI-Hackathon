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
    
    def __init__(self, api_key: str, base_url: str = "https://api.memories.ai/v1"):
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
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
        
        logger.info("Memories.ai client initialized")
    
    def upload_video(self, video_path: Path) -> Optional[str]:
        """
        Upload video file to Memories.ai.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Object ID for the uploaded video or None if failed
        """
        logger.info(f"Uploading video to Memories.ai: {video_path}")
        
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return None
        
        try:
            # For hackathon: Mock upload (implement actual API call in production)
            import uuid
            object_id = f"mem_obj_{uuid.uuid4()}"
            
            logger.info(f"Video uploaded to Memories.ai: {object_id}")
            logger.warning("Using mock upload (implement actual Memories.ai API)")
            
            return object_id
        
        except Exception as e:
            logger.error(f"Failed to upload video: {e}", exc_info=True)
            return None
    
    def create_chat_session(
        self,
        object_ids: List[str],
        initial_message: str
    ) -> Optional[str]:
        """
        Create a chat session with uploaded objects.
        
        Args:
            object_ids: List of object IDs (uploaded videos/images)
            initial_message: Initial analysis prompt
            
        Returns:
            Chat session ID or None if failed
        """
        logger.info(f"Creating Memories.ai chat session with {len(object_ids)} objects")
        
        try:
            # Mock implementation
            import uuid
            session_id = f"chat_session_{uuid.uuid4()}"
            
            logger.info(f"Chat session created: {session_id}")
            logger.warning("Using mock chat session (implement actual Memories.ai API)")
            
            return session_id
        
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}", exc_info=True)
            return None
    
    def send_message(
        self,
        session_id: str,
        message: str,
        schema: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send message to chat session with optional schema constraint.
        
        Args:
            session_id: Chat session ID
            message: Message/prompt to send
            schema: Optional JSON schema for structured output
            
        Returns:
            Response data or None if failed
        """
        logger.info(f"Sending message to Memories.ai session: {session_id}")
        
        try:
            # Mock implementation - return structured analysis
            response = self._generate_mock_analysis()
            
            logger.info("Received Memories.ai response")
            return response
        
        except Exception as e:
            logger.error(f"Failed to send message: {e}", exc_info=True)
            return None
    
    def _generate_mock_analysis(self) -> Dict[str, Any]:
        """Generate mock analysis results for testing."""
        return {
            "segments": [
                {
                    "start_time": 0.0,
                    "end_time": 300.0,
                    "label": "Focus",
                    "task_hypothesis": "Working on code",
                    "apps": [
                        {"app_class": "Code", "share": 0.8},
                        {"app_class": "Terminal", "share": 0.2}
                    ],
                    "distractions": []
                },
                {
                    "start_time": 300.0,
                    "end_time": 450.0,
                    "label": "Distraction",
                    "task_hypothesis": "Watching video content",
                    "apps": [
                        {"app_class": "Video", "share": 0.9}
                    ],
                    "distractions": [
                        {
                            "type": "VideoOnScreen",
                            "confidence": 0.9,
                            "description": "User was watching YouTube video"
                        }
                    ]
                }
            ],
            "insights": {
                "focus_ratio": 0.67,
                "primary_distractor": "VideoOnScreen",
                "productivity_score": 0.72
            }
        }
    
    def analyze_session(
        self,
        cam_video_path: Path,
        screen_video_path: Path,
        snapshots_dir: Path
    ) -> Optional[Dict[str, Any]]:
        """
        Comprehensive session analysis using Memories.ai.
        
        Args:
            cam_video_path: Path to webcam video
            screen_video_path: Path to screen video
            snapshots_dir: Directory containing snapshots
            
        Returns:
            Complete analysis results or None if failed
        """
        logger.info("Starting comprehensive Memories.ai analysis")
        
        try:
            # Upload videos
            cam_obj_id = self.upload_video(cam_video_path)
            screen_obj_id = self.upload_video(screen_video_path)
            
            if not cam_obj_id or not screen_obj_id:
                logger.error("Failed to upload videos")
                return None
            
            # Create chat session
            session_id = self.create_chat_session(
                object_ids=[cam_obj_id, screen_obj_id],
                initial_message="Analyze this focus session"
            )
            
            if not session_id:
                logger.error("Failed to create chat session")
                return None
            
            # Send analysis prompt with schema
            schema = self._build_analysis_schema()
            prompt = self._build_analysis_prompt()
            
            results = self.send_message(session_id, prompt, schema)
            
            if results:
                logger.info("Memories.ai analysis completed successfully")
            
            return results
        
        except Exception as e:
            logger.error(f"Memories.ai analysis failed: {e}", exc_info=True)
            return None
    
    def _build_analysis_prompt(self) -> str:
        """Build prompt for session analysis."""
        return """Analyze this focus session and provide:

1. Time segmentation - Break the session into segments labeled as Focus, Break, or Distraction
2. Task hypothesis - What was the user working on in each segment?
3. App usage - What applications were visible on screen?
4. Distraction analysis - When did distractions occur and what caused them?
5. Insights - Overall focus ratio, primary distractors, productivity patterns

Return structured JSON following the schema provided."""
    
    def _build_analysis_schema(self) -> Dict[str, Any]:
        """Build JSON schema for structured output."""
        return {
            "type": "object",
            "properties": {
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start_time": {"type": "number"},
                            "end_time": {"type": "number"},
                            "label": {"type": "string", "enum": ["Focus", "Break", "Distraction"]},
                            "task_hypothesis": {"type": "string"},
                            "apps": {"type": "array"},
                            "distractions": {"type": "array"}
                        }
                    }
                },
                "insights": {
                    "type": "object",
                    "properties": {
                        "focus_ratio": {"type": "number"},
                        "primary_distractor": {"type": "string"},
                        "productivity_score": {"type": "number"}
                    }
                }
            }
        }

