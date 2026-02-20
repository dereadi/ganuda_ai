#!/usr/bin/env python3
"""
TPM Autonomic Daemon — Level 5+ Basin-Breaker
Monitors federation state, queues Jr work, calls Council, alerts Chief at phase transitions.

Council Vote: #b82aea3e6ceb8906 (PROCEED WITH CAUTION, 0.888)
Design: Polling-based (5min default), no persistent GPU, threshold comparisons only.
"""

import os
import sys
import json
import time
import hashlib
import logging
import argparse
import datetime
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

# ── Configuration ──────────────────────────────────────────────
POLL_INTERVAL = int(os.environ.get("TPM_POLL_INTERVAL", "300"))  # 5 minutes default
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:8080")
EMBEDDING_URL = os.environ.get("EMBEDDING_URL", "http://192.168.132.69:8003")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHIEF_CHAT_ID", "")

# Basin detection thresholds
COUNCIL_DISAGREEMENT_THRESHOLD = 0.3
DLQ_DEPTH_THRESHOLD = 5
STALENESS_ANOMALY_DAYS = 7
JR_FAILURE_RATE_THRESHOLD = 0.25  # >25% failure rate signals basin

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [TPM-AUTO] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/ganuda/logs/tpm_autonomic.log")
    ]
)
log = logging.getLogger("tpm_autonomic")


def get_db_connection():
    """Get database connection using secrets.env pattern."""
    db_password = os.environ.get("DB_PASSWORD", "")
    if not db_password:
        secrets_path = "/ganuda/config/secrets.env"
        if os.path.exists(secrets_path):
            with open(secrets_path) as f:
                for line in f:
                    if line.startswith("DB_PASSWORD="):
                        db_password = line.strip().split("=", 1)[1]
                        break
    return psycopg2.connect(
        host="192.168.132.222",
        port=5432,
        dbname="zammad_production",
        user="claude",
        password=db_password,
        cursor_factory=RealDictCursor
    )


def store_thermal_memory(conn, content, temperature=60, source="tpm-autonomic"):
    """Store an action record in thermal memory for audit trail."""
    memory_hash = hashlib.sha256(content.encode()).hexdigest()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, memory_hash, sacred_pattern, metadata)
            VALUES (%s, %s, %s, false, %s)
            ON CONFLICT (memory_hash) DO NOTHING
        """, (
            content,
            temperature,
            memory_hash,
            json.dumps({"source": source, "timestamp": datetime.datetime.now().isoformat()})
        ))
    conn.commit()


def send_telegram(message):
    """Send alert to Chief via Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram not configured, skipping alert")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        log.error(f"Telegram send failed: {e}")
        return False


# ── Basin Detection Signals ────────────────────────────────────

def check_council_disagreement(conn):
    """Check recent council votes for high disagreement (low agreement scores)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT audit_hash, confidence, recommendation, voted_at
            FROM council_votes
            WHERE voted_at > NOW() - INTERVAL '24 hours'
            ORDER BY voted_at DESC
            LIMIT 10
        """)
        votes = cur.fetchall()

    basin_signals = []
    for vote in votes:
        if vote["confidence"] and vote["confidence"] < (1.0 - COUNCIL_DISAGREEMENT_THRESHOLD):
            basin_signals.append({
                "type": "council_disagreement",
                "vote": vote["audit_hash"],
                "confidence": float(vote["confidence"]),
                "recommendation": vote["recommendation"],
                "timestamp": vote["voted_at"].isoformat() if vote["voted_at"] else None
            })
    return basin_signals


def check_dlq_depth(conn):
    """Check dead letter queue depth."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) as depth
            FROM jr_work_queue
            WHERE status = 'failed'
            AND updated_at > NOW() - INTERVAL '48 hours'
        """)
        result = cur.fetchone()

    depth = result["depth"] if result else 0
    if depth >= DLQ_DEPTH_THRESHOLD:
        return [{
            "type": "dlq_depth",
            "depth": depth,
            "threshold": DLQ_DEPTH_THRESHOLD
        }]
    return []


def check_jr_failure_rate(conn):
    """Check Jr task failure rate over last 24 hours."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'failed') as failed,
                COUNT(*) as total
            FROM jr_work_queue
            WHERE updated_at > NOW() - INTERVAL '24 hours'
            AND status IN ('completed', 'failed')
        """)
        result = cur.fetchone()

    if result and result["total"] > 3:
        rate = result["failed"] / result["total"]
        if rate >= JR_FAILURE_RATE_THRESHOLD:
            return [{
                "type": "jr_failure_rate",
                "rate": round(rate, 3),
                "completed": result["completed"],
                "failed": result["failed"],
                "threshold": JR_FAILURE_RATE_THRESHOLD
            }]
    return []


