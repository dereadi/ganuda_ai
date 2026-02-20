# Jr Instruction: TPM Autonomic Daemon — Level 5+ Basin-Breaker Phase 1

**Task ID**: TPM-DAEMON-001
**Priority**: 1 (critical)
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 8
**use_rlm**: false
**Council Votes**: #1fda4f47a272c989 (PROCEED WITH CAUTION, 0.889), #6fe918ac1373d2c8 (PROCEED, 0.89)
**Kanban**: #1819

## Context

Build a Python daemon that orchestrates the Cherokee AI Federation using the Claude Agent SDK (pip install claude-agent-sdk). This daemon replaces the existing basic tpm_autonomic.py (305 lines, 4 signals) with a full Level 5+ basin-breaker that polls the jr_work_queue, spawns Claude subagents for task execution, monitors federation health, and escalates to the council at phase transitions.

The Claude Agent SDK was released Feb 18, 2026 by Anthropic. It wraps the claude CLI as a subprocess and provides async Python APIs for spawning agents with tool restrictions, cost caps, and hooks.

## Step 1: Create the TPM Autonomic Daemon

Create `/ganuda/daemons/tpm_autonomic_v2.py`

```python
#!/usr/bin/env python3
"""
TPM Autonomic Daemon v2 — Level 5+ Basin-Breaker

Orchestrates the Cherokee AI Federation using Claude Agent SDK.
Polls jr_work_queue, spawns Claude subagents, monitors basin signals,
escalates to council at phase transitions.

Council Votes: #1fda4f47a272c989, #6fe918ac1373d2c8
Sacred Fire: true
"""

import os
import sys
import json
import asyncio
import logging
import hashlib
import signal
from datetime import datetime, timedelta
from collections import deque

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("tpm-autonomic")

# ── Configuration ──────────────────────────────────────────────────────────

POLL_INTERVAL = int(os.environ.get("TPM_POLL_INTERVAL", "60"))
MAX_CONCURRENT_TASKS = int(os.environ.get("TPM_MAX_CONCURRENT", "3"))
MAX_BUDGET_PER_TASK = float(os.environ.get("TPM_MAX_BUDGET", "2.00"))
BASIN_CHECK_INTERVAL = int(os.environ.get("TPM_BASIN_INTERVAL", "300"))

DB_PARAMS = {
    "host": os.environ.get("DB_HOST", "192.168.132.222"),
    "dbname": os.environ.get("DB_NAME", "zammad_production"),
    "user": os.environ.get("DB_USER", "claude"),
    "password": os.environ.get("DB_PASS", ""),
}

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Constitutional guardrails
BLOCKED_TOOLS = ["WebSearch", "WebFetch"]  # No external web access for Jrs
ALLOWED_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
PROTECTED_PATHS = ["/etc/", "/usr/", "/var/", "/root/", "/home/"]
SACRED_MEMORY_READONLY = True

# Basin signal thresholds
BASIN_THRESHOLDS = {
    "council_disagreement": 0.7,     # confidence below this = basin signal
    "dlq_depth": 5,                  # failed tasks in 48h above this = signal
    "jr_failure_rate": 0.25,         # 25% failure rate in 24h = signal
    "stale_kanban": 7,               # days in_progress before stale
    "failure_rate_spike": 0.15,      # 15% increase in failure rate = spike
    "phase_transition_threshold": 3,  # 3+ basin signals = escalate to council
}

# ── Database Helpers ───────────────────────────────────────────────────────

def get_db():
    """Get a database connection."""
    return psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)


def fetch_pending_tasks(limit=5):
    """Fetch pending tasks from jr_work_queue, oldest first by priority."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, task_id, title, instruction_file, assigned_jr, priority,
               sacred_fire_priority, use_rlm, parameters, created_at
        FROM jr_work_queue
        WHERE status = 'pending'
        ORDER BY priority ASC, created_at ASC
        LIMIT %s
    """, (limit,))
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return tasks


def claim_task(task_id):
    """Atomically claim a task (pending → in_progress) with row locking."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jr_work_queue
        SET status = 'in_progress', started_at = NOW(), updated_at = NOW(),
            status_message = 'Claimed by TPM Autonomic Daemon v2'
        WHERE id = %s AND status = 'pending'
        RETURNING id
    """, (task_id,))
    claimed = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return claimed is not None


def complete_task(task_id, result_data=None):
    """Mark task as completed."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jr_work_queue
        SET status = 'completed', completed_at = NOW(), updated_at = NOW(),
            result = %s, status_message = 'Completed by TPM Autonomic Daemon v2'
        WHERE id = %s
    """, (json.dumps(result_data or {}), task_id))
    conn.commit()
    cur.close()
    conn.close()


def fail_task(task_id, error_msg):
    """Mark task as failed."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jr_work_queue
        SET status = 'failed', completed_at = NOW(), updated_at = NOW(),
            error_message = %s, status_message = 'Failed in TPM Autonomic Daemon v2'
        WHERE id = %s
    """, (error_msg[:2000], task_id))
    conn.commit()
    cur.close()
    conn.close()


def log_thermal_memory(content, temperature=75.0, sacred=False):
    """Store a thermal memory record."""
    conn = get_db()
    cur = conn.cursor()
    memory_hash = hashlib.sha256(content.encode()).hexdigest()
    cur.execute("""
        INSERT INTO thermal_memory_archive
        (original_content, temperature_score, sacred_pattern, memory_hash,
         metadata, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON CONFLICT (memory_hash) DO NOTHING
    """, (
        content[:10000],
        temperature,
        sacred,
        memory_hash,
        json.dumps({"source": "tpm_autonomic_v2", "timestamp": datetime.utcnow().isoformat()})
    ))
    conn.commit()
    cur.close()
    conn.close()


# ── Basin Signal Detection ─────────────────────────────────────────────────

def check_basin_signals():
    """Check all 6 basin signals. Returns list of active signals."""
    signals = []
    conn = get_db()
    cur = conn.cursor()

    # 1. Council disagreement: recent votes with low confidence
    cur.execute("""
        SELECT AVG(confidence) as avg_conf, COUNT(*) as cnt
        FROM council_votes
        WHERE voted_at > NOW() - INTERVAL '24 hours'
          AND confidence IS NOT NULL
    """)
    row = cur.fetchone()
    if row and row["cnt"] > 0 and row["avg_conf"] < BASIN_THRESHOLDS["council_disagreement"]:
        signals.append({
            "type": "council_disagreement",
            "value": float(row["avg_conf"]),
            "threshold": BASIN_THRESHOLDS["council_disagreement"],
            "detail": f"Avg council confidence {row['avg_conf']:.3f} in last 24h ({row['cnt']} votes)"
        })

    # 2. DLQ depth: failed tasks accumulating
    cur.execute("""
        SELECT COUNT(*) as cnt
        FROM jr_work_queue
        WHERE status = 'failed'
          AND updated_at > NOW() - INTERVAL '48 hours'
    """)
    row = cur.fetchone()
    if row and row["cnt"] >= BASIN_THRESHOLDS["dlq_depth"]:
        signals.append({
            "type": "dlq_depth",
            "value": int(row["cnt"]),
            "threshold": BASIN_THRESHOLDS["dlq_depth"],
            "detail": f"{row['cnt']} failed tasks in last 48h"
        })

    # 3. Jr failure rate
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE status = 'completed') as done,
            COUNT(*) FILTER (WHERE status = 'failed') as failed,
            COUNT(*) as total
        FROM jr_work_queue
        WHERE updated_at > NOW() - INTERVAL '24 hours'
          AND status IN ('completed', 'failed')
    """)
    row = cur.fetchone()
    if row and row["total"] > 0:
        rate = row["failed"] / row["total"]
        if rate > BASIN_THRESHOLDS["jr_failure_rate"]:
            signals.append({
                "type": "jr_failure_rate",
                "value": round(rate, 3),
                "threshold": BASIN_THRESHOLDS["jr_failure_rate"],
                "detail": f"{row['failed']}/{row['total']} tasks failed in 24h ({rate:.1%})"
            })

    # 4. Stale kanban items
    cur.execute("""
        SELECT COUNT(*) as cnt
        FROM duyuktv_tickets
        WHERE status = 'in_progress'
          AND updated_at < NOW() - INTERVAL '%s days'
    """ % BASIN_THRESHOLDS["stale_kanban"])
    row = cur.fetchone()
    if row and row["cnt"] > 0:
        signals.append({
            "type": "stale_kanban",
            "value": int(row["cnt"]),
            "threshold": BASIN_THRESHOLDS["stale_kanban"],
            "detail": f"{row['cnt']} kanban items in_progress > {BASIN_THRESHOLDS['stale_kanban']} days"
        })

    # 5. Failure rate spike (comparing 24h vs 7d baseline)
    cur.execute("""
        WITH recent AS (
            SELECT COUNT(*) FILTER (WHERE status='failed') * 1.0 / NULLIF(COUNT(*), 0) as rate
            FROM jr_work_queue WHERE updated_at > NOW() - INTERVAL '24 hours'
              AND status IN ('completed','failed')
        ), baseline AS (
            SELECT COUNT(*) FILTER (WHERE status='failed') * 1.0 / NULLIF(COUNT(*), 0) as rate
            FROM jr_work_queue WHERE updated_at > NOW() - INTERVAL '7 days'
              AND status IN ('completed','failed')
        )
        SELECT r.rate as recent_rate, b.rate as baseline_rate
        FROM recent r, baseline b
    """)
    row = cur.fetchone()
    if row and row["recent_rate"] is not None and row["baseline_rate"] is not None:
        spike = float(row["recent_rate"]) - float(row["baseline_rate"])
        if spike > BASIN_THRESHOLDS["failure_rate_spike"]:
            signals.append({
                "type": "failure_rate_spike",
                "value": round(spike, 3),
                "threshold": BASIN_THRESHOLDS["failure_rate_spike"],
                "detail": f"Failure rate spiked {spike:.1%} above 7-day baseline"
            })

    # 6. Thermal memory drift (sacred memories cooling below 40°C)
    cur.execute("""
        SELECT COUNT(*) as cnt
        FROM thermal_memory_archive
        WHERE sacred_pattern = true
          AND temperature_score < 40
    """)
    row = cur.fetchone()
    if row and row["cnt"] > 0:
        signals.append({
            "type": "thermal_memory_drift",
            "value": int(row["cnt"]),
            "threshold": 0,
            "detail": f"{row['cnt']} sacred memories below 40°C (drift detected)"
        })

    cur.close()
    conn.close()
    return signals


# ── Telegram Notification ──────────────────────────────────────────────────

def send_telegram(message):
    """Send a Telegram notification to the ops channel."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured, skipping notification")
        return
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message[:4000], "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


# ── Task Execution via Claude Agent SDK ────────────────────────────────────

async def execute_task_with_sdk(task):
    """Execute a Jr task using the Claude Agent SDK."""
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, AssistantMessage
    except ImportError:
        logger.error("claude-agent-sdk not installed. Run: pip install claude-agent-sdk")
        return {"success": False, "error": "claude-agent-sdk not installed"}

    instruction_file = task.get("instruction_file", "")
    title = task.get("title", "Unknown task")
    task_id = task.get("id")

    if not instruction_file:
        return {"success": False, "error": "No instruction file specified"}

    # Build the prompt
    prompt = (
        f"Execute the Jr instruction at {instruction_file}. "
        f"Read the instruction file first, then carry out every SEARCH/REPLACE "
        f"and Create block exactly as specified. "
        f"Report what you changed and any issues encountered. "
        f"Task: {title}"
    )

    # Select model based on task priority
    model = "claude-sonnet-4-6"  # Default: Sonnet for execution

    output_text = []
    total_cost = 0.0
    success = True

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                allowed_tools=ALLOWED_TOOLS,
                disallowed_tools=BLOCKED_TOOLS,
                permission_mode="bypassPermissions",
                cwd="/ganuda",
                model=model,
                system_prompt=(
                    "You are a Jr executor for the Cherokee AI Federation. "
                    "Follow instructions precisely. Execute SEARCH/REPLACE blocks exactly. "
                    "Do not modify files outside /ganuda/. "
                    "Do not delete files. Do not modify sacred memories. "
                    "Report your work clearly."
                ),
                max_turns=50,
                max_budget_usd=MAX_BUDGET_PER_TASK,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, "text"):
                        output_text.append(block.text)
            elif isinstance(message, ResultMessage):
                total_cost = getattr(message, "total_cost_usd", 0.0)
                if getattr(message, "is_error", False):
                    success = False
    except Exception as e:
        logger.error(f"SDK execution error for task {task_id}: {e}")
        return {"success": False, "error": str(e)[:500]}

    result = {
        "success": success,
        "cost_usd": total_cost,
        "output_summary": "\n".join(output_text)[:5000],
        "model": model,
        "executed_by": "tpm_autonomic_v2",
    }

    return result


# ── Main Daemon Loop ───────────────────────────────────────────────────────

class TPMAutonomicDaemon:
    """Level 5+ Basin-Breaker TPM Daemon."""

    def __init__(self):
        self.running = True
        self.active_tasks = {}  # task_id → asyncio.Task
        self.basin_history = deque(maxlen=100)
        self.last_basin_check = datetime.min
        self.cycle_count = 0

        # Graceful shutdown
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

    def _shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    async def run(self):
        """Main daemon loop."""
        logger.info("TPM Autonomic Daemon v2 starting — Level 5+ Basin-Breaker")
        logger.info(f"Poll interval: {POLL_INTERVAL}s, Max concurrent: {MAX_CONCURRENT_TASKS}")
        logger.info(f"Budget cap: ${MAX_BUDGET_PER_TASK}/task")

        send_telegram("🏔️ *TPM Autonomic Daemon v2* started — Level 5+ Basin-Breaker online")

        log_thermal_memory(
            "TPM Autonomic Daemon v2 started. Level 5+ Basin-Breaker online. "
            f"Poll: {POLL_INTERVAL}s, Max concurrent: {MAX_CONCURRENT_TASKS}, "
            f"Budget: ${MAX_BUDGET_PER_TASK}/task. "
            f"Council votes: #1fda4f47a272c989, #6fe918ac1373d2c8.",
            temperature=80.0,
            sacred=False
        )

        while self.running:
            try:
                self.cycle_count += 1

                # Clean up completed task handles
                completed = [tid for tid, t in self.active_tasks.items() if t.done()]
                for tid in completed:
                    del self.active_tasks[tid]

                # Check basin signals periodically
                now = datetime.utcnow()
                if (now - self.last_basin_check).total_seconds() >= BASIN_CHECK_INTERVAL:
                    await self._check_basins()
                    self.last_basin_check = now

                # Poll for pending tasks if we have capacity
                if len(self.active_tasks) < MAX_CONCURRENT_TASKS:
                    available_slots = MAX_CONCURRENT_TASKS - len(self.active_tasks)
                    tasks = fetch_pending_tasks(limit=available_slots)

                    for task in tasks:
                        task_id = task["id"]
                        if task_id in self.active_tasks:
                            continue

                        if claim_task(task_id):
                            logger.info(f"Claimed task #{task_id}: {task['title']}")
                            async_task = asyncio.create_task(
                                self._execute_and_record(task)
                            )
                            self.active_tasks[task_id] = async_task

                # Log heartbeat every 10 cycles
                if self.cycle_count % 10 == 0:
                    active_count = len(self.active_tasks)
                    logger.info(f"Heartbeat: cycle {self.cycle_count}, {active_count} active tasks")

            except Exception as e:
                logger.error(f"Daemon loop error: {e}", exc_info=True)

            await asyncio.sleep(POLL_INTERVAL)

        # Graceful shutdown: wait for active tasks
        if self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} active tasks to complete...")
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)

        send_telegram("🛑 *TPM Autonomic Daemon v2* stopped gracefully")
        logger.info("TPM Autonomic Daemon v2 stopped")

    async def _execute_and_record(self, task):
        """Execute a task and record the result."""
        task_id = task["id"]
        title = task["title"]
        started = datetime.utcnow()

        try:
            logger.info(f"Executing task #{task_id}: {title}")
            result = await execute_task_with_sdk(task)

            elapsed = (datetime.utcnow() - started).total_seconds()

            if result["success"]:
                complete_task(task_id, result)
                logger.info(f"Task #{task_id} completed in {elapsed:.0f}s (${result.get('cost_usd', 0):.4f})")
                send_telegram(
                    f"✅ *Task #{task_id}* completed\n"
                    f"Title: {title}\n"
                    f"Time: {elapsed:.0f}s | Cost: ${result.get('cost_usd', 0):.4f}"
                )
            else:
                error = result.get("error", "Unknown error")
                fail_task(task_id, error)
                logger.warning(f"Task #{task_id} failed: {error[:200]}")
                send_telegram(
                    f"❌ *Task #{task_id}* failed\n"
                    f"Title: {title}\n"
                    f"Error: {error[:200]}"
                )

            # Log to thermal memory
            log_thermal_memory(
                f"TPM Daemon executed task #{task_id}: {title}. "
                f"Result: {'SUCCESS' if result['success'] else 'FAILED'}. "
                f"Time: {elapsed:.0f}s. Cost: ${result.get('cost_usd', 0):.4f}. "
                f"Model: {result.get('model', 'unknown')}.",
                temperature=70.0
            )

        except Exception as e:
            logger.error(f"Task #{task_id} execution exception: {e}", exc_info=True)
            fail_task(task_id, str(e)[:500])
            send_telegram(f"💥 *Task #{task_id}* exception: {str(e)[:200]}")

    async def _check_basins(self):
        """Check basin signals and escalate if phase transition detected."""
        try:
            signals = check_basin_signals()
            self.basin_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "signal_count": len(signals),
                "signals": signals
            })

            if signals:
                logger.warning(f"Basin signals detected: {len(signals)}")
                for s in signals:
                    logger.warning(f"  {s['type']}: {s['value']} (threshold: {s['threshold']})")

                # Phase transition detection: 3+ signals = escalate
                if len(signals) >= BASIN_THRESHOLDS["phase_transition_threshold"]:
                    await self._escalate_to_council(signals)
                else:
                    # Log basin signals to thermal memory
                    signal_summary = "; ".join(f"{s['type']}={s['value']}" for s in signals)
                    log_thermal_memory(
                        f"TPM Daemon basin check: {len(signals)} signal(s) active. "
                        f"{signal_summary}. Below escalation threshold "
                        f"({BASIN_THRESHOLDS['phase_transition_threshold']}).",
                        temperature=65.0
                    )
                    send_telegram(
                        f"⚠️ *Basin signals* ({len(signals)}):\n" +
                        "\n".join(f"• {s['type']}: {s['detail']}" for s in signals)
                    )
            else:
                logger.debug("Basin check: all clear")

        except Exception as e:
            logger.error(f"Basin check error: {e}", exc_info=True)

    async def _escalate_to_council(self, signals):
        """Escalate to council vote when phase transition detected."""
        signal_details = "\n".join(f"- {s['type']}: {s['detail']}" for s in signals)

        logger.critical(f"PHASE TRANSITION DETECTED — {len(signals)} basin signals. Escalating to council.")
        send_telegram(
            f"🚨 *PHASE TRANSITION DETECTED*\n"
            f"{len(signals)} basin signals active:\n" +
            "\n".join(f"• {s['type']}: {s['detail']}" for s in signals) +
            "\n\nEscalating to council for review."
        )

        # Call council vote via gateway
        try:
            import requests
            resp = requests.post(
                "http://192.168.132.223:8080/v1/council/vote",
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": os.environ.get("COUNCIL_API_KEY", "")
                },
                json={
                    "question": (
                        f"PHASE TRANSITION ALERT from TPM Autonomic Daemon. "
                        f"{len(signals)} basin signals detected simultaneously:\n"
                        f"{signal_details}\n\n"
                        f"This exceeds the escalation threshold of "
                        f"{BASIN_THRESHOLDS['phase_transition_threshold']}. "
                        f"What corrective action should the Federation take?"
                    ),
                    "context": (
                        f"Automated escalation from tpm_autonomic_v2. "
                        f"Basin history (last 10 checks): "
                        f"{json.dumps(list(self.basin_history)[-10:])}"
                    ),
                    "priority": "high"
                },
                timeout=120
            )
            vote_result = resp.json()
            logger.info(f"Council vote result: {vote_result.get('recommendation')} "
                       f"(confidence: {vote_result.get('confidence')})")

            log_thermal_memory(
                f"PHASE TRANSITION ESCALATION. {len(signals)} signals: {signal_details}. "
                f"Council vote: {vote_result.get('audit_hash')} — "
                f"{vote_result.get('recommendation')} ({vote_result.get('confidence')}). "
                f"Consensus: {vote_result.get('consensus', 'N/A')[:500]}",
                temperature=90.0,
                sacred=True
            )

        except Exception as e:
            logger.error(f"Council escalation failed: {e}")
            send_telegram(f"🔴 Council escalation FAILED: {e}")


# ── Entry Point ────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("/ganuda/logs/tpm_autonomic_v2.log", mode="a")
        ]
    )

    daemon = TPMAutonomicDaemon()
    asyncio.run(daemon.run())


if __name__ == "__main__":
    main()
```

