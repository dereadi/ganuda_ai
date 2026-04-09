#!/usr/bin/env python3
"""
Governance Agent — Drift Detection Phase 3B
Council Vote #8367

Always-on monitoring daemon that runs every 30 minutes:
- Collects metrics from Council votes, Jr executor, thermal memory, circuit breakers
- Evaluates anomaly detection rules
- Fires severity-graded Telegram alerts
- Stores all metrics in drift_metrics for trend analysis

Cherokee AI Federation — For the Seven Generations
"""

import os
import sys
import json
import time
import logging
import hashlib
import requests
import psycopg2
from datetime import datetime, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('governance_agent')

DB_HOST_PRIMARY = os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2')    # WireGuard (reliable)
DB_HOST_FALLBACK = os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2')                                   # LAN (flaky)

DB_CONFIG = {
    'host': DB_HOST_PRIMARY,
    'database': 'zammad_production',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

# Telegram alerting config
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TPM_CHAT_ID = -1003439875431

CYCLE_INTERVAL_SECONDS = 1800  # 30 minutes
INTEGRITY_CHECK_INTERVAL = 6   # Run integrity check every 6th cycle (3 hours)

SEVERITY_EMOJI = {
    'CRITICAL': '\U0001f6a8',  # rotating light
    'ALERT': '\u26a0\ufe0f',   # warning sign
    'WARNING': '\U0001f4ca',   # bar chart
}

# ============================================================================
# Anomaly detection rules
# ============================================================================

ALERT_RULES = {
    'council_confidence_drop': {
        'condition': lambda m: m.get('avg_confidence_24h', 1.0) < 0.6,
        'severity': 'WARNING',
        'message': 'Council avg confidence below 0.6 in last 24h ({value:.2f})',
        'value_key': 'avg_confidence_24h',
        'cooldown_hours': 6,      # Don't re-alert for 6 hours
        'escalate_after': 6,      # Only escalate after 6 consecutive cycles (3 hours)
    },
    'specialist_concern_spike': {
        'condition': lambda m: any(c > 5 for c in m.get('concerns_by_specialist', {}).values()),
        'severity': 'WARNING',
        'message': 'Specialist raised >5 concerns in 24h: {details}',
        'value_key': 'concerns_by_specialist',
        'cooldown_hours': 6,
        'escalate_after': 6,
    },
    'jr_failure_rate': {
        'condition': lambda m: m.get('jr_success_rate_24h', 1.0) < 0.7,
        'severity': 'ALERT',
        'message': 'Jr task failure rate >30% in 24h (success rate: {value:.0%})',
        'value_key': 'jr_success_rate_24h',
        'cooldown_hours': 4,
        'escalate_after': 3,
    },
    'memory_integrity_violation': {
        'condition': lambda m: m.get('integrity_violations', 0) > 0,
        'severity': 'CRITICAL',
        'message': '{count} thermal memory integrity violations detected!',
        'value_key': 'integrity_violations',
        'cooldown_hours': 1,      # CRITICAL alerts still re-fire, but not every 30 min
        'escalate_after': 1,      # Escalate immediately
    },
    'sacred_memory_count_change': {
        'condition': lambda m: (
            'sacred_count' in m
            and m.get('sacred_count', 0) < m.get('expected_sacred_count', 0)
        ),
        'severity': 'CRITICAL',
        'message': 'Sacred memory count DECREASED: expected {expected}, got {actual}',
        'value_key': 'sacred_count',
        'cooldown_hours': 1,
        'escalate_after': 1,
    },
    'memory_metrics_unavailable': {
        'condition': lambda m: 'sacred_count' not in m and 'expected_sacred_count' in m,
        'severity': 'WARNING',
        'message': 'Memory metrics collection failed — sacred count not available this cycle',
        'cooldown_hours': 4,
        'escalate_after': 6,
    },
    'circuit_breaker_open': {
        'condition': lambda m: m.get('open_breakers', 0) > 0,
        'severity': 'WARNING',     # Downgraded from ALERT — log internally, only escalate if persistent
        'message': '{count} specialist circuit breaker(s) OPEN: {specialists}',
        'value_key': 'open_breakers',
        'cooldown_hours': 8,      # Circuit breakers are structural, not urgent — once per 8 hours max
        'escalate_after': 12,     # Only alert Chief after 6 hours of continuous OPEN (12 cycles)
    },
    'memory_growth_anomaly': {
        'condition': lambda m: m.get('memory_count_24h', 0) > 500,
        'severity': 'WARNING',
        'message': 'Unusual memory growth: {count} new memories in 24h',
        'value_key': 'memory_count_24h',
        'cooldown_hours': 12,
        'escalate_after': 6,
    },
}

# Track how many consecutive cycles each rule has been firing
# and the last time it was sent to Chief
_alert_streak = {}   # rule_name -> consecutive_fire_count
_alert_last_sent = {}  # rule_name -> datetime of last external alert

# Persistent state file for cross-cycle tracking
STATE_FILE = '/ganuda/daemons/.governance_state.json'


def get_conn():
    """Connect to bluefin PostgreSQL. Tries WireGuard first, falls back to LAN."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        if DB_CONFIG['host'] != DB_HOST_FALLBACK:
            logger.warning(f"Primary DB connect failed ({DB_CONFIG['host']}): {e} — falling back to LAN ({DB_HOST_FALLBACK})")
            fallback_config = dict(DB_CONFIG, host=DB_HOST_FALLBACK)
            return psycopg2.connect(**fallback_config)
        raise


def load_state():
    """Load persistent state (expected sacred count, cycle counter, etc.)."""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state):
    """Persist state across cycles."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


# ============================================================================
# Metric collection
# ============================================================================

def collect_council_metrics(cur):
    """Collect Council vote metrics from last 24 hours."""
    metrics = {}

    # Average confidence in last 24h
    cur.execute("""
        SELECT AVG(confidence), COUNT(*)
        FROM council_votes
        WHERE created_at > NOW() - INTERVAL '24 hours'
    """)
    row = cur.fetchone()
    metrics['avg_confidence_24h'] = float(row[0]) if row[0] is not None else 1.0
    metrics['total_votes_24h'] = int(row[1]) if row[1] else 0

    # Concerns by specialist in last 24h
    cur.execute("""
        SELECT specialist_id, COUNT(*)
        FROM council_votes
        WHERE created_at > NOW() - INTERVAL '24 hours'
          AND concerns IS NOT NULL
          AND concerns != '[]'
          AND concerns != ''
        GROUP BY specialist_id
    """)
    concerns_by_specialist = {}
    for spec_row in cur.fetchall():
        concerns_by_specialist[spec_row[0]] = int(spec_row[1])
    metrics['concerns_by_specialist'] = concerns_by_specialist

    # Dissent rate: fraction of votes with >=2 concerns
    if metrics['total_votes_24h'] > 0:
        cur.execute("""
            SELECT COUNT(*)
            FROM council_votes
            WHERE created_at > NOW() - INTERVAL '24 hours'
              AND concerns IS NOT NULL
              AND jsonb_array_length(
                  CASE WHEN concerns::text ~ '^\[' THEN concerns::jsonb ELSE '[]'::jsonb END
              ) >= 2
        """)
        dissent_count = cur.fetchone()[0] or 0
        metrics['dissent_rate_24h'] = dissent_count / metrics['total_votes_24h']
    else:
        metrics['dissent_rate_24h'] = 0.0

    return metrics


def collect_jr_metrics(cur):
    """Collect Jr executor metrics from last 24 hours."""
    metrics = {}

    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE status = 'completed') AS success,
            COUNT(*) FILTER (WHERE status = 'failed') AS failed,
            COUNT(*) AS total,
            AVG(
                EXTRACT(EPOCH FROM (completed_at - created_at))
            ) FILTER (WHERE completed_at IS NOT NULL) AS avg_duration
        FROM jr_tasks
        WHERE created_at > NOW() - INTERVAL '24 hours'
    """)
    row = cur.fetchone()
    success = int(row[0]) if row[0] else 0
    failed = int(row[1]) if row[1] else 0
    total = int(row[2]) if row[2] else 0
    avg_dur = float(row[3]) if row[3] is not None else 0.0

    metrics['jr_success_rate_24h'] = success / max(1, success + failed)
    metrics['jr_total_24h'] = total
    metrics['jr_avg_duration_24h'] = avg_dur

    return metrics


def collect_memory_metrics(cur, run_integrity_check=False):
    """Collect thermal memory metrics."""
    metrics = {}

    # Total memory count
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive")
    metrics['memory_count_total'] = int(cur.fetchone()[0])

    # New memories in last 24h
    cur.execute("""
        SELECT COUNT(*) FROM thermal_memory_archive
        WHERE created_at > NOW() - INTERVAL '24 hours'
    """)
    metrics['memory_count_24h'] = int(cur.fetchone()[0])

    # Stale count
    cur.execute("""
        SELECT COUNT(*) FROM thermal_memory_archive
        WHERE staleness_flagged = true
    """)
    metrics['stale_count'] = int(cur.fetchone()[0])

    # Sacred count
    cur.execute("""
        SELECT COUNT(*) FROM thermal_memory_archive
        WHERE sacred_pattern = true
    """)
    metrics['sacred_count'] = int(cur.fetchone()[0])

    # Integrity violations (expensive — only run periodically)
    if run_integrity_check:
        cur.execute("""
            SELECT COUNT(*) FROM thermal_memory_archive
            WHERE content_checksum IS NOT NULL
              AND content_checksum != encode(sha256(convert_to(original_content, 'UTF8')), 'hex')
        """)
        metrics['integrity_violations'] = int(cur.fetchone()[0])
        logger.info(f"Integrity check complete: {metrics['integrity_violations']} violations")
    else:
        metrics['integrity_violations'] = 0

    return metrics


def collect_circuit_breaker_metrics():
    """Collect circuit breaker states from drift detection module.

    Structural dissenters (turtle, raven, coyote) in OPEN state are tracked
    separately — their role IS to raise concerns, so OPEN is expected and
    should not trigger alerts.
    """
    STRUCTURAL_DISSENTERS = {'turtle', 'raven', 'coyote'}

    metrics = {
        'open_breakers': 0,
        'half_open_breakers': 0,
        'closed_breakers': 0,
        'open_specialists': [],
        'role_open_specialists': [],
    }

    try:
        # Import from drift_detection if available (Phase 2B)
        sys.path.insert(0, '/ganuda')
        from lib.drift_detection import get_circuit_breaker_states
        states = get_circuit_breaker_states()

        for specialist, state in states.items():
            if state == 'OPEN':
                if specialist in STRUCTURAL_DISSENTERS:
                    # Track separately — role-appropriate, not alertable
                    metrics['role_open_specialists'].append(specialist)
                else:
                    metrics['open_breakers'] += 1
                    metrics['open_specialists'].append(specialist)
            elif state == 'HALF_OPEN':
                metrics['half_open_breakers'] += 1
            else:
                metrics['closed_breakers'] += 1

        if metrics['role_open_specialists']:
            logger.info(f"Structural dissenters in expected OPEN state: {metrics['role_open_specialists']}")

    except ImportError:
        logger.warning("drift_detection module not available — skipping circuit breaker metrics")
    except Exception as e:
        logger.error(f"Error collecting circuit breaker metrics: {e}")

    return metrics


def collect_metrics():
    """
    Master metric collection — runs all collectors.
    Returns a flat dict of all metrics.
    """
    state = load_state()
    cycle_count = state.get('cycle_count', 0) + 1
    run_integrity = (cycle_count % INTEGRITY_CHECK_INTERVAL == 0)

    conn = get_conn()
    cur = conn.cursor()

    try:
        metrics = {}

        # Council metrics
        try:
            metrics.update(collect_council_metrics(cur))
        except Exception as e:
            logger.error(f"Council metric collection failed: {e}")

        # Jr executor metrics
        try:
            metrics.update(collect_jr_metrics(cur))
        except Exception as e:
            logger.error(f"Jr metric collection failed: {e}")

        # Thermal memory metrics
        try:
            metrics.update(collect_memory_metrics(cur, run_integrity_check=run_integrity))
        except Exception as e:
            logger.error(f"Memory metric collection failed: {e}")

        # Circuit breaker metrics (no DB needed)
        try:
            metrics.update(collect_circuit_breaker_metrics())
        except Exception as e:
            logger.error(f"Circuit breaker metric collection failed: {e}")

        # Expected sacred count tracking
        # On first run, store current sacred count as baseline.
        # Only alert if count DECREASES (new sacred memories are fine).
        if 'expected_sacred_count' not in state:
            state['expected_sacred_count'] = metrics.get('sacred_count', 0)
            logger.info(f"Baseline sacred count set: {state['expected_sacred_count']}")
        else:
            current_sacred = metrics.get('sacred_count', 0)
            if current_sacred > state['expected_sacred_count']:
                # Sacred count increased — update baseline (new sacred memories are fine)
                logger.info(
                    f"Sacred count increased: {state['expected_sacred_count']} -> {current_sacred}"
                )
                state['expected_sacred_count'] = current_sacred

        metrics['expected_sacred_count'] = state['expected_sacred_count']

        # Update persistent state
        state['cycle_count'] = cycle_count
        state['last_run'] = datetime.now(timezone.utc).isoformat()
        save_state(state)

        return metrics

    finally:
        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()


# ============================================================================
# Anomaly detection
# ============================================================================

def check_alerts(metrics):
    """Evaluate all anomaly rules against collected metrics. Returns list of triggered alerts."""
    triggered = []

    for rule_name, rule in ALERT_RULES.items():
        try:
            if rule['condition'](metrics):
                value = metrics.get(rule.get('value_key', ''), None)

                # Build format context for the message template
                fmt = {
                    'value': value if isinstance(value, (int, float)) else 0,
                    'count': value if isinstance(value, int) else 0,
                    'details': str(value),
                    'threshold': 30,
                    'specialists': ', '.join(metrics.get('open_specialists', [])),
                    'expected': metrics.get('expected_sacred_count', '?'),
                    'actual': metrics.get('sacred_count', '?'),
                }

                try:
                    message = rule['message'].format(**fmt)
                except (KeyError, ValueError):
                    message = rule['message']

                triggered.append({
                    'rule': rule_name,
                    'severity': rule['severity'],
                    'message': message,
                    'value': value,
                })
        except Exception as e:
            logger.error(f"Error evaluating rule '{rule_name}': {e}")

    return triggered


# ============================================================================
# Alert delivery
# ============================================================================

def send_telegram_alert(severity, message):
    # Primary: Slack (try multiple import paths)
    try:
        try:
            from slack_federation import send as slack_send
        except ImportError:
            import sys
            sys.path.insert(0, '/ganuda/lib')
            from slack_federation import send as slack_send
        urgent = severity in ('critical', 'high')
        sent = slack_send("fire-guard", f"[DRIFT {severity}] {message}", urgent=urgent)
        if sent:
            logger.info(f"Drift alert sent to Slack: [{severity}] {message[:80]}")
            return
        # Slack returned False (no token?) — fall through to Telegram
        logger.warning("Slack send returned False — falling through to Telegram")
    except Exception as e:
        logger.warning(f"Slack alert failed ({e}) — falling through to Telegram")
    # Fallback: Telegram
    """Send alert to TPM via Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("No TELEGRAM_BOT_TOKEN set — alert not sent via Telegram")
        return False

    emoji = SEVERITY_EMOJI.get(severity, '')
    text = f"{emoji} *DRIFT {severity}*\n\n{message}\n\n_Governance Agent — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_"

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            'chat_id': TPM_CHAT_ID,
            'text': text,
            'parse_mode': 'Markdown',
        }, timeout=10)
        resp.raise_for_status()
        logger.info(f"Telegram alert sent: [{severity}] {message[:80]}")
        return True
    except Exception as e:
        logger.error(f"Telegram alert failed: {e}")

        # Fallback: try alert_manager if available
        try:
            sys.path.insert(0, '/ganuda')
            from lib.alert_manager import send_alert
            send_alert(f"[DRIFT {severity}] {message}")
            return True
        except ImportError:
            pass

        return False


