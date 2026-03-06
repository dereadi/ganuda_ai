# KB: Executor Reaper + Idempotency Guard

**Date:** 2026-02-22
**Author:** TPM (direct fix)
**Severity:** P1 — Prevented 3 data corruption incidents in one session
**Related:** KB-DLQ-TRIAGE-PATTERNS-FEB22-2026 (Root Causes #3, #5)

---

## Problem

Two compounding executor bugs caused repeated data corruption:

### 1. Orphaned in_progress Tasks
- `get_pending_tasks()` atomically claims tasks → sets `in_progress`
- If executor crashes before task completes, task stays `in_progress` forever
- Next executor instance ignores it (only polls `pending` or `assigned`)
- **Impact:** 3 separate manual resets required in Feb 22 session alone

### 2. Retry Duplication
- When a SEARCH/REPLACE step fails, executor retries with vLLM reflection
- The SEARCH block matches a substring that includes the just-inserted REPLACE text
- Each retry prepends another copy of the same content
- **Impact:** CFR 4.10 = 12x duplication, AutoSave = 13x duplication

## Fixes Applied

### Reaper (jr_queue_client.py)
```python
def reap_stale_tasks(self, timeout_minutes=10):
    # Resets tasks stuck in_progress > N minutes back to pending
    # Called before get_pending_tasks in every poll cycle
```
- Located between `heartbeat()` and `get_pending_tasks()`
- Uses f-string for INTERVAL (psycopg2 can't parameterize intervals)
- Logs each reset: `[Reaper] Reset stale task #N: title`

### Idempotency Guard (search_replace_editor.py)
```python
# Before creating backup:
if replace_text in content and replace_text != search_text:
    # Already applied — return success without modifying
```
- Checks if REPLACE text already exists in file
- Skips the edit, returns `success=True`
- Prevents retry loop from prepending duplicate content
- The `replace_text != search_text` guard prevents false positives on no-op edits

### Call Site (jr_cli.py)
```python
self.queue_client.reap_stale_tasks(timeout_minutes=10)
```
Added before `get_pending_tasks()` in the daemon poll loop.

## Deployment

Requires executor restart to take effect:
```
kill <PID> && cd /ganuda/jr_executor && python3 -u jr_cli.py --daemon --poll-interval 30 &
```
Or: `sudo systemctl restart it-jr-executor`

## Testing

The idempotency guard can be tested by running a SEARCH/REPLACE where the REPLACE text already exists in the file — it should return success immediately without modifying the file.

## Files Modified
- `/ganuda/jr_executor/jr_queue_client.py` — Added `reap_stale_tasks()` method
- `/ganuda/jr_executor/search_replace_editor.py` — Added idempotency check
- `/ganuda/jr_executor/jr_cli.py` — Added reaper call before polling
