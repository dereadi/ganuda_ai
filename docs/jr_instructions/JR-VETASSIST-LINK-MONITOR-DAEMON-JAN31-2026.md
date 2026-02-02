# JR Instruction: VetAssist Resource Link Monitor Daemon

**Task ID:** VETASSIST-LINK-MONITOR-001
**Date:** January 31, 2026
**Assigned To:** Infrastructure Jr.
**Priority:** P2
**Depends On:** VETASSIST-RESOURCES-SCHEMA-001 (vetassist_resource_links table must exist)
**Estimated Effort:** 1 day

---

## Objective

Create a lightweight daemon that periodically checks all active URLs in the `vetassist_resource_links` table, marks broken links as inactive, and logs results. This ensures veterans are never presented with dead links to VA resources, benefits portals, or crisis hotline pages.

---

## Background

The VetAssist resource links table stores URLs to VA.gov pages, eBenefits portals, crisis resources, and legal references. These links can go stale -- VA reorganizes pages, external sites sunset endpoints, and seasonal programs rotate. A veteran clicking a dead link during a stressful claims process erodes trust in the platform. This daemon prevents that by catching broken links before users do.

---

## Architecture

```
vetassist_resource_links table (bluefin - 192.168.132.222)
        |
        v
link_monitor.py (cron or systemd timer, every 15 min)
        |
        +-- HTTP HEAD check each link due for its frequency
        |
        +-- Update last_checked, last_status in DB
        |
        +-- Deactivate broken links (404, 500, timeout)
        |
        +-- Log results to /ganuda/logs/link_monitor.log
        |
        +-- Write alerts to /ganuda/logs/link_monitor_alerts.log
```

---

## Implementation

### Step 1: Create the Link Monitor Script

**File to create:** `/ganuda/vetassist/backend/scripts/link_monitor.py`

The script must be under 100 lines. Use only stdlib + `psycopg2` + `requests`. No frameworks, no async.

```python
#!/usr/bin/env python3
"""
VetAssist Resource Link Monitor
Checks active links in vetassist_resource_links and deactivates broken ones.

Cherokee AI Federation - For Seven Generations
Created: January 31, 2026
"""

import sys
import logging
import datetime
import requests
import psycopg2

# ── Configuration ──────────────────────────────────────────────
DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2",
    "port": 5432,
}

LOG_FILE = "/ganuda/logs/link_monitor.log"
ALERT_FILE = "/ganuda/logs/link_monitor_alerts.log"
REQUEST_TIMEOUT = 10  # seconds

# Frequency thresholds in hours
FREQUENCY_HOURS = {
    "daily": 24,
    "weekly": 168,      # 7 * 24
    "seasonal": 720,    # 30 * 24
}

# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a"),
    ],
)
log = logging.getLogger("link_monitor")


def get_links_due(cur):
    """
    Query active links that are due for checking based on their frequency.

    Rules:
      - daily:    last_checked > 24h ago OR last_checked IS NULL
      - weekly:   last_checked > 7 days ago OR last_checked IS NULL
      - seasonal: last_checked > 30 days ago OR last_checked IS NULL
                  OR current month is December (year-end refresh)
    """
    now = datetime.datetime.utcnow()
    december = now.month == 12

    cur.execute("""
        SELECT id, url, check_frequency
        FROM vetassist_resource_links
        WHERE is_active = true
          AND (
            (check_frequency = 'daily'
              AND (last_checked < NOW() - INTERVAL '24 hours' OR last_checked IS NULL))
            OR
            (check_frequency = 'weekly'
              AND (last_checked < NOW() - INTERVAL '7 days' OR last_checked IS NULL))
            OR
            (check_frequency = 'seasonal'
              AND (last_checked < NOW() - INTERVAL '30 days' OR last_checked IS NULL
                   OR %s))
          )
        ORDER BY last_checked ASC NULLS FIRST
    """, (december,))

    return cur.fetchall()


def check_link(url):
    """
    HTTP HEAD request to verify a link is alive.
    Returns (status_code, redirect_url_or_None, error_message_or_None).
    """
    try:
        resp = requests.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=False)
        redirect_url = resp.headers.get("Location") if resp.status_code in (301, 302) else None
        return resp.status_code, redirect_url, None
    except requests.exceptions.Timeout:
        return None, None, "timeout"
    except requests.exceptions.ConnectionError:
        return None, None, "connection_error"
    except Exception as e:
        return None, None, str(e)


def write_alert(message):
    """Append an alert line to the alerts log file."""
    timestamp = datetime.datetime.utcnow().isoformat()
    with open(ALERT_FILE, "a") as f:
        f.write(f"{timestamp} ALERT: {message}\n")


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    links = get_links_due(cur)
    log.info(f"Links due for check: {len(links)}")

    checked = 0
    broken = 0
    redirected = 0

    for link_id, url, freq in links:
        status, redirect_url, error = check_link(url)

        if error:
            # Timeout or connection error -- deactivate
            log.warning(f"BROKEN id={link_id} url={url} error={error}")
            cur.execute("""
                UPDATE vetassist_resource_links
                SET is_active = false,
                    last_checked = NOW(),
                    last_status = %s
                WHERE id = %s
            """, (f"error:{error}", link_id))
            write_alert(f"Link DEACTIVATED id={link_id} url={url} reason={error}")
            broken += 1

        elif status in (404, 410, 500, 502, 503):
            # Server error or not found -- deactivate
            log.warning(f"BROKEN id={link_id} url={url} status={status}")
            cur.execute("""
                UPDATE vetassist_resource_links
                SET is_active = false,
                    last_checked = NOW(),
                    last_status = %s
                WHERE id = %s
            """, (str(status), link_id))
            write_alert(f"Link DEACTIVATED id={link_id} url={url} status={status}")
            broken += 1

        elif status in (301, 302):
            # Redirect -- log but keep active
            log.info(f"REDIRECT id={link_id} url={url} -> {redirect_url}")
            cur.execute("""
                UPDATE vetassist_resource_links
                SET last_checked = NOW(),
                    last_status = %s,
                    last_redirect_url = %s
                WHERE id = %s
            """, (str(status), redirect_url, link_id))
            redirected += 1

        else:
            # Healthy (200, 204, etc.)
            cur.execute("""
                UPDATE vetassist_resource_links
                SET last_checked = NOW(),
                    last_status = %s
                WHERE id = %s
            """, (str(status), link_id))

        checked += 1

    conn.commit()
    cur.close()
    conn.close()

    log.info(f"Run complete: checked={checked} broken={broken} redirected={redirected}")
    if broken > 0:
        write_alert(f"Run summary: {broken} link(s) deactivated out of {checked} checked")


if __name__ == "__main__":
    main()
```

