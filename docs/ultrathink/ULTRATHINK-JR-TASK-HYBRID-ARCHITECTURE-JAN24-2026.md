# ULTRATHINK: Jr Task System Hybrid Architecture
## Date: January 24, 2026
## Cherokee AI Federation - For Seven Generations

---

## Council Vote Summary

**Question:** Jr Task Architecture - how to fix tasks stuck in `open` status?

**Decision:** Hybrid Approach
**Confidence:** 88.8% (High)
**Concerns:** 5 specialists flagged concerns

| Specialist | Concern | Interpretation |
|------------|---------|----------------|
| Gecko | PERF CONCERN | Don't add unnecessary overhead |
| Turtle | 7GEN CONCERN | Build for long-term sustainability |
| Raven | STRATEGY CONCERN | Consider future scaling needs |
| Crawdad | SECURITY CONCERN | Don't create race conditions or auth gaps |
| Eagle Eye | VISIBILITY CONCERN | Need observability into task flow |

**Coyote Wisdom:** "The rabbit who only looks for the hawk above misses the snake below."
- Don't just fix the obvious problem (bidding daemon not running)
- Also handle edge cases (dead agents, stuck tasks, network partitions)

---

## Root Cause Analysis

### Current State
```
[Task Queued] → status: 'open' → STUCK HERE
                     ↓
[Bidding Daemon] → NOT RUNNING → never assigns
                     ↓
[Task Executor] → only sees 'assigned' → nothing to do
```

### Additional Issues Found
1. `JR-HIVEMIND-LEARNING-002` stuck `in_progress` for 30+ days (assigned to dead agent)
2. `hive_mind` module not available (collective learning disabled)
3. Only bluefin runs executor (5 other nodes idle)
4. No task timeout/cleanup mechanism

---

## Hybrid Architecture Design

### Principle
**Defense in depth** - multiple mechanisms ensure tasks get executed:

1. **Primary:** Bidding daemon assigns tasks (distributed coordination)
2. **Fallback:** Executor self-assigns orphan tasks (resilience)
3. **Cleanup:** Stale task recovery (dead agent handling)

### Architecture Diagram
```
                    ┌─────────────────────────────────────┐
                    │         Task Announcements          │
                    │         (PostgreSQL table)          │
                    └─────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │   Bidding    │ │   Bidding    │ │   Bidding    │
            │   Daemon     │ │   Daemon     │ │   Daemon     │
            │  (bluefin)   │ │  (redfin)    │ │  (greenfin)  │
            └──────────────┘ └──────────────┘ └──────────────┘
                    │                │                │
                    │    Assigns tasks based on       │
                    │    capabilities & load          │
                    ▼                ▼                ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │   Executor   │ │   Executor   │ │   Executor   │
            │  (bluefin)   │ │  (redfin)    │ │  (greenfin)  │
            └──────────────┘ └──────────────┘ └──────────────┘
                    │                │                │
                    └────────────────┴────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      Fallback Self-Assignment    │
                    │  If no bidding daemon, executor  │
                    │  claims orphan 'open' tasks      │
                    └─────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Executor Self-Assignment (Immediate Fix)

Add to `jr_task_executor.py`:

```python
def get_orphan_tasks(self) -> List[dict]:
    """
    Get open tasks that have no assignment and no recent bids.
    Fallback mechanism when bidding daemon is not running.
    """
    try:
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Find open tasks older than 60 seconds with no bids
            cur.execute("""
                SELECT t.task_id, t.task_type, t.task_content, t.priority
                FROM jr_task_announcements t
                LEFT JOIN jr_task_bids b ON t.task_id = b.task_id
                    AND b.bid_time > NOW() - INTERVAL '60 seconds'
                WHERE t.status = 'open'
                  AND t.announced_at < NOW() - INTERVAL '60 seconds'
                  AND b.task_id IS NULL
                ORDER BY t.priority ASC, t.announced_at ASC
                LIMIT 1
            """)
            return list(cur.fetchall())
    except Exception as e:
        print(f"[{self.agent_id}] Error fetching orphan tasks: {e}")
        return []

def self_assign_task(self, task_id: str) -> bool:
    """
    Self-assign an orphan task. Uses SELECT FOR UPDATE to prevent races.
    """
    try:
        conn = self._get_connection()
        with conn.cursor() as cur:
            # Atomic assignment with row lock
            cur.execute("""
                UPDATE jr_task_announcements
                SET status = 'assigned',
                    assigned_to = %s,
                    metadata = metadata || '{"self_assigned": true, "assigned_at": "%s"}'::jsonb
                WHERE task_id = %s
                  AND status = 'open'
                RETURNING task_id
            """, (self.agent_id, datetime.now().isoformat(), task_id))

            result = cur.fetchone()
            conn.commit()

            if result:
                print(f"[{self.agent_id}] Self-assigned orphan task: {task_id}")
                return True
            return False
    except Exception as e:
        print(f"[{self.agent_id}] Failed to self-assign {task_id}: {e}")
        conn.rollback()
        return False
