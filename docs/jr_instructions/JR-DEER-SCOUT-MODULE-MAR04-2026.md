# JR INSTRUCTION: Deer Scout Email Module + Jewel Classification

**Task ID**: DEER-SCOUT-001
**Kanban**: #1945, #1946
**Priority**: 2

## Objective

Create `email_daemon/deer_scout.py` — Deer's email scouting module. Reads from the `email_classifications` table (populated by gmail_api_daemon), filters for market intelligence, and classifies findings into "jewels" using the Deer specialist prompt via the Council gateway.

## File

Create `/ganuda/email_daemon/deer_scout.py`

```python
#!/usr/bin/env python3
"""
Deer Scout — Market Intelligence Email Scanner
Cherokee AI Federation — Outer Council

Scans classified emails for market intelligence, technology trends,
and strategic signals. Classifies findings into three jewel types:

  Type 1 (Code/Algo): Has repo, pip install, pseudocode, concrete implementation
  Type 2 (Idea/Trend): Market shift, competitive signal, strategic opportunity
  Type 3 (Noise): Promotional, off-topic, already known

Jewels are stored as thermal memories with appropriate temperatures
and surfaced to Chief via Telegram digest.

Usage:
    python3 email_daemon/deer_scout.py              # scan recent emails
    python3 email_daemon/deer_scout.py --hours 48   # scan last 48 hours
"""

import sys
import os
import json
import hashlib
import logging
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, '/ganuda')
sys.path.insert(0, '/ganuda/lib')

logger = logging.getLogger("deer_scout")
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s: %(message)s')

# Jewel type constants
JEWEL_CODE = 1    # Concrete implementation, repo, algorithm
JEWEL_IDEA = 2    # Market trend, strategic signal, opportunity
JEWEL_NOISE = 3   # Promotional, off-topic, already known


def get_recent_emails(hours: int = 24) -> list:
    """Fetch recent email classifications not yet scouted by Deer."""
    from ganuda_db import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, subject, from_address AS sender, snippet AS body_preview,
                   classification, received_at, metadata
            FROM email_classifications
            WHERE received_at >= NOW() - INTERVAL '%s hours'
              AND (metadata->>'deer_scouted') IS NULL
            ORDER BY received_at DESC
            LIMIT 50
        """, (hours,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Failed to fetch emails: {e}")
        return []
    finally:
        conn.close()


def classify_jewel(subject: str, body_preview: str, sender: str) -> dict:
    """
    Classify an email as a jewel using the Deer specialist prompt
    via direct vLLM call (avoids full council overhead for scouting).

    Returns: {"jewel_type": 1|2|3, "summary": str, "confidence": float, "tags": list}
    """
    import requests

    prompt = f"""You are Deer (AW), the Market/Business scout for the Cherokee AI Federation.

Classify this email as a jewel:

SUBJECT: {subject}
FROM: {sender}
PREVIEW: {body_preview[:1000]}

Classify into exactly one type:
- Type 1 (Code/Algo): Contains a repo link, pip install, pseudocode, concrete implementation, benchmark, or technical architecture you could build with TODAY.
- Type 2 (Idea/Trend): Market shift, competitive signal, strategic opportunity, new framework announcement, industry analysis. Actionable intelligence but not code.
- Type 3 (Noise): Promotional content, webinar invites, already-known information, off-topic, generic newsletters with no signal.

Respond in JSON only:
{{"jewel_type": 1|2|3, "summary": "one-line summary of the signal", "confidence": 0.0-1.0, "tags": ["relevant", "tags"]}}"""

    try:
        resp = requests.post(
            "http://localhost:8000/v1/chat/completions",
            json={
                "model": os.environ.get("VLLM_MODEL", "/ganuda/models/qwen2.5-72b-instruct-awq"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
                "temperature": 0.1,
            },
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        # Extract JSON from response
        import re
        json_match = re.search(r'\{[^}]+\}', content)
        if json_match:
            result = json.loads(json_match.group())
            result["jewel_type"] = int(result.get("jewel_type", 3))
            result["confidence"] = float(result.get("confidence", 0.5))
            result["tags"] = result.get("tags", [])
            result["summary"] = result.get("summary", "")
            return result
    except Exception as e:
        logger.error(f"Classification failed: {e}")

    return {"jewel_type": 3, "summary": "Classification failed", "confidence": 0.0, "tags": []}


def store_jewel(email_id: int, subject: str, sender: str, classification: dict) -> int:
    """
    Store a classified jewel in thermal memory.
    Type 1: temp 85, Type 2: temp 75, Type 3: not stored.
    Returns thermal ID or 0 if not stored.
    """
    from ganuda_db import get_connection

    jewel_type = classification["jewel_type"]
    if jewel_type == JEWEL_NOISE:
        return 0

    temp = 85 if jewel_type == JEWEL_CODE else 75
    content = (
        f"DEER JEWEL (Type {jewel_type}): {classification['summary']}\n"
        f"Source: {sender} — {subject}\n"
        f"Confidence: {classification['confidence']}\n"
        f"Tags: {', '.join(classification['tags'])}"
    )
    mem_hash = hashlib.sha256(content.encode()).hexdigest()

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, temperature_score, sacred_pattern,
             current_stage, metadata, domain_tag)
            VALUES (%s, %s, %s, FALSE, 'hot', %s, 'deer_jewel')
            ON CONFLICT (memory_hash) DO NOTHING
            RETURNING id
        """, (
            mem_hash, content, temp,
            json.dumps({
                "jewel_type": jewel_type,
                "email_id": email_id,
                "sender": sender,
                "subject": subject,
                "classification": classification,
                "scouted_at": datetime.now().isoformat(),
            }),
        ))
        row = cur.fetchone()
        thermal_id = row[0] if row else 0

        # Mark email as scouted
        cur.execute("""
            UPDATE email_classifications
            SET metadata = COALESCE(metadata, '{}'::jsonb) || %s
            WHERE id = %s
        """, (
            json.dumps({
                "deer_scouted": True,
                "jewel_type": jewel_type,
                "scouted_at": datetime.now().isoformat(),
            }),
            email_id,
        ))

        conn.commit()
        return thermal_id
    except Exception as e:
        logger.error(f"Failed to store jewel: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


def scout(hours: int = 24) -> dict:
    """
    Run a full scouting pass. Returns summary stats.
    """
    emails = get_recent_emails(hours)
    logger.info(f"Scouting {len(emails)} emails from last {hours} hours")

    stats = {"scanned": 0, "type1": 0, "type2": 0, "type3": 0, "stored": 0}

    for email in emails:
        stats["scanned"] += 1
        classification = classify_jewel(
            subject=email.get("subject", ""),
            body_preview=email.get("body_preview", ""),
            sender=email.get("sender", ""),
        )

        jtype = classification["jewel_type"]
        if jtype == JEWEL_CODE:
            stats["type1"] += 1
        elif jtype == JEWEL_IDEA:
            stats["type2"] += 1
        else:
            stats["type3"] += 1

        thermal_id = store_jewel(
            email_id=email["id"],
            subject=email.get("subject", ""),
            sender=email.get("sender", ""),
            classification=classification,
        )
        if thermal_id:
            stats["stored"] += 1
            logger.info(
                f"Jewel Type {jtype}: {classification['summary'][:60]} "
                f"(thermal #{thermal_id}, conf={classification['confidence']})"
            )

    logger.info(
        f"Scout complete: {stats['scanned']} scanned, "
        f"{stats['type1']} code, {stats['type2']} idea, {stats['type3']} noise, "
        f"{stats['stored']} stored"
    )
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deer Scout — email intelligence scanner")
    parser.add_argument("--hours", type=int, default=24, help="Hours to look back (default 24)")
    args = parser.parse_args()
    scout(hours=args.hours)
```

## Verification

1. `python3 -c "from email_daemon.deer_scout import classify_jewel; print('OK')"`
2. `python3 email_daemon/deer_scout.py --hours 1` (dry run, should scan 0 or few emails)
