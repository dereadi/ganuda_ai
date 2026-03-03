# JR Instruction: Elisi Observer Phase 2 — Valence Signal

**Task ID**: ELISI-PHASE2-VALENCE
**Priority**: 2
**Assigned Jr**: Software Engineer Jr.
**Sacred Fire**: false
**Use RLM**: false
**TEG Plan**: true
**Depends On**: ELISI-STATE-TABLE (elisi_state table must exist)

## Context

Elisi Phase 2 transitions from passive logging to active valence signaling. The observer computes V = U - E[U] using existing DB fields and activates epigenetic modifiers when degradation is detected. No model inference — pure arithmetic.

Council Votes: #97485885, #293fe9209ce79b90, #35dfc9184aabe1e6 (APPROVED 0.872)
Design Doc: `/ganuda/docs/design/DESIGN-ELISI-PHASE2-CONCERN-MITIGATION-MAR02-2026.md`

## Step 1: Update module docstring and constants

File: `/ganuda/services/ulisi/observer.py`

<<<<<<< SEARCH
"""
Elisi — The Grandmother Who Watches
Cherokee AI Federation Observer Model

Phase 1: Logging-only observation of Council votes and Jr execution results.
Elisi watches, records, and learns. She does not act.

Council Vote: #fdbb0dcf4a87fe5e (Unanimous)
Name: Elisi (ay-lee-see) — Cherokee for maternal grandmother

For Seven Generations
"""
=======
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
>>>>>>> REPLACE

## Step 2: Update constants and add Phase 2 config

File: `/ganuda/services/ulisi/observer.py`

<<<<<<< SEARCH
ELISI_VLLM_URL = "http://localhost:9100/v1/chat/completions"
ELISI_MODEL = "Qwen/Qwen2.5-7B-Instruct-AWQ"
POLL_INTERVAL = 120  # Check every 2 minutes
OBSERVATION_TEMP = 65.0  # Warm but not hot — observations, not sacred
=======
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
>>>>>>> REPLACE

## Step 3: Add valence computation functions after log_observation

File: `/ganuda/services/ulisi/observer.py`

<<<<<<< SEARCH
def format_council_observation(votes):
=======
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

        # DLQ depth (failed tasks with 3+ retries)
        cur.execute("""
            SELECT COUNT(*) FROM jr_work_queue
            WHERE status = 'failed' AND retry_count >= 3
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
>>>>>>> REPLACE

## Step 4: Update main loop for Phase 2

File: `/ganuda/services/ulisi/observer.py`

<<<<<<< SEARCH
def main():
    """Main observation loop."""
    logger.info("Elisi awakens. The grandmother watches.")
    logger.info(f"Phase 1: Logging-only mode. Poll interval: {POLL_INTERVAL}s")

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

            if not votes and not tasks:
                logger.debug("Quiet period — nothing to observe")

        except Exception as e:
            logger.error(f"Observation cycle error: {e}")

        time.sleep(POLL_INTERVAL)
=======
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
>>>>>>> REPLACE

## Verification

1. Ensure `elisi_state` table exists (run ELISI-STATE-TABLE migration first)
2. `python3 /ganuda/services/ulisi/observer.py` — should start with "Phase 2: Valence signaling"
3. After one cycle with activity, journal should show `Valence: U=... E[U]=... V=...`
4. After a quiet period (no votes or tasks for 90s+), should show "valence decaying toward neutral"

## Files Modified

- `/ganuda/services/ulisi/observer.py` (4 SEARCH/REPLACE blocks)
