"""
AI-powered session summary generator using GPT-4.

Generates beautiful, personalized, encouraging summaries of focus sessions
that feel human and supportive rather than robotic.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from openai import OpenAI

from ..core.database import Database
from ..core.models import Session, SessionReport
from ..utils.logger import get_logger, log_performance, TimerContext

logger = get_logger(__name__)


class AISummaryGenerator:
    """Generates AI-powered session summaries using GPT-4."""

    def __init__(self, api_key: str, database: Optional[Database] = None):
        """
        Initialize AI summary generator.

        Args:
            api_key: OpenAI API key
            database: Optional database for loading user history
        """
        self.client = OpenAI(api_key=api_key)
        self.database = database
        self.model = "gpt-5-nano"  # Cheapest option for text summaries ($0.05/1M input)

        logger.info("AI summary generator initialized")

    def generate_session_summary(
        self,
        session: Session,
        report_data: Dict[str, Any],
        emotion_data: Optional[Dict[str, Any]] = None,
        include_history: bool = True
    ) -> Dict[str, str]:
        """
        Generate beautiful AI summary for a session.

        Args:
            session: Session object
            report_data: Session report data (KPIs, events, etc.)
            emotion_data: Optional Hume AI emotion data
            include_history: Whether to include user history for personalization

        Returns:
            Dictionary with summary types:
            - executive: 2-3 sentence overview
            - detailed: Paragraph with insights
            - highlights: Bullet points of key moments
            - encouragement: Motivational message
        """
        with TimerContext(logger, "generate_ai_summary"):
            # Build context for GPT-4
            context = self._build_session_context(session, report_data, emotion_data, include_history)

            # Generate summary
            summary = self._call_gpt4_for_summary(context)

            logger.info(f"Generated AI summary for session {session.session_id}")
            return summary

    def _build_session_context(
        self,
        session: Session,
        report_data: Dict[str, Any],
        emotion_data: Optional[Dict[str, Any]],
        include_history: bool
    ) -> str:
        """Build context prompt for GPT-4."""
        
        # Extract key metrics
        duration_min = report_data.get("meta", {}).get("total_duration_minutes", 0)
        focus_ratio = report_data.get("kpis", {}).get("focus_ratio", 0) * 100
        num_distractions = report_data.get("kpis", {}).get("num_alerts", 0)
        
        # Safely get snapshot count
        segments = report_data.get("segments", [])
        num_snapshots = len(segments[0].get("snapshot_refs", [])) if segments else 0

        # Build emotional context
        emotion_summary = ""
        if emotion_data:
            primary_emotion = emotion_data.get("primary_emotion", "unknown")
            emotion_changes = emotion_data.get("transitions", [])
            emotion_summary = f"\n\nEmotional Journey: Started {primary_emotion}, {len(emotion_changes)} mood shifts during session."

        # User history context
        history_context = ""
        if include_history and self.database:
            history_context = self._get_user_history_context(session)

        # Build full context
        context = f"""You are a supportive ADHD coach analyzing a focus session.

**Session Details:**
- Task: {session.task_name}
- Duration: {duration_min:.0f} minutes
- Focus Ratio: {focus_ratio:.0f}%
- Distractions: {num_distractions}
- Snapshots Analyzed: {num_snapshots}
{emotion_summary}

**Task Context:**
{self._infer_task_type(session.task_name)}

{history_context}

**Your Role:**
You're an encouraging coach who celebrates wins, is gentle with challenges, and provides specific, actionable insights.