```

Update main loop:

```python
def run(self):
    while self.running:
        try:
            # Primary: Check for assigned tasks
            tasks = self.get_assigned_tasks()

            # Fallback: Check for orphan tasks if nothing assigned
            if not tasks:
                orphans = self.get_orphan_tasks()
                if orphans:
                    task = orphans[0]
                    if self.self_assign_task(task['task_id']):
                        tasks = self.get_assigned_tasks()

            if tasks:
                # Execute task...
```

### Phase 2: Stale Task Cleanup

Add cleanup for stuck tasks:

```python
def cleanup_stale_tasks(self):
    """
    Reset tasks stuck in_progress for too long (dead agent recovery).
    Run periodically (every 5 minutes).
    """
    try:
        conn = self._get_connection()
        with conn.cursor() as cur:
            # Reset tasks in_progress for more than 1 hour
            cur.execute("""
                UPDATE jr_task_announcements
                SET status = 'open',
                    assigned_to = NULL,
                    metadata = metadata || '{"reset_reason": "stale_timeout", "reset_at": "%s"}'::jsonb
                WHERE status = 'in_progress'
                  AND announced_at < NOW() - INTERVAL '1 hour'
                RETURNING task_id, assigned_to
            """, (datetime.now().isoformat(),))

            reset_tasks = cur.fetchall()
            conn.commit()

            for task_id, old_agent in reset_tasks:
                print(f"[{self.agent_id}] Reset stale task {task_id} (was assigned to {old_agent})")

    except Exception as e:
        print(f"[{self.agent_id}] Stale task cleanup error: {e}")
```

### Phase 3: Bidding Daemon Service (Future)

Create `/etc/systemd/system/jr-bidding.service`:

```ini
[Unit]
Description=Jr Bidding Daemon - Cherokee AI Federation
After=network.target postgresql.service

[Service]
Type=simple
User=dereadi
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/dereadi/cherokee_venv/bin/python3 -u /ganuda/jr_executor/jr_bidding_daemon.py "Infrastructure Jr." bluefin
Restart=always
RestartSec=10
StandardOutput=append:/var/log/ganuda/jr-bidding.log
StandardError=append:/var/log/ganuda/jr-bidding.log

[Install]
WantedBy=multi-user.target
```

---

## Observability (Eagle Eye)

Add logging and metrics:

```python
# Task lifecycle logging
print(f"[TASK:{task_id}] announced → {status} by {agent}")
print(f"[TASK:{task_id}] execution started")
print(f"[TASK:{task_id}] execution completed in {duration}ms")
print(f"[TASK:{task_id}] execution failed: {error}")

# Metrics to track
# - Tasks by status (open, assigned, in_progress, completed, failed)
# - Average time in each status
# - Self-assignment rate (indicator bidding daemon health)
# - Stale task resets (indicator of agent health)
```

---

## Security (Crawdad)

Prevent race conditions and unauthorized execution:

1. **Atomic assignment:** Use `SELECT FOR UPDATE` or single UPDATE with WHERE clause
2. **Agent validation:** Only execute tasks assigned to this specific agent
3. **Capability matching:** Self-assignment respects required_capabilities
4. **Audit trail:** Log all state changes with timestamps and agent IDs

---

## Thermal Memory Entry

```json
{
    "type": "architectural_decision",
    "topic": "jr_task_hybrid_architecture",
    "decision": "Hybrid approach: Executor self-assigns orphan tasks as fallback, bidding daemon handles distributed coordination. Defense in depth ensures tasks execute even when components fail.",
    "council_vote": "b1bd2fe778eb2267",
    "confidence": 0.888,
    "concerns": ["performance", "7gen", "strategy", "security", "visibility"],
    "coyote_wisdom": "The rabbit who only looks for the hawk above misses the snake below",
    "timestamp": "2026-01-24"
}
```

---

## Success Criteria

- [ ] Executor self-assigns orphan tasks after 60s
- [ ] No race conditions on assignment (atomic update)
- [ ] Stale tasks (1hr+) reset to open
- [ ] JR-HIVEMIND-LEARNING-002 recovered
- [ ] New tasks (VETASSIST-SEC-001, etc.) execute
- [ ] Logging shows task lifecycle
- [ ] Thermal memory updated

---

**FOR SEVEN GENERATIONS** - Build systems that heal themselves.