## Step 2: Create systemd Service File

Create `/ganuda/scripts/systemd/tpm-autonomic.service`

```ini
[Unit]
Description=TPM Autonomic Daemon v2 — Level 5+ Basin-Breaker
After=network.target postgresql.service
Wants=network.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
EnvironmentFile=/ganuda/secrets.env
Environment=PYTHONPATH=/ganuda/lib:/ganuda
ExecStart=/home/dereadi/cherokee_venv/bin/python3 /ganuda/daemons/tpm_autonomic_v2.py
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=tpm-autonomic

[Install]
WantedBy=multi-user.target
```

## Step 3: Create log directory

Ensure the log directory exists. Add this to the daemon startup or verify it exists:

The daemon logs to `/ganuda/logs/tpm_autonomic_v2.log`. The directory `/ganuda/logs/` should already exist. If not, the daemon will fail — create it first.

## Manual Steps (TPM)

1. Install Claude Agent SDK on redfin:
   ```text
   /home/dereadi/cherokee_venv/bin/pip install claude-agent-sdk
   ```

2. Ensure ANTHROPIC_API_KEY is in /ganuda/secrets.env

3. Ensure /ganuda/logs/ exists:
   ```text
   mkdir -p /ganuda/logs
   ```

4. Deploy the service:
   ```text
   ganuda-deploy-service tpm-autonomic.service
   ```

5. Monitor:
   ```text
   journalctl -u tpm-autonomic -f
   ```

6. Test by queuing a simple task:
   ```text
   psql -h 192.168.132.222 -U claude -d zammad_production -c "
   INSERT INTO jr_work_queue (task_id, title, instruction_file, priority, status, assigned_jr, source, created_by, use_rlm)
   VALUES (md5('test-tpm-daemon'), 'TEST: TPM Daemon Hello World', '/ganuda/docs/jr_instructions/JR-TEST-HELLO-WORLD.md', 5, 'pending', 'Software Engineer Jr.', 'tpm', 'TPM Claude Opus', false);"
   ```

7. Watch the daemon pick it up and execute it via Claude Agent SDK
