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
        model: str = "gpt-4.1-nano",
        detail: str = "high",
        config=None,
        label_profile=None  # Optional LabelProfile instance
    ):
        """
        Initialize OpenAI Vision client.

        Args:
            api_key: OpenAI API key
            timeout_sec: Request timeout in seconds
            model: Model to use - gpt-4.1-nano RECOMMENDED (best cost/performance)
                   
                   Working models with base64 support:
                   - gpt-4.1-nano: $0.10/1M (RECOMMENDED - 37x cheaper than gpt-4o-mini!)
                   - gpt-4o-mini: $0.15/1M (works but more expensive)
                   - gpt-4.1-mini: $0.40/1M (works but very expensive)
                   
                   BROKEN models (return empty responses with base64):
                   - gpt-5-nano: Only works with public URLs
                   - gpt-5-mini: Only works with public URLs
                   
            detail: Image detail level - "low" (85 tokens) or "high" (variable)
                   gpt-4.1-nano: Efficient token usage (~2400 tokens/image with high detail)
                   High detail recommended for better accuracy with 120s intervals.
            config: Optional Config instance for custom prompts
            label_profile: Optional LabelProfile for custom labels
        """
        self.api_key = api_key
        self.timeout_sec = timeout_sec
        self.model = model
        self.detail = detail
        self.config = config  # Store config for custom prompts
        self.label_profile = label_profile  # Store profile for dynamic prompts/validation

        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key, timeout=timeout_sec)

        if label_profile:
            logger.info(
                f"OpenAI Vision client initialized (model: {model}, detail: {detail}, profile: {label_profile.name})"
            )
        else:
            logger.info(
                f"OpenAI Vision client initialized (model: {model}, detail: {detail}, profile: hardcoded)"
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
        # Check for custom prompt first
        if self.config:
            custom = self.config.get_custom_prompt("cam_snapshot")
            if custom:
                return custom
        
        # Generate prompt dynamically from label profile
        if self.label_profile:
            return self._generate_dynamic_cam_prompt(self.label_profile)
        
        # Fallback: Default hardcoded prompt
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
    
    def _generate_dynamic_cam_prompt(self, profile) -> str:
        """Generate camera prompt dynamically from label profile."""
        prompt = "Analyze this webcam image and classify the user's attention state.\n\n"
        prompt += "Possible classifications (return ONLY the most dominant ones with confidence 0.0-1.0):\n\n"
        
        # Group labels by category
        distraction_labels = profile.get_cam_labels_by_category("distraction")
        focus_labels = profile.get_cam_labels_by_category("focus")
        absence_labels = profile.get_cam_labels_by_category("absence")
        
        if distraction_labels:
            prompt += "**Distraction Indicators:**\n"
            for label_name in sorted(distraction_labels):
                label_def = profile.cam_labels[label_name]
                prompt += f"- {label_name}: {label_def.description}\n"
            prompt += "\n"
        
        if absence_labels:
            prompt += "**Absence Indicators:**\n"
            for label_name in sorted(absence_labels):
                label_def = profile.cam_labels[label_name]
                prompt += f"- {label_name}: {label_def.description}\n"
            prompt += "\n"
        
        if focus_labels:
            prompt += "**Focus Indicators:**\n"
            for label_name in sorted(focus_labels):
                label_def = profile.cam_labels[label_name]
                prompt += f"- {label_name}: {label_def.description}\n"
            prompt += "\n"
        
        prompt += """**Instructions:**
1. Look carefully at head orientation, eye gaze, and body language
2. Return ONLY labels that are clearly present with high confidence
3. Multiple labels can apply if multiple conditions are met
4. Be precise and consistent in your classifications

Return as JSON:
{
  "labels": {"LabelName": confidence, ...},
  "reasoning": "brief explanation"
}"""
        
        return prompt
    
    def _build_screen_prompt(self) -> str:
        """Build prompt for screen snapshot classification."""
        # Check for custom prompt first
        if self.config:
            custom = self.config.get_custom_prompt("screen_snapshot")
            if custom:
                return custom
        
        # Generate prompt dynamically from label profile
        if self.label_profile:
            return self._generate_dynamic_screen_prompt(self.label_profile)
        
        # Fallback: Default hardcoded prompt
        return """Analyze this screen capture and classify the visible content/applications.

Possible classifications (return ONLY clearly visible ones with confidence 0.0-1.0):

**HIGH-RISK DISTRACTION Content (Always flag these):**
- VideoOnScreen: Video player showing entertainment/non-work content (YouTube, Netflix, TikTok, Twitch)
  * Look for: play buttons, video timelines, thumbnails, entertainment titles
  * Even if paused, flag if video content is visible
  * Exception: Tutorial/educational videos WITH code/terminal visible = WorkRelatedVideo instead
- SocialFeed: Social media feed scrolling (Twitter, Instagram, Facebook, Reddit, LinkedIn feed)
- Games: Gaming applications or entertainment software
- ChatWindow: Personal chat/messaging apps (Discord, WhatsApp, iMessage - NOT work Slack)

**WORK-RELATED Video (Educational/Tutorial):**
- WorkRelatedVideo: Tutorial, coding video, educational content WITH evidence of work context
  * Must see: Code editor, terminal, or technical content alongside video
  * Or: Video shows coding, technical tutorial, documentation walkthrough
  
**Focus Content:**
- Code: Code editor or IDE (VS Code, PyCharm, Sublime, JetBrains, Vim)
- Docs: Documentation, technical reading, wikis, API docs, Stack Overflow
- Reading: Long-form reading (ebooks, PDFs, research papers)
- Slides: Presentation software (PowerPoint, Google Slides, Keynote)
- Terminal: Command line terminal or shell

**Work Communication:**
- Email: Email client (Gmail, Outlook, Apple Mail)
- VideoCall: Video conferencing UI (Zoom, Meet, Teams, FaceTime)
- WorkChat: Work messaging (Slack, Teams chat, work Discord server)

**Borderline Content:**
- MultipleMonitors: Multiple windows visible, potential context switching
- Browser: Generic browser without clear content type

**Neutral:**
- Unknown: Cannot determine content type clearly

**CRITICAL Instructions for Video Detection:**
1. If you see a video player (YouTube, etc.), check the CONTEXT:
   - Is there code, terminal, or work tools visible? → WorkRelatedVideo (productive)
   - Is it just entertainment content? → VideoOnScreen (distraction)
   - Look at video title, thumbnails, related videos for clues
2. Entertainment videos are ALWAYS flagged as VideoOnScreen (distraction)
3. Tutorial/educational videos WITH work context → WorkRelatedVideo (not flagged)
4. Social media is ALWAYS a distraction (even LinkedIn feed browsing)
5. Return labels with confidence ≥ 0.6 only
6. Multiple labels can apply if multiple windows visible

Return as JSON:
{
  "labels": {"LabelName": confidence, ...},
  "reasoning": "detailed explanation of what you see and why you classified it this way"
}"""
    
    def _generate_dynamic_screen_prompt(self, profile) -> str:
        """Generate screen prompt dynamically from label profile."""
        prompt = "Analyze this screen capture and classify the visible content/applications.\n\n"
        prompt += "Possible classifications (return ONLY clearly visible ones with confidence 0.0-1.0):\n\n"
        
        # Group labels by category
        distraction_labels = profile.get_screen_labels_by_category("distraction")
        focus_labels = profile.get_screen_labels_by_category("focus")
        borderline_labels = profile.get_screen_labels_by_category("borderline")
        neutral_labels = profile.get_screen_labels_by_category("neutral")
        
        if distraction_labels:
            prompt += "**DISTRACTION Content:**\n"
            for label_name in sorted(distraction_labels):
                label_def = profile.screen_labels[label_name]
                prompt += f"- {label_name}: {label_def.description}\n"
            prompt += "\n"
        
        if focus_labels:
            prompt += "**FOCUS Content:**\n"
            for label_name in sorted(focus_labels):
                label_def = profile.screen_labels[label_name]
                prompt += f"- {label_name}: {label_def.description}\n"
            prompt += "\n"
        
        if borderline_labels:
            prompt += "**Borderline Content:**\n"
            for label_name in sorted(borderline_labels):
                label_def = profile.screen_labels[label_name]
                prompt += f"- {label_name}: {label_def.description}\n"
            prompt += "\n"
        
        if neutral_labels:
            prompt += "**Neutral:**\n"
            for label_name in sorted(neutral_labels):
                label_def = profile.screen_labels[label_name]
                prompt += f"- {label_name}: {label_def.description}\n"
            prompt += "\n"
        
        prompt += """**Instructions:**
1. Look at visible windows, applications, and content
2. Return ONLY labels that are clearly present with high confidence
3. Multiple labels can apply if multiple windows are visible
4. Be precise in distinguishing work content from distracting content

Return as JSON:
{
  "labels": {"LabelName": confidence, ...},
  "reasoning": "detailed explanation"
}"""
        
        return prompt
    
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
            # Use response_format for structured JSON output (works with all models)
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
                "max_completion_tokens": 300,
                "response_format": {"type": "json_object"},  # Force JSON output
                "timeout": self.timeout_sec
            }
            
            # Only add temperature for models that support it
            # GPT-5 series doesn't support custom temperature, GPT-4 series does
            if not self.model.startswith("gpt-5"):
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
            
            # Log the actual response for debugging
            logger.debug(f"Vision API response for {kind}: {content[:200] if content else '(empty)'}...")
            
            # With response_format=json_object, the response should be valid JSON
            try:
                result_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Vision API response: {e}")
                logger.error(f"Content was: {content}")
                raise VisionAPIError(f"Invalid JSON in response: {e}")
            
            labels = result_data.get("labels", {})
            reasoning = result_data.get("reasoning", "")
            
            # Validate labels against profile or hardcoded taxonomy
            if self.label_profile:
                # Use profile's labels and thresholds
                if kind == "cam":
                    valid_labels = self.label_profile.get_cam_label_names()
                    thresholds = self.label_profile.get_cam_thresholds()
                else:
                    valid_labels = self.label_profile.get_screen_label_names()
                    thresholds = self.label_profile.get_screen_thresholds()
            else:
                # Fallback to hardcoded labels
                valid_labels = CAM_LABELS if kind == "cam" else SCREEN_LABELS
                thresholds = CONFIDENCE_THRESHOLDS
            
            filtered_labels = {}
            
            for label, confidence in labels.items():
                if label in valid_labels:
                    # Apply confidence threshold
                    threshold = thresholds.get(label, 0.5)
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