**Key design decisions:**
- `requests.head()` instead of `GET` -- lighter, faster, sufficient for liveness checks.
- `allow_redirects=False` -- we catch redirects explicitly to record the destination.
- Deactivate on 404, 410, 500, 502, 503, timeout, and connection error.
- Keep redirects active but log the new URL for future manual update.
- Seasonal links also recheck in December regardless of last_checked date.
- Single DB transaction per run -- all updates commit atomically.

---

### Step 2: Create Cron Entry

Add to dereadi's crontab (`crontab -e`):

```cron
# VetAssist link monitor - check resource links every 15 minutes
*/15 * * * * /ganuda/vetassist/backend/venv/bin/python /ganuda/vetassist/backend/scripts/link_monitor.py >> /ganuda/logs/link_monitor.log 2>&1
```

The script internally handles frequency grouping (daily/weekly/seasonal), so running the cron every 15 minutes does NOT mean every link is checked every 15 minutes. Each run only checks links that are past due for their configured frequency.

---

### Step 3: Create systemd Timer (Optional, More Robust)

This is an alternative to cron. More visible in `systemctl` output, better logging integration, and survives crontab accidents.

**File to create:** `/ganuda/scripts/systemd/vetassist-link-monitor.service`

```ini
[Unit]
Description=VetAssist Resource Link Monitor
After=network.target postgresql.service

[Service]
Type=oneshot
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/vetassist/backend
Environment="PATH=/ganuda/vetassist/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/ganuda/vetassist/backend/venv/bin/python /ganuda/vetassist/backend/scripts/link_monitor.py
StandardOutput=append:/ganuda/logs/link_monitor.log
StandardError=append:/ganuda/logs/link_monitor.log
```

**File to create:** `/ganuda/scripts/systemd/vetassist-link-monitor.timer`

```ini
[Unit]
Description=Run VetAssist Link Monitor every 15 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
AccuracySec=1min

[Install]
WantedBy=timers.target
```

