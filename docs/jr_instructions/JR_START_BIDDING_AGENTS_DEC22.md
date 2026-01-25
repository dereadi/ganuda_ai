# Jr Task: Start Jr Bidding Agents

**Task ID:** task-start-bidding-agents-001
**Priority:** P0 (Blocking - no agents bidding on announced tasks)
**Node:** redfin (primary), sasass, bluefin
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation

---

## Problem Statement

Three research-based implementation tasks were announced to `jr_task_announcements`:
- task-stigmergy-density-001 (P1 - arXiv:2512.10166)
- task-smith-difficulty-001 (P2 - arXiv:2512.11303)
- task-rl-rewards-001 (P3 - arXiv:2509.20095)

**Current State:** Tasks show `status = 'open'` but NO bids have been received because:
1. The `JrBidder` class from `JR_TASK_BIDDING_SYSTEM.md` isn't deployed
2. The existing `jr_queue_worker.py` only polls `jr_work_queue` (FIFO system)
3. No daemon is actively polling `jr_task_announcements`

**Result:** Observer logs show "Learning plateau detected" because Jrs are idle, waiting for work that never arrives.

---

## Solution Architecture

Create a **Jr Bidding Daemon** that:
1. Polls `jr_task_announcements` for `status = 'open'` tasks
2. Calculates bid scores using `jr_agent_state` capabilities
3. Submits bids to `jr_task_bids`
4. After bidding window closes, winner executes task

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│  TPM Announces  │───>│ jr_task_announcements│<───│  Jr Bidding     │
│  Task           │    │ (status='open')      │    │  Daemon (polls) │
└─────────────────┘    └──────────────────────┘    └────────┬────────┘
                                                            │
                                                            ▼
                       ┌──────────────────────┐    ┌─────────────────┐
                       │    jr_task_bids      │<───│  Submit Bid     │
                       │ (composite_score)    │    │                 │
                       └──────────────────────┘    └─────────────────┘
                                │
                                ▼ (after bidding window)
                       ┌──────────────────────┐
                       │ Winner Executes Task │
                       └──────────────────────┘
```

---

## Implementation

### Phase 1: Create Jr Bidding Daemon

**File:** `/ganuda/jr_executor/jr_bidding_daemon.py`

```python
#!/usr/bin/env python3
"""
Jr Bidding Daemon - Polls for announced tasks and submits bids.

Based on Contract Net Protocol from JR_TASK_BIDDING_SYSTEM.md.
Implements arXiv research-based task assignment.

Run as: python3 jr_bidding_daemon.py <agent_id> <node_name>
Example: python3 jr_bidding_daemon.py jr-redfin-gecko redfin

For Seven Generations - Cherokee AI Federation
"""

import os
import sys
import time
import signal
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import hashlib

# Configuration
POLL_INTERVAL = 10  # seconds between task polls
HEARTBEAT_INTERVAL = 60  # seconds between heartbeats
BIDDING_WINDOW = 5  # seconds to wait for other bids

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
}


