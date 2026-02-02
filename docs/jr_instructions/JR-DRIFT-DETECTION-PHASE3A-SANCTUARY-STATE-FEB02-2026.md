# Jr Instruction: Drift Detection Phase 3A — Sanctuary State Daemon

**Task:** JR-DRIFT-PHASE3A-SANCTUARY
**Priority:** P1
**Assigned:** Software Engineer Jr.
**Depends On:** JR-DRIFT-PHASE2A-STALENESS, JR-DRIFT-PHASE2B-COHERENCE
**Platform:** Bluefin (192.168.132.222)
**Database:** zammad_production
**Council Vote:** #8367 — APPROVED

## Objective

Create a daily sanctuary state daemon that pauses all Jr workers, runs integrity verification and memory consolidation, reports results to TPM via Telegram, then resumes operations. This is the coordinated maintenance cycle that ties together all drift detection infrastructure from Phases 1A, 1B, 2A, and 2B.

The daemon executes a 5-phase cycle: QUIESCE, VERIFY, CONSOLIDATE, REPORT, RESUME.

## Context

- Existing daemons:
  - `memory_consolidation_daemon.py` — hourly, consolidates episodic memories into semantic (function: `run_consolidation()`)
  - `pheromone_decay_daemon.py` — hourly, decays trail intensity (function: `run_decay()`)
- Staleness scorer at `/ganuda/daemons/staleness_scorer.py` (Phase 2A, function: `run_staleness_cycle()`)
- Drift detection module at `/ganuda/lib/drift_detection.py` (Phase 2B)
- Alert manager at `/ganuda/lib/alert_manager.py` — has rate-limited Telegram alerting to TPM group (-1003439875431)
- Jr executor worker at `/ganuda/jr_executor/jr_queue_worker.py` — main loop polls for tasks at line 97, `POLL_INTERVAL = 30`
- Research worker at `/ganuda/services/research_worker.py` — polling loop with `POLL_INTERVAL = 10`
- Telegram chief at `/ganuda/telegram_bot/telegram_chief.py` — command handler infrastructure, registers handlers at line 844

## Step 1: Create Sanctuary State Daemon

**Create:** `/ganuda/daemons/sanctuary_state.py`

