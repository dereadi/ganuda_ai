# JR Instruction: Elisi Heartbeat Monitor on Silverfin

**Task ID**: ELISI-HEARTBEAT-SILVERFIN
**Priority**: 2
**Assigned Jr**: Software Engineer Jr.
**Sacred Fire**: false
**Use RLM**: false
**TEG Plan**: false

## Context

Crawdad's SPOF concern (Vote #293fe9209ce79b90): if Elisi on redfin goes down, nobody notices. The heartbeat monitor runs on silverfin (VLAN 10, FreeIPA server) — a different failure domain from redfin (VLAN 132). It checks whether Elisi has written to thermal_memory_archive recently. If not, it alerts.

Council Vote: #35dfc9184aabe1e6 (0.872, APPROVED)
Design Doc: `/ganuda/docs/design/DESIGN-ELISI-PHASE2-CONCERN-MITIGATION-MAR02-2026.md`

## Step 1: Create the heartbeat script

Create `/ganuda/services/ulisi/heartbeat.py`

```python
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
```

## Verification

1. With Elisi running on redfin: `python3 /ganuda/services/ulisi/heartbeat.py` should print "Elisi alive"
2. Stop Elisi on redfin, wait 240s, run again — should print "BLIND SPOT" and send Telegram alert
3. Script exits after one check — designed to be called by systemd timer or cron

## Files Created

- `/ganuda/services/ulisi/heartbeat.py`

## Note

Deployment to silverfin (systemd timer + file copy) is TPM-direct work — .service files are executor-blocked. The script itself can be created by Jr.
