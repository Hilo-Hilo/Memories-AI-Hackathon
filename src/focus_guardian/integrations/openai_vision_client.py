"""
OpenAI Vision API client for snapshot classification.

Provides realtime inference for camera and screen snapshots using GPT-4 Vision,
with carefully engineered prompts to detect the canonical label taxonomy.
"""

import time
import base64
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass

import openai
from openai import OpenAI

from ..core.models import (
    CAM_LABELS, SCREEN_LABELS,
    CAM_DISTRACTION_LABELS, CAM_FOCUS_LABELS, CAM_ABSENCE_LABELS,
    SCREEN_DISTRACTION_LABELS, SCREEN_FOCUS_LABELS,
    CONFIDENCE_THRESHOLDS
)
from ..utils.logger import get_logger
from ..utils.error_handler import (
    handle_error, with_circuit_breaker, ErrorSeverity, ErrorCategory
)

logger = get_logger(__name__)


@dataclass
class VisionResult:
    """Result from OpenAI Vision API classification."""
    labels: Dict[str, float]     # {label: confidence}
    raw_response: Dict[str, Any]  # Full API response
    processed_at: datetime
    latency_ms: float


class RateLimitError(Exception):
    """Raised when API rate limit is hit (429 response)."""
    pass


class VisionAPIError(Exception):
    """Raised when Vision API call fails."""
    pass