class JrBiddingDaemon:
    """
    Daemon that polls for announced tasks and submits bids.

    One daemon runs per Jr agent, watching for tasks it can do.
    """

    def __init__(self, agent_id: str, node_name: str):
        self.agent_id = agent_id
        self.node_name = node_name
        self.running = True
        self.last_heartbeat = 0
        self._conn = None

        # Load agent capabilities
        self.capabilities = self._load_capabilities()

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
        return self._conn

    def _shutdown(self, signum, frame):
        print(f"\n[{self.agent_id}] Shutting down bidding daemon...")
        self.running = False

    def _load_capabilities(self):
        """Load agent capabilities from jr_agent_state"""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT specialization, specialization_scores, success_rate
                    FROM jr_agent_state
                    WHERE agent_id = %s
                """, (self.agent_id,))
                result = cur.fetchone()

                if result:
                    return {
                        'specialization': result['specialization'],
                        'scores': result.get('specialization_scores') or {},
                        'success_rate': result.get('success_rate') or 0.5
                    }
        except Exception as e:
            print(f"[{self.agent_id}] Error loading capabilities: {e}")

        return {'specialization': 'general', 'scores': {}, 'success_rate': 0.5}

    def _heartbeat(self):
        """Update agent's last_active timestamp"""
        now = time.time()
        if now - self.last_heartbeat >= HEARTBEAT_INTERVAL:
            try:
                conn = self._get_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE jr_agent_state
                        SET last_active = NOW()
                        WHERE agent_id = %s
                    """, (self.agent_id,))

                    if cur.rowcount == 0:
                        # Agent doesn't exist, create it
                        cur.execute("""
                            INSERT INTO jr_agent_state (agent_id, node_name, specialization)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (agent_id) DO UPDATE SET last_active = NOW()
                        """, (self.agent_id, self.node_name, 'general'))

                    conn.commit()
                self.last_heartbeat = now

            except Exception as e:
                print(f"[{self.agent_id}] Heartbeat failed: {e}")

    def get_open_tasks(self):
        """Get tasks open for bidding"""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT task_id, task_type, task_content,
                           required_capabilities, preferred_node, priority, deadline
                    FROM jr_task_announcements
                    WHERE status = 'open'
                    ORDER BY priority ASC, announced_at ASC
                    LIMIT 10
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"[{self.agent_id}] Error fetching tasks: {e}")
            return []

    def already_bid_on(self, task_id: str) -> bool:
        """Check if we already bid on this task"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM jr_task_bids
                    WHERE task_id = %s AND agent_id = %s
                """, (task_id, self.agent_id))
                return cur.fetchone() is not None
        except:
            return False

    def calculate_bid(self, task: dict) -> dict:
        """Calculate bid score for a task"""

        # Capability score: How well do we match required capabilities?
        required_caps = task.get('required_capabilities') or []
        if not required_caps:
            capability_score = 0.7  # No requirements = assume capable
        else:
            matches = sum(1 for cap in required_caps
                         if cap in str(self.capabilities.get('scores', {})))
            capability_score = matches / len(required_caps) if required_caps else 0.7

        # Experience score: Based on success rate
        experience_score = self.capabilities.get('success_rate', 0.5)

        # Load score: Check current assignments (1.0 = fully available)
        load_score = self._calculate_load()

        # Confidence: Based on task complexity (content length as proxy)
        content_len = len(task.get('task_content', ''))
        if content_len < 500:
            confidence = 0.9
        elif content_len < 2000:
            confidence = 0.7
        else:
            confidence = 0.5

        # Composite score calculation
        # Weights: capability 40%, experience 30%, load 20%, confidence 10%
        composite = (
            0.40 * capability_score +
            0.30 * experience_score +
            0.20 * load_score +
            0.10 * confidence
        )

        # Bonus for preferred node
        if task.get('preferred_node') == self.node_name:
            composite *= 1.1

        return {
            'task_id': task['task_id'],
            'agent_id': self.agent_id,
            'node_name': self.node_name,
            'capability_score': capability_score,
            'experience_score': experience_score,
            'load_score': load_score,
            'confidence': confidence,
            'composite_score': min(1.0, composite)
        }

    def _calculate_load(self) -> float:
        """Calculate load score (higher = more available)"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM jr_task_announcements
                    WHERE assigned_to = %s AND status = 'assigned'
                """, (self.agent_id,))
                current_tasks = cur.fetchone()[0]

                # Assume max 3 concurrent tasks
                return max(0.1, 1.0 - (current_tasks / 3.0))
        except:
            return 0.5

    def submit_bid(self, bid: dict):
        """Submit bid to database"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO jr_task_bids
                    (task_id, agent_id, node_name, capability_score,
                     experience_score, load_score, confidence, composite_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    bid['task_id'], bid['agent_id'], bid['node_name'],
                    bid['capability_score'], bid['experience_score'],
                    bid['load_score'], bid['confidence'], bid['composite_score']
                ))
                conn.commit()
                print(f"[{self.agent_id}] Bid submitted: {bid['task_id']} (score: {bid['composite_score']:.2f})")
        except Exception as e:
            print(f"[{self.agent_id}] Bid submission failed: {e}")

    def run(self):
        """Main daemon loop"""
        print(f"[{self.agent_id}] Bidding daemon starting on {self.node_name}")
        print(f"[{self.agent_id}] Capabilities: {self.capabilities}")
        print(f"[{self.agent_id}] Poll interval: {POLL_INTERVAL}s")

        self._heartbeat()

        while self.running:
            try:
                self._heartbeat()

                # Get open tasks
                tasks = self.get_open_tasks()

                for task in tasks:
                    task_id = task['task_id']

                    # Skip if already bid
                    if self.already_bid_on(task_id):
                        continue

                    # Calculate and submit bid
                    bid = self.calculate_bid(task)
                    self.submit_bid(bid)

                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[{self.agent_id}] Error in main loop: {e}")
                time.sleep(POLL_INTERVAL)

        print(f"[{self.agent_id}] Bidding daemon stopped")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 jr_bidding_daemon.py <agent_id> <node_name>")
        print("Example: python3 jr_bidding_daemon.py jr-redfin-gecko redfin")
        sys.exit(1)

    agent_id = sys.argv[1]
    node_name = sys.argv[2]

    daemon = JrBiddingDaemon(agent_id, node_name)
    daemon.run()