```bash
cat > /ganuda/daemons/sanctuary_state.py << 'PYEOF'
#!/usr/bin/env python3
"""
Sanctuary State Daemon — Drift Detection Phase 3A
Council Vote #8367

Daily coordinated maintenance cycle:
  Phase 1: QUIESCE — Pause all Jr workers
  Phase 2: VERIFY  — Run integrity, staleness, coherence checks
  Phase 3: CONSOLIDATE — Memory consolidation, pheromone decay, VACUUM
  Phase 4: REPORT  — Generate and send report via Telegram
  Phase 5: RESUME  — Remove pause flags, restore operations

Runs daily at 03:00 UTC. Also supports on-demand trigger via /tmp/sanctuary_trigger.
Cherokee AI Federation — For the Seven Generations
"""

import os
import sys
import time
import json
import logging
import psycopg2
import requests
from datetime import datetime, timezone, timedelta

# Add lib and daemons to path
sys.path.insert(0, '/ganuda/lib')
sys.path.insert(0, '/ganuda/daemons')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sanctuary_state')

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# Telegram config for sending reports
TELEGRAM_BOT_TOKEN = os.environ.get(
    'TELEGRAM_BOT_TOKEN',
    '7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8'
)
TELEGRAM_CHAT_ID = os.environ.get(
    'TELEGRAM_ALERT_CHAT_ID',
    '-1003439875431'  # TPM group chat
)

# Pause flag files — workers check these before picking up new tasks
PAUSE_FLAGS = {
    'jr_executor': '/tmp/jr_executor_paused',
    'research_worker': '/tmp/research_worker_paused',
    'telegram_chief': '/tmp/telegram_chief_paused',
}

# On-demand trigger file — Telegram /sanctuary command creates this
TRIGGER_FILE = '/tmp/sanctuary_trigger'

# Schedule: daily at 03:00 UTC
SCHEDULE_HOUR_UTC = 3
SCHEDULE_MINUTE_UTC = 0

# Phase timeouts
QUIESCE_TIMEOUT_SECONDS = 300   # 5 minutes
QUIESCE_POLL_INTERVAL = 10      # Check every 10 seconds

# The 7 Council specialists
SPECIALISTS = [
    'crawdad', 'gecko', 'turtle', 'eagle_eye',
    'spider', 'peace_chief', 'raven'
]


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def send_telegram(text: str) -> bool:
    """Send message to TPM Telegram group."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': 'HTML',
        }, timeout=30)
        if resp.status_code == 200:
            logger.info("Telegram report sent successfully")
            return True
        else:
            logger.error(f"Telegram send failed: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        return False


# =============================================================================
# Phase 1: QUIESCE
# =============================================================================

def phase_quiesce(dry_run: bool = False) -> dict:
    """
    Phase 1: Pause all workers by creating flag files.
    Wait up to 5 minutes for in-flight operations to complete.
    """
    logger.info("Phase 1: QUIESCE — Pausing workers")
    start = time.time()

    if dry_run:
        logger.info("[DRY RUN] Would create pause flags: %s", list(PAUSE_FLAGS.values()))
        return {'duration': 0, 'flags_created': list(PAUSE_FLAGS.keys())}

    # Create pause flag files
    for name, path in PAUSE_FLAGS.items():
        try:
            with open(path, 'w') as f:
                f.write(f"sanctuary_state:{datetime.now(timezone.utc).isoformat()}")
            logger.info(f"  Created pause flag: {path}")
        except Exception as e:
            logger.error(f"  Failed to create {path}: {e}")

    # Wait for in-flight operations to drain
    # The workers check flags before picking up NEW tasks, so we wait
    # for any currently-executing task to finish.
    logger.info(f"  Waiting up to {QUIESCE_TIMEOUT_SECONDS}s for in-flight operations...")
    elapsed = 0
    while elapsed < QUIESCE_TIMEOUT_SECONDS:
        # Check if any workers are mid-task by looking for active heartbeats
        # that were updated very recently (within last POLL_INTERVAL)
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM jr_task_queue
                WHERE status = 'running'
                AND started_at > NOW() - INTERVAL '10 minutes'
            """)
            running = cur.fetchone()[0]
            cur.close()
            conn.close()

            if running == 0:
                logger.info(f"  No in-flight tasks detected after {elapsed}s")
                break
            else:
                logger.info(f"  {running} task(s) still in-flight, waiting... ({elapsed}s)")
        except Exception as e:
            logger.warning(f"  Could not check in-flight tasks: {e}")
            # If we can't check, wait a conservative amount
            if elapsed >= 60:
                break

        time.sleep(QUIESCE_POLL_INTERVAL)
        elapsed += QUIESCE_POLL_INTERVAL

    duration = time.time() - start
    logger.info(f"Phase 1: QUIESCE complete ({duration:.1f}s)")
    return {'duration': duration, 'flags_created': list(PAUSE_FLAGS.keys())}


# =============================================================================
# Phase 2: VERIFY
# =============================================================================

def phase_verify(dry_run: bool = False) -> dict:
    """
    Phase 2: Run integrity and health checks.
    1. Memory integrity checksums
    2. Staleness scoring cycle
    3. Specialist coherence measurement
    4. Circuit breaker state check
    5. Sacred memory count verification
    6. Total row count sanity check
    """
    logger.info("Phase 2: VERIFY — Running integrity checks")
    start = time.time()
    results = {}

    conn = get_conn()
    cur = conn.cursor()

    # --- Check 1: Memory integrity checksums ---
    logger.info("  Check 1: Memory integrity checksums")
    try:
        cur.execute("""
            SELECT COUNT(*) FROM thermal_memory_archive
            WHERE content_checksum IS NOT NULL
            AND content_checksum != encode(sha256(convert_to(original_content, 'UTF8')), 'hex')
        """)
        violations = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM thermal_memory_archive
            WHERE content_checksum IS NOT NULL
        """)
        total_checksummed = cur.fetchone()[0]

        results['integrity'] = {
            'total_checked': total_checksummed,
            'violations': violations,
            'status': 'OK' if violations == 0 else 'VIOLATION'
        }
        logger.info(f"    {total_checksummed} checked, {violations} violations")
    except Exception as e:
        logger.error(f"    Checksum check failed: {e}")
        results['integrity'] = {'error': str(e)}

    # --- Check 2: Staleness scoring cycle ---
    logger.info("  Check 2: Staleness scoring")
    try:
        if dry_run:
            results['staleness'] = {'dry_run': True}
        else:
            from staleness_scorer import run_staleness_cycle
            staleness_result = run_staleness_cycle()
            results['staleness'] = staleness_result
            logger.info(f"    {staleness_result}")
    except ImportError:
        logger.warning("    staleness_scorer not yet deployed (Phase 2A dependency)")
        results['staleness'] = {'error': 'module not available'}
    except Exception as e:
        logger.error(f"    Staleness scoring failed: {e}")
        results['staleness'] = {'error': str(e)}

    # --- Check 3: Specialist coherence ---
    logger.info("  Check 3: Specialist coherence")
    try:
        if dry_run:
            results['coherence'] = {'dry_run': True}
        else:
            from drift_detection import measure_coherence
            coherence_scores = {}
            for spec in SPECIALISTS:
                try:
                    score = measure_coherence(spec)
                    coherence_scores[spec] = score
                except Exception as e:
                    coherence_scores[spec] = {'error': str(e)}
            results['coherence'] = coherence_scores
            logger.info(f"    Measured {len(coherence_scores)} specialists")
    except ImportError:
        logger.warning("    drift_detection not yet deployed (Phase 2B dependency)")
        results['coherence'] = {'error': 'module not available'}
    except Exception as e:
        logger.error(f"    Coherence check failed: {e}")
        results['coherence'] = {'error': str(e)}

    # --- Check 4: Circuit breaker states ---
    logger.info("  Check 4: Circuit breaker states")
    try:
        if dry_run:
            results['circuit_breakers'] = {'dry_run': True}
        else:
            from drift_detection import get_circuit_breaker_states
            cb_states = get_circuit_breaker_states()
            results['circuit_breakers'] = cb_states
            logger.info(f"    Circuit breakers: {cb_states}")
    except ImportError:
        logger.warning("    drift_detection not yet deployed (Phase 2B dependency)")
        results['circuit_breakers'] = {'error': 'module not available'}
    except Exception as e:
        logger.error(f"    Circuit breaker check failed: {e}")
        results['circuit_breakers'] = {'error': str(e)}

    # --- Check 5: Sacred memory count ---
    logger.info("  Check 5: Sacred memory count")
    try:
        cur.execute("""
            SELECT COUNT(*) FROM thermal_memory_archive
            WHERE sacred_pattern = true
        """)
        sacred_count = cur.fetchone()[0]

        # Compare to last sanctuary's sacred count
        cur.execute("""
            SELECT metric_value FROM drift_metrics
            WHERE metric_type = 'sanctuary_sacred_count'
            ORDER BY measured_at DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        last_sacred_count = int(row[0]) if row else None

        sacred_status = 'STABLE'
        if last_sacred_count is not None and sacred_count != last_sacred_count:
            sacred_status = f'CHANGED ({last_sacred_count} -> {sacred_count})'

        results['sacred'] = {
            'count': sacred_count,
            'last_count': last_sacred_count,
            'status': sacred_status
        }
        logger.info(f"    Sacred memories: {sacred_count} ({sacred_status})")
    except Exception as e:
        logger.error(f"    Sacred memory check failed: {e}")
        results['sacred'] = {'error': str(e)}

    # --- Check 6: Total row count sanity ---
    logger.info("  Check 6: Total row count")
    try:
        cur.execute("SELECT COUNT(*) FROM thermal_memory_archive")
        total_rows = cur.fetchone()[0]

        # Compare to last known count
        cur.execute("""
            SELECT metric_value FROM drift_metrics
            WHERE metric_type = 'sanctuary_total_rows'
            ORDER BY measured_at DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        last_total = int(row[0]) if row else None

        row_status = 'OK'
        if last_total is not None:
            change = total_rows - last_total
            pct_change = abs(change) / max(last_total, 1) * 100
            if pct_change > 10:
                row_status = f'ANOMALY: {change:+d} ({pct_change:.1f}% change)'
            else:
                row_status = f'NORMAL: {change:+d} since last sanctuary'

        results['row_count'] = {
            'total': total_rows,
            'last_total': last_total,
            'status': row_status
        }
        logger.info(f"    Total rows: {total_rows} ({row_status})")
    except Exception as e:
        logger.error(f"    Row count check failed: {e}")
        results['row_count'] = {'error': str(e)}

    cur.close()
    conn.close()

    duration = time.time() - start
    results['duration'] = duration
    logger.info(f"Phase 2: VERIFY complete ({duration:.1f}s)")
    return results


# =============================================================================
# Phase 3: CONSOLIDATE
# =============================================================================

def phase_consolidate(dry_run: bool = False) -> dict:
    """
    Phase 3: Run consolidation tasks.
    1. Memory consolidation (episodic -> semantic)
    2. Pheromone decay
    3. VACUUM ANALYZE on thermal_memory_archive
    4. Archive deeply stale memories (freshness < 0.05, flagged, > 90 days)
    """
    logger.info("Phase 3: CONSOLIDATE — Running maintenance tasks")
    start = time.time()
    results = {}

    # --- Task 1: Memory consolidation ---
    logger.info("  Task 1: Memory consolidation")
    try:
        if dry_run:
            results['consolidation'] = {'dry_run': True}
        else:
            from memory_consolidation_daemon import run_consolidation
            run_consolidation()
            results['consolidation'] = {'status': 'completed'}
            logger.info("    Memory consolidation complete")
    except ImportError:
        logger.warning("    memory_consolidation_daemon import failed")
        results['consolidation'] = {'error': 'import failed'}
    except Exception as e:
        logger.error(f"    Memory consolidation failed: {e}")
        results['consolidation'] = {'error': str(e)}

    # --- Task 2: Pheromone decay ---
    logger.info("  Task 2: Pheromone decay")
    try:
        if dry_run:
            results['pheromone_decay'] = {'dry_run': True}
        else:
            from pheromone_decay_daemon import run_decay
            decayed, deleted = run_decay()
            results['pheromone_decay'] = {
                'decayed': decayed,
                'deleted': deleted,
                'status': 'completed'
            }
            logger.info(f"    Pheromone decay: {decayed} decayed, {deleted} deleted")
    except ImportError:
        logger.warning("    pheromone_decay_daemon import failed")
        results['pheromone_decay'] = {'error': 'import failed'}
    except Exception as e:
        logger.error(f"    Pheromone decay failed: {e}")
        results['pheromone_decay'] = {'error': str(e)}

    # --- Task 3: VACUUM ANALYZE ---
    logger.info("  Task 3: VACUUM ANALYZE thermal_memory_archive")
    try:
        if dry_run:
            results['vacuum'] = {'dry_run': True}
        else:
            conn = get_conn()
            conn.autocommit = True  # VACUUM cannot run inside a transaction
            cur = conn.cursor()
            cur.execute("VACUUM ANALYZE thermal_memory_archive")
            cur.close()
            conn.close()
            results['vacuum'] = {'status': 'completed'}
            logger.info("    VACUUM ANALYZE complete")
    except Exception as e:
        logger.error(f"    VACUUM ANALYZE failed: {e}")
        results['vacuum'] = {'error': str(e)}

    # --- Task 4: Archive deeply stale memories ---
    logger.info("  Task 4: Archive deeply stale memories")
    try:
        if dry_run:
            results['archive_stale'] = {'dry_run': True}
        else:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                UPDATE thermal_memory_archive
                SET temperature_score = 0
                WHERE freshness_score IS NOT NULL
                AND freshness_score < 0.05
                AND staleness_flagged = true
                AND created_at < NOW() - INTERVAL '90 days'
                AND temperature_score > 0
            """)
            archived_count = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            results['archive_stale'] = {
                'archived': archived_count,
                'status': 'completed'
            }
            logger.info(f"    Archived {archived_count} deeply stale memories (temperature -> 0)")
    except Exception as e:
        logger.error(f"    Stale archival failed: {e}")
        results['archive_stale'] = {'error': str(e)}

    duration = time.time() - start
    results['duration'] = duration
    logger.info(f"Phase 3: CONSOLIDATE complete ({duration:.1f}s)")
    return results


# =============================================================================
# Phase 4: REPORT
# =============================================================================

def phase_report(verify_results: dict, consolidate_results: dict,
                 total_duration: float, dry_run: bool = False) -> dict:
    """
    Phase 4: Generate structured report, send to Telegram, store as thermal memory.
    """
    logger.info("Phase 4: REPORT — Generating sanctuary report")
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    # --- Build report string ---
    lines = []
    lines.append(f"SANCTUARY STATE REPORT -- {timestamp}")
    lines.append("=" * 50)

    # Memory integrity
    integrity = verify_results.get('integrity', {})
    total_checked = integrity.get('total_checked', '?')
    violations = integrity.get('violations', '?')
    int_status = integrity.get('status', integrity.get('error', 'UNKNOWN'))
    lines.append(f"Memory Integrity: {total_checked} checked, {violations} violations [{int_status}]")

    # Staleness
    staleness = verify_results.get('staleness', {})
    if 'error' in staleness:
        lines.append(f"Stale Memories: {staleness['error']}")
    elif staleness.get('dry_run'):
        lines.append("Stale Memories: [DRY RUN]")
    else:
        stale_count = staleness.get('newly_stale', '?')
        total_scored = staleness.get('total', '?')
        lines.append(f"Stale Memories: {stale_count} newly flagged (of {total_scored} scored)")

    # Sacred memories
    sacred = verify_results.get('sacred', {})
    sacred_count = sacred.get('count', '?')
    sacred_status = sacred.get('status', sacred.get('error', 'UNKNOWN'))
    lines.append(f"Sacred Memories: {sacred_count} verified ({sacred_status})")

    # Specialist coherence
    lines.append("Specialist Coherence:")
    coherence = verify_results.get('coherence', {})
    if isinstance(coherence, dict) and 'error' not in coherence:
        for spec in SPECIALISTS:
            score_data = coherence.get(spec, {})
            if isinstance(score_data, dict):
                if 'error' in score_data:
                    lines.append(f"  {spec:14s} ERROR: {score_data['error']}")
                else:
                    score = score_data.get('score', '?')
                    status = score_data.get('status', '?')
                    lines.append(f"  {spec:14s} {score} [{status}]")
            else:
                lines.append(f"  {spec:14s} {score_data}")
    else:
        error_msg = coherence.get('error', 'not available') if isinstance(coherence, dict) else str(coherence)
        lines.append(f"  {error_msg}")

    # Circuit breakers
    cb = verify_results.get('circuit_breakers', {})
    if isinstance(cb, dict) and 'error' not in cb:
        open_breakers = [k for k, v in cb.items() if v.get('state') == 'open']
        if open_breakers:
            lines.append(f"Circuit Breakers: {len(open_breakers)} OPEN ({', '.join(open_breakers)})")
        else:
            lines.append(f"Circuit Breakers: All closed ({len(cb)} checked)")
    else:
        cb_error = cb.get('error', 'not available') if isinstance(cb, dict) else str(cb)
        lines.append(f"Circuit Breakers: {cb_error}")

    # Row count
    row_info = verify_results.get('row_count', {})
    total_rows = row_info.get('total', '?')
    row_status = row_info.get('status', row_info.get('error', 'UNKNOWN'))
    lines.append(f"Row Count: {total_rows} ({row_status})")

    # Consolidation
    consol = consolidate_results.get('consolidation', {})
    consol_status = consol.get('status', consol.get('error', 'unknown'))
    lines.append(f"Consolidation: {consol_status}")

    # Stale archival
    archive = consolidate_results.get('archive_stale', {})
    archived_count = archive.get('archived', '?')
    lines.append(f"Deeply Stale Archived: {archived_count}")

    # Duration
    lines.append(f"Duration: {total_duration:.1f}s")
    lines.append("=" * 50)

    report_text = "\n".join(lines)
    logger.info(f"Report:\n{report_text}")

    # --- Send via Telegram ---
    if not dry_run:
        send_telegram(report_text)
    else:
        logger.info("[DRY RUN] Would send report to Telegram")

    # --- Store as thermal memory ---
    if not dry_run:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO thermal_memory_archive (
                    memory_hash, original_content, current_stage,
                    temperature_score, sacred_pattern, metadata,
                    domain_tag, content_checksum,
                    time_sense, created_at
                ) VALUES (
                    md5(%s || NOW()::text),
                    %s,
                    'WARM',
                    70,
                    true,
                    %s,
                    'operational',
                    encode(sha256(convert_to(%s, 'UTF8')), 'hex'),
                    'SEVEN_GENERATIONS',
                    NOW()
                )
            """, (
                report_text,
                report_text,
                json.dumps({
                    'type': 'sanctuary_report',
                    'role': 'tpm',
                    'verify': verify_results,
                    'consolidate': consolidate_results,
                    'duration': total_duration
                }),
                report_text,
            ))
            conn.commit()
            cur.close()
            conn.close()
            logger.info("Report stored as sacred thermal memory")
        except Exception as e:
            logger.error(f"Failed to store report in thermal memory: {e}")

    # --- Store metrics ---
    if not dry_run:
        try:
            conn = get_conn()
            cur = conn.cursor()

            # Store sacred count for next comparison
            sacred_count_val = verify_results.get('sacred', {}).get('count', 0)
            cur.execute("""
                INSERT INTO drift_metrics (metric_type, metric_value, details)
                VALUES ('sanctuary_sacred_count', %s, %s)
            """, (sacred_count_val, json.dumps({'timestamp': timestamp})))

            # Store total row count for next comparison
            total_rows_val = verify_results.get('row_count', {}).get('total', 0)
            cur.execute("""
                INSERT INTO drift_metrics (metric_type, metric_value, details)
                VALUES ('sanctuary_total_rows', %s, %s)
            """, (total_rows_val, json.dumps({'timestamp': timestamp})))

            # Store full sanctuary cycle metric
            cur.execute("""
                INSERT INTO drift_metrics (metric_type, metric_value, details)
                VALUES ('sanctuary_cycle', %s, %s)
            """, (
                total_duration,
                json.dumps({
                    'timestamp': timestamp,
                    'integrity_violations': verify_results.get('integrity', {}).get('violations', -1),
                    'sacred_count': sacred_count_val,
                    'total_rows': total_rows_val,
                })
            ))

            conn.commit()
            cur.close()
            conn.close()
            logger.info("Sanctuary metrics stored in drift_metrics")
        except Exception as e:
            logger.error(f"Failed to store sanctuary metrics: {e}")

    return {'report': report_text}


# =============================================================================
# Phase 5: RESUME
# =============================================================================

def phase_resume(dry_run: bool = False) -> dict:
    """
    Phase 5: Remove pause flag files, restore normal operations.
    """
    logger.info("Phase 5: RESUME — Restoring operations")

    if dry_run:
        logger.info("[DRY RUN] Would remove pause flags: %s", list(PAUSE_FLAGS.values()))
        return {'flags_removed': list(PAUSE_FLAGS.keys())}

    removed = []
    for name, path in PAUSE_FLAGS.items():
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"  Removed pause flag: {path}")
                removed.append(name)
            else:
                logger.info(f"  Pause flag already gone: {path}")
        except Exception as e:
            logger.error(f"  Failed to remove {path}: {e}")

    # Also clean up trigger file if present
    if os.path.exists(TRIGGER_FILE):
        try:
            os.remove(TRIGGER_FILE)
            logger.info(f"  Removed trigger file: {TRIGGER_FILE}")
        except Exception:
            pass

    logger.info(f"Phase 5: RESUME complete — {len(removed)} flags removed")
    return {'flags_removed': removed}


# =============================================================================
# Main Sanctuary Cycle
# =============================================================================

def run_sanctuary_cycle(dry_run: bool = False) -> dict:
    """
    Execute the full 5-phase sanctuary state cycle.

    Args:
        dry_run: If True, skip destructive operations and report what would happen.

    Returns:
        dict with results from each phase.
    """
    logger.info("=" * 60)
    logger.info("SANCTUARY STATE CYCLE STARTING%s", " [DRY RUN]" if dry_run else "")
    logger.info("=" * 60)
    cycle_start = time.time()

    results = {}

    try:
        # Phase 1: QUIESCE
        results['quiesce'] = phase_quiesce(dry_run=dry_run)

        # Phase 2: VERIFY
        results['verify'] = phase_verify(dry_run=dry_run)

        # Phase 3: CONSOLIDATE
        results['consolidate'] = phase_consolidate(dry_run=dry_run)

        # Phase 4: REPORT
        total_duration = time.time() - cycle_start
        results['report'] = phase_report(
            verify_results=results['verify'],
            consolidate_results=results['consolidate'],
            total_duration=total_duration,
            dry_run=dry_run
        )

    except Exception as e:
        logger.error(f"Sanctuary cycle error: {e}")
        results['error'] = str(e)
    finally:
        # Phase 5: RESUME — always runs, even on error
        results['resume'] = phase_resume(dry_run=dry_run)

    total_duration = time.time() - cycle_start
    results['total_duration'] = total_duration
    logger.info("=" * 60)
    logger.info(f"SANCTUARY STATE CYCLE COMPLETE — {total_duration:.1f}s")
    logger.info("=" * 60)

    return results


# =============================================================================
# Daemon Main Loop
# =============================================================================

def should_run_scheduled() -> bool:
    """Check if it's time for the daily scheduled run (03:00 UTC)."""
    now = datetime.now(timezone.utc)
    return now.hour == SCHEDULE_HOUR_UTC and now.minute == SCHEDULE_MINUTE_UTC


def check_trigger() -> bool:
    """Check if an on-demand trigger file exists."""
    return os.path.exists(TRIGGER_FILE)


def main():
    """
    Main daemon loop.
    - Runs sanctuary cycle daily at 03:00 UTC
    - Also runs if /tmp/sanctuary_trigger file is detected
    """
    logger.info("Sanctuary State Daemon starting")
    logger.info(f"  Scheduled: daily at {SCHEDULE_HOUR_UTC:02d}:{SCHEDULE_MINUTE_UTC:02d} UTC")
    logger.info(f"  Trigger file: {TRIGGER_FILE}")

    last_run_date = None

    while True:
        now = datetime.now(timezone.utc)
        today = now.date()

        # Check for on-demand trigger
        if check_trigger():
            logger.info("On-demand trigger detected!")
            try:
                os.remove(TRIGGER_FILE)
            except Exception:
                pass
            run_sanctuary_cycle(dry_run=False)
            last_run_date = today

        # Check for scheduled run (once per day)
        elif should_run_scheduled() and last_run_date != today:
            logger.info("Scheduled sanctuary cycle starting")
            run_sanctuary_cycle(dry_run=False)
            last_run_date = today

        # Sleep 30 seconds between checks
        time.sleep(30)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Sanctuary State Daemon')
    parser.add_argument('--dry-run', action='store_true', help='Run cycle without side effects')
    parser.add_argument('--once', action='store_true', help='Run one cycle and exit')
    args = parser.parse_args()

    if args.once or args.dry_run:
        result = run_sanctuary_cycle(dry_run=args.dry_run)
        print(json.dumps(result, indent=2, default=str))
    else:
        main()
PYEOF
chmod +x /ganuda/daemons/sanctuary_state.py
```