class OpenAIVisionClient:
    """OpenAI Vision API client for snapshot classification."""
    
    def __init__(
        self,
        api_key: str,
        timeout_sec: int = 30,
        model: str = "gpt-5-nano",
        detail: str = "high"
    ):
        """
        Initialize OpenAI Vision client.

        Args:
            api_key: OpenAI API key
            timeout_sec: Request timeout in seconds
            model: Model to use (gpt-5-nano recommended for best cost efficiency)
                   Options: gpt-5-nano ($0.055/image), gpt-4o-mini ($0.165/image)
            detail: Image detail level - "low" (85 tokens) or "high" (1100 tokens)
                   gpt-5-nano pricing: low=$0.00425/image, high=$0.055/image
                   High detail recommended for better accuracy with 120s intervals.
        """
        self.api_key = api_key
        self.timeout_sec = timeout_sec
        self.model = model
        self.detail = detail

        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key, timeout=timeout_sec)

        logger.info(
            f"OpenAI Vision client initialized (model: {model}, detail: {detail})"
        )
    
    def classify_cam_snapshot(self, image_path: Path) -> VisionResult:
        """
        Classify webcam snapshot to detect user attention state.
        
        Detects: HeadAway, EyesOffScreen, Absent, MicroSleep, PhoneLikely, Focused
        
        Args:
            image_path: Path to JPEG image file
            
        Returns:
            VisionResult with labels and confidences
            
        Raises:
            VisionAPIError: If API call fails
            RateLimitError: If rate limited (429)
        """
        prompt = self._build_cam_prompt()
        return self._classify_image(image_path, prompt, "cam")
    
    def classify_screen_snapshot(self, image_path: Path) -> VisionResult:
        """
        Classify screen snapshot to detect application/content type.
        
        Detects: VideoOnScreen, SocialFeed, Code, Docs, Email, VideoCall,
                Reading, Slides, Terminal, ChatWindow, Games, MultipleMonitors, Unknown
        
        Args:
            image_path: Path to JPEG image file
            
        Returns:
            VisionResult with labels and confidences
            
        Raises:
            VisionAPIError: If API call fails
            RateLimitError: If rate limited (429)
        """
        prompt = self._build_screen_prompt()
        return self._classify_image(image_path, prompt, "screen")
    
    def _build_cam_prompt(self) -> str:
        """Build prompt for camera snapshot classification."""
        return """Analyze this webcam image and classify the user's attention state.

Possible classifications (return ONLY the most dominant ones with confidence 0.0-1.0):

**Distraction Indicators:**
- HeadAway: Head turned >45° away from screen (looking elsewhere)
- EyesOffScreen: Gaze not directed at screen (looking down, away, or unfocused)
- MicroSleep: Eyes closed or drowsy appearance (tired, nodding off)
- PhoneLikely: Phone visible in hand or user looking down at phone

**Absence Indicators:**
- Absent: No person visible in frame (empty chair, person left desk)

**Focus Indicators:**
- Focused: Engaged posture, eyes on screen, attentive appearance

**Instructions:**
1. Look carefully at head orientation, eye gaze, and body language
2. Return ONLY labels that are clearly present (confidence ≥ 0.6)
3. Multiple labels can apply (e.g., HeadAway + PhoneLikely)
4. If person is attentive and looking at screen, return Focused
5. If no person visible, return Absent

Return as JSON:
{
  "labels": {"LabelName": confidence, ...},
  "reasoning": "brief explanation"
}"""
    
    def _build_screen_prompt(self) -> str:
        """Build prompt for screen snapshot classification."""
        return """Analyze this screen capture and classify the visible content/applications.

Possible classifications (return ONLY clearly visible ones with confidence 0.0-1.0):

**Distraction Content:**
- VideoOnScreen: Video player or streaming (YouTube, Netflix, etc.)
- SocialFeed: Social media feed scrolling (Twitter, Instagram, Facebook, LinkedIn, TikTok)
- Games: Gaming applications or entertainment software
- ChatWindow: Chat/messaging apps (Slack, Discord, WhatsApp, iMessage)

**Focus Content:**
- Code: Code editor or IDE (VS Code, PyCharm, Sublime, JetBrains, Vim)
- Docs: Documentation, technical reading, wikis, API docs
- Reading: Long-form reading (ebooks, PDFs, news articles, NOT code)
- Slides: Presentation software (PowerPoint, Google Slides, Keynote)
- Terminal: Command line terminal or shell

**Borderline Content:**
- Email: Email client (Gmail, Outlook, Apple Mail)
- VideoCall: Video conferencing UI (Zoom, Meet, Teams, FaceTime)
- MultipleMonitors: Multiple windows visible, potential context switching

**Neutral:**
- Unknown: Cannot determine content type clearly

**Instructions:**
1. Look at window titles, icons, UI elements, visible content
2. Return ONLY labels that are clearly identifiable (confidence ≥ 0.6)
3. Multiple labels can apply if multiple windows visible
4. If uncertain, use Unknown
5. Prioritize the largest/most prominent window

Return as JSON:
{
  "labels": {"LabelName": confidence, ...},
  "reasoning": "brief explanation of what you see"
}"""
    
    @with_circuit_breaker('openai_vision', failure_threshold=3, recovery_timeout=30.0)
    @handle_error(
        component='openai_vision_client',
        operation='classify_image',
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.API,
        user_visible=True,
        can_retry=True
    )
    def _classify_image(
        self,
        image_path: Path,
        prompt: str,
        kind: str
    ) -> VisionResult:
        """
        Classify image using OpenAI Vision API.

        Args:
            image_path: Path to image file
            prompt: Classification prompt
            kind: "cam" or "screen" for logging

        Returns:
            VisionResult
        """
        start_time = time.time()

        # Validate image file exists and is readable
        if not image_path.exists():
            raise VisionAPIError(f"Image file not found: {image_path}")

        if image_path.stat().st_size == 0:
            raise VisionAPIError(f"Image file is empty: {image_path}")

        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()

            base64_image = base64.b64encode(image_data).decode('utf-8')

            # Validate base64 encoding
            if not base64_image:
                raise VisionAPIError("Failed to encode image to base64")

            # Call OpenAI Vision API with enhanced error handling
            # Note: gpt-5-nano only supports temperature=1 (default)
            api_params = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": self.detail  # Configurable: low (cheap) or high (accurate)
                                }
                            }
                        ]
                    }
                ],
                "max_completion_tokens": 300,  # Changed from max_tokens for newer models (gpt-5-nano, gpt-4o-mini)
                "timeout": self.timeout_sec
            }
            
            # Only add temperature for models that support it (not gpt-5-nano)
            if "gpt-5-nano" not in self.model:
                api_params["temperature"] = 0.1  # Low temperature for consistent classifications
            
            response = self.client.chat.completions.create(**api_params)

            # Validate response structure
            if not response or not response.choices:
                raise VisionAPIError("Invalid response from OpenAI Vision API")

            latency_ms = (time.time() - start_time) * 1000
            
            # Parse response
            content = response.choices[0].message.content
            
            # Validate content exists
            if not content or content.strip() == "":
                logger.error("Empty response from OpenAI Vision API")
                raise VisionAPIError("Empty response from OpenAI Vision API")
            
            # Extract JSON from response
            import json
            import re
            
            # Log the actual response for debugging
            logger.debug(f"Vision API response for {kind}: {content[:200]}...")
            
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    result_data = json.loads(json_match.group())
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from Vision API response: {e}")
                    logger.error(f"Content was: {content}")
                    raise VisionAPIError(f"Invalid JSON in response: {e}")
            else:
                logger.warning(f"Could not find JSON in Vision API response: {content}")
                # Try to extract labels from plain text response
                result_data = {"labels": {}, "reasoning": content}
            
            labels = result_data.get("labels", {})
            reasoning = result_data.get("reasoning", "")
            
            # Validate labels against canonical taxonomy
            valid_labels = CAM_LABELS if kind == "cam" else SCREEN_LABELS
            filtered_labels = {}
            
            for label, confidence in labels.items():
                if label in valid_labels:
                    # Apply confidence threshold
                    threshold = CONFIDENCE_THRESHOLDS.get(label, 0.5)
                    if confidence >= threshold:
                        filtered_labels[label] = float(confidence)
                else:
                    logger.warning(f"Invalid label '{label}' returned by Vision API for {kind}")
            
            # Log result
            logger.debug(
                f"Vision API ({kind}): {filtered_labels} "
                f"(latency: {latency_ms:.0f}ms, reasoning: {reasoning[:100]})"
            )
            
            return VisionResult(
                labels=filtered_labels,
                raw_response={
                    "labels": labels,
                    "reasoning": reasoning,
                    "model": self.model,
                    "usage": response.usage.model_dump() if response.usage else {}
                },
                processed_at=datetime.now(),
                latency_ms=latency_ms
            )
        
        except openai.RateLimitError as e:
            logger.warning(f"OpenAI Vision API rate limit hit: {e}")
            raise RateLimitError(str(e)) from e

        except openai.APIError as e:
            # Handle specific OpenAI API errors
            if "insufficient_quota" in str(e).lower():
                logger.error(f"OpenAI API quota exceeded: {e}")
                raise VisionAPIError("OpenAI API quota exceeded. Please check your billing.") from e
            elif "invalid_api_key" in str(e).lower():
                logger.error(f"OpenAI API key invalid: {e}")
                raise VisionAPIError("OpenAI API key is invalid. Please check your configuration.") from e
            else:
                logger.error(f"OpenAI Vision API error: {e}", exc_info=True)
                raise VisionAPIError(str(e)) from e

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Network error calling OpenAI Vision API: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in OpenAI Vision API call: {e}", exc_info=True)
            raise VisionAPIError(f"Unexpected error: {str(e)}") from e
    
    def batch_classify(
        self,
        cam_path: Path,
        screen_path: Optional[Path]
    ) -> tuple[VisionResult, Optional[VisionResult]]:
        """
        Classify both camera and screen snapshots.
        
        This is a convenience method that calls both classify methods sequentially.
        In the future, could be optimized with batch API calls.
        
        Args:
            cam_path: Path to camera snapshot
            screen_path: Path to screen snapshot (optional)
            
        Returns:
            Tuple of (cam_result, screen_result)
        """
        cam_result = self.classify_cam_snapshot(cam_path)
        
        screen_result = None
        if screen_path:
            screen_result = self.classify_screen_snapshot(screen_path)
        
        return cam_result, screen_result


