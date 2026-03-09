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


def run_standup():
    """Gather items, run council vote, store results."""
    conn = None
    try:
        conn = get_connection()
        cur = get_dict_cursor(conn)

        # Gather the three items
        forward = forward_look(cur)
        backward = backward_look(cur)
        pulse = health_pulse(cur)

        digest = f"""DAWN MIST STANDUP — {datetime.now().strftime('%A %B %d, %Y')}

{forward}

{backward}

{pulse}

Council: Review this morning's standup. Flag anything that needs deeper attention today. Keep it brief — this is a standup, not a deliberation."""

        logger.info(f"Dawn mist digest assembled, running council vote...")

        # Run lightweight council vote (low max_tokens = standup, not deliberation)
        council = SpecialistCouncil(max_tokens=150)
        result = council.vote(digest, include_responses=True)

        # Reconnect — council vote may have taken minutes, DB conn may be stale
        conn.close()
        conn = get_connection()
        cur = get_dict_cursor(conn)

        # Extract paper IDs mentioned in forward look for marking
        import re
        paper_ids = re.findall(r'\[(\d+)\]', forward)

        # Mark papers as reviewed
        if paper_ids:
            for pid in paper_ids:
                cur.execute("""
                    UPDATE ai_research_papers
                    SET council_vote_hash = %s, assessed_at = NOW()
                    WHERE paper_id = %s AND council_vote_hash IS NULL
                """, (result.audit_hash, int(pid)))
            conn.commit()

        # Store standup in thermal memory
        summary = (
            f"DAWN MIST STANDUP — {datetime.now().strftime('%Y-%m-%d')}\n"
            f"Council Vote: {result.audit_hash} (confidence: {result.confidence})\n"
            f"Recommendation: {result.recommendation}\n\n"
            f"{forward}\n\n{backward}\n\n{pulse}"
        )

        safe_thermal_write(
            content=summary,
            temperature=60.0,
            sacred=False,
            metadata={
                "type": "dawn_mist_standup",
                "audit_hash": result.audit_hash,
                "confidence": result.confidence,
                "papers_reviewed": [int(p) for p in paper_ids],
                "date": datetime.now().strftime('%Y-%m-%d'),
            }
        )

        # One-line summary for systemd journal
        concern_count = len([r for r in result.responses if r.has_concern])
        logger.info(
            f"[DAWN MIST] Vote {result.audit_hash} | "
            f"confidence {result.confidence} | "
            f"{len(paper_ids)} papers reviewed | "
            f"{concern_count} concerns | "
            f"{result.recommendation}"
        )

    except Exception as e:
        logger.error(f"[DAWN MIST] Standup failed: {e}")
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    run_standup()