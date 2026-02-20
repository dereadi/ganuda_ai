#!/usr/bin/env python3
"""
Flywheel Dashboard — Cherokee AI Federation Moltbook Proxy

Provides visibility into the Research Jr + Moltbook engagement flywheel.
Exposes metrics for the SAG Unified Interface dashboard widget.

Phase 5 of the Research Jr + Moltbook Flywheel.
Eagle Eye's mandate: Full visibility into all flywheel activity.
For Seven Generations
"""

import os
import logging
import psycopg2
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Add parent to path for imports
import sys
sys.path.insert(0, '/ganuda')
from lib.secrets_loader import get_db_config

logger = logging.getLogger('moltbook_proxy')


@dataclass
class FlywheelMetrics:
    """Current flywheel metrics."""
    # Today's activity
    scans_today: int = 0
    topics_detected: int = 0
    research_dispatched: int = 0
    responses_drafted: int = 0
    council_approved: int = 0
    posted: int = 0

    # Budget
    budget_spent: float = 0.0
    budget_limit: float = 10.0
    budget_percent: float = 0.0

    # Queue status
    pending_drafts: int = 0
    pending_research: int = 0

    # Last activity
    last_scan: Optional[str] = None
    last_post: Optional[str] = None
    last_post_title: Optional[str] = None

    # Engagement stats
    total_karma: int = 0
    avg_upvotes: float = 0.0


