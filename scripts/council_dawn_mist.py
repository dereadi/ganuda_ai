```python
#!/usr/bin/env python3
"""
council_dawn_mist.py — Daily Council Standup

"Dawn mist rises from the river. The council gathers before the day's work."

Three items per standup:
1. FORWARD LOOK (Peace Eagle): Top unreviewed papers from arxiv crawler
2. BACKWARD LOOK (Owl): Failed Jr tasks, stale specs, unfinished debt
3. HEALTH PULSE: Thermal memory count, vote backlog, Jr queue depth

Council Vote: ed5c12c7ab7e9ba7 (March 2 2026)
"""
import sys
sys.path.insert(0, '/ganuda')
sys.path.insert(0, '/ganuda/lib')

import json
import logging
from datetime import datetime, timedelta

from ganuda_db import get_connection, get_dict_cursor, safe_thermal_write
from specialist_council import SpecialistCouncil
from partner_rhythm import PartnerRhythmEngine

try:
    from slack_federation import send as slack_send
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger("dawn_mist")


def forward_look(cur) -> str:
    """Peace Eagle: What's new on the horizon?"""
    # Top 5 unreviewed papers by relevance
    cur.execute("""
        SELECT paper_id, title, published_date, relevance_score,
               LEFT(abstract, 150) as abstract_short
        FROM ai_research_papers
        WHERE council_vote_hash IS NULL
          AND relevance_score IS NOT NULL
        ORDER BY relevance_score DESC, published_date DESC
        LIMIT 5
    """)
    papers = cur.fetchall()

    if not papers:
        return "FORWARD LOOK: No unreviewed papers in the crawler. Quiet morning."

    lines = ["FORWARD LOOK — Top 5 unreviewed papers:"]
    for p in papers:
        lines.append(
            f"  [{p['paper_id']}] {p['title'][:80]} "
            f"(relevance: {p['relevance_score']}, {p['published_date']})"
        )
    return "\n".join(lines)


def backward_look(cur) -> str:
    """Owl: What debt are we carrying?"""
    items = []

    # Failed Jr tasks in last 7 days
    cur.execute("""
        SELECT COUNT(*) as cnt FROM jr_work_queue
        WHERE status = 'failed'
          AND created_at > NOW() - INTERVAL '7 days'
    """)
    failed = cur.fetchone()['cnt']
    if failed > 0:
        items.append(f"  {failed} failed Jr task(s) in last 7 days")

    # Stale in-progress tasks (older than 24h)
    cur.execute("""
        SELECT COUNT(*) as cnt FROM jr_work_queue
        WHERE status = 'in_progress'
          AND updated_at < NOW() - INTERVAL '24 hours'
    """)
    stale = cur.fetchone()['cnt']
    if stale > 0:
        items.append(f"  {stale} stale in-progress Jr task(s) (>24h)")

    # Unfinalized council votes
    cur.execute("""
        SELECT COUNT(*) as cnt FROM council_votes
        WHERE vote_finalized = FALSE
          AND auto_finalize = FALSE
    """)
    unfinalized = cur.fetchone()['cnt']
    if unfinalized > 0:
        items.append(f"  {unfinalized} unfinalized deliberative council vote(s)")

    # Specs not verified
    cur.execute("""
        SELECT COUNT(*) as cnt FROM project_specifications
        WHERE status IN ('approved', 'in_progress')
    """)
    unverified = cur.fetchone()['cnt']
    if unverified > 0:
        items.append(f"  {unverified} spec(s) awaiting verification")

    if not items:
        return "BACKWARD LOOK: Clean slate. No visible debt this morning."

    return "BACKWARD LOOK — Debt in peripheral vision:\n" + "\n".join(items)


def health_pulse(cur) -> str:
    """Quick vitals."""
    stats = {}

    cur.execute("SELECT COUNT(*) as cnt FROM thermal_memory_archive")
    stats['thermal_memories'] = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) as cnt FROM thermal_memory_archive WHERE sacred_pattern = TRUE")
    stats['sacred'] = cur.fetchone()['cnt']

    cur.execute("""
        SELECT COUNT(*) as cnt FROM jr_work_queue
        WHERE status = 'pending'
    """)
    stats['jr_pending'] = cur.fetchone()['cnt']

    cur.execute("""
        SELECT COUNT(*) as cnt FROM council_votes
        WHERE voted_at > NOW() - INTERVAL '24 hours'
    """)
    stats['votes_24h'] = cur.fetchone()['cnt']

    return (
        f"HEALTH PULSE: {stats['thermal_memories']:,} thermal memories "
        f"({stats['sacred']:,} sacred), "
        f"{stats['jr_pending']} Jr tasks pending, "
        f"{stats['votes_24h']} council votes in last 24h"
    )


def attractor_metrics(cur) -> str:
    """Strange Attractors: Key metrics from attractor validation."""
    stats = {}

    # Temperature Distribution
    cur.execute("""
        SELECT 
            SUM(CASE WHEN temperature BETWEEN 0 AND 30 THEN 1 ELSE 0 END) as cold,
            SUM(CASE WHEN temperature BETWEEN 30 AND 60 THEN 1 ELSE 0 END) as warm,
            SUM(CASE WHEN temperature BETWEEN 60 AND 70 THEN 1 ELSE 0 END) as boundary,
            SUM(CASE WHEN temperature BETWEEN 70 AND 90 THEN 1 ELSE 0 END) as hot,
            SUM(CASE WHEN temperature BETWEEN 90 AND 100 THEN 1 ELSE 0 END) as sacred
        FROM thermal_memory_archive
    """)
    temp_stats = cur.fetchone()
    total = sum(temp_stats.values())
    stats['temp_gap_60_70'] = f"{temp_stats['boundary']} ({temp_stats['boundary']/total:.1%})"

    # Vote Confidence Clusters
    cur.execute("""
        SELECT 
            FLOOR(vote_confidence * 10) / 10.0 as bucket,
            COUNT(*) as count
        FROM council_votes
        GROUP BY bucket
        ORDER BY bucket
    """)
    vote_clusters = cur.fetchall()
    avg_count = sum(c['count'] for c in vote_clusters) / len(vote_clusters)
    flagged_buckets = [f"{v['bucket']} ({v['count']})" for v in vote_clusters if v['count'] > 2 * avg_count]
    stats['vote_flagged_clusters'] = ", ".join(flagged_buckets)

    # Circadian Pattern
    cur.execute("""
        SELECT 
            DATE_TRUNC('hour', created_at) as hour,
            COUNT(*) as count
        FROM thermal_memory_archive
        WHERE created_at > NOW() - INTERVAL '24 hours'
        GROUP BY hour
        ORDER BY hour
    """)
    circadian_pattern = cur.fetchall()
    peak_hours = [str(h['hour'].hour) + "AM" if h['hour'].hour < 12 else str(h['hour'].hour - 12) + "PM" for h in circadian_pattern if h['count'] == max(c['count'] for c in circadian_pattern)]
    stats['peak_hours'] = ", ".join(peak_hours)

    # Drift Trend
    cur.execute("""
        SELECT 
            DATE_TRUNC('hour', created_at) as hour,
            COUNT(*) as count
        FROM drift_alerts
        WHERE created_at > NOW() - INTERVAL '24 hours'
        GROUP BY hour
        ORDER BY hour
    """)
    drift_trend = cur.fetchall()
    stats['drift_trend'] = ", ".join([f"{h['hour'].hour}: {h['count']}" for h in drift_trend])

    if not any(stats.values()):
        return ""

    return (
        f"ATTRACTORS: Temp gap 60-70: {stats['temp_gap_60_70']} | "
        f"Vote flagged clusters: {stats['vote_flagged_clusters']} | "
        f"Peak hours: {stats['peak_hours']} | "
        f"Drift trend: {stats['drift_trend']}"
    )


def partner_rhythm_report(cur) -> str:
    """Partner Rhythm: Predictive insights from partner's digital breadcrumbs."""
    engine = PartnerRhythmEngine()
    report = engine.generate_report()

    return (
        f"PARTNER RHYTHM — {datetime.now().strftime('%A %B %d, %Y %H:%M CT')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Partner Phase: {report['current_phase']}\n"
        f"Predicted Focus: {', '.join(report['predicted_focus'])}\n"
        f"Sacred Window: {report['sacred_window']['next_likely_window']} "
        f"({report['sacred_window']['confidence']}% confidence)\n\n"
        f"Overnight:\n"
        f"  Fire Guard: {report['overnight']['fire_guard']} alerts