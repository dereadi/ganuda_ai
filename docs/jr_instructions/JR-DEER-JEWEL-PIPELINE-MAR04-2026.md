# JR INSTRUCTION: Deer Jewel Storage Pipeline + Telegram Digest

**Task ID**: DEER-JEWEL-001
**Kanban**: #1948, #1949
**Priority**: 3

## Objective

Create `scripts/deer_jewel_digest.py` — a daily Telegram digest script that summarizes Deer's jewel findings from the last 24 hours and sends them to Chief.

Also create the `deer_sources` table for autonomous source management (#1950).

## File 1: Daily Jewel Digest

Create `/ganuda/scripts/deer_jewel_digest.py`

```python
#!/usr/bin/env python3
"""
Deer Jewel Digest — Daily Telegram Summary for Chief
Cherokee AI Federation — Outer Council

Sends a daily summary of Deer's jewel findings via Telegram.
Designed to run as a systemd timer (daily at 7:00 AM).

Usage:
    python3 scripts/deer_jewel_digest.py             # last 24 hours
    python3 scripts/deer_jewel_digest.py --hours 48  # last 48 hours
"""

import sys
import os
import json
import argparse

sys.path.insert(0, '/ganuda')
sys.path.insert(0, '/ganuda/lib')


def get_recent_jewels(hours: int = 24) -> list:
    """Fetch jewels from thermal memory stored in the last N hours."""
    from ganuda_db import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, original_content, temperature_score, metadata
            FROM thermal_memory_archive
            WHERE domain_tag = 'deer_jewel'
              AND created_at >= NOW() - INTERVAL '%s hours'
            ORDER BY temperature_score DESC, created_at DESC
        """, (hours,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()


def format_digest(jewels: list, hours: int) -> str:
    """Format jewels into a Telegram message."""
    if not jewels:
        return f"Deer Scout: No jewels found in last {hours}h. Quiet day."

    type1 = [j for j in jewels if j.get("metadata", {}).get("jewel_type") == 1]
    type2 = [j for j in jewels if j.get("metadata", {}).get("jewel_type") == 2]

    lines = [f"Deer Scout Daily Digest ({hours}h)\n"]
    lines.append(f"Code/Algo jewels: {len(type1)}")
    lines.append(f"Idea/Trend jewels: {len(type2)}")
    lines.append(f"Total stored: {len(jewels)}\n")

    # Top jewels (max 5)
    top = sorted(jewels, key=lambda j: j.get("temperature_score", 0), reverse=True)[:5]
    if top:
        lines.append("Top signals:")
        for i, j in enumerate(top, 1):
            meta = j.get("metadata", {})
            jtype = "Code" if meta.get("jewel_type") == 1 else "Idea"
            summary = meta.get("classification", {}).get("summary", "")
            source = meta.get("sender", "unknown")
            lines.append(f"  {i}. [{jtype}] {summary[:80]}")
            lines.append(f"     From: {source}")

    return "\n".join(lines)


def send_digest(hours: int = 24) -> bool:
    """Fetch jewels, format, and send via Telegram."""
    import requests

    jewels = get_recent_jewels(hours)
    message = format_digest(jewels, hours)

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_GROUP_CHAT_ID", "-1003439875431")

    if not bot_token:
        print(f"No TELEGRAM_BOT_TOKEN. Would send:\n{message}")
        return False

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": message},
            timeout=10,
        )
        result = resp.json()
        if result.get("ok"):
            print(f"Digest sent (message #{result['result']['message_id']})")
            return True
        else:
            print(f"Send failed: {result}")
            return False
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deer Jewel Daily Digest")
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args()
    send_digest(hours=args.hours)
```

## File 2: Deer Sources Table Migration

Create `/ganuda/scripts/migrations/deer_sources_schema.sql`

```sql
-- Deer Scout: Autonomous source management
-- Tracks which email sources produce high-quality jewels

CREATE TABLE IF NOT EXISTS deer_sources (
    id              SERIAL PRIMARY KEY,
    source_name     VARCHAR(200) NOT NULL,
    source_type     VARCHAR(50) NOT NULL DEFAULT 'newsletter',
    sender_email    VARCHAR(200),
    confidence_score FLOAT DEFAULT 0.5,
    jewels_found    INTEGER DEFAULT 0,
    noise_count     INTEGER DEFAULT 0,
    active          BOOLEAN DEFAULT TRUE,
    added_by        VARCHAR(50) DEFAULT 'deer',
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_deer_sources_active ON deer_sources(active) WHERE active = TRUE;
CREATE INDEX IF NOT EXISTS idx_deer_sources_email ON deer_sources(sender_email);

-- Jewel feedback table for Chief bidirectional feedback
CREATE TABLE IF NOT EXISTS jewel_feedback (
    id              SERIAL PRIMARY KEY,
    jewel_thermal_id INTEGER REFERENCES thermal_memory_archive(id),
    feedback_type   VARCHAR(20) NOT NULL CHECK (feedback_type IN ('useful', 'noise', 'acted_on')),
    feedback_by     VARCHAR(50) DEFAULT 'chief',
    feedback_at     TIMESTAMPTZ DEFAULT NOW(),
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_jewel_feedback_thermal ON jewel_feedback(jewel_thermal_id);

COMMENT ON TABLE deer_sources IS 'Deer Scout autonomous source tracking — which senders produce signal vs noise';
COMMENT ON TABLE jewel_feedback IS 'Bidirectional feedback from Chief on Deer jewel quality';
```

## Verification

1. Files exist at specified paths
2. `python3 -c "from scripts.deer_jewel_digest import format_digest; print('OK')"`
