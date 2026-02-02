# KB Article: ii-researcher Async Job Pattern

**KB ID:** KB-II-RESEARCHER-ASYNC-PATTERN-JAN28-2026
**Category:** Architecture
**Author:** TPM via Council Vote 166956a7959c2232

---

## Problem Statement

ii-researcher deep search takes 3-5 minutes per query. Synchronous API calls timeout and block user interfaces.

---

## Solution

Implemented async job queue pattern:

```
User Request → Queue (PostgreSQL) → Background Worker → Output File → Notify User
```

### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| research_dispatcher.py | /ganuda/lib/ | Queue jobs, check status |
| research_worker.py | /ganuda/services/ | Process jobs from queue |
| research-worker.service | systemd | Run worker as daemon |
| research_jobs table | zammad_production | Job queue and status |
| /ganuda/research/completed/ | Output dir | JSON result files |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /v1/research/async | POST | Queue research job |
| /v1/research/status/{job_id} | GET | Check job status |
| /v1/research/jobs | GET | List jobs |

---

## Key Design Decisions

### 1. File-based completion detection

User insight: "modified date at least a minute old = file complete"

Worker writes JSON output, watchers detect completion by file age.

### 2. PostgreSQL job queue

Uses `FOR UPDATE SKIP LOCKED` for worker concurrency safety.

### 3. Callback support

Jobs can trigger:
- Telegram notification
- Webhook call
- File watcher detection

---

## Lessons Learned

### Bug: Infinite loop in ii-researcher

**Root cause:** `max_steps` parameter accepted but never enforced. Agent ran `while True:` indefinitely.

**Fix:** Patched agent.py to add step counter:
```python
step = 0
while step < self.max_steps:
    step += 1
    ...
```

**Prevention:** Always verify loop termination conditions when integrating external LLM agents.

### Bug: SearXNG port mapping

**Root cause:** Mapped 8888:8888 but SearXNG listens on 8080 internally.

**Fix:** Changed to 8888:8080 in podman run command.

**Prevention:** Check container documentation for internal ports.

### Issue: Python __pycache__

**Symptom:** Code patches not taking effect.

**Fix:** Clear `__pycache__` directories after modifying Python files.

---

## Integration Points

| Consumer | JR Instruction | Status |
|----------|---------------|--------|
| API (direct) | Core pattern | ✅ Ready |
| Telegram Chief | JR-TELEGRAM-RESEARCH-COMMAND-JAN28-2026 | ⏳ Pending |
| VetAssist Dashboard | JR-VETASSIST-II-RESEARCHER-INTEGRATION-JAN28-2026 | ⏳ Pending |

---

## Related

- JR-II-RESEARCHER-ASYNC-PATTERN-JAN28-2026
- JR-II-RESEARCHER-STEP-LIMIT-FIX-JAN28-2026
- JR-DEPLOY-RESEARCH-WORKER-JAN28-2026
- JR-RESEARCH-SECURITY-ADDENDUM-JAN28-2026
- JR-RESEARCH-DEPLOYMENT-VALIDATION-JAN28-2026
- JR-TELEGRAM-RESEARCH-COMMAND-JAN28-2026
- JR-VETASSIST-II-RESEARCHER-INTEGRATION-JAN28-2026

---

FOR SEVEN GENERATIONS