```

---

### Phase 2: Create Startup Script

**File:** `/ganuda/jr_executor/start_bidding_agents.sh`

```bash
#!/bin/bash
# Start Jr Bidding Agents on this node
# Usage: ./start_bidding_agents.sh [node_name]

NODE_NAME=${1:-$(hostname)}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="/ganuda/logs"
VENV="/home/dereadi/cherokee_venv/bin/python3"

mkdir -p "$LOG_DIR"

echo "[$(date)] Starting bidding agents on $NODE_NAME..."

# Define agents per node
case "$NODE_NAME" in
    redfin)
        AGENTS=("jr-redfin-gecko" "jr-redfin-eagle")
        ;;
    bluefin)
        AGENTS=("jr-bluefin-turtle" "jr-bluefin-crawdad")
        ;;
    sasass|greenfin)
        AGENTS=("jr-$NODE_NAME-spider" "jr-$NODE_NAME-raven")
        ;;
    *)
        AGENTS=("jr-$NODE_NAME-general")
        ;;
esac

for agent in "${AGENTS[@]}"; do
    echo "[$(date)] Starting $agent..."

    nohup $VENV "$SCRIPT_DIR/jr_bidding_daemon.py" "$agent" "$NODE_NAME" \
        >> "$LOG_DIR/bidding_$agent.log" 2>&1 &

    echo "[$(date)] Started $agent with PID $!"
done

echo "[$(date)] All bidding agents started on $NODE_NAME"
```

---

### Phase 3: Add Task Assignment Cron

The bidding coordinator that closes bidding and assigns tasks needs to run periodically.

**File:** `/ganuda/jr_executor/close_bidding.py`

```python
#!/usr/bin/env python3
"""
Close bidding on tasks with sufficient bids and assign to winners.
Run via cron every minute.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

BIDDING_WINDOW_MINUTES = 2  # Close bidding after 2 minutes


def main():
    conn = psycopg2.connect(**DB_CONFIG)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Find tasks open for more than BIDDING_WINDOW_MINUTES with bids
        cur.execute("""
            SELECT a.task_id, a.task_content, a.announced_at
            FROM jr_task_announcements a
            WHERE a.status = 'open'
              AND a.announced_at < NOW() - INTERVAL '%s minutes'
              AND EXISTS (
                  SELECT 1 FROM jr_task_bids b WHERE b.task_id = a.task_id
              )
        """, (BIDDING_WINDOW_MINUTES,))

        tasks = cur.fetchall()

        for task in tasks:
            task_id = task['task_id']

            # Get winning bid
            cur.execute("""
                SELECT agent_id, node_name, composite_score
                FROM jr_task_bids
                WHERE task_id = %s
                ORDER BY composite_score DESC
                LIMIT 1
            """, (task_id,))

            winner = cur.fetchone()

            if winner:
                # Assign task to winner
                cur.execute("""
                    UPDATE jr_task_announcements
                    SET status = 'assigned',
                        assigned_to = %s
                    WHERE task_id = %s
                """, (winner['agent_id'], task_id))

                print(f"[{datetime.now()}] Assigned {task_id} to {winner['agent_id']} "
                      f"(score: {winner['composite_score']:.2f})")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
```

---

### Phase 4: Deploy on redfin

```bash
# On redfin as dereadi

# 1. Copy daemon script
cd /ganuda/jr_executor

# 2. Make executable
chmod +x jr_bidding_daemon.py start_bidding_agents.sh close_bidding.py

# 3. Start bidding agents
./start_bidding_agents.sh redfin

# 4. Add close_bidding to cron
(crontab -l 2>/dev/null; echo "* * * * * /home/dereadi/cherokee_venv/bin/python3 /ganuda/jr_executor/close_bidding.py >> /ganuda/logs/close_bidding.log 2>&1") | crontab -

# 5. Verify agents are running
pgrep -a -f jr_bidding_daemon

# 6. Check logs
tail -f /ganuda/logs/bidding_jr-redfin-gecko.log
```

---

## Verification

After deployment, verify bids are coming in:

```sql
-- On bluefin
SELECT task_id, agent_id, composite_score, bid_at
FROM jr_task_bids
WHERE bid_at > NOW() - INTERVAL '10 minutes'
ORDER BY bid_at DESC;

-- Check task statuses
SELECT task_id, status, assigned_to
FROM jr_task_announcements
WHERE announced_at > NOW() - INTERVAL '24 hours';
```

---

## Success Criteria

1. ✅ `jr_bidding_daemon.py` created and deployed
2. ✅ Agents on redfin bidding on open tasks
3. ✅ Bids appearing in `jr_task_bids` table
4. ✅ `close_bidding.py` assigning winners after 2-minute window
5. ✅ 3 research tasks (stigmergy, SMITH, RL) get bids and assignments

---

*For Seven Generations - Cherokee AI Federation*
