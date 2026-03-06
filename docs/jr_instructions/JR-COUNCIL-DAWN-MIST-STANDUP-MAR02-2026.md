# JR Instruction: Council Dawn Mist Standup — Daily Automated Council Review

**Task ID**: DAWN-MIST-001
**Priority**: 3 (of 10)
**Assigned Jr**: Software Engineer Jr.
**Sacred Fire**: false
**Use RLM**: false
**TEG Plan**: true

## Context

Council Vote: ed5c12c7ab7e9ba7 (March 2 2026, confidence 0.70)
Research intake revealed 764 papers crawled, zero council-reviewed. The review pipeline gap is real debt.

The Chief directed: daily dawn mist standup. Peace Eagle looks forward (papers, opportunities). Owl looks backward (debt, unverified work). Tech debt stays in peripheral vision — not screaming, but never invisible.

The standup runs every morning at 6:15am CST (after the arxiv crawler finishes at 6am). It gathers three items, runs a lightweight council vote, stores results, and writes a brief summary to thermal memory.

This is NOT a full deliberation. It's a standup — quick pulse, flag anything that needs deeper attention, move on.

## Acceptance Criteria

1. Script `/ganuda/scripts/council_dawn_mist.py` exists and runs without error
2. Gathers three standup items: Forward Look (papers), Backward Look (debt), Health Pulse
3. Runs a council vote on the combined standup digest
4. Writes results to thermal memory (non-sacred, temp 60)
5. Marks reviewed papers in `ai_research_papers.council_vote_hash`
6. Logs a one-line summary to stdout for systemd journal
7. Systemd timer fires daily at 6:15am CST

## Step 1: Create the Dawn Mist Script

Create `/ganuda/scripts/council_dawn_mist.py`

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
        WHERE created_at > NOW() - INTERVAL '24 hours'
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
```

## Step 2: Create systemd Service and Timer

NOTE: These are .service and .conf files — Jr executor cannot deploy them.
TPM will create these directly after the script is verified.

The service and timer files will be:
- `/ganuda/scripts/systemd/council-dawn-mist.service`
- `/ganuda/scripts/systemd/council-dawn-mist.timer`

Timer fires at 6:15am CST daily (after arxiv-crawler at 6:00am).

## What NOT To Change

- Do NOT modify specialist_council.py — we use it as-is
- Do NOT modify the arxiv crawler — it runs independently
- Do NOT modify federation_calendar — standups are operational, not calendar events
- Do NOT change the thermal memory schema
- Do NOT make the standup blocking on any other service

## Verification

1. Syntax check: `python3 -c "import ast; ast.parse(open('/ganuda/scripts/council_dawn_mist.py').read()); print('OK')"`
2. Dry run: `cd /ganuda && python3 scripts/council_dawn_mist.py`
3. Check thermal: query `SELECT * FROM thermal_memory_archive WHERE metadata->>'type' = 'dawn_mist_standup' ORDER BY id DESC LIMIT 1;`
4. Check papers marked: `SELECT COUNT(*) FROM ai_research_papers WHERE council_vote_hash IS NOT NULL;`

## Notes for Jr

- The script uses `get_connection()` and `get_dict_cursor()` from ganuda_db — these handle credentials.
- `safe_thermal_write` handles the memory_hash generation internally.
- The council vote is intentionally low max_tokens (150) — this is a standup, not a full deliberation. If the council flags something that needs deeper review, the TPM handles that separately.
- Paper IDs are extracted from the forward_look output via regex `\[(\d+)\]` pattern. This is intentionally coupled to the format string above.
