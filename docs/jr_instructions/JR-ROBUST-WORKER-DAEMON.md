# Jr Instruction: Robust Worker Daemon Architecture

## Priority: HIGH
## Estimated Effort: Medium
## Category: Infrastructure

---

## Objective

Make the Jr queue workers bulletproof with:
1. Systemd service with automatic restart
2. Health monitoring and self-healing
3. Graceful degradation on errors
4. Proper logging and alerting
5. Auto-assignment of unassigned tasks

---

## Context

Current workers stop unexpectedly and don't auto-restart. Tasks sit unassigned in the queue. We need production-grade reliability.

---

## Implementation

### 1. Systemd Service Unit

**File:** `/ganuda/scripts/systemd/jr-queue-worker@.service`

```ini
[Unit]
Description=Cherokee Jr Queue Worker (%i)
After=network.target postgresql.service
Wants=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment="PATH=/home/dereadi/cherokee_venv/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONUNBUFFERED=1"

# Main process
ExecStart=/home/dereadi/cherokee_venv/bin/python3 jr_queue_worker.py %i

# Restart configuration - BULLETPROOF
Restart=always
RestartSec=10
StartLimitIntervalSec=300
StartLimitBurst=5

# Resource limits
MemoryMax=2G
CPUQuota=50%

# Logging
StandardOutput=append:/ganuda/logs/jr_worker_%i.log
StandardError=append:/ganuda/logs/jr_worker_%i.log

# Watchdog - worker must ping within 5 minutes or gets restarted
WatchdogSec=300

[Install]
WantedBy=multi-user.target
```

### 2. Watchdog Integration

**Modify:** `/ganuda/jr_executor/jr_queue_worker.py`

Add systemd watchdog support:

```python
import sdnotify  # pip install sdnotify

class JrQueueWorker:
    def __init__(self, jr_name: str):
        # ... existing init ...
        self.notifier = sdnotify.SystemdNotifier()

    def _heartbeat(self):
        """Send heartbeat to both database AND systemd."""
        now = time.time()
        if now - self.last_heartbeat >= HEARTBEAT_INTERVAL:
            try:
                self.client.heartbeat()
                self.notifier.notify("WATCHDOG=1")  # Systemd watchdog ping
                self.last_heartbeat = now
            except Exception as e:
                print(f"[{self.jr_name}] Heartbeat failed: {e}")
```

### 3. Auto-Assignment Daemon

**File:** `/ganuda/jr_executor/task_auto_assigner.py`

```python
#!/usr/bin/env python3
"""
Task Auto-Assigner - Assigns pending tasks to available Jrs.
Runs every minute to ensure no tasks sit unassigned.
"""
import time
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

ASSIGN_INTERVAL = 60  # seconds

def get_online_workers():
    """Get list of online Jr workers."""
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT jr_name, current_load
            FROM jr_status
            WHERE is_online = TRUE
              AND last_seen > NOW() - INTERVAL '5 minutes'
            ORDER BY current_load ASC
        """)
        return cur.fetchall()

def assign_pending_tasks():
    """Assign unassigned pending tasks to available workers."""
    conn = psycopg2.connect(**DB_CONFIG)

    # Get available workers
    workers = get_online_workers()
    if not workers:
        print("[AutoAssign] No online workers available")
        return 0

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get unassigned pending tasks
        cur.execute("""
            SELECT id, title, priority
            FROM jr_work_queue
            WHERE status = 'pending'
              AND assigned_jr IS NULL
            ORDER BY sacred_fire_priority DESC, priority ASC, created_at ASC
            LIMIT 20
        """)
        tasks = cur.fetchall()

        if not tasks:
            return 0

        assigned = 0
        for task in tasks:
            # Round-robin to least-loaded worker
            worker = workers[assigned % len(workers)]

            cur.execute("""
                UPDATE jr_work_queue
                SET assigned_jr = %s, status = 'assigned'
                WHERE id = %s
            """, (worker['jr_name'], task['id']))

            print(f"[AutoAssign] Assigned task {task['id']} to {worker['jr_name']}")
            assigned += 1

        conn.commit()
        return assigned

def main():
    print("[AutoAssign] Task auto-assigner starting...")
    while True:
        try:
            count = assign_pending_tasks()
            if count:
                print(f"[AutoAssign] Assigned {count} task(s)")
        except Exception as e:
            print(f"[AutoAssign] Error: {e}")

        time.sleep(ASSIGN_INTERVAL)

if __name__ == '__main__':
    main()
```

### 4. Health Monitor

**File:** `/ganuda/jr_executor/worker_health_monitor.py`

