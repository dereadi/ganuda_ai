#!/usr/bin/env python3
"""
Elisi Heartbeat Monitor — runs on silverfin (VLAN 10)
Checks whether Elisi observer on redfin is still writing to thermal_memory_archive.
Alerts via thermal memory + Telegram if Elisi goes silent for 240s.

Council Vote: #35dfc9184aabe1e6 (APPROVED)
Design: Crawdad SPOF mitigation — different failure domain from redfin.
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime

import psycopg2
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [ElisiHeartbeat] %(message)s'
)
logger = logging.getLogger('elisi_heartbeat')

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", ""),
}

SILENCE_THRESHOLD_SECONDS = 240  # 2x Phase 2 poll interval (30s * 8)


def check_elisi_heartbeat():
    """Check if Elisi has written to thermal memory recently."""
    try:
        conn = psycopg2.connect(**DB_CONFIG, connect_timeout=10)
        cur = conn.cursor()

        cur.execute("""
            SELECT COUNT(*) FROM thermal_memory_archive
            WHERE metadata->>'source' = 'elisi_observer'
            AND created_at > NOW() - INTERVAL '%s seconds'
        """, (SILENCE_THRESHOLD_SECONDS,))

        count = cur.fetchone()[0]
        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()

        if count > 0:
            logger.info(f"Elisi alive — {count} observation(s) in last {SILENCE_THRESHOLD_SECONDS}s")
            return True
        else:
            logger.warning(f"BLIND SPOT: No Elisi observations in {SILENCE_THRESHOLD_SECONDS}s")
            alert_blind_spot()
            return False

    except psycopg2.OperationalError as e:
        # DB unreachable — likely bluefin is down too
        logger.error(f"Cannot reach bluefin DB: {e}")
        alert_blind_spot(db_down=True)
        return False


def alert_blind_spot(db_down=False):
    """Log blind spot alert to thermal memory + Telegram."""
    # Slack-first routing (Leaders Meeting #1, Mar 10 2026)
    try:
        import sys
        if '/ganuda/lib' not in sys.path:
            sys.path.insert(0, '/ganuda/lib')
        from slack_federation import send as _slack_send
        channel = 'fire-guard'
        _blind_msg = (
            f"ELISI BLIND SPOT: No observations in {SILENCE_THRESHOLD_SECONDS}s. "
            f"{'Additionally, bluefin DB is unreachable from silverfin. Possible multi-node outage.' if db_down else 'Elisi observer on redfin may be down. Check: ssh redfin systemctl status elisi-observer'}"
        )
        if _slack_send(channel, _blind_msg):
            return True
    except Exception:
        pass  # fall through to existing Telegram code
    if db_down:
        msg = (f"ELISI BLIND SPOT: No observations in {SILENCE_THRESHOLD_SECONDS}s. "
               f"Additionally, bluefin DB is unreachable from silverfin. "
               f"Possible multi-node outage.")
    else:
        msg = (f"ELISI BLIND SPOT: No Elisi observations in {SILENCE_THRESHOLD_SECONDS}s. "
               f"Elisi observer on redfin may be down. "
               f"Check: ssh redfin 'systemctl status elisi-observer'")

    # Try to write to thermal memory (may fail if DB is down)
    if not db_down:
        try:
            conn = psycopg2.connect(**DB_CONFIG, connect_timeout=10)
            cur = conn.cursor()
            memory_hash = hashlib.sha256(
                (msg + datetime.now().strftime('%Y-%m-%d-%H')).encode()
            ).hexdigest()

            cur.execute("""
                INSERT INTO thermal_memory_archive
                (original_content, temperature_score, sacred_pattern, memory_hash, metadata)
                VALUES (%s, 85.0, false, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                msg, memory_hash,
                json.dumps({
                    'source': 'elisi_heartbeat',
                    'type': 'blind_spot_alert',
                    'node': 'silverfin',
                    'timestamp': datetime.now().isoformat()
                })
            ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to write thermal alert: {e}")

    # Telegram alert (works even if DB is down — silverfin has its own internet)
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    tg_chat = os.environ.get('TELEGRAM_CHAT_ID', '')
    if tg_token and tg_chat:
        try:
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={"chat_id": tg_chat, "text": msg},
                timeout=10
            )
            logger.info("Telegram blind spot alert sent")
        except Exception as e:
            logger.error(f"Telegram alert failed: {e}")
    else:
        logger.warning("Telegram not configured — alert logged only")


if __name__ == "__main__":
    check_elisi_heartbeat()