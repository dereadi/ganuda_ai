#!/usr/bin/env python3
"""
Eagle Eye Pulse — Hourly federation heartbeat to #fire-guard.

One line. Living proof the organism breathes.

    92,233 memories | 797 kanban | 8,839 votes | 4 Jr active | Raven: OPEN

Run via cron or systemd timer every hour.
Leaders Meeting #1, Mar 10 2026.
"""

import os
import sys

sys.path.insert(0, '/ganuda/lib')
sys.path.insert(0, '/ganuda')

import psycopg2
from lib.secrets_loader import get_db_config
from slack_federation import send


def get_pulse():
    """Gather one-line pulse from the federation."""
    conn = psycopg2.connect(**get_db_config())
    cur = conn.cursor()

    # Thermal memories
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive")
    thermals = cur.fetchone()[0]

    # Sacred
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE sacred_pattern = true")
    sacred = cur.fetchone()[0]

    # Kanban completed
    cur.execute("SELECT COUNT(*) FROM duyuktv_tickets WHERE status = 'completed'")
    kanban_done = cur.fetchone()[0]

    # Council votes
    cur.execute("SELECT COUNT(*) FROM council_votes")
    votes = cur.fetchone()[0]

    # Jr active
    cur.execute("SELECT COUNT(*) FROM jr_work_queue WHERE status IN ('in_progress', 'pending')")
    jr_active = cur.fetchone()[0]

    # Circuit breakers
    cur.execute("""
        SELECT specialist_id, circuit_breaker_state
        FROM specialist_health
        WHERE id IN (
            SELECT MAX(id) FROM specialist_health GROUP BY specialist_id
        )
        AND circuit_breaker_state != 'CLOSED'
    """)
    breakers = cur.fetchall()
    breaker_str = ", ".join(f"{row[0]}: {row[1]}" for row in breakers) if breakers else "all clear"

    # TTD baseline
    cur.execute("SELECT COUNT(*) FROM failure_detection_log WHERE ttd_seconds <= 7200")
    ttd_ok = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM failure_detection_log")
    ttd_total = cur.fetchone()[0]

    # Coyote metric — ratified not deployed
    cur.execute("SELECT COUNT(*) FROM duyuktv_tickets WHERE ratification_hash IS NOT NULL AND deployed_at IS NULL")
    not_deployed = cur.fetchone()[0]

    cur.close()
    conn.commit()  # explicit commit before close
    conn.close()

    pulse = (
        f":eagle: *Pulse* | "
        f"{thermals:,} memories ({sacred} sacred) | "
        f"{kanban_done} kanban done | "
        f"{votes:,} votes | "
        f"{jr_active} Jr active | "
        f"Breakers: {breaker_str} | "
        f"Coyote: {not_deployed} ratified/undeployed"
    )

    return pulse


def main():
    pulse = get_pulse()

    if '--dry-run' in sys.argv:
        print(pulse)
        return

    # Load tokens
    with open('/ganuda/config/secrets.env') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

    sent = send("fire-guard", pulse, urgent=False)
    if sent:
        print(f"Pulse sent to #fire-guard")
    else:
        print(f"Pulse suppressed (silent hours or rate limit) — {pulse}")


if __name__ == "__main__":
    main()
