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

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
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
    },
    'specialist_concern_spike': {
        'condition': lambda m: any(c > 5 for c in m.get('concerns_by_specialist', {}).values()),
        'severity': 'WARNING',
        'message': 'Specialist raised >5 concerns in 24h: {details}',
        'value_key': 'concerns_by_specialist',
    },
    'jr_failure_rate': {
        'condition': lambda m: m.get('jr_success_rate_24h', 1.0) < 0.7,
        'severity': 'ALERT',
        'message': 'Jr task failure rate >30% in 24h (success rate: {value:.0%})',
        'value_key': 'jr_success_rate_24h',
    },
    'memory_integrity_violation': {
        'condition': lambda m: m.get('integrity_violations', 0) > 0,
        'severity': 'CRITICAL',
        'message': '{count} thermal memory integrity violations detected!',
        'value_key': 'integrity_violations',
    },
    'sacred_memory_count_change': {
        'condition': lambda m: (
            m.get('sacred_count', 0) < m.get('expected_sacred_count', 0)
        ),
        'severity': 'CRITICAL',
        'message': 'Sacred memory count DECREASED: expected {expected}, got {actual}',
        'value_key': 'sacred_count',
    },
    'circuit_breaker_open': {
        'condition': lambda m: m.get('open_breakers', 0) > 0,
        'severity': 'ALERT',
        'message': '{count} specialist circuit breaker(s) OPEN: {specialists}',
        'value_key': 'open_breakers',
    },
    'memory_growth_anomaly': {
        'condition': lambda m: m.get('memory_count_24h', 0) > 500,
        'severity': 'WARNING',
        'message': 'Unusual memory growth: {count} new memories in 24h',
        'value_key': 'memory_count_24h',
    },
}

# Persistent state file for cross-cycle tracking
STATE_FILE = '/ganuda/daemons/.governance_state.json'


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


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
              AND content_checksum != encode(sha256(original_content::bytea), 'hex')
        """)
        metrics['integrity_violations'] = int(cur.fetchone()[0])
        logger.info(f"Integrity check complete: {metrics['integrity_violations']} violations")
    else:
        metrics['integrity_violations'] = 0

    return metrics


def collect_circuit_breaker_metrics():
    """Collect circuit breaker states from drift detection module."""
    metrics = {
        'open_breakers': 0,
        'half_open_breakers': 0,
        'closed_breakers': 0,
        'open_specialists': [],
    }

    try:
        # Import from drift_detection if available (Phase 2B)
        sys.path.insert(0, '/ganuda')
        from lib.drift_detection import get_circuit_breaker_states
        states = get_circuit_breaker_states()

        for specialist, state in states.items():
            if state == 'OPEN':
                metrics['open_breakers'] += 1
                metrics['open_specialists'].append(specialist)
            elif state == 'HALF_OPEN':
                metrics['half_open_breakers'] += 1
            else:
                metrics['closed_breakers'] += 1
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
    """Deliver all triggered alerts via Telegram."""
    for alert in alerts:
        send_telegram_alert(alert['severity'], alert['message'])


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
async def cmd_drift_status(self, update, context):
    """Show current drift detection status from governance agent metrics."""
    try:
        conn = self.get_db()
        cur = conn.cursor()

        # Get most recent value for each metric type
        cur.execute("""
            SELECT DISTINCT ON (metric_type)
                metric_type, metric_value, details, measured_at
            FROM drift_metrics
            WHERE metric_type IN (
                'avg_confidence_24h', 'jr_success_rate_24h',
                'integrity_violations', 'stale_count', 'sacred_count',
                'open_breakers', 'memory_count_total', 'memory_count_24h'
            )
            ORDER BY metric_type, measured_at DESC
        """)
        rows = cur.fetchall()
        cur.close()

        if not rows:
            await update.message.reply_text(
                "No drift metrics found. Governance agent may not have run yet."
            )
            return

        metrics = {}
        last_measured = None
        for row in rows:
            metrics[row[0]] = row[1]
            if last_measured is None or row[3] > last_measured:
                last_measured = row[3]

        timestamp = last_measured.strftime('%Y-%m-%d %H:%M UTC') if last_measured else 'Unknown'
        confidence = metrics.get('avg_confidence_24h', 0)
        jr_rate = metrics.get('jr_success_rate_24h', 0) * 100
        violations = int(metrics.get('integrity_violations', 0))
        stale = int(metrics.get('stale_count', 0))
        sacred = int(metrics.get('sacred_count', 0))
        open_cb = int(metrics.get('open_breakers', 0))
        mem_total = int(metrics.get('memory_count_total', 0))
        mem_24h = int(metrics.get('memory_count_24h', 0))

        cb_summary = f"{open_cb} OPEN" if open_cb > 0 else "All CLOSED"
        integrity_display = f"{violations} violations" if violations > 0 else "Clean"

        status_text = (
            f"\U0001f4ca *DRIFT STATUS* \u2014 {timestamp}\n\n"
            f"*Council Confidence (24h):* {confidence:.2f}\n"
            f"*Jr Success Rate (24h):* {jr_rate:.0f}%\n"
            f"*Memory Integrity:* {integrity_display}\n"
            f"*Stale Memories:* {stale}\n"
            f"*Sacred Memories:* {sacred}\n"
            f"*Total Memories:* {mem_total} (+{mem_24h} in 24h)\n"
            f"*Circuit Breakers:* {cb_summary}\n"
        )

        await update.message.reply_text(status_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"drift-status command failed: {e}")
        await update.message.reply_text(f"Error fetching drift status: {e}")

