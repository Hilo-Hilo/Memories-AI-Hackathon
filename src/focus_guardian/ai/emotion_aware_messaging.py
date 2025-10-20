"""
Emotion-aware messaging system for Focus Guardian.

Adapts alerts, notifications, and coaching messages based on user's
emotional state detected through Hume AI analysis.
"""

from typing import Dict, Optional, List
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmotionState(Enum):
    """Detected emotional states."""
    CALM = "calm"
    FOCUSED = "focused"
    FRUSTRATED = "frustrated"
    ANXIOUS = "anxious"
    BORED = "bored"
    TIRED = "tired"
    HAPPY = "happy"
    STRESSED = "stressed"
    UNKNOWN = "unknown"


class MessageTone(Enum):
    """Message tone styles."""
    GENTLE = "gentle"
    ENCOURAGING = "encouraging"
    ENERGIZING = "energizing"
    CALMING = "calming"
    CELEBRATORY = "celebratory"
    DIRECT = "direct"


class EmotionAwareMessenger:
    """Generates emotion-aware messages for user interactions."""

    def __init__(self):
        """Initialize emotion-aware messenger."""
        self.emotion_history: List[EmotionState] = []
        logger.info("Emotion-aware messenger initialized")

    def detect_emotion_state(self, hume_data: Optional[Dict] = None) -> EmotionState:
        """
        Detect current emotional state from Hume AI data.

        Args:
            hume_data: Recent Hume AI emotion data

        Returns:
            Detected emotion state
        """
        if not hume_data:
            return EmotionState.UNKNOWN

        # Extract dominant emotion from recent frames
        try:
            emotions = hume_data.get("recent_emotions", {})
            
            # Priority-based emotion detection
            if emotions.get("Frustration", 0) > 0.6:
                return EmotionState.FRUSTRATED
            elif emotions.get("Anxiety", 0) > 0.6:
                return EmotionState.ANXIOUS
            elif emotions.get("Boredom", 0) > 0.6:
                return EmotionState.BORED
            elif emotions.get("Tiredness", 0) > 0.6 or emotions.get("Drowsiness", 0) > 0.6:
                return EmotionState.TIRED
            elif emotions.get("Concentration", 0) > 0.6:
                return EmotionState.FOCUSED
            elif emotions.get("Joy", 0) > 0.5 or emotions.get("Satisfaction", 0) > 0.5:
                return EmotionState.HAPPY
            elif emotions.get("Stress", 0) > 0.6:
                return EmotionState.STRESSED
            elif emotions.get("Calmness", 0) > 0.5:
                return EmotionState.CALM
            else:
                return EmotionState.UNKNOWN

        except Exception as e:
            logger.error(f"Failed to detect emotion state: {e}")
            return EmotionState.UNKNOWN

    def generate_distraction_alert(
        self,
        distraction_type: str,
        duration_minutes: float,
        task_name: str,
        emotion_state: Optional[EmotionState] = None
    ) -> Dict[str, str]:
        """
        Generate emotion-aware distraction alert message.

        Args:
            distraction_type: Type of distraction detected
            duration_minutes: How long user has been distracted
            task_name: Current task name
            emotion_state: User's current emotional state

        Returns:
            Dictionary with title and message
        """
        emotion = emotion_state or EmotionState.UNKNOWN

        # Adapt message based on emotional state
        if emotion == EmotionState.FRUSTRATED:
            return {
                "title": "I Notice You're Frustrated 💭",
                "message": f"You've been away from '{task_name}' for {duration_minutes:.0f} minutes.\n\n"
                           f"Frustration is completely normal when tackling hard problems! "
                           f"Sometimes stepping away helps. If this is a break, great! 🙂\n\n"
                           f"If you got pulled away unintentionally, your work is waiting when you're ready.",
                "tone": "gentle",
                "actions": ["Take a real break (5 min)", "Back to work", "Change task"]
            }

        elif emotion == EmotionState.TIRED:
            return {
                "title": "Energy Check ⚡",
                "message": f"I see you've moved away from '{task_name}'.\n\n"
                           f"You seem tired - pushing through fatigue often leads to more distractions. "
                           f"Maybe this is your brain telling you it needs a recharge?\n\n"
                           f"A short break or some movement might help more than pushing through.",
                "tone": "caring",
                "actions": ["Take a 5-min energy break", "Continue anyway", "End session"]
            }

        elif emotion == EmotionState.BORED:
            return {
                "title": "Engagement Check 🎯",
                "message": f"You've switched away from '{task_name}' for {duration_minutes:.0f} minutes.\n\n"
                           f"This task might need a fresh approach. Consider:\n"
                           f"• Breaking it into smaller challenges\n"
                           f"• Adding a time challenge (gamify it!)\n"
                           f"• Taking a quick break and returning with new energy\n\n"
                           f"What feels right?",
                "tone": "energizing",
                "actions": ["Break it down", "Quick break", "Back to work"]
            }

        elif emotion == EmotionState.ANXIOUS:
            return {
                "title": "You've Got This 💪",
                "message": f"I notice you've moved away from '{task_name}'.\n\n"
                           f"Feeling overwhelmed? Remember: one step at a time. "
                           f"You don't have to do everything perfectly right now.\n\n"
                           f"Focus on just the next small action. You've handled harder things before!",
                "tone": "reassuring",
                "actions": ["Focus on one small step", "Take a calming break", "Refocus"]
            }

        elif emotion == EmotionState.HAPPY or emotion == EmotionState.CALM:
            return {
                "title": "Quick Check-In ✨",
                "message": f"You seem to be in a good headspace! 😊\n\n"
                           f"If this is an intentional break from '{task_name}', enjoy it! "
                           f"You've been focused for a while.\n\n"
                           f"If you got distracted unintentionally, now's a great time to refocus while "
                           f"your energy is good.",
                "tone": "friendly",
                "actions": ["This is a break", "Back to work"]
            }

        else:
            # Default message (unknown emotion)
            return {
                "title": "Focus Check 🔔",
                "message": f"You've been away from '{task_name}' for {duration_minutes:.0f} minutes.\n\n"
                           f"If this is a break, that's perfectly fine! Your brain needs rest.\n\n"
                           f"If you got pulled away unintentionally, your task is ready when you are.",
                "tone": "neutral",
                "actions": ["This is a break - remind me in 5 min", "Back to work now"]
            }

    def generate_session_start_message(self, task_name: str, user_history: Optional[Dict] = None) -> str:
        """Generate welcoming message for session start."""
        
        if user_history and user_history.get("session_count", 0) > 0:
            avg_focus = user_history.get("avg_focus_ratio", 0) * 100
            
            messages = [
                f"Welcome back! Ready to focus on '{task_name}'? 😊",
                f"Let's make this session great! Your average focus is {avg_focus:.0f}% - let's beat it! 🎯",
                f"Time to get into the zone! You've got this. 💪",
                f"Another session, another step forward. Let's do this! 🚀"
            ]
            
            # Rotate messages for variety
            import random
            return random.choice(messages)
        else:
            return f"Welcome to your first Focus Guardian session! Let's build great focus habits together. 🌟"

    def generate_break_suggestion(
        self,
        session_duration_min: float,
        emotion_state: EmotionState
    ) -> Dict[str, str]:
        """
        Generate emotion-aware break suggestion.

        Args:
            session_duration_min: How long user has been working
            emotion_state: Current emotional state

        Returns:
            Break suggestion with type and duration
        """
        suggestions = {
            EmotionState.FRUSTRATED: {
                "type": "Calming Break",
                "duration": 3,
                "activity": "🧘 Deep breathing or step outside",
                "reason": "Frustration clouds thinking. A quick reset helps you return clearer."
            },
            EmotionState.TIRED: {
                "type": "Energy Break",
                "duration": 5,
                "activity": "🚶 Quick walk or stretching",
                "reason": "Movement boosts energy better than pushing through fatigue."
            },
            EmotionState.BORED: {
                "type": "Engagement Reset",
                "duration": 2,
                "activity": "🎵 Music or quick physical movement",
                "reason": "Your brain needs novelty. A brief change resets engagement."
            },
            EmotionState.ANXIOUS: {
                "type": "Grounding Break",
                "duration": 4,
                "activity": "🧘 Box breathing (4-4-4-4) or walk",
                "reason": "Anxiety makes it hard to focus. Ground yourself first."
            },
            EmotionState.STRESSED: {
                "type": "Decompression",
                "duration": 5,
                "activity": "🌊 Step away from all screens, breathe",
                "reason": "Stress accumulates. Release it before continuing."
            },
        }

        suggestion = suggestions.get(emotion_state, {
            "type": "Standard Break",
            "duration": 3,
            "activity": "☕ Your choice - whatever refreshes you",
            "reason": f"You've been focused for {session_duration_min:.0f} minutes. Time for a reset!"
        })

        return suggestion

    def generate_completion_message(
        self,
        focus_ratio: float,
        duration_min: float,
        personal_best: bool = False,
        emotion_state: Optional[EmotionState] = None
    ) -> str:
        """
        Generate session completion message.

        Args:
            focus_ratio: Focus percentage (0-1)
            duration_min: Session duration in minutes
            personal_best: Whether this is a personal best
            emotion_state: Ending emotional state

        Returns:
            Completion message
        """
        focus_pct = focus_ratio * 100

        if personal_best:
            return (
                f"🎉 PERSONAL BEST! 🎉\n\n"
                f"You just completed your best session ever!\n"
                f"{focus_pct:.0f}% focus for {duration_min:.0f} minutes.\n\n"
                f"This is what peak performance looks like for you. Remember this feeling! ⭐"
            )

        elif focus_pct >= 85:
            return (
                f"Outstanding session! 🌟\n\n"
                f"You maintained {focus_pct:.0f}% focus for {duration_min:.0f} minutes. "
                f"That's excellent concentration! "
                f"Your focus muscle is getting stronger every day. Keep it up! 💪"
            )

        elif focus_pct >= 70:
            return (
                f"Solid work! ✓\n\n"
                f"You stayed {focus_pct:.0f}% focused for {duration_min:.0f} minutes. "
                f"Not perfect, but that's totally fine - progress over perfection! "
                f"You're building a strong focus habit. 🎯"
            )

        elif focus_pct >= 50:
            return (
                f"Session complete! 🎯\n\n"
                f"You maintained {focus_pct:.0f}% focus - there's room to improve, "
                f"but you showed up and did the work! "
                f"Each session is practice. Tomorrow's session will be even better. 📈"
            )

        else:
            # Difficult session - be extra supportive
            if emotion_state == EmotionState.FRUSTRATED:
                return (
                    f"Tough session, I know. 💭\n\n"
                    f"The frustration you felt is real - this task was challenging! "
                    f"But you stuck with it for {duration_min:.0f} minutes despite the struggle. "
                    f"That persistence matters more than the focus percentage. "
                    f"Sometimes the hard days teach us the most. 🌱"
                )
            else:
                return (
                    f"Session complete. 🎯\n\n"
                    f"This one was challenging - {focus_pct:.0f}% focus is below your usual. "
                    f"But you didn't give up! Every session builds your focus muscle, "
                    f"even the difficult ones. What can you learn from this one? 💡"
                )

    def get_intervention_tone(self, emotion_state: EmotionState) -> MessageTone:
        """Get appropriate message tone based on emotion."""
        tone_map = {
            EmotionState.FRUSTRATED: MessageTone.GENTLE,
            EmotionState.ANXIOUS: MessageTone.CALMING,
            EmotionState.BORED: MessageTone.ENERGIZING,
            EmotionState.TIRED: MessageTone.GENTLE,
            EmotionState.HAPPY: MessageTone.CELEBRATORY,
            EmotionState.CALM: MessageTone.DIRECT,
            EmotionState.FOCUSED: MessageTone.ENCOURAGING,
            EmotionState.STRESSED: MessageTone.CALMING,
        }

        return tone_map.get(emotion_state, MessageTone.DIRECT)

