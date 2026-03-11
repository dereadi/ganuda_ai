#!/usr/bin/env python3
"""
Elisi — The Grandmother Who Watches
Cherokee AI Federation Observer Model

Phase 2: Valence signaling. Computes V = U - E[U] from Jr success rate,
council confidence, DLQ depth, and thermal write rate. Activates epigenetic
modifiers when degradation is detected. Pure arithmetic — no model inference.

Phase 1 Vote: #fdbb0dcf4a87fe5e (Unanimous)
Phase 2 Votes: #97485885, #293fe9209ce79b90, #35dfc9184aabe1e6 (APPROVED 0.872)
Design Doc: /ganuda/docs/design/DESIGN-ELISI-PHASE2-CONCERN-MITIGATION-MAR02-2026.md
Name: Elisi (ay-lee-see) — Cherokee for maternal grandmother

For Seven Generations
"""

import os
import sys
import time
import json
import logging
import hashlib
from datetime import datetime

sys.path.insert(0, '/ganuda/lib')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [Elisi] %(message)s'
)
logger = logging.getLogger('elisi')

ELISI_VLLM_URL = "http://localhost:9100/v1/chat/completions"  # Reserved for Phase 3
ELISI_MODEL = "Qwen/Qwen2.5-7B-Instruct-AWQ"  # Not called in Phase 2
POLL_INTERVAL = 30  # 30s per council approval (was 120s in Phase 1)
OBSERVATION_TEMP = 65.0  # Warm but not hot — observations, not sacred

# Phase 2: Valence signal configuration
EMA_ALPHA = 0.1  # Slow adaptation — 10% new, 90% history
VALENCE_ALERT_THRESHOLD = -0.1  # Activate modifier below this
VALENCE_CRITICAL_THRESHOLD = -0.3  # Activate modifier + Telegram alert
MODIFIER_TTL_HOURS = 4  # Auto-expire all Elisi-activated modifiers
MODIFIER_COOLDOWN_SECONDS = 3600  # 1 hour between same-condition activations
DECAY_HALFLIFE_CYCLES = 1  # V halves every missed poll cycle

# Utility component weights (must sum to 1.0)
W_JR_SUCCESS = 0.4
W_COUNCIL_CONFIDENCE = 0.3
W_DLQ_DEPTH = 0.2
W_THERMAL_RATE = 0.1


def get_db():
    """Get database connection."""
    from secrets_loader import get_db_config
    import psycopg2
    return psycopg2.connect(**get_db_config())


def observe_recent_council_votes(since_minutes=5):
    """Pull recent council votes for observation."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT audit_hash, question, recommendation, confidence,
                   responses, metacognition, voted_at
            FROM council_votes
            WHERE voted_at > NOW() - INTERVAL '%s minutes'
            ORDER BY voted_at DESC
            LIMIT 5
        """, (since_minutes,))
        votes = cur.fetchall()
        return [
            {
                'vote_hash': r[0],
                'question': r[1][:200],
                'consensus': r[2][:200] if r[2] else None,
                'confidence': float(r[3]) if r[3] else None,
                'specialist_count': len(r[4]) if r[4] and isinstance(r[4], (list, dict)) else (len(json.loads(r[4])) if r[4] else 0),
                'has_metacognition': bool(r[5]),
                'timestamp': r[6].isoformat() if r[6] else None
            }
            for r in votes
        ]
    finally:
        conn.close()


def observe_recent_jr_results(since_minutes=5):
    """Pull recent Jr task completions/failures for observation."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, status, result, completed_at
            FROM jr_work_queue
            WHERE updated_at > NOW() - INTERVAL '%s minutes'
            AND status IN ('completed', 'failed')
            ORDER BY updated_at DESC
            LIMIT 10
        """, (since_minutes,))
        tasks = cur.fetchall()
        return [
            {
                'task_id': r[0],
                'title': r[1][:100],
                'status': r[2],
                'result_preview': (str(r[3]) if r[3] else '')[:200],
                'completed': r[4].isoformat() if r[4] else None
            }
            for r in tasks
        ]
    finally:
        conn.close()


