"""
Session report generator with schema v1.3.

Generates comprehensive session reports by combining:
- Realtime OpenAI Vision snapshot results
- Post-hoc Hume AI emotion analysis
- Post-hoc Memories.ai pattern analysis
"""

import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

from ..core.database import Database
from ..core.models import (
    SessionReport, SessionMeta, Segment, SegmentLabel,
    KPIs, Recommendation, Artifacts,
    AppUsage, DistractionDetail, PostureAnalysis, ExpressionAnalysis
)
from ..integrations.hume_client import HumeExpressionClient
from ..integrations.memories_client import MemoriesClient
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """Generates session reports with schema v1.3."""
    
    def __init__(
        self,
        database: Database,
        hume_client: Optional[HumeExpressionClient] = None,
        memories_client: Optional[MemoriesClient] = None
    ):
        """
        Initialize report generator.
        
        Args:
            database: Database interface
            hume_client: Optional Hume AI client for emotion analysis
            memories_client: Optional Memories.ai client for pattern analysis
        """
        self.database = database
        self.hume_client = hume_client
        self.memories_client = memories_client
        
        logger.info("Report generator initialized")
    
    def generate(self, session_id: str, data_dir: Path) -> SessionReport:
        """
        Generate session report from local data.
        
        Args:
            session_id: Session ID to generate report for
            data_dir: Data directory containing session files
            
        Returns:
            SessionReport object
        """
        logger.info(f"Generating report for session: {session_id}")
        
        # Get session from database
        session = self.database.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Get all events
        events = self.database.get_session_events(session_id)
        
        # Get all snapshots
        snapshots = self.database.get_snapshots_for_session(session_id)
        
        # Generate metadata
        meta = self._generate_meta(session)
        
        # Generate segments from events and snapshots
        segments = self._generate_segments(session, events, snapshots)
        
        # Calculate KPIs
        kpis = self._calculate_kpis(session, events)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(kpis, events)
        
        # Create artifacts placeholder
        artifacts = Artifacts(
            memories_urls={},
            hume_job_id=None
        )
        
        report = SessionReport(
            session_id=session_id,
            meta=meta,
            segments=segments,
            kpis=kpis,
            recommendations=recommendations,
            artifacts=artifacts
        )
        
        # Save report to database
        self.database.store_session_report(session_id, report)
        
        logger.info(f"Report generated: {len(segments)} segments, {kpis.num_alerts} alerts")
        
        return report
    
    def _generate_meta(self, session) -> SessionMeta:
        """Generate session metadata."""
        duration = 0.0
        if session.started_at and session.ended_at:
            duration = (session.ended_at - session.started_at).total_seconds() / 60.0
        
        return SessionMeta(
            started_at=session.started_at.isoformat(),
            ended_at=session.ended_at.isoformat() if session.ended_at else datetime.now().isoformat(),
            profile=session.quality_profile.value,
            total_duration_minutes=duration,
            snapshot_interval_sec=5  # TODO: Get from config
        )
    
    def _generate_segments(self, session, events, snapshots) -> List[Segment]:
        """Generate session segments from events."""
        segments = []
        
        if not session.started_at:
            return segments
        
        # Simple segmentation: create one segment per distraction
        # and fill gaps with focus segments
        
        session_start = session.started_at
        session_end = session.ended_at or datetime.now()
        
        if not events:
            # No distractions - entire session is focus
            segment = Segment(
                t0=0.0,
                t1=(session_end - session_start).total_seconds(),
                label=SegmentLabel.FOCUS,
                task_hypothesis=session.task_name,
                apps=[AppUsage(app_class="Code", share=1.0)],
                distractions=[],
                snapshot_refs=[]
            )
            segments.append(segment)
        else:
            # Create segments from events
            current_time = 0.0
            
            for event in sorted(events, key=lambda e: e.started_at):
                event_start = (event.started_at - session_start).total_seconds()
                event_end = (event.ended_at - session_start).total_seconds()
                
                # Add focus segment before distraction (if gap exists)
                if event_start > current_time:
                    segments.append(Segment(
                        t0=current_time,
                        t1=event_start,
                        label=SegmentLabel.FOCUS,
                        task_hypothesis=session.task_name,
                        apps=[AppUsage(app_class="Code", share=1.0)],
                        distractions=[],
                        snapshot_refs=[]
                    ))
                
                # Add distraction segment
                distraction_detail = DistractionDetail(
                    t0=event_start,
                    t1=event_end,
                    distraction_type=event.event_type.value,
                    evidence=event.evidence,
                    vision_votes=event.vision_votes
                )
                
                segments.append(Segment(
                    t0=event_start,
                    t1=event_end,
                    label=SegmentLabel.FOCUS,  # Mark as admin/distraction
                    task_hypothesis="Distracted",
                    apps=[],
                    distractions=[distraction_detail],
                    snapshot_refs=event.snapshot_refs
                ))
                
                current_time = event_end
            
            # Add final focus segment if needed
            session_duration = (session_end - session_start).total_seconds()
            if current_time < session_duration:
                segments.append(Segment(
                    t0=current_time,
                    t1=session_duration,
                    label=SegmentLabel.FOCUS,
                    task_hypothesis=session.task_name,
                    apps=[],
                    distractions=[],
                    snapshot_refs=[]
                ))
        
        return segments
    
    def _calculate_kpis(self, session, events) -> KPIs:
        """Calculate key performance indicators."""
        # Total session time
        if session.started_at and session.ended_at:
            total_time = (session.ended_at - session.started_at).total_seconds()
        else:
            total_time = 0.0
        
        # Total distraction time
        total_distraction_time = sum(e.duration_seconds for e in events)
        
        # Focus ratio
        focus_ratio = 1.0
        if total_time > 0:
            focus_ratio = max(0.0, (total_time - total_distraction_time) / total_time)
        
        # Average focus bout (time between distractions)
        if len(events) > 0 and total_time > 0:
            num_focus_bouts = len(events) + 1
            total_focus_time = total_time - total_distraction_time
            avg_focus_bout = total_focus_time / num_focus_bouts / 60.0  # Convert to minutes
        else:
            avg_focus_bout = total_time / 60.0 if total_time > 0 else 0.0
        
        # Top triggers (most common distraction types)
        distraction_types = [e.event_type.value for e in events]
        from collections import Counter
        top_triggers = [t for t, _ in Counter(distraction_types).most_common(3)]
        
        # Peak distraction hour (simplified - just use first event hour)
        peak_hour = "N/A"
        if events:
            first_event = events[0]
            hour = first_event.started_at.hour
            peak_hour = f"{hour:02d}:00-{hour+1:02d}:00"
        
        return KPIs(
            focus_ratio=focus_ratio,
            avg_focus_bout_min=avg_focus_bout,
            num_alerts=len(events),
            top_triggers=top_triggers,
            peak_distraction_hour=peak_hour
        )
    
    def _generate_recommendations(self, kpis: KPIs, events) -> List[Recommendation]:
        """Generate personalized recommendations."""
        recommendations = []
        
        # Low focus ratio
        if kpis.focus_ratio < 0.7:
            recommendations.append(Recommendation(
                rec_type="BreakSchedule",
                message=f"Your focus ratio is {kpis.focus_ratio:.0%}. Try scheduling regular "
                        f"5-minute breaks every 25 minutes (Pomodoro technique).",
                priority=1
            ))
        
        # Frequent alerts
        if kpis.num_alerts >= 3:
            recommendations.append(Recommendation(
                rec_type="TaskSplit",
                message=f"You had {kpis.num_alerts} distraction alerts. Consider breaking "
                        f"your task into smaller, more manageable chunks.",
                priority=2
            ))
        
        # Specific distraction types
        if "Video" in kpis.top_triggers or "Social" in kpis.top_triggers:
            recommendations.append(Recommendation(
                rec_type="AppBlock",
                message="Video and social media are your main distractors. Consider using "
                        "a website blocker during focus sessions.",
                priority=1
            ))
        
        return recommendations
    
    def generate_with_cloud_analysis(
        self,
        session_id: str,
        data_dir: Path,
        run_hume: bool = False,
        run_memories: bool = False
    ) -> SessionReport:
        """
        Generate report with optional cloud analysis.
        
        Args:
            session_id: Session ID
            data_dir: Data directory
            run_hume: Whether to run Hume AI analysis
            run_memories: Whether to run Memories.ai analysis
            
        Returns:
            SessionReport with cloud data merged
        """
        # Generate base report from local data
        report = self.generate(session_id, data_dir)
        
        session = self.database.get_session(session_id)
        if not session:
            return report
        
        # Run Hume AI emotion analysis if enabled
        hume_data = None
        if run_hume and self.hume_client:
            cam_video = Path(session.cam_mp4_path)
            if cam_video.exists():
                logger.info("Running Hume AI emotion analysis...")
                hume_data = self.hume_client.analyze_video_sync(cam_video)
                
                if hume_data:
                    report.artifacts.hume_job_id = hume_data.get("job_id")
                    logger.info("Hume AI analysis completed")
        
        # Run Memories.ai analysis if enabled
        memories_data = None
        if run_memories and self.memories_client:
            cam_video = Path(session.cam_mp4_path)
            screen_video = Path(session.screen_mp4_path) if session.screen_mp4_path else None
            snapshots_dir = Path(session.snapshots_dir)
            
            if cam_video.exists() and screen_video and screen_video.exists():
                logger.info("Running Memories.ai pattern analysis...")
                memories_data = self.memories_client.analyze_session(
                    cam_video, screen_video, snapshots_dir
                )
                
                if memories_data:
                    logger.info("Memories.ai analysis completed")
        
        # Merge cloud data if available
        if hume_data or memories_data:
            report = self.merge_cloud_data(report, memories_data, hume_data)
        
        # Update database with final report
        self.database.store_session_report(session_id, report)
        
        return report
    
    def merge_cloud_data(
        self,
        base_report: SessionReport,
        memories_data: Optional[Dict],
        hume_data: Optional[Dict]
    ) -> SessionReport:
        """
        Merge cloud analysis with base report.
        
        Args:
            base_report: Base report from local data
            memories_data: Memories.ai analysis results
            hume_data: Hume AI emotion timeline
            
        Returns:
            Updated SessionReport
        """
        logger.info("Merging cloud analysis data with base report")
        
        # Merge Hume AI emotion data into segments
        if hume_data:
            emotion_summary = hume_data.get("summary", {})
            
            for segment in base_report.segments:
                segment.expressions = ExpressionAnalysis(
                    frustration_mean=emotion_summary.get("avg_frustration", 0.0),
                    valence_mean=emotion_summary.get("avg_valence", 0.0),
                    arousal_mean=emotion_summary.get("avg_arousal", 0.0)
                )
        
        # Merge Memories.ai insights
        if memories_data:
            insights = memories_data.get("insights", {})
            
            # Update KPIs with Memories.ai data (if higher confidence)
            if insights.get("focus_ratio") is not None:
                # Weighted average: 70% local, 30% Memories.ai
                base_report.kpis.focus_ratio = (
                    0.7 * base_report.kpis.focus_ratio +
                    0.3 * insights["focus_ratio"]
                )
        
        logger.info("Cloud data merged successfully")
        return base_report
    
    def export_to_json(self, report: SessionReport, output_path: Path) -> None:
        """
        Export report to JSON file.
        
        Args:
            report: SessionReport to export
            output_path: Path to save JSON file
        """
        # Convert report to dict (simplified for now)
        report_dict = {
            "session_id": report.session_id,
            "meta": {
                "started_at": report.meta.started_at,
                "ended_at": report.meta.ended_at,
                "profile": report.meta.profile,
                "total_duration_minutes": report.meta.total_duration_minutes,
                "snapshot_interval_sec": report.meta.snapshot_interval_sec
            },
            "kpis": {
                "focus_ratio": report.kpis.focus_ratio,
                "avg_focus_bout_min": report.kpis.avg_focus_bout_min,
                "num_alerts": report.kpis.num_alerts,
                "top_triggers": report.kpis.top_triggers,
                "peak_distraction_hour": report.kpis.peak_distraction_hour
            },
            "recommendations": [
                {
                    "type": rec.rec_type,
                    "message": rec.message,
                    "priority": rec.priority
                }
                for rec in report.recommendations
            ],
            "segments": len(report.segments),
            "artifacts": {
                "hume_job_id": report.artifacts.hume_job_id,
                "memories_urls": report.artifacts.memories_urls
            }
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        logger.info(f"Report exported to {output_path}")