**To activate (requires sudo):**
```bash
sudo cp /ganuda/scripts/systemd/vetassist-link-monitor.service /etc/systemd/system/
sudo cp /ganuda/scripts/systemd/vetassist-link-monitor.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now vetassist-link-monitor.timer
```

**Verify timer is active:**
```bash
systemctl list-timers | grep link-monitor
```

Use EITHER cron OR the systemd timer, not both.

---

### Step 4: Ensure Log Directory Exists

```bash
mkdir -p /ganuda/logs
touch /ganuda/logs/link_monitor.log
touch /ganuda/logs/link_monitor_alerts.log
```

---

### Step 5: Run Initial Baseline Check

After the script is deployed:

```bash
cd /ganuda/vetassist/backend
/ganuda/vetassist/backend/venv/bin/python /ganuda/vetassist/backend/scripts/link_monitor.py
```

This first run will check ALL active links (since none have `last_checked` set yet) and establish the baseline. Review the output:

```bash
cat /ganuda/logs/link_monitor.log | tail -30
cat /ganuda/logs/link_monitor_alerts.log
```

---

### Step 6: Verify

1. **All links checked:** Query the database to confirm `last_checked` is populated for all active links:
   ```sql
   SELECT COUNT(*) AS unchecked
   FROM vetassist_resource_links
   WHERE is_active = true AND last_checked IS NULL;
   ```
   Expected result: `0`

2. **Broken links deactivated:** Check for any links marked inactive during the run:
   ```sql
   SELECT id, url, last_status
   FROM vetassist_resource_links
   WHERE is_active = false AND last_checked IS NOT NULL
   ORDER BY last_checked DESC;
   ```

3. **Alerts written:** If any links were broken, `/ganuda/logs/link_monitor_alerts.log` should have entries.

4. **Timer running (if using systemd):**
   ```bash
   systemctl status vetassist-link-monitor.timer
   journalctl -u vetassist-link-monitor.service --since "15 min ago"
   ```

5. **Cron running (if using cron):**
   ```bash
   grep link_monitor /ganuda/logs/link_monitor.log | tail -5
   ```
   Confirm entries appear every ~15 minutes.

---

## Files Summary

| File | Action |
|------|--------|
| `/ganuda/vetassist/backend/scripts/link_monitor.py` | CREATE |
| `/ganuda/scripts/systemd/vetassist-link-monitor.service` | CREATE (optional) |
| `/ganuda/scripts/systemd/vetassist-link-monitor.timer` | CREATE (optional) |
| dereadi crontab | MODIFY (add entry, unless using systemd timer) |

---

## Security Notes

- Database credentials are hardcoded in this script for simplicity. Once the centralized `vetassist_db_config` module from VETASSIST-CONFIG-CONSOLIDATION is fully adopted, migrate this script to use `get_non_pii_connection()` from `/ganuda/lib/vetassist_db_config.py` instead.
- The script only issues SELECT and UPDATE queries against `vetassist_resource_links`. It does not create, drop, or alter tables.
- HTTP HEAD requests use a 10-second timeout. The script does not follow redirects automatically, so it will not chase redirect chains to unknown destinations.
- No user data is logged. Only link IDs, URLs, and HTTP status codes appear in logs.

---

## Future Enhancements (Not in Scope)

- **Telegram alerting:** Wire alerts to the telegram_chief bot infrastructure for real-time notifications when links break. The alert log file provides the data; integration is a separate task.
- **Auto-reactivation:** If a previously broken link starts responding again, automatically reactivate it.
- **Redirect resolution:** Automatically update the stored URL when a permanent redirect (301) is detected.

---

## Success Criteria

- [ ] `link_monitor.py` exists at `/ganuda/vetassist/backend/scripts/link_monitor.py` and runs without error
- [ ] Script connects to bluefin PostgreSQL and queries `vetassist_resource_links`
- [ ] Frequency grouping works: daily/weekly/seasonal links checked at correct intervals
- [ ] Broken links (404, 500, timeout) are set to `is_active = false`
- [ ] Redirects are logged with `last_redirect_url` but kept active
- [ ] Results logged to `/ganuda/logs/link_monitor.log`
- [ ] Alerts for broken links written to `/ganuda/logs/link_monitor_alerts.log`
- [ ] Cron or systemd timer is active and running every 15 minutes
- [ ] Initial baseline run completes with `last_checked` populated for all active links

---

FOR SEVEN GENERATIONS
