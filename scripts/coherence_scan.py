#!/usr/bin/env python3
"""
coherence_scan.py — Session Boot Coherence Scan

"Wake up. Check the room before you check the calendar."

DC-14 Three-Body Memory, Watershed Layer Amendment — Sub-check #1.
Delta detection at session start: what changed since last session?

Queries:
  1. Thermal memories created/modified in last 24h
  2. Active Fire Guard alerts (open circuit breakers)
  3. Jr tasks in flight (pending/in_progress/assigned)
  4. Last 3 council votes
  5. Thread bookmarks (local file, optional)

Usage:
    python3 coherence_scan.py              # write to stdout
    python3 coherence_scan.py --dry-run    # same as default (print to stdout)
    python3 coherence_scan.py --json       # output as JSON
"""

import sys
sys.path.insert(0, '/ganuda/lib')
sys.path.insert(0, '/ganuda')

import argparse
import json
import logging
import os
import time
from datetime import datetime

import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger("coherence_scan")

THREAD_BOOKMARKS_PATH = '/ganuda/config/thread_bookmarks.json'


def get_connection():
    """Get DB connection via ganuda_db or manual fallback."""
    try:
        from ganuda_db import get_db_config
        config = get_db_config()
        return psycopg2.connect(**config)
    except Exception as e:
        logger.warning("ganuda_db unavailable (%s), using manual config", e)
        password = os.environ.get('CHEROKEE_DB_PASS')
        if not password:
            raise RuntimeError(
                "CHEROKEE_DB_PASS not set and ganuda_db unavailable. "
                "Set the env var or check /ganuda/config/secrets.env."
            )
        return psycopg2.connect(
            host='192.168.132.222',
            dbname='zammad_production',
            user='claude',
            password=password,
        )


def scan_thermal_delta(cur) -> dict:
    """Thermal memories created or modified in last 24h."""
    cur.execute("""
        SELECT COUNT(*) as cnt
        FROM thermal_memory_archive
        WHERE created_at > NOW() - INTERVAL '24 hours'
    """)
    count = cur.fetchone()['cnt']

    cur.execute("""
        SELECT id, LEFT(original_content, 120) as content_preview,
               temperature_score, sacred_pattern,
               created_at
        FROM thermal_memory_archive
        WHERE created_at > NOW() - INTERVAL '24 hours'
        ORDER BY temperature_score DESC
        LIMIT 5
    """)
    top_entries = cur.fetchall()

    return {
        'count_24h': count,
        'top_by_temperature': [dict(row) for row in top_entries],
    }


def scan_fire_guard_alerts(cur) -> dict:
    """Active circuit breakers — most recent state per specialist."""
    cur.execute("""
        SELECT DISTINCT ON (specialist_id)
            specialist_id, circuit_breaker_state, measured_at
        FROM specialist_health
        WHERE circuit_breaker_state != 'CLOSED'
        ORDER BY specialist_id, measured_at DESC
    """)
    alerts = [dict(row) for row in cur.fetchall()]

    return {
        'open_breakers': len(alerts),
        'alerts': alerts,
    }


def scan_jr_tasks(cur) -> dict:
    """Jr tasks currently in flight."""
    cur.execute("""
        SELECT COUNT(*) as cnt
        FROM jr_work_queue
        WHERE status IN ('pending', 'in_progress', 'assigned')
    """)
    count = cur.fetchone()['cnt']

    cur.execute("""
        SELECT id, LEFT(title, 100) as title, status, priority,
               created_at
        FROM jr_work_queue
        WHERE status IN ('pending', 'in_progress', 'assigned')
        ORDER BY priority ASC NULLS LAST, created_at DESC
    """)
    tasks = [dict(row) for row in cur.fetchall()]

    return {
        'in_flight': count,
        'tasks': tasks,
    }


def scan_recent_votes(cur) -> dict:
    """Last 3 council votes."""
    cur.execute("""
        SELECT LEFT(question, 100) as question_snippet,
               confidence,
               audit_hash,
               voted_at
        FROM council_votes
        ORDER BY voted_at DESC
        LIMIT 3
    """)
    votes = [dict(row) for row in cur.fetchall()]

    return {
        'recent_votes': votes,
    }


def scan_thread_bookmarks() -> dict:
    """Read thread bookmarks file if it exists."""
    if not os.path.exists(THREAD_BOOKMARKS_PATH):
        return {'available': False, 'note': 'thread_bookmarks.json not found'}

    try:
        with open(THREAD_BOOKMARKS_PATH, 'r') as f:
            bookmarks = json.load(f)
        return {'available': True, 'bookmarks': bookmarks}
    except (json.JSONDecodeError, IOError) as e:
        return {'available': False, 'error': str(e)}


