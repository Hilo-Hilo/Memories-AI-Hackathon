"""
Comprehensive AI report generator using all available data sources.

Integrates:
- Hume AI emotion analysis
- Memories.ai pattern detection
- OpenAI Vision snapshot results
- Historical session trends
- GPT-4 for long-form narrative report generation
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from openai import OpenAI

from ..core.database import Database
from ..core.models import Session
from ..utils.logger import get_logger, TimerContext

logger = get_logger(__name__)


class ComprehensiveReportGenerator:
    """Generates comprehensive AI-powered reports using all data sources."""

    def __init__(self, api_key: str, database: Database):
        """
        Initialize comprehensive report generator.

        Args:
            api_key: OpenAI API key
            database: Database for accessing session data and history
        """
        self.client = OpenAI(api_key=api_key)
        self.database = database
        self.model = "gpt-5-nano"  # Cheapest option with intelligent context management

        logger.info("Comprehensive AI report generator initialized")

    def generate_comprehensive_report(
        self,
        session_id: str,
        hume_results: Optional[Dict] = None,
        memories_results: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive AI report combining all data sources.

        Args:
            session_id: Session ID to generate report for
            hume_results: Hume AI emotion analysis results
            memories_results: Memories.ai pattern analysis results

        Returns:
            Dictionary with comprehensive report sections
        """
        with TimerContext(logger, "generate_comprehensive_report"):
            logger.info(f"Generating comprehensive AI report for session {session_id}")

            # Gather all data sources
            context = self._gather_all_data(session_id, hume_results, memories_results)

            # Generate comprehensive narrative report
            report = self._generate_narrative_report(context)

            logger.info("Comprehensive AI report generated")
            return report

    def _gather_all_data(
        self,
        session_id: str,
        hume_results: Optional[Dict],
        memories_results: Optional[Dict]
    ) -> Dict[str, Any]:
        """Gather all available data for report generation."""
        
        # Current session data
        session = self.database.get_session(session_id)
        report_data = self.database.get_session_report(session_id)
        events = self.database.get_session_events(session_id)
        snapshots = self.database.get_snapshots_for_session(session_id)

        # Historical data (past week)
        week_sessions = self._get_historical_sessions(days=7)
        month_sessions = self._get_historical_sessions(days=30)

        # Calculate historical trends
        week_trends = self._calculate_trends(week_sessions)
        month_trends = self._calculate_trends(month_sessions)

        return {
            "session": {
                "id": session_id,
                "task_name": session.task_name if session else "Unknown",
                "duration_min": (session.ended_at - session.started_at).total_seconds() / 60 if session and session.ended_at else 0,
                "started_at": session.started_at.isoformat() if session else None,
                "ended_at": session.ended_at.isoformat() if session and session.ended_at else None
            },
            "kpis": report_data.get("kpis", {}) if report_data else {},
            "events": [
                {
                    "type": e.event_type,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "data": e.event_data
                }
                for e in events
            ],
            "snapshots_count": len(snapshots),
            "hume_analysis": hume_results or {},
            "memories_analysis": memories_results or {},
            "historical_trends": {
                "week": week_trends,
                "month": month_trends
            }
        }

    def _get_historical_sessions(self, days: int) -> List[Session]:
        """Get sessions from the past N days."""
        all_sessions = self.database.get_all_sessions(limit=100)
        cutoff = datetime.now() - timedelta(days=days)
        
        return [s for s in all_sessions if s.started_at >= cutoff]

    def _calculate_trends(self, sessions: List[Session]) -> Dict[str, Any]:
        """Calculate statistical trends from session list."""
        if not sessions:
            return {
                "count": 0,
                "avg_duration_min": 0,
                "avg_focus_ratio": 0,
                "total_time_min": 0
            }

        total_duration = sum(
            (s.ended_at - s.started_at).total_seconds() / 60
            for s in sessions if s.ended_at
        )
        
        avg_duration = total_duration / len(sessions) if sessions else 0
        
        # Get focus ratios from reports
        focus_ratios = []
        for s in sessions:
            report = self.database.get_session_report(s.session_id)
            if report and report.get("kpis"):
                focus_ratios.append(report["kpis"].get("focus_ratio", 0))
        
        avg_focus = sum(focus_ratios) / len(focus_ratios) if focus_ratios else 0

        return {
            "count": len(sessions),
            "avg_duration_min": avg_duration,
            "avg_focus_ratio": avg_focus,
            "total_time_min": total_duration,
            "sessions": [s.task_name for s in sessions[:5]]  # Last 5 task names
        }

    def _generate_narrative_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate narrative report using GPT-4."""
        
        # Build comprehensive prompt
        prompt = self._build_comprehensive_prompt(context)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,  # Long-form report
                temperature=0.7
            )

            report_text = response.choices[0].message.content

            return {
                "generated_at": datetime.now().isoformat(),
                "session_id": context["session"]["id"],
                "report_text": report_text,
                "data_sources": {
                    "hume_ai": bool(context.get("hume_analysis")),
                    "memories_ai": bool(context.get("memories_analysis")),
                    "historical_data": True,
                    "snapshot_analysis": context.get("snapshots_count", 0) > 0
                },
                "token_usage": response.usage.total_tokens if response.usage else 0
            }

        except Exception as e:
            logger.error(f"Failed to generate comprehensive report: {e}", exc_info=True)
            return {
                "generated_at": datetime.now().isoformat(),
                "session_id": context["session"]["id"],
                "report_text": "Failed to generate AI report. Please try again.",
                "error": str(e)
            }

    def _build_comprehensive_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for GPT-4 report generation."""
        
        session = context["session"]
        kpis = context["kpis"]
        hume = context.get("hume_analysis", {})
        memories = context.get("memories_analysis", {})
        week_trends = context["historical_trends"]["week"]
        month_trends = context["historical_trends"]["month"]

        prompt = f"""You are an expert ADHD coach analyzing a focus session with comprehensive AI data.

## SESSION OVERVIEW
**Task:** {session['task_name']}
**Duration:** {session['duration_min']:.0f} minutes
**Focus Ratio:** {kpis.get('focus_ratio', 0) * 100:.0f}%
**Distractions:** {kpis.get('num_alerts', 0)}
**Snapshots Analyzed:** {context['snapshots_count']}

## HISTORICAL CONTEXT

**Past Week ({week_trends['count']} sessions):**
- Average Focus: {week_trends['avg_focus_ratio'] * 100:.0f}%
- Average Duration: {week_trends['avg_duration_min']:.0f} min
- Total Focus Time: {week_trends['total_time_min']:.0f} min
- Recent Tasks: {', '.join(week_trends.get('sessions', [])[:3])}

**Past Month ({month_trends['count']} sessions):**
- Average Focus: {month_trends['avg_focus_ratio'] * 100:.0f}%
- Average Duration: {month_trends['avg_duration_min']:.0f} min
- Total Focus Time: {month_trends['total_time_min']:.0f} min

## EMOTION ANALYSIS (Hume AI)
{self._summarize_hume_data(hume) if hume else "Not available"}

## PATTERN ANALYSIS (Memories.ai)
{self._summarize_memories_data(memories) if memories else "Not available"}

## DISTRACTION EVENTS
{self._summarize_events(context.get('events', []))}

## YOUR TASK

Generate a **comprehensive, long-form report** (800-1200 words) that:

1. **Session Story** - Tell the narrative of this session
   - How did it go?
   - What patterns emerged?
   - Key moments and turning points

2. **Emotional Journey** (if Hume AI data available)
   - How emotions evolved during the session
   - Correlation between emotions and focus
   - Emotional triggers for distraction

3. **Behavioral Patterns** (if Memories.ai data available)
   - What activities dominated?
   - Distraction triggers
   - Productive vs unproductive patterns

4. **Historical Comparison**
   - How does this session compare to past week?
   - How does it compare to past month?
   - Are you improving or struggling?
   - Notable trends (better/worse times, tasks, etc.)

5. **Deep Insights**
   - Non-obvious patterns you discover
   - Correlations between factors
   - What's working well?
   - What needs improvement?

6. **Actionable Recommendations**
   - Specific, personalized strategies
   - Based on YOUR actual data, not generic advice
   - Short-term (next session)
   - Long-term (next week/month)

7. **Encouragement & Motivation**
   - Celebrate wins (even small ones)
   - Frame challenges as growth opportunities
   - Keep it positive and supportive

## TONE & STYLE

- **Personal:** Use "you" and "your" - this is about THEM
- **Data-driven:** Reference specific numbers and patterns
- **Supportive:** Be encouraging, not judgmental
- **Insightful:** Go beyond surface-level observations
- **Actionable:** Every insight should have a "what next"

## FORMAT

Return as markdown with clear sections, headers, and formatting.
Use emojis sparingly but effectively.
Make it feel like a coaching session, not a data dump.

Be honest about challenges while celebrating progress.
This person is building a focus practice - help them see their growth!"""

        return prompt
    
    def _summarize_hume_data(self, hume: Dict) -> str:
        """Intelligently summarize Hume AI data - keep under 200 tokens."""
        if not hume:
            return "Not available"
        
        summary = hume.get('summary', {})
        if summary:
            # Extract only top 3 emotions with highest mean values
            top_emotions = sorted(
                [(k, v.get('mean', 0)) for k, v in summary.items() if isinstance(v, dict)],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            return "Key emotions: " + ", ".join([f"{name}({val:.1f})" for name, val in top_emotions])
        
        return f"{hume.get('frame_count', 0)} frames analyzed"
    
    def _summarize_memories_data(self, memories: Dict) -> str:
        """Intelligently summarize Memories.ai data - keep under 300 tokens."""
        if not memories:
            return "Not available"
        
        # Extract ONLY the key insights, not full report
        report = memories.get('markdown_report', '')
        
        # Find key sections (insights, patterns, recommendations)
        lines = report.split('\n')
        key_points = []
        
        for line in lines[:30]:  # Only first 30 lines
            if any(keyword in line.lower() for keyword in ['insight', 'pattern', 'detected', 'primarily', 'focus']):
                key_points.append(line.strip())
                if len(key_points) >= 5:  # Max 5 key points
                    break
        
        if key_points:
            return '\n'.join(key_points[:5])
        
        # Fallback: first 200 chars only
        return report[:200] + "..."
    
    def _summarize_events(self, events: List[Dict]) -> str:
        """Intelligently summarize events - keep under 150 tokens."""
        if not events:
            return "No events"
        
        distraction_events = [e for e in events if e.get('type') == 'distraction']
        if not distraction_events:
            return "No distractions"
        
        # Ultra-compact format
        summary = f"{len(distraction_events)} distractions: "
        types = {}
        for e in distraction_events:
            dtype = e.get('data', {}).get('distraction_type', 'Unknown')
            types[dtype] = types.get(dtype, 0) + 1
        
        summary += ", ".join([f"{count}x {dtype}" for dtype, count in types.items()])
        return summary

    def save_comprehensive_report(
        self,
        session_id: str,
        report: Dict[str, Any]
    ) -> Path:
        """Save comprehensive report to session folder."""
        try:
            from pathlib import Path
            
            # Get session directory
            session_dir = Path(self.database.get_session(session_id).cam_mp4_path).parent if self.database.get_session(session_id) else None
            
            if not session_dir:
                # Fallback to constructing path
                data_dir = Path("data/sessions")  # Will be replaced with config
                session_dir = data_dir / session_id
            
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Save report
            report_file = session_dir / "comprehensive_ai_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Comprehensive AI report saved to {report_file}")
            return report_file
            
        except Exception as e:
            logger.error(f"Failed to save comprehensive report: {e}", exc_info=True)
            raise