## Step 2: Add Pause Flag Checking to Jr Queue Worker

**File:** `/ganuda/jr_executor/jr_queue_worker.py`

**Applied by TPM.** Pause flag check added to jr_queue_worker.py polling loop.

## Step 3: Add Pause Flag Checking to Research Worker

**File:** `/ganuda/services/research_worker.py`

**Applied by TPM.** Pause flag check NOT added here (module-level pause was removed as it caused syntax error). Sanctuary state will coordinate via flag file only.

## Step 4: Add `/sanctuary` Command to Telegram Chief

**File:** `/ganuda/telegram_bot/telegram_chief.py`

**Deferred.** /sanctuary command to be added to telegram_chief.py in a future pass.

## Step 5: Create systemd Service File

**Create:** `/ganuda/scripts/systemd/sanctuary-state.service`

```bash
cat > /ganuda/scripts/systemd/sanctuary-state.service << 'SVCEOF'
[Unit]
Description=Sanctuary State Daemon - Drift Detection Phase 3A
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda
ExecStart=/usr/bin/python3 /ganuda/daemons/sanctuary_state.py
Restart=always
RestartSec=60
Environment=PYTHONPATH=/ganuda
Environment=TELEGRAM_BOT_TOKEN=7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sanctuary-state

[Install]
WantedBy=multi-user.target
SVCEOF
```