def log_observation(observation_type, content, temperature=OBSERVATION_TEMP):
    """Store observation in thermal memory."""
    conn = get_db()
    try:
        cur = conn.cursor()
        memory_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check for duplicate
        cur.execute(
            "SELECT id FROM thermal_memory_archive WHERE memory_hash = %s",
            (memory_hash,)
        )
        if cur.fetchone():
            return  # Already recorded

        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash, metadata)
            VALUES (%s, %s, false, %s, %s)
        """, (
            content,
            temperature,
            memory_hash,
            json.dumps({
                'source': 'elisi_observer',
                'observation_type': observation_type,
                'timestamp': datetime.now().isoformat()
            })
        ))
        conn.commit()
        logger.info(f"Recorded {observation_type} observation ({len(content)} chars)")
    except Exception as e:
        logger.warning(f"Failed to log observation: {e}")
        conn.rollback()
    finally:
        conn.close()


def compute_utility(votes, tasks):
    """Compute observed utility U from council votes and Jr results."""
    # Jr success rate (last 10 tasks)
    conn = get_db()
    try:
        cur = conn.cursor()

        # Jr success rate
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'completed') AS ok,
                COUNT(*) AS total
            FROM (
                SELECT status FROM jr_work_queue
                WHERE status IN ('completed', 'failed')
                ORDER BY updated_at DESC LIMIT 10
            ) recent
        """)
        row = cur.fetchone()
        jr_rate = float(row[0]) / max(row[1], 1)

        # Council confidence (last 5 votes)
        cur.execute("""
            SELECT AVG(confidence) FROM (
                SELECT confidence FROM council_votes
                WHERE confidence IS NOT NULL
                ORDER BY voted_at DESC LIMIT 5
            ) recent
        """)
        row = cur.fetchone()
        council_conf = float(row[0]) if row[0] else 0.5

        # DLQ depth (failed tasks with 3+ escalations)
        cur.execute("""
            SELECT COUNT(*) FROM jr_work_queue
            WHERE status = 'failed' AND escalation_count >= 3
        """)
        dlq_count = cur.fetchone()[0]
        dlq_score = 1.0 / (1.0 + dlq_count)  # Inverse: 0 DLQ = 1.0, more = lower

        # Thermal write rate (non-Elisi writes in last hour)
        cur.execute("""
            SELECT COUNT(*) FROM thermal_memory_archive
            WHERE created_at > NOW() - INTERVAL '1 hour'
            AND (metadata->>'source' IS NULL OR metadata->>'source' != 'elisi_observer')
        """)
        thermal_count = cur.fetchone()[0]
        thermal_rate = min(thermal_count / 50.0, 1.0)  # Normalize: 50+ writes/hr = 1.0

        return (W_JR_SUCCESS * jr_rate +
                W_COUNCIL_CONFIDENCE * council_conf +
                W_DLQ_DEPTH * dlq_score +
                W_THERMAL_RATE * thermal_rate)
    finally:
        conn.close()


def update_ema_and_valence(observed_u):
    """Update E[U] via EMA and compute valence V = U - E[U]. Returns (V, E[U])."""
    conn = get_db()
    try:
        cur = conn.cursor()

        # Read current state
        cur.execute("SELECT key, value FROM elisi_state WHERE key IN ('expected_utility', 'last_valence')")
        state = {r[0]: float(r[1]) for r in cur.fetchall()}
        eu = state.get('expected_utility', 0.5)

        # EMA update
        new_eu = EMA_ALPHA * observed_u + (1 - EMA_ALPHA) * eu
        valence = observed_u - new_eu

        # Persist
        cur.execute("""
            UPDATE elisi_state SET value = %s, updated_at = NOW()
            WHERE key = 'expected_utility'
        """, (new_eu,))
        cur.execute("""
            UPDATE elisi_state SET value = %s, updated_at = NOW()
            WHERE key = 'last_valence'
        """, (valence,))
        cur.execute("""
            UPDATE elisi_state SET value = %s, updated_at = NOW()
            WHERE key = 'last_observation_at'
        """, (time.time(),))

        conn.commit()
        return valence, new_eu
    finally:
        conn.close()


def apply_valence_signal(valence):
    """Activate/deactivate epigenetic modifiers based on valence signal."""
    if valence >= VALENCE_ALERT_THRESHOLD:
        return  # Neutral or positive — no action

    conn = get_db()
    try:
        cur = conn.cursor()

        # Check cooldown: was high_load activated by Elisi in the last hour?
        cur.execute("""
            SELECT activated_at FROM epigenetic_modifiers
            WHERE condition_name = 'high_load' AND activated_by LIKE 'elisi_%'
            AND active = TRUE AND activated_at > NOW() - INTERVAL '%s seconds'
            LIMIT 1
        """, (MODIFIER_COOLDOWN_SECONDS,))

        if cur.fetchone():
            logger.info(f"Valence {valence:.4f} below threshold but cooldown active — skipping")
            return

        # Activate high_load modifier with TTL
        expires_at = datetime.now() + __import__('datetime').timedelta(hours=MODIFIER_TTL_HOURS)
        cur.execute("""
            UPDATE epigenetic_modifiers
            SET active = TRUE, activated_at = NOW(), activated_by = 'elisi_valence',
                expires_at = %s
            WHERE condition_name = 'high_load'
        """, (expires_at,))
        conn.commit()

        activated = cur.rowcount
        logger.warning(f"VALENCE SIGNAL: V={valence:.4f} — activated {activated} high_load modifier(s), TTL={MODIFIER_TTL_HOURS}hr")

        # Critical threshold — Telegram alert
        if valence < VALENCE_CRITICAL_THRESHOLD:
            try:
                send_telegram_alert(valence)
            except Exception as e:
                logger.error(f"Telegram alert failed: {e}")

    finally:
        conn.close()