```python
#!/usr/bin/env python3
"""
Worker Health Monitor - Restarts dead workers, alerts on issues.
"""
import subprocess
import psycopg2
from datetime import datetime, timedelta

WORKER_SERVICES = [
    'jr-queue-worker@it_triad_jr',
]

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def check_worker_health():
    """Check worker health and restart if needed."""
    conn = psycopg2.connect(**DB_CONFIG)

    with conn.cursor() as cur:
        # Check for stuck in_progress tasks
        cur.execute("""
            SELECT id, title, assigned_jr, started_at
            FROM jr_work_queue
            WHERE status = 'in_progress'
              AND started_at < NOW() - INTERVAL '30 minutes'
        """)
        stuck_tasks = cur.fetchall()

        for task in stuck_tasks:
            print(f"[Health] Task {task[0]} stuck: {task[1]}")
            # Reset to assigned for retry
            cur.execute("""
                UPDATE jr_work_queue
                SET status = 'assigned', started_at = NULL, progress_percent = 0
                WHERE id = %s
            """, (task[0],))

        if stuck_tasks:
            conn.commit()
            print(f"[Health] Reset {len(stuck_tasks)} stuck task(s)")

        # Check for dead workers
        cur.execute("""
            SELECT jr_name, last_seen
            FROM jr_status
            WHERE is_online = TRUE
              AND last_seen < NOW() - INTERVAL '5 minutes'
        """)
        dead_workers = cur.fetchall()

        for worker in dead_workers:
            print(f"[Health] Worker {worker[0]} appears dead, last seen: {worker[1]}")
            # Mark offline
            cur.execute("""
                UPDATE jr_status SET is_online = FALSE WHERE jr_name = %s
            """, (worker[0],))

            # Try to restart via systemd
            service = f"jr-queue-worker@{worker[0]}"
            subprocess.run(['systemctl', '--user', 'restart', service], check=False)

        conn.commit()

if __name__ == '__main__':
    check_worker_health()
```

### 5. Deployment Script

**File:** `/ganuda/scripts/deploy_robust_workers.sh`

```bash
#!/bin/bash
# Deploy robust Jr worker infrastructure

set -e

echo "=== Deploying Robust Jr Worker Infrastructure ==="

# 1. Install sdnotify
/home/dereadi/cherokee_venv/bin/pip install sdnotify

# 2. Copy systemd units
mkdir -p ~/.config/systemd/user
cp /ganuda/scripts/systemd/jr-queue-worker@.service ~/.config/systemd/user/
cp /ganuda/scripts/systemd/jr-auto-assigner.service ~/.config/systemd/user/
cp /ganuda/scripts/systemd/jr-health-monitor.service ~/.config/systemd/user/
cp /ganuda/scripts/systemd/jr-health-monitor.timer ~/.config/systemd/user/

# 3. Reload systemd
systemctl --user daemon-reload

# 4. Enable and start services
systemctl --user enable jr-queue-worker@it_triad_jr
systemctl --user enable jr-auto-assigner
systemctl --user enable jr-health-monitor.timer

systemctl --user start jr-queue-worker@it_triad_jr
systemctl --user start jr-auto-assigner
systemctl --user start jr-health-monitor.timer

# 5. Enable linger for user services to run at boot
sudo loginctl enable-linger dereadi

echo "=== Deployment Complete ==="
echo "Check status with: systemctl --user status jr-queue-worker@it_triad_jr"
```

---

## Systemd Timer for Health Monitor

**File:** `/ganuda/scripts/systemd/jr-health-monitor.timer`

```ini
[Unit]
Description=Jr Worker Health Monitor Timer

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

**File:** `/ganuda/scripts/systemd/jr-health-monitor.service`

```ini
[Unit]
Description=Jr Worker Health Monitor

[Service]
Type=oneshot
ExecStart=/home/dereadi/cherokee_venv/bin/python3 /ganuda/jr_executor/worker_health_monitor.py
```

---

## Auto-Assigner Systemd Service

**File:** `/ganuda/scripts/systemd/jr-auto-assigner.service`

```ini
[Unit]
Description=Jr Task Auto-Assigner
After=network.target

[Service]
Type=simple
User=dereadi
ExecStart=/home/dereadi/cherokee_venv/bin/python3 /ganuda/jr_executor/task_auto_assigner.py
Restart=always
RestartSec=30

StandardOutput=append:/ganuda/logs/jr_auto_assigner.log
StandardError=append:/ganuda/logs/jr_auto_assigner.log

[Install]
WantedBy=multi-user.target
```

---

## Verification

1. Deploy services:
```bash
chmod +x /ganuda/scripts/deploy_robust_workers.sh
/ganuda/scripts/deploy_robust_workers.sh
```

2. Test auto-restart:
```bash
# Kill worker process
pkill -f "jr_queue_worker"
# Wait 15 seconds
sleep 15
# Should auto-restart
systemctl --user status jr-queue-worker@it_triad_jr
```

3. Test auto-assignment:
```bash
# Insert unassigned task
psql -c "INSERT INTO jr_work_queue (title, description, source, created_by) VALUES ('Test Auto-Assign', 'Test', 'tpm', 'claude_tpm')"
# Wait 60 seconds
sleep 65
# Should be assigned
psql -c "SELECT title, assigned_jr FROM jr_work_queue WHERE title = 'Test Auto-Assign'"
```

---

## Success Criteria

- [ ] Workers restart automatically on crash
- [ ] Stuck tasks get reset for retry
- [ ] Unassigned tasks get auto-assigned
- [ ] Health monitor runs every 5 minutes
- [ ] All services survive reboot (linger enabled)
- [ ] Logs capture all worker activity

---

*Cherokee AI Federation - For Seven Generations*