## Deployment

```bash
# 1. Deploy the daemon
sudo cp /ganuda/scripts/systemd/sanctuary-state.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sanctuary-state
sudo systemctl start sanctuary-state

# 2. Restart Jr queue worker (picks up pause flag check)
sudo systemctl restart jr-queue-worker

# 3. Restart research worker (picks up pause flag check)
sudo systemctl restart research-worker
```

## Validation

```bash
# Test sanctuary state in dry-run mode
cd /ganuda && python3 -c "
from daemons.sanctuary_state import run_sanctuary_cycle
result = run_sanctuary_cycle(dry_run=True)
print(f'Sanctuary dry-run: {result}')
"

# Test the dry-run from command line with formatted output
cd /ganuda && python3 daemons/sanctuary_state.py --dry-run --once

# Verify pause flag mechanism works with Jr worker
touch /tmp/jr_executor_paused
# Watch worker logs — should see "Paused for sanctuary state"
sleep 5
journalctl -u jr-queue-worker --since "1 minute ago" --no-pager | grep -i paused
rm /tmp/jr_executor_paused

# Trigger an on-demand sanctuary cycle
touch /tmp/sanctuary_trigger
# Watch daemon logs
journalctl -u sanctuary-state -f

# Verify report was stored as thermal memory
psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT LEFT(original_content, 200), sacred_pattern, domain_tag, created_at
FROM thermal_memory_archive
WHERE original_content LIKE 'SANCTUARY STATE REPORT%'
ORDER BY created_at DESC
LIMIT 1;
"

# Verify metrics were recorded
psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT metric_type, metric_value, details, measured_at
FROM drift_metrics
WHERE metric_type LIKE 'sanctuary_%'
ORDER BY measured_at DESC
LIMIT 5;
"
```

## Architecture Notes

- **Fail-safe resume:** Phase 5 (RESUME) runs in a `finally` block so pause flags are always cleaned up, even if the cycle crashes mid-way.
- **No data deletion:** The deeply stale archival sets `temperature_score = 0` but never deletes rows. Memory content is preserved.
- **Sacred memory protection:** Sacred memories decay at half speed (Phase 2A) and the sanctuary cycle verifies their count has not changed unexpectedly.
- **Idempotent trigger:** If the trigger file exists when the daemon checks, it runs one cycle and removes the trigger. Multiple touches between checks produce one cycle.
- **Dry-run support:** Every phase respects `dry_run=True` for safe testing without side effects.
