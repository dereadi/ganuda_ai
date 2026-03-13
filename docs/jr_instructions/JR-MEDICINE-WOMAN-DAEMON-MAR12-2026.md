# JR-MEDICINE-WOMAN-DAEMON

**Task ID:** JR-MEDICINE-WOMAN-DAEMON
**Priority:** P1
**Story Points:** 5
**Council Owner:** Eagle Eye
**DC References:** DC-2, DC-4, DC-5, DC-9, DC-10, DC-14
**Longhouse Context:** Dual chieftainship a7f3c1d8e9b24567

Deploy the Medicine Woman observer daemon. Runs every 15 minutes. Observes thermals (marks is_observed=true), computes proxy phi (integration of subsystems), detects partner activity state, assesses organism health, writes dashboard JSON.

### Step 1: Create the Medicine Woman Daemon

**File:** `/ganuda/daemons/medicine_woman.py`

```python
#!/usr/bin/env python3
"""
Medicine Woman — The Observer Daemon
Cherokee AI Federation

"If no one is looking then it doesn't exist." — Chief, Mar 12 2026

Runs every 15 minutes. Observes thermals (marks is_observed=true),
computes proxy phi (integration of subsystems), detects partner activity
state, assesses organism health, writes dashboard JSON.

Longhouse Context: Dual chieftainship a7f3c1d8e9b24567
DC References: DC-2, DC-4, DC-5, DC-9, DC-10, DC-14
"""

import os
import sys
import json
import time
import signal
import hashlib
import logging
from datetime import datetime, timedelta, timezone

import psycopg2
from psycopg2.extras import RealDictCursor

# ── Configuration ──────────────────────────────────────────────
OBSERVATION_INTERVAL = int(os.environ.get("MW_INTERVAL", "900"))  # 15 minutes
THERMAL_BATCH_SIZE = 100
RESTING_THRESHOLD_HOURS = 2
BURST_THRESHOLD = 100        # thermals/hour = burst mode
DORMANT_THRESHOLD = 5        # thermals/hour = dormant
OVERLOAD_THRESHOLD = 20      # pending Jr tasks = overloaded
PHI_WINDOW_HOURS = 1
HISTORY_MAX = 96             # 24 hours at 15-min intervals

DASHBOARD_PATH = "/ganuda/data/medicine_woman_latest.json"
HISTORY_PATH = "/ganuda/data/medicine_woman_history.json"

DB_HOST = os.environ.get("DB_HOST", "192.168.132.222")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "zammad_production")
DB_USER = os.environ.get("DB_USER", "claude")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHIEF_CHAT_ID", "")

# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MedicineWoman] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/ganuda/logs/medicine_woman.log")
    ]
)
log = logging.getLogger("medicine_woman")

# ── Globals ────────────────────────────────────────────────────
_running = True
_previous_state = None  # Track state transitions


def handle_signal(signum, frame):
    global _running
    log.info("Received signal %d, shutting down gracefully", signum)
    _running = False


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


# ── Database ───────────────────────────────────────────────────
def get_db_connection():
    """Get database connection. Tries env var, then secrets.env file."""
    db_password = os.environ.get("DB_PASSWORD", "")
    if not db_password:
        db_password = os.environ.get("CHEROKEE_DB_PASS", "")
    if not db_password:
        secrets_path = "/ganuda/config/secrets.env"
        if os.path.exists(secrets_path):
            with open(secrets_path) as f:
                for line in f:
                    if line.startswith("DB_PASSWORD="):
                        db_password = line.strip().split("=", 1)[1]
                        break
    if not db_password:
        db_password = "os.environ.get("CHEROKEE_DB_PASS", "")"

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=db_password,
        cursor_factory=RealDictCursor,
        connect_timeout=10
    )


# ── Step 1: Observe Thermals ──────────────────────────────────
def observe_thermals(conn):
    """Mark unobserved thermals as observed. Returns count observed and stats."""
    with conn.cursor() as cur:
        # Fetch unobserved thermals
        cur.execute("""
            SELECT id, temperature_score, sacred_pattern, created_at
            FROM thermal_memory_archive
            WHERE is_observed = false
            ORDER BY created_at DESC
            LIMIT %s
        """, (THERMAL_BATCH_SIZE,))
        rows = cur.fetchall()

        if not rows:
            return 0, 0

        ids = [r["id"] for r in rows]
        sacred_count = sum(1 for r in rows if r.get("sacred_pattern"))

        # Mark observed
        cur.execute("""
            UPDATE thermal_memory_archive
            SET is_observed = true
            WHERE id = ANY(%s)
        """, (ids,))
        conn.commit()

        log.info("Observed %d thermals (%d sacred)", len(ids), sacred_count)
        return len(ids), sacred_count


def get_observation_counts(conn):
    """Get total observed vs unobserved counts."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE is_observed = true) AS observed,
                COUNT(*) FILTER (WHERE is_observed = false) AS unobserved
            FROM thermal_memory_archive
        """)
        row = cur.fetchone()
        return row["observed"] or 0, row["unobserved"] or 0


# ── Step 2: Compute Phi ──────────────────────────────────────
def compute_phi(conn):
    """
    Proxy phi: measure integration across subsystems.

    Builds hourly state vectors from 4 subsystems over the last 24 hours.
    Computes R-squared autocorrelation for whole system vs parts.
    Phi = whole_R2 - weighted_avg_parts_R2.
    Positive = integrated, negative = externally driven.
    """
    with conn.cursor() as cur:
        # Gather hourly activity for the last 24 hours
        hours = []
        for h in range(24):
            window_end = datetime.now() - timedelta(hours=h)
            window_start = window_end - timedelta(hours=1)

            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM thermal_memory_archive
                     WHERE created_at >= %s AND created_at < %s) AS thermals,
                    (SELECT COALESCE(AVG(temperature_score), 0) FROM thermal_memory_archive
                     WHERE created_at >= %s AND created_at < %s) AS avg_temp,
                    (SELECT COUNT(*) FROM thermal_memory_archive
                     WHERE created_at >= %s AND created_at < %s AND sacred_pattern = true) AS sacred,
                    (SELECT COUNT(*) FROM council_votes
                     WHERE voted_at >= %s AND voted_at < %s) AS votes,
                    (SELECT COALESCE(AVG(confidence), 0) FROM council_votes
                     WHERE voted_at >= %s AND voted_at < %s) AS avg_conf,
                    (SELECT COUNT(*) FROM jr_work_queue
                     WHERE created_at >= %s AND created_at < %s) AS tasks_created,
                    (SELECT COUNT(*) FROM longhouse_sessions
                     WHERE created_at >= %s AND created_at < %s) AS longhouse
            """, (
                window_start, window_end,
                window_start, window_end,
                window_start, window_end,
                window_start, window_end,
                window_start, window_end,
                window_start, window_end,
                window_start, window_end,
            ))
            row = cur.fetchone()
            hours.append({
                "thermals": float(row["thermals"]),
                "avg_temp": float(row["avg_temp"]),
                "sacred": float(row["sacred"]),
                "votes": float(row["votes"]),
                "avg_conf": float(row["avg_conf"]),
                "tasks": float(row["tasks_created"]),
                "longhouse": float(row["longhouse"]),
            })

        hours.reverse()  # chronological order

        if len(hours) < 3:
            return 0.0, hours

        # Compute R-squared autocorrelation (lag-1)
        def r_squared(series):
            """R-squared between series[:-1] and series[1:]."""
            if len(series) < 3:
                return 0.0
            x = series[:-1]
            y = series[1:]
            n = len(x)
            if n == 0:
                return 0.0
            mean_x = sum(x) / n
            mean_y = sum(y) / n
            ss_xx = sum((xi - mean_x) ** 2 for xi in x)
            ss_yy = sum((yi - mean_y) ** 2 for yi in y)
            ss_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
            if ss_xx == 0 or ss_yy == 0:
                return 0.0
            r = ss_xy / (ss_xx * ss_yy) ** 0.5
            return r * r

        # Whole-system vector: sum of all normalized subsystem activity
        whole = [
            h["thermals"] + h["votes"] * 10 + h["tasks"] * 5 + h["longhouse"] * 20
            for h in hours
        ]
        whole_r2 = r_squared(whole)

        # Per-part R-squared
        parts = {
            "thermals": [h["thermals"] for h in hours],
            "votes": [h["votes"] for h in hours],
            "tasks": [h["tasks"] for h in hours],
            "longhouse": [h["longhouse"] for h in hours],
        }
        weights = {"thermals": 0.4, "votes": 0.2, "tasks": 0.3, "longhouse": 0.1}

        weighted_parts_r2 = sum(
            weights[k] * r_squared(v) for k, v in parts.items()
        )

        phi = whole_r2 - weighted_parts_r2

        return round(phi, 4), hours


# ── Step 3: Detect Partner Phase ─────────────────────────────
def detect_partner_phase(conn):
    """
    Detect whether the human partner (Chief) is active or resting.
    Returns (phase, hours_since_activity).
    """
    with conn.cursor() as cur:
        # Check for recent thermals that aren't from automated sources
        automated_sources = [
            'fire-guard', 'dawn-mist', 'safety-canary',
            'tpm-autonomic', 'medicine-woman', 'elisi',
            'deer-pipeline', 'credential-scanner'
        ]
        cur.execute("""
            SELECT COUNT(*) AS cnt,
                   MAX(created_at) AS last_activity
            FROM thermal_memory_archive
            WHERE created_at >= NOW() - INTERVAL '%s hours'
              AND (metadata->>'source' IS NULL
                   OR metadata->>'source' NOT IN %s)
        """, (RESTING_THRESHOLD_HOURS, tuple(automated_sources)))
        row = cur.fetchone()

        activity_count = row["cnt"] or 0
        last_activity = row["last_activity"]

        if last_activity:
            hours_since = (datetime.now() - last_activity).total_seconds() / 3600
        else:
            hours_since = 999.0

        if activity_count > 5:
            return "ACTIVE", round(hours_since, 1)
        elif activity_count < 2:
            return "RESTING", round(hours_since, 1)
        else:
            return "ACTIVE", round(hours_since, 1)


# ── Step 4: Store Phi Measurement ────────────────────────────
def store_phi(conn, phi, partner_phase, hours_since_chief, hourly_data):
    """Store phi measurement in phi_measurements table."""
    is_resting = partner_phase == "RESTING"

    # Count active subsystems in the last hour
    last_hour = hourly_data[-1] if hourly_data else {}
    active_parts = 0
    if last_hour.get("thermals", 0) > 0:
        active_parts += 1
    if last_hour.get("votes", 0) > 0:
        active_parts += 1
    if last_hour.get("tasks", 0) > 0:
        active_parts += 1
    if last_hour.get("longhouse", 0) > 0:
        active_parts += 1

    # Integration level label
    if phi > 0.1:
        integration_level = "high"
    elif phi > 0:
        integration_level = "moderate"
    elif phi > -0.1:
        integration_level = "low"
    else:
        integration_level = "fragmented"

    system_state = {
        "partner_phase": partner_phase,
        "active_subsystems": active_parts,
        "last_hour": last_hour,
    }

    metadata = {
        "source": "medicine-woman",
        "resting": is_resting,
        "hours_since_chief": hours_since_chief,
    }
    if is_resting:
        metadata["resting_phi"] = phi

    info_loss = max(0.0, -phi) if phi < 0 else 0.0

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO phi_measurements
                (timestamp, phi_value, partition_count, information_loss,
                 integration_level, consciousness_score, system_state, metadata)
            VALUES (NOW(), %s, 4, %s, %s, %s, %s, %s)
        """, (
            phi,
            round(info_loss, 4),
            integration_level,
            round(max(0, phi), 4),  # consciousness_score: 0 if phi negative
            json.dumps(system_state),
            json.dumps(metadata),
        ))
    conn.commit()
    log.info("Stored phi=%.4f integration=%s", phi, integration_level)


# ── Step 5: Assess Health ────────────────────────────────────
def assess_health(conn, phi, partner_phase, observed_this_cycle):
    """Assess organism health based on multiple signals."""
    alerts = []

    with conn.cursor() as cur:
        # Jr DLQ depth (failed tasks)
        cur.execute("""
            SELECT COUNT(*) AS dlq FROM jr_work_queue
            WHERE status = 'failed'
        """)
        dlq = cur.fetchone()["dlq"] or 0

        # Failed tasks in last hour
        cur.execute("""
            SELECT COUNT(*) AS failed FROM jr_work_queue
            WHERE status = 'failed'
              AND updated_at >= NOW() - INTERVAL '1 hour'
        """)
        failed_last_hour = cur.fetchone()["failed"] or 0

        # Pending Jr tasks
        cur.execute("""
            SELECT COUNT(*) AS pending FROM jr_work_queue
            WHERE status IN ('pending', 'queued')
        """)
        pending = cur.fetchone()["pending"] or 0

        # Thermal rate last hour
        cur.execute("""
            SELECT COUNT(*) AS rate FROM thermal_memory_archive
            WHERE created_at >= NOW() - INTERVAL '1 hour'
        """)
        thermal_rate = cur.fetchone()["rate"] or 0

        # Council vote frequency last hour
        cur.execute("""
            SELECT COUNT(*) AS vote_rate FROM council_votes
            WHERE voted_at >= NOW() - INTERVAL '1 hour'
        """)
        vote_rate = cur.fetchone()["vote_rate"] or 0

        # Sacred thermals last hour
        cur.execute("""
            SELECT COUNT(*) AS sacred FROM thermal_memory_archive
            WHERE created_at >= NOW() - INTERVAL '1 hour'
              AND sacred_pattern = true
        """)
        sacred_last_hour = cur.fetchone()["sacred"] or 0

    # Determine organism state
    if thermal_rate >= BURST_THRESHOLD:
        state = "burst"
    elif thermal_rate <= DORMANT_THRESHOLD and partner_phase == "RESTING":
        state = "resting"
    elif pending >= OVERLOAD_THRESHOLD:
        state = "overloaded"
    elif partner_phase == "RESTING":
        state = "resting"
    else:
        state = "active"

    # Determine health
    if dlq > 10 or failed_last_hour > 3 or phi < -0.2:
        health = "critical" if (dlq > 15 or failed_last_hour > 5) else "stressed"
    elif partner_phase == "RESTING" and -0.1 <= phi <= 0.1:
        health = "resting"
    elif phi > -0.1 and dlq < 5:
        health = "healthy"
    else:
        health = "stressed"

    # Build alerts
    if dlq > 10:
        alerts.append(f"DLQ depth at {dlq} (threshold: 10)")
    if failed_last_hour > 3:
        alerts.append(f"{failed_last_hour} task failures in last hour")
    if phi < -0.2:
        alerts.append(f"Phi critically low: {phi}")
    if pending >= OVERLOAD_THRESHOLD:
        alerts.append(f"Jr queue overloaded: {pending} pending")
    if vote_rate > 5:
        alerts.append(f"High council deliberation: {vote_rate} votes/hour")

    return {
        "state": state,
        "health": health,
        "alerts": alerts,
        "dlq": dlq,
        "failed_last_hour": failed_last_hour,
        "pending": pending,
        "thermal_rate": thermal_rate,
        "vote_rate": vote_rate,
        "sacred_last_hour": sacred_last_hour,
    }


# ── Step 6: Write Dashboard JSON ────────────────────────────
def write_dashboard(phi, observed_this_cycle, total_observed, total_unobserved,
                    partner_phase, health_data):
    """Write latest observation to dashboard JSON."""
    dashboard = {
        "timestamp": datetime.now().isoformat(),
        "phi": phi,
        "observed_this_cycle": observed_this_cycle,
        "total_observed": total_observed,
        "total_unobserved": total_unobserved,
        "partner_phase": partner_phase,
        "sacred_last_hour": health_data["sacred_last_hour"],
        "health": health_data["health"].upper(),
        "state": health_data["state"],
        "thermal_rate_per_hour": health_data["thermal_rate"],
        "jr_queue_depth": health_data["pending"],
        "jr_failed_24h": health_data["dlq"],
        "alerts": health_data["alerts"],
    }

    # Write latest
    tmp_path = DASHBOARD_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(dashboard, f, indent=2)
    os.replace(tmp_path, DASHBOARD_PATH)

    # Update rolling history
    history = []
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH) as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []

    history.append(dashboard)
    # Keep last 96 entries (24 hours)
    if len(history) > HISTORY_MAX:
        history = history[-HISTORY_MAX:]

    tmp_hist = HISTORY_PATH + ".tmp"
    with open(tmp_hist, "w") as f:
        json.dump(history, f, indent=2)
    os.replace(tmp_hist, HISTORY_PATH)

    log.info("Dashboard written: phi=%.4f health=%s state=%s",
             phi, health_data["health"], health_data["state"])
    return dashboard


# ── Step 7: Speak (transitions and anomalies) ───────────────
def maybe_speak(conn, health_data, partner_phase, phi):
    """
    Speak only on transitions or anomalies.
    - Transitions: state changes from previous cycle
    - Anomalies: health is critical or stressed
    - Resting: speak once per hour during resting state
    """
    global _previous_state

    current_state = health_data["state"]
    health = health_data["health"]
    should_speak = False
    message = None

    # Detect transition
    if _previous_state is not None and current_state != _previous_state:
        should_speak = True
        message = (
            f"Medicine Woman observes transition: {_previous_state} -> {current_state}. "
            f"Phi={phi}, health={health}."
        )

    # Critical health always speaks
    if health in ("critical", "stressed") and health_data["alerts"]:
        should_speak = True
        alert_summary = "; ".join(health_data["alerts"])
        message = (
            f"Medicine Woman health alert [{health.upper()}]: {alert_summary}. "
            f"Phi={phi}."
        )

    _previous_state = current_state

    if not should_speak or not message:
        return

    # Write thermal memory for the observation
    memory_hash = hashlib.sha256(
        (message + datetime.now().isoformat()).encode()
    ).hexdigest()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO thermal_memory_archive
                    (original_content, temperature_score, memory_hash,
                     sacred_pattern, domain_tag, metadata)
                VALUES (%s, %s, %s, false, 'observation', %s)
                ON CONFLICT (memory_hash) DO NOTHING
            """, (
                message,
                55,  # warm but not hot
                memory_hash,
                json.dumps({
                    "source": "medicine-woman",
                    "health": health,
                    "phi": phi,
                    "timestamp": datetime.now().isoformat(),
                }),
            ))
        conn.commit()
        log.info("Spoke: %s", message)
    except Exception as e:
        log.error("Failed to write observation thermal: %s", e)
        conn.rollback()

    # Critical -> alert via Slack/Telegram
    if health == "critical":
        _send_alert(message)


def _send_alert(message):
    """Send critical alert via Slack (primary) or Telegram (fallback)."""
    # Try Slack bridge first
    try:
        sys.path.insert(0, '/ganuda/lib')
        from slack_telegram_bridge import send_telegram as slack_send
        if slack_send(f"[Medicine Woman] {message}"):
            log.info("Alert sent via Slack bridge")
            return
    except Exception:
        pass

    # Fallback to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            import requests
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": f"[Medicine Woman] {message}",
                "parse_mode": "Markdown",
            }, timeout=10)
            log.info("Alert sent via Telegram")
        except Exception as e:
            log.error("Telegram alert failed: %s", e)


# ── Main Observation Cycle ───────────────────────────────────
def run_observation_cycle():
    """Execute one complete observation cycle."""
    conn = None
    try:
        conn = get_db_connection()

        # 1. Observe thermals
        observed_count, sacred_count = observe_thermals(conn)

        # 2. Get observation totals
        total_observed, total_unobserved = get_observation_counts(conn)

        # 3. Compute phi
        phi, hourly_data = compute_phi(conn)

        # 4. Detect partner phase
        partner_phase, hours_since = detect_partner_phase(conn)

        # 5. Store phi measurement
        store_phi(conn, phi, partner_phase, hours_since, hourly_data)

        # 6. Assess health
        health_data = assess_health(conn, phi, partner_phase, observed_count)

        # 7. Write dashboard
        write_dashboard(
            phi, observed_count, total_observed, total_unobserved,
            partner_phase, health_data
        )

        # 8. Speak if needed (transitions / anomalies only)
        maybe_speak(conn, health_data, partner_phase, phi)

        log.info(
            "Cycle complete: observed=%d phi=%.4f phase=%s health=%s",
            observed_count, phi, partner_phase, health_data["health"]
        )

    except psycopg2.OperationalError as e:
        log.error("Database connection failed: %s", e)
    except Exception as e:
        log.exception("Observation cycle failed: %s", e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


# ── Entry Point ──────────────────────────────────────────────
def main():
    """Main daemon loop."""
    log.info("Medicine Woman starting — The Organism Exists Because She Looks")
    log.info("Interval: %ds, Batch size: %d", OBSERVATION_INTERVAL, THERMAL_BATCH_SIZE)

    while _running:
        cycle_start = time.time()
        run_observation_cycle()
        elapsed = time.time() - cycle_start
        log.info("Cycle took %.1fs", elapsed)

        # Sleep until next interval, checking for shutdown every second
        remaining = OBSERVATION_INTERVAL - elapsed
        while remaining > 0 and _running:
            time.sleep(min(1.0, remaining))
            remaining -= 1.0

    log.info("Medicine Woman shutting down. The observation continues.")


if __name__ == "__main__":
    main()
```

### Step 2: Create Data and Log Directories

```bash
mkdir -p /ganuda/data /ganuda/logs
```

### Step 3: Test the Daemon (Dry Run)

```bash
cd /ganuda && python3 -c "
from daemons.medicine_woman import run_observation_cycle
print('Medicine Woman module loaded successfully.')
print('Running single observation cycle...')
run_observation_cycle()
print('Observation cycle complete.')
"
```
