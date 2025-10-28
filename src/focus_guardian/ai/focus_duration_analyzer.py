"""
Optimal Focus Duration Analyzer.

Analyzes historical distraction patterns to recommend optimal focus block durations.
"""

from typing import Optional, List, Tuple
from statistics import mean, median
from datetime import datetime, timedelta

from ..core.database import Database
from ..core.models import Session
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FocusDurationAnalyzer:
    """Analyzes past sessions to recommend optimal focus durations."""
    
    def __init__(
        self,
        database: Database,
        min_sessions: int = 3,
        lookback_days: int = 30,
        recommendation_factor: float = 0.75  # Recommend 75% of typical first distraction time
    ):
        """
        Initialize focus duration analyzer.
        
        Args:
            database: Database interface
            min_sessions: Minimum number of sessions needed for recommendation
            lookback_days: Days to look back for historical data
            recommendation_factor: Factor to apply to mean first distraction time
        """
        self.database = database
        self.min_sessions = min_sessions
        self.lookback_days = lookback_days
        self.recommendation_factor = recommendation_factor
        
        logger.info(
            f"Focus duration analyzer initialized "
            f"(min_sessions={min_sessions}, lookback={lookback_days} days, factor={recommendation_factor})"
        )
    
    def analyze_and_recommend(self) -> Optional[dict]:
        """
        Analyze historical sessions and generate recommendation.
        
        Returns:
            Dictionary with recommendation data, or None if insufficient data:
            {
                "first_distraction_mean_minutes": float,
                "first_distraction_median_minutes": float,
                "recommended_duration_minutes": int,
                "sessions_analyzed": int,
                "confidence": str,  # "high", "medium", "low"
                "message": str
            }
        """
        # Get historical sessions
        sessions = self.database.get_sessions_with_distractions(limit=50)
        
        # Filter by lookback window
        cutoff_date = datetime.now() - timedelta(days=self.lookback_days)
        recent_sessions = [
            s for s in sessions 
            if s.started_at >= cutoff_date and s.status.value == "completed"
        ]
        
        if len(recent_sessions) < self.min_sessions:
            logger.debug(
                f"Insufficient data: {len(recent_sessions)} sessions "
                f"(need {self.min_sessions})"
            )
            return None
        
        # Get first distraction times for each session
        first_distraction_times = []
        for session in recent_sessions:
            time_to_first = self.database.get_first_distraction_time(session.session_id)
            if time_to_first is not None:
                first_distraction_times.append(time_to_first)
        
        if len(first_distraction_times) < self.min_sessions:
            logger.debug(f"Insufficient distraction data: {len(first_distraction_times)} events")
            return None
        
        # Calculate statistics (times in minutes)
        times_minutes = [t / 60.0 for t in first_distraction_times]
        mean_time = mean(times_minutes)
        median_time = median(times_minutes)
        
        # Generate recommendation (80% of median for safety)
        recommended_minutes = int(median_time * self.recommendation_factor)
        
        # Ensure minimum of 5 minutes
        recommended_minutes = max(5, recommended_minutes)
        
        # Determine confidence level
        if len(first_distraction_times) >= 10:
            confidence = "high"
        elif len(first_distraction_times) >= 5:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Generate message
        if recommended_minutes < 10:
            message = f"Based on your past sessions, you typically start getting distracted after ~{median_time:.0f} minutes. We recommend short {recommended_minutes}-minute focus blocks for optimal productivity."
        elif recommended_minutes < 25:
            message = f"Based on your past {len(recent_sessions)} sessions, your typical first distraction occurs around {median_time:.0f} minutes. We recommend {recommended_minutes}-minute focus blocks to maximize your productivity."
        else:
            message = f"Based on your past sessions, you maintain focus well for about {median_time:.0f} minutes. We recommend longer {recommended_minutes}-minute focus blocks."
        
        logger.info(
            f"Generated focus recommendation: {recommended_minutes} minutes "
            f"(mean: {mean_time:.1f}, median: {median_time:.1f} min, sessions: {len(recent_sessions)})"
        )
        
        return {
            "first_distraction_mean_minutes": round(mean_time, 1),
            "first_distraction_median_minutes": round(median_time, 1),
            "recommended_duration_minutes": recommended_minutes,
            "sessions_analyzed": len(recent_sessions),
            "confidence": confidence,
            "message": message
        }
    
    def get_dashboard_insight(self) -> Optional[str]:
        """
        Get a short insight message for the dashboard.
        
        Returns:
            Short recommendation message or None
        """
        recommendation = self.analyze_and_recommend()
        
        if not recommendation:
            return None
        
        return f"💡 Recommended focus blocks: {recommendation['recommended_duration_minutes']} minutes"

