# KB: Jr Executor Dual-Pipeline Architecture

**Date**: February 11, 2026
**Discovered During**: Post-power-outage Jr pipeline debugging
**Related Thermals**: #84024 (power outage recovery)
**Severity**: HIGH — Root cause of multiple "lost" task submissions

---

## Executive Summary

The Jr executor system has **two completely independent task execution pipelines** that do NOT communicate. Submitting a task to the wrong pipeline (or without the correct fields) results in the task being silently ignored or only partially processed.

---

## The Two Pipelines

### Pipeline A: jr_work_queue (Direct Execution)

**Table**: `jr_work_queue`
**Workers**: `jr_queue_worker.py` → `task_executor.py`
**What it does**: Executes SEARCH/REPLACE blocks and Create blocks from Jr instruction files. Actually writes code.

**Critical field**: `assigned_jr` — **MUST be set on INSERT**. Workers query `WHERE assigned_jr = %s`, so NULL assigned_jr = invisible task.

**How to submit**:
```sql
INSERT INTO jr_work_queue (title, description, instruction_file, assigned_jr, use_rlm, status)
VALUES (
  'Task Title Here',
  'Description of what to build',
  '/ganuda/docs/jr_instructions/JR-INSTRUCTION-FILE.md',
  'Software Engineer Jr.',  -- REQUIRED, must match a registered Jr
  false,                     -- use_rlm: false for well-structured instructions
  'pending'
);
```

**Valid assigned_jr values** (check jr_status table for current):
- `Software Engineer Jr.`
- `Infrastructure Jr.`
- `Vision Jr.`
- `Research Jr.` (caution: may route to ResearchTaskExecutor)

### Pipeline B: jr_task_announcements (Bidding System)

**Table**: `jr_task_announcements`
**Workers**: `jr_bidding_daemon.py` → `close_bidding.py` → `jr_task_executor.py`
**What it does**: Announces tasks, Jrs bid on them, highest bidder wins. But the executor **only generates implementation plans** — it does NOT execute SEARCH/REPLACE blocks or create files.

**How it works**:
1. Insert task with `status = 'open'`
2. `jr_bidding_daemon.py` polls for open tasks, Jrs submit bids
3. `close_bidding.py` selects winner, sets `status = 'assigned'`
4. `jr_task_executor.py` generates an implementation plan (text only)

**When to use**: Research tasks, planning, deliberation — NOT code execution.

---

## Common Mistakes

### 1. Missing `assigned_jr` (Pipeline A)

**Symptom**: Task inserted into jr_work_queue, shows as 'pending', but never picked up.
**Cause**: `assigned_jr` is NULL. Queue workers filter by `WHERE assigned_jr = %s`.
**Fix**: `UPDATE jr_work_queue SET assigned_jr = 'Software Engineer Jr.' WHERE id = <task_id>;`

### 2. Inserting code tasks into Pipeline B

**Symptom**: Task gets "executed" but no files are created. Only a plan document is produced.
**Cause**: `jr_task_executor.py` (Pipeline B) generates plans, not code. It doesn't read instruction files or execute SEARCH/REPLACE blocks.
**Fix**: Insert into `jr_work_queue` (Pipeline A) with `assigned_jr` set.

### 3. Title containing "research"

**Symptom**: Task gets routed to `ResearchTaskExecutor` instead of the code executor.
**Cause**: `is_research_task()` function checks if the title contains "research" (case-insensitive).
**Fix**: Avoid the word "research" in jr_work_queue titles for code execution tasks.

### 4. jr-bidding missing EnvironmentFile

**Symptom**: `fe_sendauth: no password supplied` in jr-bidding logs.
**Cause**: The jr-bidding.service unit file doesn't include `EnvironmentFile=/ganuda/config/secrets.env`.
**Fix**: Create systemd drop-in:
```
/etc/systemd/system/jr-bidding.service.d/secrets.conf
[Service]
EnvironmentFile=/ganuda/config/secrets.env
```
Then: `sudo systemctl daemon-reload && sudo systemctl restart jr-bidding`

### 5. jr-orchestrator thrashing on stale heartbeat

**Symptom**: Logs show spawning/killing workers every 3 seconds in infinite loop for a specific Jr type.
**Cause**: Worker heartbeat in DB is stale but orchestrator has no circuit breaker.
**Fix**: `sudo systemctl restart jr-orchestrator` (clears internal state)

---

## Decision Guide: Which Pipeline To Use

| Task Type | Pipeline | Table | assigned_jr |
|-----------|----------|-------|-------------|
| Code execution (SEARCH/REPLACE) | A | jr_work_queue | Required |
| File creation (Create blocks) | A | jr_work_queue | Required |
| Research/deliberation | B | jr_task_announcements | Set by bidding |
| Planning/architecture | B | jr_task_announcements | Set by bidding |

---

## Post-Outage Recovery Checklist

After a power outage, these Jr pipeline components need verification:

1. **vLLM** — `systemctl status vllm` (GPU model serving)
2. **jr-executor** — `systemctl status jr-executor` (Pipeline A worker)
3. **jr-orchestrator** — `systemctl status jr-orchestrator` (Pipeline A coordinator)
4. **jr-bidding** — `systemctl status jr-bidding` (Pipeline B announcements)
5. **llm-gateway** — `systemctl status llm-gateway` (API gateway)
6. **Check for stale tasks**: `SELECT id, title, status, assigned_jr FROM jr_work_queue WHERE status = 'in_progress' AND updated_at < NOW() - interval '1 hour';`

---

## RLM Interaction

For well-structured Jr instructions with explicit SEARCH/REPLACE or Create blocks, **always set `use_rlm = false`** in the jr_work_queue INSERT. The RLM (Reasoning Language Model) interceptor has a threshold of >8000 chars AND >5 files — below that threshold, direct execution is faster and more reliable.

---

*For Seven Generations — know which door you're knocking on before you knock.*