class FlywheelDashboard:
    """
    Dashboard for Moltbook flywheel visibility.

    Aggregates metrics from:
    - moltbook_post_queue (posts/comments)
    - thermal_memory_archive (research activity)
    - council_votes (approval history)
    """

    def __init__(self):
        self.db_config = get_db_config()

    def get_metrics(self) -> FlywheelMetrics:
        """
        Get current flywheel metrics.

        Returns comprehensive metrics for dashboard display.
        """
        metrics = FlywheelMetrics()

        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()

            # Today's date for filtering
            today = date.today()

            # Count posts by status today
            cur.execute("""
                SELECT status, COUNT(*)
                FROM moltbook_post_queue
                WHERE DATE(created_at) = %s
                GROUP BY status
            """, (today,))

            for row in cur.fetchall():
                status, count = row
                if status == 'posted':
                    metrics.posted = count
                elif status == 'pending':
                    metrics.pending_drafts = count
                elif status == 'approved':
                    metrics.council_approved = count + metrics.posted  # Approved includes posted

            # Count responses drafted today (all entries)
            cur.execute("""
                SELECT COUNT(*)
                FROM moltbook_post_queue
                WHERE DATE(created_at) = %s
            """, (today,))
            metrics.responses_drafted = cur.fetchone()[0] or 0

            # Get last post info
            cur.execute("""
                SELECT created_at, LEFT(content, 50)
                FROM moltbook_post_queue
                WHERE status = 'posted'
                ORDER BY created_at DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            if row:
                metrics.last_post = row[0].strftime('%H:%M UTC') if row[0] else None
                metrics.last_post_title = row[1]

            # Count research dispatched today (from thermal memory)
            cur.execute("""
                SELECT COUNT(*)
                FROM thermal_memory_archive
                WHERE keywords && ARRAY['moltbook', 'research']
                AND DATE(created_at) = %s
            """, (today,))
            metrics.research_dispatched = cur.fetchone()[0] or 0

            # Get budget info from thermal memory (latest budget record)
            cur.execute("""
                SELECT original_content
                FROM thermal_memory_archive
                WHERE keywords && ARRAY['flywheel', 'budget']
                ORDER BY created_at DESC
                LIMIT 1
            """)
            # Budget comes from research_dispatcher in-memory, estimate from activity
            metrics.budget_spent = metrics.research_dispatched * 0.15  # Estimated cost per research
            metrics.budget_limit = 10.0
            metrics.budget_percent = (metrics.budget_spent / metrics.budget_limit) * 100

            # Engagement stats (all time)
            cur.execute("""
                SELECT
                    COUNT(*),
                    COALESCE(AVG((metadata->>'upvotes')::int), 0)
                FROM moltbook_post_queue
                WHERE status = 'posted'
                AND metadata->>'upvotes' IS NOT NULL
            """)
            row = cur.fetchone()
            if row:
                metrics.avg_upvotes = float(row[1] or 0)

            # Topics detected (estimate from research activity)
            metrics.topics_detected = metrics.research_dispatched * 3  # ~3 topics per research

            # Scans (estimate: 5min interval = 288/day max, use fraction of day)
            now = datetime.now()
            minutes_today = now.hour * 60 + now.minute
            metrics.scans_today = minutes_today // 5

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error fetching flywheel metrics: {e}")

        return metrics

    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """
        Get recent flywheel activity for activity feed.
        """
        activity = []

        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    created_at,
                    post_type,
                    status,
                    LEFT(content, 100) as preview
                FROM moltbook_post_queue
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))

            for row in cur.fetchall():
                activity.append({
                    'timestamp': row[0].isoformat() if row[0] else None,
                    'type': row[1],
                    'status': row[2],
                    'preview': row[3],
                })

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error fetching recent activity: {e}")

        return activity

    def get_widget_html(self) -> str:
        """
        Generate HTML widget for SAG dashboard.
        """
        metrics = self.get_metrics()

        # Budget bar color
        if metrics.budget_percent < 50:
            bar_color = '#22c55e'  # Green
        elif metrics.budget_percent < 80:
            bar_color = '#eab308'  # Yellow
        else:
            bar_color = '#ef4444'  # Red

        html = f"""
        <div class="flywheel-widget" style="border: 1px solid #374151; border-radius: 8px; padding: 16px; background: #1f2937; color: #f3f4f6; font-family: monospace;">
            <h3 style="margin: 0 0 12px 0; color: #60a5fa;">MOLTBOOK FLYWHEEL STATUS</h3>

            <div style="margin-bottom: 12px;">
                <strong>Today's Activity:</strong>
                <ul style="margin: 4px 0; padding-left: 20px;">
                    <li>Scans: {metrics.scans_today} (every 5 min)</li>
                    <li>Topics Detected: {metrics.topics_detected}</li>
                    <li>Research Dispatched: {metrics.research_dispatched}</li>
                    <li>Responses Drafted: {metrics.responses_drafted}</li>
                    <li>Council Approved: {metrics.council_approved}</li>
                    <li>Posted: {metrics.posted}</li>
                </ul>
            </div>

            <div style="margin-bottom: 12px;">
                <strong>Budget:</strong> ${metrics.budget_spent:.2f} / ${metrics.budget_limit:.2f}
                <div style="background: #374151; border-radius: 4px; height: 12px; margin-top: 4px;">
                    <div style="background: {bar_color}; width: {min(metrics.budget_percent, 100):.0f}%; height: 100%; border-radius: 4px;"></div>
                </div>
                <span style="font-size: 12px; color: #9ca3af;">{metrics.budget_percent:.0f}%</span>
            </div>

            <div style="margin-bottom: 12px;">
                <strong>Last Post:</strong> {metrics.last_post or 'None today'}
                <div style="font-size: 12px; color: #9ca3af; overflow: hidden; text-overflow: ellipsis;">
                    "{metrics.last_post_title or 'N/A'}"
                </div>
            </div>

            <div>
                <strong>Pending:</strong>
                <ul style="margin: 4px 0; padding-left: 20px;">
                    <li>Drafts: {metrics.pending_drafts}</li>
                    <li>Research: {metrics.pending_research}</li>
                </ul>
            </div>

            <div style="margin-top: 12px; font-size: 11px; color: #6b7280; text-align: center;">
                FOR SEVEN GENERATIONS
            </div>
        </div>
        """

        return html

    def to_json(self) -> Dict:
        """Convert metrics to JSON for API response."""
        metrics = self.get_metrics()
        return {
            'metrics': asdict(metrics),
            'recent_activity': self.get_recent_activity(5),
            'timestamp': datetime.now().isoformat(),
        }


# Singleton instance
_dashboard = None


def get_dashboard() -> FlywheelDashboard:
    """Get or create the singleton dashboard instance."""
    global _dashboard
    if _dashboard is None:
        _dashboard = FlywheelDashboard()
    return _dashboard


# Self-test
if __name__ == '__main__':
    print("Flywheel Dashboard Self-Test")
    print("=" * 60)

    dashboard = FlywheelDashboard()
    metrics = dashboard.get_metrics()

    print(f"Today's Activity:")
    print(f"  Scans: {metrics.scans_today}")
    print(f"  Topics: {metrics.topics_detected}")
    print(f"  Research: {metrics.research_dispatched}")
    print(f"  Drafted: {metrics.responses_drafted}")
    print(f"  Posted: {metrics.posted}")
    print()
    print(f"Budget: ${metrics.budget_spent:.2f}/${metrics.budget_limit:.2f} ({metrics.budget_percent:.0f}%)")
    print()
    print(f"Last Post: {metrics.last_post}")
    print()

    print("Widget HTML preview:")
    print("-" * 40)
    print(dashboard.get_widget_html()[:500] + "...")

    print("=" * 60)
    print("FOR SEVEN GENERATIONS")