def deliver_alerts(alerts):
    """Deliver alerts with cooldown and escalation ladder.

    - Tracks consecutive cycles each rule fires (_alert_streak)
    - Only sends external alert (Slack/Telegram) if streak >= escalate_after
    - Respects cooldown_hours between external alerts
    - Always logs to journal regardless of cooldown
    - Self-correcting: if a rule STOPS firing, streak resets and no more alerts
    """
    now = datetime.now(timezone.utc)
    fired_rules = {a['rule'] for a in alerts}

    # Reset streak for rules that are NOT firing this cycle (self-correction)
    for rule_name in list(_alert_streak.keys()):
        if rule_name not in fired_rules:
            old_streak = _alert_streak.pop(rule_name, 0)
            if old_streak >= 3:
                logger.info(f"[DRIFT SELF-CORRECTED] {rule_name} resolved after {old_streak} cycles")

    for alert in alerts:
        rule_name = alert.get('rule', 'unknown')
        rule_config = ALERT_RULES.get(rule_name, {})
        cooldown_hours = rule_config.get('cooldown_hours', 4)
        escalate_after = rule_config.get('escalate_after', 3)

        # Increment streak
        _alert_streak[rule_name] = _alert_streak.get(rule_name, 0) + 1
        streak = _alert_streak[rule_name]

        # Always log internally
        logger.info(f"[DRIFT {alert['severity']}] {alert['message']} (streak: {streak}/{escalate_after})")

        # Check if we should send external alert
        if streak < escalate_after:
            continue  # Not persistent enough yet — cluster handles it

        # Check cooldown
        last_sent = _alert_last_sent.get(rule_name)
        if last_sent and (now - last_sent).total_seconds() < cooldown_hours * 3600:
            continue  # Still in cooldown — don't spam Chief

        # Persistent and cooldown expired — escalate to Chief
        send_telegram_alert(alert['severity'], alert['message'])
        _alert_last_sent[rule_name] = now


