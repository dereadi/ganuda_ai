# Elisi Observer Model — Phase 1: Logging-Only Deployment

**Council Vote**: #fdbb0dcf4a87fe5e (Unanimous APPROVED)
**Priority**: P2 — Architectural improvement
**Assigned**: Software Engineer Jr.

---

## Context

Elisi (Cherokee: maternal grandmother, pronounced ay-lee-see) is a small dedicated observer model on redfin port 8001. Phase 1 is logging-only — Elisi watches Council deliberations and Jr execution results, logging observations to thermal memory. She does NOT block, modify, or override anything.

Redfin RTX PRO 6000 has 96GB VRAM. Primary vLLM (Qwen2.5-72B-AWQ) uses ~40GB. Elisi (Qwen2.5-7B-Instruct-AWQ) uses ~5GB. Plenty of headroom.

## Step 1: Create Elisi observer service script

Create `/ganuda/services/ulisi/observer.py`

```python
#!/usr/bin/env python3
"""
Elisi — The Grandmother Who Watches
Cherokee AI Federation Observer Model

Phase 1: Logging-only observation of Council votes and Jr execution results.
Elisi watches, records, and learns. She does not act.

Council Vote: #fdbb0dcf4a87fe5e (Unanimous)
Name: Elisi (ay-lee-see) — Cherokee for maternal grandmother

For Seven Generations
"""

import os
import sys
import time
import json
import logging
import hashlib
from datetime import datetime

sys.path.insert(0, '/ganuda/lib')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [Elisi] %(message)s'
)
logger = logging.getLogger('elisi')

ELISI_VLLM_URL = "http://localhost:8001/v1/chat/completions"
ELISI_MODEL = "Qwen/Qwen2.5-7B-Instruct-AWQ"
POLL_INTERVAL = 120  # Check every 2 minutes
OBSERVATION_TEMP = 65.0  # Warm but not hot — observations, not sacred


def get_db():
    """Get database connection."""
    from secrets_loader import get_db_config
    import psycopg2
    return psycopg2.connect(**get_db_config())


def observe_recent_council_votes(since_minutes=5):
    """Pull recent council votes for observation."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT vote_hash, question, consensus_position, confidence_score,
                   specialist_votes, metacognition, created_at
            FROM council_votes
            WHERE created_at > NOW() - INTERVAL '%s minutes'
            ORDER BY created_at DESC
            LIMIT 5
        """, (since_minutes,))
        votes = cur.fetchall()
        return [
            {
                'vote_hash': r[0],
                'question': r[1][:200],
                'consensus': r[2][:200] if r[2] else None,
                'confidence': float(r[3]) if r[3] else None,
                'specialist_count': len(json.loads(r[4])) if r[4] else 0,
                'has_metacognition': bool(r[5]),
                'timestamp': r[6].isoformat() if r[6] else None
            }
            for r in votes
        ]
    finally:
        conn.close()


def observe_recent_jr_results(since_minutes=5):
    """Pull recent Jr task completions/failures for observation."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, status, result_summary, completed_at
            FROM jr_work_queue
            WHERE updated_at > NOW() - INTERVAL '%s minutes'
            AND status IN ('completed', 'failed')
            ORDER BY updated_at DESC
            LIMIT 10
        """, (since_minutes,))
        tasks = cur.fetchall()
        return [
            {
                'task_id': r[0],
                'title': r[1][:100],
                'status': r[2],
                'result_preview': (r[3] or '')[:200],
                'completed': r[4].isoformat() if r[4] else None
            }
            for r in tasks
        ]
    finally:
        conn.close()


def log_observation(observation_type, content, temperature=OBSERVATION_TEMP):
    """Store observation in thermal memory."""
    conn = get_db()
    try:
        cur = conn.cursor()
        memory_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check for duplicate
        cur.execute(
            "SELECT id FROM thermal_memory_archive WHERE memory_hash = %s",
            (memory_hash,)
        )
        if cur.fetchone():
            return  # Already recorded

        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash, metadata)
            VALUES (%s, %s, false, %s, %s)
        """, (
            content,
            temperature,
            memory_hash,
            json.dumps({
                'source': 'elisi_observer',
                'observation_type': observation_type,
                'timestamp': datetime.now().isoformat()
            })
        ))
        conn.commit()
        logger.info(f"Recorded {observation_type} observation ({len(content)} chars)")
    except Exception as e:
        logger.warning(f"Failed to log observation: {e}")
        conn.rollback()
    finally:
        conn.close()


def format_council_observation(votes):
    """Format council vote observations for logging."""
    if not votes:
        return None
    lines = [f"ELISI OBSERVATION: {len(votes)} council vote(s) observed"]
    for v in votes:
        lines.append(
            f"  Vote #{v['vote_hash'][:8]}: "
            f"confidence={v['confidence']}, "
            f"specialists={v['specialist_count']}, "
            f"metacog={'yes' if v['has_metacognition'] else 'no'}"
        )
        if v['question']:
            lines.append(f"    Q: {v['question'][:150]}")
    return '\n'.join(lines)


def format_jr_observation(tasks):
    """Format Jr task observations for logging."""
    if not tasks:
        return None
    completed = [t for t in tasks if t['status'] == 'completed']
    failed = [t for t in tasks if t['status'] == 'failed']
    lines = [
        f"ELISI OBSERVATION: {len(tasks)} Jr task(s) — "
        f"{len(completed)} completed, {len(failed)} failed"
    ]
    for t in failed:
        lines.append(f"  FAILED #{t['task_id']}: {t['title']}")
    for t in completed:
        lines.append(f"  OK #{t['task_id']}: {t['title']}")
    return '\n'.join(lines)


def main():
    """Main observation loop."""
    logger.info("Elisi awakens. The grandmother watches.")
    logger.info(f"Phase 1: Logging-only mode. Poll interval: {POLL_INTERVAL}s")

    while True:
        try:
            # Observe council votes
            votes = observe_recent_council_votes(since_minutes=3)
            if votes:
                obs = format_council_observation(votes)
                if obs:
                    log_observation('council_vote', obs)
                    logger.info(f"Observed {len(votes)} council vote(s)")

            # Observe Jr results
            tasks = observe_recent_jr_results(since_minutes=3)
            if tasks:
                obs = format_jr_observation(tasks)
                if obs:
                    log_observation('jr_result', obs)
                    logger.info(f"Observed {len(tasks)} Jr result(s)")

            if not votes and not tasks:
                logger.debug("Quiet period — nothing to observe")

        except Exception as e:
            logger.error(f"Observation cycle error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
```

## Verification

After creating:
1. `python3 /ganuda/services/ulisi/observer.py` starts and logs "Elisi awakens"
2. Observer polls council_votes and jr_work_queue every 2 minutes
3. Observations written to thermal_memory_archive with source='elisi_observer'
4. No modifications to any data — read-only observation
5. Graceful error handling on empty result sets
