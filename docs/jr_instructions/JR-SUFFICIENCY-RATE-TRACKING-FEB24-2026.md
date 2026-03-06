# Jr Instruction: Sufficiency Rate Tracking

**Kanban**: #1889
**Priority**: 5
**Story Points**: 5
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.

---

## Overview

Create a script that queries thermal_memory_archive for memories whose jsonb `metadata` column contains `sufficient_context` or `cache_hit` keys. Calculates sufficiency rate, cache hit rate, and daily trends over the last 7 days. Outputs to stdout and saves a JSON report. Uses psycopg2. Runs on redfin.

---

## Steps

### Step 1: Create the sufficiency rate tracker script

Create `/ganuda/scripts/sufficiency_rate_tracker.py`

```python
#!/usr/bin/env python3
"""
Sufficiency Rate Tracker
Kanban #1889 - Cherokee AI Federation

Queries thermal_memory_archive for memories with metadata containing
'sufficient_context' or 'cache_hit' keys. Calculates rates and
trends over the last 7 days.

Usage:
    python3 /ganuda/scripts/sufficiency_rate_tracker.py

Output:
    /ganuda/reports/sufficiency_rates.json

For Seven Generations
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.extras

DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", ""),
}

REPORT_PATH = "/ganuda/reports/sufficiency_rates.json"
LOOKBACK_DAYS = 7


def get_db_connection():
    """Connect to the federation database."""
    if not DB_CONFIG["password"]:
        print("ERROR: CHEROKEE_DB_PASS environment variable not set", file=sys.stderr)
        sys.exit(1)
    return psycopg2.connect(**DB_CONFIG)


def query_sufficiency_memories(conn, since):
    """Fetch memories that have sufficient_context in metadata."""
    sql = """
        SELECT
            id,
            created_at,
            metadata->>'sufficient_context' AS sufficient_context
        FROM thermal_memory_archive
        WHERE metadata ? 'sufficient_context'
          AND created_at >= %s
        ORDER BY created_at DESC
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (since,))
        return cur.fetchall()


def query_cache_hit_memories(conn, since):
    """Fetch memories that have cache_hit in metadata."""
    sql = """
        SELECT
            id,
            created_at,
            metadata->>'cache_hit' AS cache_hit
        FROM thermal_memory_archive
        WHERE metadata ? 'cache_hit'
          AND created_at >= %s
        ORDER BY created_at DESC
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (since,))
        return cur.fetchall()


def query_total_memories_by_day(conn, since):
    """Get total memory count per day for rate calculation."""
    sql = """
        SELECT
            DATE(created_at) AS day,
            COUNT(*) AS total
        FROM thermal_memory_archive
        WHERE created_at >= %s
        GROUP BY DATE(created_at)
        ORDER BY day
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (since,))
        return cur.fetchall()


def compute_daily_rates(memories, total_by_day, value_key, true_values=("true", "True", "1", "yes")):
    """Compute daily rates from a list of memories with a boolean-ish key."""
    daily_hits = defaultdict(int)
    daily_total = defaultdict(int)

    for mem in memories:
        day = mem["created_at"].date().isoformat() if hasattr(mem["created_at"], "date") else str(mem["created_at"])[:10]
        daily_total[day] += 1
        val = mem.get(value_key)
        if val and str(val).strip().lower() in [v.lower() for v in true_values]:
            daily_hits[day] += 1

    daily_rates = {}
    for day_row in total_by_day:
        day_str = str(day_row["day"])
        total = day_row["total"]
        hits = daily_hits.get(day_str, 0)
        tagged = daily_total.get(day_str, 0)
        daily_rates[day_str] = {
            "total_memories": total,
            "tagged_memories": tagged,
            "positive_hits": hits,
            "rate": round(hits / tagged, 4) if tagged > 0 else None,
            "coverage": round(tagged / total, 4) if total > 0 else 0.0,
        }

    return daily_rates


def compute_overall_rate(memories, value_key, true_values=("true", "True", "1", "yes")):
    """Compute overall rate from a set of memories."""
    if not memories:
        return {"total": 0, "positive": 0, "rate": None}

    positive = sum(
        1 for m in memories
        if m.get(value_key) and str(m[value_key]).strip().lower() in [v.lower() for v in true_values]
    )
    return {
        "total": len(memories),
        "positive": positive,
        "rate": round(positive / len(memories), 4) if memories else None,
    }


def compute_trend(daily_rates):
    """Compute simple trend (rising/falling/stable) from daily rates."""
    rates = []
    for day in sorted(daily_rates.keys()):
        r = daily_rates[day]["rate"]
        if r is not None:
            rates.append(r)

    if len(rates) < 2:
        return "insufficient_data"

    first_half = sum(rates[: len(rates) // 2]) / (len(rates) // 2)
    second_half = sum(rates[len(rates) // 2 :]) / (len(rates) - len(rates) // 2)

    diff = second_half - first_half
    if abs(diff) < 0.02:
        return "stable"
    elif diff > 0:
        return "rising"
    else:
        return "falling"


def main():
    print("Sufficiency Rate Tracker")
    print("=" * 40)
    print()

    conn = get_db_connection()
    since = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)

    try:
        print(f"Querying memories since {since.date()} ({LOOKBACK_DAYS} days)...")
        print()

        sufficiency_memories = query_sufficiency_memories(conn, since)
        cache_hit_memories = query_cache_hit_memories(conn, since)
        total_by_day = query_total_memories_by_day(conn, since)

        print(f"  Memories with sufficient_context tag: {len(sufficiency_memories)}")
        print(f"  Memories with cache_hit tag: {len(cache_hit_memories)}")
        print(f"  Days with data: {len(total_by_day)}")
        print()

        # Compute rates
        sufficiency_overall = compute_overall_rate(sufficiency_memories, "sufficient_context")
        cache_hit_overall = compute_overall_rate(cache_hit_memories, "cache_hit")

        sufficiency_daily = compute_daily_rates(sufficiency_memories, total_by_day, "sufficient_context")
        cache_hit_daily = compute_daily_rates(cache_hit_memories, total_by_day, "cache_hit")

        sufficiency_trend = compute_trend(sufficiency_daily)
        cache_hit_trend = compute_trend(cache_hit_daily)

        # Build report
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "lookback_days": LOOKBACK_DAYS,
            "since": since.isoformat(),
            "sufficiency": {
                "overall": sufficiency_overall,
                "trend": sufficiency_trend,
                "daily": sufficiency_daily,
            },
            "cache_hit": {
                "overall": cache_hit_overall,
                "trend": cache_hit_trend,
                "daily": cache_hit_daily,
            },
        }

        # Ensure output directory exists
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

        with open(REPORT_PATH, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Print summary
        print("--- Sufficiency Rate ---")
        print(f"  Total tagged: {sufficiency_overall['total']}")
        print(f"  Positive (sufficient=true): {sufficiency_overall['positive']}")
        print(f"  Rate: {sufficiency_overall['rate']}")
        print(f"  Trend: {sufficiency_trend}")
        print()
        print("--- Cache Hit Rate ---")
        print(f"  Total tagged: {cache_hit_overall['total']}")
        print(f"  Positive (hit=true): {cache_hit_overall['positive']}")
        print(f"  Rate: {cache_hit_overall['rate']}")
        print(f"  Trend: {cache_hit_trend}")
        print()
        print(f"Report saved to {REPORT_PATH}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
```

---

## Verification

After execution, confirm:
1. Script runs without errors: `python3 /ganuda/scripts/sufficiency_rate_tracker.py`
2. Report exists: `cat /ganuda/reports/sufficiency_rates.json | python3 -m json.tool | head -30`
3. Daily breakdown includes up to 7 days of data
4. Trend value is one of: rising, falling, stable, insufficient_data
