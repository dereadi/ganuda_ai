# Jr Instruction: Implement Hybrid Task Self-Assignment

**Task ID:** JR-HYBRID-001
**Priority:** P0 (Critical - blocks all other Jr work)
**Date:** January 24, 2026
**Council Vote:** b1bd2fe778eb2267 (88.8% confidence)

## Problem

Tasks queued to `jr_task_announcements` stay `open` forever because:
1. Bidding daemon (`jr_bidding_daemon.py`) is not running as a service
2. Executor (`jr_task_executor.py`) only processes tasks with `status='assigned'`
3. No fallback mechanism when bidding fails

## Council Decision

**Hybrid Approach:** Executor self-assigns orphan tasks as fallback while supporting distributed bidding when available.

## Implementation

### File: `/ganuda/jr_executor/jr_task_executor.py`

### Step 1: Add Orphan Task Detection

Add after `get_assigned_tasks()` method (around line 240):

```python
def get_orphan_tasks(self) -> List[dict]:
    """
    Get open tasks with no recent bids - fallback when bidding daemon not running.

    Orphan criteria:
    - Status is 'open'
    - Announced more than 60 seconds ago (give bidding daemon a chance)
    - No bids in the last 60 seconds

    This is the "snake below" - catches tasks the normal system missed.
    """
    try:
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT t.task_id, t.task_type, t.task_content, t.priority,
                       t.required_capabilities
                FROM jr_task_announcements t
                LEFT JOIN jr_task_bids b ON t.task_id = b.task_id
                    AND b.bid_time > NOW() - INTERVAL '60 seconds'
                WHERE t.status = 'open'
                  AND t.announced_at < NOW() - INTERVAL '60 seconds'
                  AND b.task_id IS NULL
                ORDER BY t.priority ASC, t.announced_at ASC
                LIMIT 1
            """)
            result = cur.fetchall()
            if result:
                print(f"[{self.agent_id}] Found {len(result)} orphan task(s)")
            return list(result)
    except Exception as e:
        print(f"[{self.agent_id}] Error fetching orphan tasks: {e}")
        try:
            if self._conn and not self._conn.closed:
                self._conn.rollback()
        except:
            pass
        return []
```

### Step 2: Add Self-Assignment Method

Add after `get_orphan_tasks()`:

```python
def self_assign_task(self, task_id: str) -> bool:
    """
    Atomically self-assign an orphan task.

    Uses UPDATE with WHERE status='open' to prevent race conditions
    if multiple executors try to claim the same task.

    Returns True if successfully assigned, False if already taken.
    """
    try:
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE jr_task_announcements
                SET status = 'assigned',
                    assigned_to = %s,
                    metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                WHERE task_id = %s
                  AND status = 'open'
                RETURNING task_id
            """, (
                self.agent_id,
                json.dumps({
                    "self_assigned": True,
                    "assigned_at": datetime.now().isoformat(),
                    "fallback_reason": "no_bidding_daemon"
                }),
                task_id
            ))

            result = cur.fetchone()
            conn.commit()

            if result:
                print(f"[{self.agent_id}] Self-assigned orphan task: {task_id}")
                return True
            else:
                print(f"[{self.agent_id}] Task {task_id} already claimed by another agent")
                return False

    except Exception as e:
        print(f"[{self.agent_id}] Failed to self-assign {task_id}: {e}")
        try:
            if self._conn and not self._conn.closed:
                self._conn.rollback()
        except:
            pass
        return False
```

### Step 3: Add Stale Task Cleanup

Add method to handle stuck tasks:

```python
def cleanup_stale_tasks(self):
    """
    Reset tasks stuck in_progress for too long.

    This handles the case where an agent crashed mid-execution
    or a task is taking unreasonably long.

    Stale threshold: 1 hour in_progress without completion.
    """
    try:
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE jr_task_announcements
                SET status = 'open',
                    assigned_to = NULL,
                    metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                WHERE status = 'in_progress'
                  AND announced_at < NOW() - INTERVAL '1 hour'
                RETURNING task_id, assigned_to
            """, (json.dumps({
                "reset_reason": "stale_timeout",
                "reset_at": datetime.now().isoformat(),
                "reset_by": self.agent_id
            }),))

            reset_tasks = cur.fetchall()
            conn.commit()

            for task in reset_tasks:
                print(f"[{self.agent_id}] Reset stale task {task['task_id']} "
                      f"(was assigned to {task['assigned_to']})")

    except Exception as e:
        print(f"[{self.agent_id}] Stale task cleanup error: {e}")
        try:
            if self._conn and not self._conn.closed:
                self._conn.rollback()
        except:
            pass
```

### Step 4: Update Main Loop

Find the `run()` method (around line 990) and update the task fetching logic:

**Before:**
```python
tasks = self.get_assigned_tasks()
if tasks:
    print(f"[{self.agent_id}] Found {len(tasks)} assigned task(s)")
```

**After:**
```python
# Primary: Check for tasks assigned to us
tasks = self.get_assigned_tasks()

# Fallback: If nothing assigned, check for orphan tasks
if not tasks:
    orphans = self.get_orphan_tasks()
    if orphans:
        orphan = orphans[0]
        print(f"[{self.agent_id}] No assigned tasks, attempting self-assign of {orphan['task_id']}")
        if self.self_assign_task(orphan['task_id']):
            # Re-fetch now that we've assigned it
            tasks = self.get_assigned_tasks()

if tasks:
    print(f"[{self.agent_id}] Found {len(tasks)} assigned task(s)")
```

### Step 5: Add Periodic Cleanup

In the main loop, add cleanup every 5 minutes:

```python
# Add at class level
self.last_cleanup = 0
CLEANUP_INTERVAL = 300  # 5 minutes

# In run() loop, add before task fetching:
if time.time() - self.last_cleanup > CLEANUP_INTERVAL:
    self.cleanup_stale_tasks()
    self.last_cleanup = time.time()
```

### Step 6: Add Required Import

At top of file, ensure json is imported:

```python
import json
```

---

## Immediate Fix: Reset Stuck Task

Before deploying the code fix, manually reset the month-old stuck task:

```sql
-- Run on bluefin
UPDATE jr_task_announcements
SET status = 'open',
    assigned_to = NULL,
    metadata = metadata || '{"reset_reason": "manual_dead_agent", "reset_at": "2026-01-24"}'::jsonb
WHERE task_id = 'JR-HIVEMIND-LEARNING-002';
```

---

## Testing

After deploying changes:

1. Restart executor: `sudo systemctl restart jr-executor`
2. Check logs: `tail -f /var/log/ganuda/jr-executor.log`
3. Verify orphan detection:
   - Should see "Found X orphan task(s)" within 60 seconds
   - Should see "Self-assigned orphan task: VETASSIST-SEC-001"
4. Verify execution begins
5. Check task status in database

---

## Success Criteria

- [ ] `get_orphan_tasks()` method added
- [ ] `self_assign_task()` method added
- [ ] `cleanup_stale_tasks()` method added
- [ ] Main loop updated with fallback logic
- [ ] Periodic cleanup running every 5 minutes
- [ ] JR-HIVEMIND-LEARNING-002 reset and re-queued
- [ ] VETASSIST-SEC-001 executes successfully
- [ ] No race conditions (tested with multiple agents)

---

## Thermal Memory

This fix implements the Council's Coyote Wisdom: "The rabbit who only looks for the hawk above misses the snake below."

We're not just fixing the obvious problem (start bidding daemon) - we're adding defense in depth so the system self-heals when components fail.

---

**FOR SEVEN GENERATIONS** - Systems that heal themselves protect those who come after.
