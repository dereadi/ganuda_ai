# Jr Instruction: Executor Task Reaper — Reset Orphaned in_progress Tasks

**Task ID:** EXECUTOR-TASK-REAPER
**Kanban:** #1884
**Priority:** 2
**Assigned Jr:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

Tasks claimed by the executor via `get_pending_tasks()` are set to `in_progress` atomically. If the executor crashes or restarts before completing the task, those tasks stay `in_progress` forever — the next poll cycle only picks up `pending` or `assigned` tasks. This has caused 3 separate incidents in Feb 22 alone. Fix: add a reaper that resets tasks stuck in_progress for more than 10 minutes.

---

## Step 1: Add reap_stale_tasks method to JrQueueClient

File: `/ganuda/jr_executor/jr_queue_client.py`

```python
<<<<<<< SEARCH
    def get_pending_tasks(self, limit: int = 10) -> List[Dict]:
=======
    def reap_stale_tasks(self, timeout_minutes: int = 10) -> int:
        """
        Reset tasks stuck in_progress for longer than timeout.
        Called before get_pending_tasks to recover from executor crashes.
        Returns number of tasks reset.
        """
        try:
            rows = self._execute("""
                UPDATE jr_work_queue
                SET status = 'pending',
                    started_at = NULL,
                    status_message = 'Reset by reaper (stale in_progress > %s min)'
                WHERE assigned_jr = %s
                  AND status = 'in_progress'
                  AND started_at < NOW() - INTERVAL '%s minutes'
                RETURNING id, title
            """, (timeout_minutes, self.jr_name, timeout_minutes))
            if rows:
                for r in rows:
                    print(f"[Reaper] Reset stale task #{r['id']}: {r['title']}")
            return len(rows) if rows else 0
        except Exception as e:
            print(f"[Reaper] Error: {e}")
            return 0

    def get_pending_tasks(self, limit: int = 10) -> List[Dict]:
>>>>>>> REPLACE
```

---

## Step 2: Call reaper before polling for new tasks

File: `/ganuda/jr_executor/jr_cli.py`

```python
<<<<<<< SEARCH
                        try:
                            self.queue_client.heartbeat()
                            pending_tasks = self.queue_client.get_pending_tasks(limit=1)
=======
                        try:
                            self.queue_client.heartbeat()
                            self.queue_client.reap_stale_tasks(timeout_minutes=10)
                            pending_tasks = self.queue_client.get_pending_tasks(limit=1)
>>>>>>> REPLACE
```

---

## Verification

```text
cd /ganuda/jr_executor && python3 -c "from jr_queue_client import JrQueueClient; print('Import OK')"
```

## What NOT to Change

- Do NOT modify get_pending_tasks query
- Do NOT modify task completion or failure handling
- Do NOT add any new imports