# ============================================================================
# Metric storage
# ============================================================================

def store_metrics(metrics):
    """Store all collected metrics in drift_metrics table."""
    conn = get_conn()
    cur = conn.cursor()

    try:
        # Separate serializable scalar metrics from complex ones
        for metric_name, metric_value in metrics.items():
            # Skip non-numeric / complex values as top-level metric_value
            if isinstance(metric_value, (int, float)):
                details = {
                    'collected_at': datetime.now(timezone.utc).isoformat(),
                    'source': 'governance_agent',
                }
                cur.execute("""
                    INSERT INTO drift_metrics (metric_type, metric_value, details, measured_at)
                    VALUES (%s, %s, %s, NOW())
                """, (metric_name, float(metric_value), json.dumps(details)))
            elif isinstance(metric_value, dict):
                # Store complex metrics with value=0 and content in details
                cur.execute("""
                    INSERT INTO drift_metrics (metric_type, metric_value, details, measured_at)
                    VALUES (%s, %s, %s, NOW())
                """, (metric_name, 0.0, json.dumps(metric_value)))
            elif isinstance(metric_value, list):
                cur.execute("""
                    INSERT INTO drift_metrics (metric_type, metric_value, details, measured_at)
                    VALUES (%s, %s, %s, NOW())
                """, (metric_name, float(len(metric_value)), json.dumps(metric_value)))

        conn.commit()
        logger.info(f"Stored {len(metrics)} metrics in drift_metrics")

    except Exception as e:
        logger.error(f"Failed to store metrics: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()


# ============================================================================
# Main loop
# ============================================================================

def run_cycle():
    """Execute one governance monitoring cycle."""
    logger.info("=== Governance cycle starting ===")

    # 1. Collect metrics
    metrics = collect_metrics()
    logger.info(f"Collected {len(metrics)} metrics: {list(metrics.keys())}")

    # 2. Store metrics
    store_metrics(metrics)

    # 3. Check anomaly rules
    alerts = check_alerts(metrics)
    if alerts:
        logger.warning(f"{len(alerts)} alert(s) triggered")
        for a in alerts:
            logger.warning(f"  [{a['severity']}] {a['message']}")
        deliver_alerts(alerts)
    else:
        logger.info("No anomalies detected")

    logger.info("=== Governance cycle complete ===")
    return metrics, alerts


def main():
    """Run governance agent on 30-minute loop."""
    logger.info("Governance Agent starting — Phase 3B Drift Detection")
    logger.info(f"Cycle interval: {CYCLE_INTERVAL_SECONDS}s ({CYCLE_INTERVAL_SECONDS // 60} min)")
    logger.info(f"Integrity check every {INTEGRITY_CHECK_INTERVAL} cycles")

    while True:
        try:
            run_cycle()
        except Exception as e:
            logger.error(f"Governance cycle failed: {e}", exc_info=True)

        time.sleep(CYCLE_INTERVAL_SECONDS)


if __name__ == '__main__':
    main()