def format_text(scan: dict) -> str:
    """Format scan results as structured text for session context."""
    now = datetime.now().strftime('%A %B %d, %Y %H:%M CT')
    lines = [
        f"COHERENCE SCAN — {now}",
        "=" * 60,
        "",
    ]

    # Thermal delta
    td = scan['thermal_delta']
    lines.append(f"THERMAL DELTA: {td['count_24h']} memories in last 24h")
    if td['top_by_temperature']:
        lines.append("  Top 5 by temperature:")
        for m in td['top_by_temperature']:
            sacred = " [SACRED]" if m.get('sacred_pattern') else ""
            lines.append(
                f"    #{m['id']} (temp {m['temperature_score']}){sacred}: "
                f"{m['content_preview']}"
            )
    lines.append("")

    # Fire Guard
    fg = scan['fire_guard']
    if fg['open_breakers'] == 0:
        lines.append("FIRE GUARD: All circuits CLOSED. No active alerts.")
    else:
        lines.append(f"FIRE GUARD: {fg['open_breakers']} OPEN circuit breaker(s)")
        for a in fg['alerts']:
            lines.append(
                f"    {a['specialist_id']}: {a['circuit_breaker_state']} "
                f"(at {a.get('measured_at', '?')})"
            )
    lines.append("")

    # Jr tasks
    jr = scan['jr_tasks']
    lines.append(f"JR TASKS IN FLIGHT: {jr['in_flight']}")
    if jr['tasks']:
        for t in jr['tasks'][:10]:
            lines.append(f"    [{t['status']}] {t.get('priority', '?')} #{t['id']}: {t['title']}")
    lines.append("")

    # Council votes
    cv = scan['council_votes']
    lines.append("RECENT COUNCIL VOTES (last 3):")
    if cv['recent_votes']:
        for v in cv['recent_votes']:
            lines.append(
                f"    [{v.get('audit_hash', '?')[:16]}] "
                f"conf={v.get('confidence', '?')} — {v['question_snippet']}"
            )
    else:
        lines.append("    No recent votes found.")
    lines.append("")

    # Thread bookmarks
    tb = scan['thread_bookmarks']
    if tb.get('available'):
        lines.append(f"THREAD BOOKMARKS: {len(tb.get('bookmarks', {}))} active bookmark(s)")
    else:
        lines.append(f"THREAD BOOKMARKS: {tb.get('note', tb.get('error', 'unavailable'))}")

    # Overhead (DC-9)
    overhead = scan.get('overhead_seconds', {})
    if overhead:
        lines.append("OVERHEAD (DC-9 Waste Heat Budget):")
        for k, v in overhead.items():
            if k != 'total':
                lines.append(f"    {k}: {v}s")
        lines.append(f"    TOTAL: {overhead.get('total', '?')}s")

    lines.append("")
    lines.append("=" * 60)
    lines.append("End coherence scan. Room checked. Ready to proceed.")
    return "\n".join(lines)


def json_serializer(obj):
    """Handle datetime serialization for JSON output."""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def main():
    parser = argparse.ArgumentParser(description="DC-14 Coherence Scan — session boot delta detection")
    parser.add_argument('--dry-run', action='store_true', help='Print to stdout (default behavior)')
    parser.add_argument('--json', action='store_true', dest='as_json', help='Output as JSON')
    args = parser.parse_args()

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        timings = {}
        scan_start = time.monotonic()

        t0 = time.monotonic()
        thermal_delta = scan_thermal_delta(cur)
        timings['thermal_delta'] = round(time.monotonic() - t0, 4)

        t0 = time.monotonic()
        fire_guard = scan_fire_guard_alerts(cur)
        timings['fire_guard'] = round(time.monotonic() - t0, 4)

        t0 = time.monotonic()
        jr_tasks = scan_jr_tasks(cur)
        timings['jr_tasks'] = round(time.monotonic() - t0, 4)

        t0 = time.monotonic()
        council_votes = scan_recent_votes(cur)
        timings['council_votes'] = round(time.monotonic() - t0, 4)

        t0 = time.monotonic()
        thread_bookmarks = scan_thread_bookmarks()
        timings['thread_bookmarks'] = round(time.monotonic() - t0, 4)

        timings['total'] = round(time.monotonic() - scan_start, 4)

        scan = {
            'scan_time': datetime.now().isoformat(),
            'thermal_delta': thermal_delta,
            'fire_guard': fire_guard,
            'jr_tasks': jr_tasks,
            'council_votes': council_votes,
            'thread_bookmarks': thread_bookmarks,
            'overhead_seconds': timings,
        }

        if args.as_json:
            print(json.dumps(scan, indent=2, default=json_serializer))
        else:
            print(format_text(scan))

    except Exception as e:
        logger.error("Coherence scan failed: %s", e)
        sys.exit(1)
    finally:
        if conn:
            conn.commit()  # explicit commit before close
            conn.close()


if __name__ == '__main__':
    main()