**Guidelines:**
- Be warm and supportive (use emojis sparingly but effectively)
- Focus on progress and patterns, not just results
- Frame distractions as learning opportunities
- Provide specific insights based on the data
- Keep it concise but meaningful
- Use "you" and "your" to make it personal
"""
        return context

    def _infer_task_type(self, task_name: str) -> str:
        """Infer task type from task name for better context."""
        task_lower = task_name.lower()
        
        if any(word in task_lower for word in ["code", "coding", "debug", "api", "backend", "frontend", "programming"]):
            return "Task Type: Technical/Coding (requires deep focus, Stack Overflow is productive)"
        elif any(word in task_lower for word in ["write", "writing", "blog", "article", "documentation", "docs"]):
            return "Task Type: Writing (requires sustained concentration, research breaks are normal)"
        elif any(word in task_lower for word in ["study", "learn", "reading", "research"]):
            return "Task Type: Learning (context switching to multiple sources is expected)"
        elif any(word in task_lower for word in ["design", "ui", "ux", "graphic"]):
            return "Task Type: Creative/Design (inspiration breaks are valuable)"
        else:
            return "Task Type: General focus work"

    def _get_user_history_context(self, session: Session) -> str:
        """Get user's historical context for personalization."""
        try:
            # Get recent sessions (last 10)
            recent_sessions = self.database.get_all_sessions(limit=10)
            
            if len(recent_sessions) < 2:
                return ""

            # Calculate averages
            total_focus = sum(s.focus_ratio for s in recent_sessions if hasattr(s, 'focus_ratio') and s.focus_ratio) / len(recent_sessions) if recent_sessions else 0
            avg_duration = sum((s.ended_at - s.started_at).total_seconds() / 60 for s in recent_sessions if s.ended_at) / len(recent_sessions)

            # Find best session
            best_focus = max((s.focus_ratio for s in recent_sessions if hasattr(s, 'focus_ratio') and s.focus_ratio), default=0)

            return f"""
**User History (for personalization):**
- Average focus ratio: {total_focus * 100:.0f}%
- Average session length: {avg_duration:.0f} minutes
- Personal best focus: {best_focus * 100:.0f}%
- Total sessions completed: {len(recent_sessions)}

Use this to provide comparative insights ("better than your average", "approaching your personal best", etc.)
"""
        except Exception as e:
            logger.error(f"Failed to get user history: {e}")
            return ""

    def _call_gpt4_for_summary(self, context: str) -> Dict[str, str]:
        """Call GPT-4 to generate summaries."""
        
        try:
            # Generate executive summary
            executive_prompt = f"""{context}

Generate a brief, encouraging 2-3 sentence executive summary of this session.
Focus on the positive while being honest about challenges.
Make it feel personal and meaningful."""

            executive_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": executive_prompt}],
                max_tokens=150,
                temperature=0.7
            )
            executive = executive_response.choices[0].message.content.strip()

            # Generate detailed summary
            detailed_prompt = f"""{context}

Generate a detailed paragraph summary (4-6 sentences) that:
1. Highlights what went well
2. Identifies any challenges
3. Notes interesting patterns
4. Provides one specific, actionable insight

Be warm, specific, and data-driven."""

            detailed_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": detailed_prompt}],
                max_tokens=300,
                temperature=0.7
            )
            detailed = detailed_response.choices[0].message.content.strip()

            # Generate highlights
            highlights_prompt = f"""{context}

Generate 3-4 highlight bullet points for this session.
Focus on specific moments or patterns.
Use emojis for visual interest.
Format as markdown list."""

            highlights_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": highlights_prompt}],
                max_tokens=200,
                temperature=0.7
            )
            highlights = highlights_response.choices[0].message.content.strip()

            # Generate encouragement
            encouragement_prompt = f"""{context}

Generate a brief (1-2 sentences) encouraging message.
If the session went well, celebrate it!
If there were struggles, frame them as growth opportunities.
Be genuinely supportive."""

            encouragement_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": encouragement_prompt}],
                max_tokens=100,
                temperature=0.8  # Higher temp for more varied encouragement
            )
            encouragement = encouragement_response.choices[0].message.content.strip()

            return {
                "executive": executive,
                "detailed": detailed,
                "highlights": highlights,
                "encouragement": encouragement
            }

        except Exception as e:
            logger.error(f"Failed to generate AI summary: {e}", exc_info=True)
            # Return fallback summaries
            return self._generate_fallback_summary(context)

    def _generate_fallback_summary(self, context: str) -> Dict[str, str]:
        """Generate simple fallback summaries if GPT-4 fails."""
        return {
            "executive": "Session completed successfully. Review the detailed statistics for more insights.",
            "detailed": "This session has been recorded and analyzed. Check the session statistics and timeline for details about your focus patterns.",
            "highlights": "- Session completed\n- Data analyzed\n- Report generated",
            "encouragement": "Good work on completing this session! Keep building your focus habit."
        }

    def generate_comparative_insight(
        self,
        current_session: Session,
        report_data: Dict[str, Any]
    ) -> str:
        """
        Generate AI insight comparing current session to user history.

        Args:
            current_session: Current session
            report_data: Current session report data

        Returns:
            Comparative insight text
        """
        if not self.database:
            return ""

        try:
            # Get recent sessions for comparison
            recent_sessions = self.database.get_all_sessions(limit=10)
            
            if len(recent_sessions) < 2:
                return "This is one of your first sessions. Keep going to unlock personalized insights!"

            # Calculate metrics
            current_focus = report_data.get("kpis", {}).get("focus_ratio", 0) * 100
            current_duration = report_data.get("meta", {}).get("total_duration_minutes", 0)

            # Historical averages
            avg_focus = sum(getattr(s, 'focus_ratio', 0) for s in recent_sessions) / len(recent_sessions) * 100
            avg_duration = sum((s.ended_at - s.started_at).total_seconds() / 60 for s in recent_sessions if s.ended_at) / len(recent_sessions)

            # Build comparison prompt
            prompt = f"""Generate a brief, encouraging comparative insight:

Current Session:
- Focus: {current_focus:.0f}%
- Duration: {current_duration:.0f} min

Your Recent Average:
- Focus: {avg_focus:.0f}%
- Duration: {avg_duration:.0f} min

Generate 1-2 sentences highlighting:
- How this session compares (better/similar/different)
- Any notable improvements or trends
- Encouraging spin

Be specific with numbers, warm in tone."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Failed to generate comparative insight: {e}")
            return ""