def check_stale_kanban(conn):
    """Check for kanban items stuck in_progress too long."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT ticket_id, title, updated_at
            FROM duyuktv_tickets
            WHERE status = 'in_progress'
            AND updated_at < NOW() - INTERVAL '%s days'
        """ % STALENESS_ANOMALY_DAYS)
        stale = cur.fetchall()

    if stale:
        return [{
            "type": "stale_kanban",
            "count": len(stale),
            "tickets": [{"id": s["ticket_id"], "title": s["title"]} for s in stale[:5]]
        }]
    return []


def check_pending_work(conn):
    """Get count of pending Jr work and open kanban items."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) as pending_jr
            FROM jr_work_queue WHERE status = 'pending'
        """)
        jr_pending = cur.fetchone()["pending_jr"]

        cur.execute("""
            SELECT COUNT(*) as open_kanban
            FROM duyuktv_tickets WHERE status = 'open'
        """)
        kanban_open = cur.fetchone()["open_kanban"]

    return {"pending_jr": jr_pending, "open_kanban": kanban_open}


# ── Main Loop ──────────────────────────────────────────────────

def run_cycle(conn):
    """Run one monitoring cycle. Returns list of basin signals."""
    signals = []
    signals.extend(check_council_disagreement(conn))
    signals.extend(check_dlq_depth(conn))
    signals.extend(check_jr_failure_rate(conn))
    signals.extend(check_stale_kanban(conn))

    work_state = check_pending_work(conn)

    if signals:
        log.warning(f"BASIN SIGNALS DETECTED: {len(signals)} signals")
        for s in signals:
            log.warning(f"  Signal: {s['type']} — {json.dumps(s)}")

        # Store basin detection in thermal memory
        store_thermal_memory(
            conn,
            f"TPM AUTONOMIC BASIN DETECTION: {len(signals)} signals detected. "
            f"Types: {', '.join(s['type'] for s in signals)}. "
            f"Details: {json.dumps(signals)}",
            temperature=75,
            source="tpm-autonomic-basin-detect"
        )

        # Alert Chief via Telegram
        alert_msg = f"*BASIN ALERT* — {len(signals)} signal(s) detected:\n"
        for s in signals:
            if s["type"] == "council_disagreement":
                alert_msg += f"• Council vote {s['vote'][:8]} confidence {s['confidence']:.3f}\n"
            elif s["type"] == "dlq_depth":
                alert_msg += f"• DLQ depth: {s['depth']} (threshold: {s['threshold']})\n"
            elif s["type"] == "jr_failure_rate":
                alert_msg += f"• Jr failure rate: {s['rate']*100:.1f}% ({s['failed']}/{s['failed']+s['completed']})\n"
            elif s["type"] == "stale_kanban":
                alert_msg += f"• Stale kanban: {s['count']} items stuck >7 days\n"
        alert_msg += f"\nWork state: {work_state['pending_jr']} Jr pending, {work_state['open_kanban']} kanban open"
        send_telegram(alert_msg)
    else:
        log.info(f"Clean cycle. Jr pending: {work_state['pending_jr']}, Kanban open: {work_state['open_kanban']}")

    return signals


def main():
    parser = argparse.ArgumentParser(description="TPM Autonomic Daemon — Level 5+ Basin-Breaker")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--interval", type=int, default=POLL_INTERVAL, help="Poll interval in seconds")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    log.info(f"TPM Autonomic Daemon starting. Interval: {args.interval}s")
    log.info(f"Basin thresholds: disagreement>{COUNCIL_DISAGREEMENT_THRESHOLD}, "
             f"DLQ>{DLQ_DEPTH_THRESHOLD}, failure_rate>{JR_FAILURE_RATE_THRESHOLD}, "
             f"staleness>{STALENESS_ANOMALY_DAYS}d")

    conn = get_db_connection()

    if args.once:
        signals = run_cycle(conn)
        log.info(f"Single cycle complete. {len(signals)} basin signals.")
        conn.close()
        return

    while True:
        try:
            # Reconnect if needed
            if conn.closed:
                conn = get_db_connection()
            run_cycle(conn)
        except psycopg2.OperationalError as e:
            log.error(f"DB connection error: {e}")
            try:
                conn = get_db_connection()
            except Exception:
                log.error("DB reconnect failed, waiting for next cycle")
        except Exception as e:
            log.exception(f"Cycle error: {e}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()