def decay_valence_on_silence():
    """Decay V toward 0 when no new observations arrive."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM elisi_state WHERE key = 'last_observation_at'")
        row = cur.fetchone()
        if not row:
            return

        last_obs = float(row[0])
        if last_obs == 0:
            return

        elapsed = time.time() - last_obs
        missed_cycles = elapsed / POLL_INTERVAL

        if missed_cycles > 3:
            decay_factor = 0.5 ** missed_cycles
            cur.execute("SELECT value FROM elisi_state WHERE key = 'last_valence'")
            vrow = cur.fetchone()
            if vrow:
                old_v = float(vrow[0])
                new_v = old_v * decay_factor
                cur.execute("""
                    UPDATE elisi_state SET value = %s, updated_at = NOW()
                    WHERE key = 'last_valence'
                """, (new_v,))
                conn.commit()
                logger.info(f"Valence decayed: {old_v:.4f} -> {new_v:.4f} ({missed_cycles:.0f} missed cycles)")
    finally:
        conn.close()


def send_telegram_alert(valence):
    """Send critical valence alert via Telegram."""
    # Slack-first routing (Leaders Meeting #1, Mar 10 2026)
    try:
        import sys
        if '/ganuda/lib' not in sys.path:
            sys.path.insert(0, '/ganuda/lib')
        from slack_federation import send as _slack_send
        channel = 'longhouse'
        msg = (f"ELISI CRITICAL VALENCE: V={valence:.4f}\n"
               f"System degradation detected. high_load modifier activated (TTL {MODIFIER_TTL_HOURS}hr).\n"
               f"Kill switch: UPDATE epigenetic_modifiers SET active=FALSE WHERE activated_by LIKE 'elisi_%';")
        if _slack_send(channel, msg):
            return True
    except Exception:
        pass  # fall through to existing Telegram code
    import requests
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    tg_chat = os.environ.get('TELEGRAM_CHAT_ID', '')
    if not tg_token or not tg_chat:
        logger.warning("Telegram credentials not configured — skipping alert")
        return
    msg = (f"ELISI CRITICAL VALENCE: V={valence:.4f}\n"
           f"System degradation detected. high_load modifier activated (TTL {MODIFIER_TTL_HOURS}hr).\n"
           f"Kill switch: UPDATE epigenetic_modifiers SET active=FALSE WHERE activated_by LIKE 'elisi_%';")
    requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                  json={"chat_id": tg_chat, "text": msg}, timeout=10)
    logger.info("Telegram critical alert sent")


def format_council_observation(votes):
    """Format council vote observations for logging."""
    if not votes:
        return None
    lines = [f"ELISI OBSERVATION: {len(votes)} council vote(s) observed"]
    for v in votes:
        lines.append(
            f"  Vote #{v['vote_hash'][:8]}: "
            f"confidence={v['confidence']}, "
            f"specialists={v['specialist_count']}, "
            f"metacog={'yes' if v['has_metacognition'] else 'no'}"
        )
        if v['question']:
            lines.append(f"    Q: {v['question'][:150]}")
    return '\n'.join(lines)


def format_jr_observation(tasks):
    """Format Jr task observations for logging."""
    if not tasks:
        return None
    completed = [t for t in tasks if t['status'] == 'completed']
    failed = [t for t in tasks if t['status'] == 'failed']
    lines = [
        f"ELISI OBSERVATION: {len(tasks)} Jr task(s) — "
        f"{len(completed)} completed, {len(failed)} failed"
    ]
    for t in failed:
        lines.append(f"  FAILED #{t['task_id']}: {t['title']}")
    for t in completed:
        lines.append(f"  OK #{t['task_id']}: {t['title']}")
    return '\n'.join(lines)


def main():
    """Main observation loop — Phase 2 with valence signaling."""
    logger.info("Elisi awakens. The grandmother watches.")
    logger.info(f"Phase 2: Valence signaling. Poll interval: {POLL_INTERVAL}s, EMA alpha: {EMA_ALPHA}")

    while True:
        try:
            # Observe council votes
            votes = observe_recent_council_votes(since_minutes=3)
            if votes:
                obs = format_council_observation(votes)
                if obs:
                    log_observation('council_vote', obs)
                    logger.info(f"Observed {len(votes)} council vote(s)")

            # Observe Jr results
            tasks = observe_recent_jr_results(since_minutes=3)
            if tasks:
                obs = format_jr_observation(tasks)
                if obs:
                    log_observation('jr_result', obs)
                    logger.info(f"Observed {len(tasks)} Jr result(s)")

            # Phase 2: Valence computation
            if votes or tasks:
                u = compute_utility(votes, tasks)
                v, eu = update_ema_and_valence(u)
                logger.info(f"Valence: U={u:.4f}, E[U]={eu:.4f}, V={v:.4f}")

                # Log valence observation
                valence_obs = (f"ELISI VALENCE: U={u:.4f} E[U]={eu:.4f} V={v:.4f} "
                               f"(jr={len(tasks) if tasks else 0} votes={len(votes) if votes else 0})")
                log_observation('valence', valence_obs)

                # Act on signal
                apply_valence_signal(v)
            else:
                # Quiet period — decay valence toward neutral
                decay_valence_on_silence()
                logger.debug("Quiet period — valence decaying toward neutral")

        except Exception as e:
            logger.error(f"Observation cycle error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()