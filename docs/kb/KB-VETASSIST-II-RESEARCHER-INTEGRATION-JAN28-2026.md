# KB Article: VetAssist ii-researcher Production Integration

**KB ID:** KB-VETASSIST-II-RESEARCHER-INTEGRATION-JAN28-2026
**Category:** Architecture / Integration
**Author:** TPM
**Status:** Deployed

---

## Summary

Production integration of ii-researcher async research pattern with VetAssist dashboard. Veterans ask research questions, results appear on dashboard in 3-5 minutes.

---

## Architecture

```
VetAssist Chat
     │
     ▼ POST /api/v1/research/trigger
     │
/ganuda/research/requests/{veteran_id}-{uuid}.json
     │
     ▼ (file watcher detects, 5s old)
     │
LLM Gateway /v1/research/async
     │
     ▼ (research-worker processes)
     │
/ganuda/research/completed/{job_id}.json
     │
     ▼ (file watcher detects, 60s old = complete)
     │
INSERT INTO vetassist_research_results
     │
     ▼
Dashboard displays in research_history
```

---

## Components Deployed

| Component | Location | Service |
|-----------|----------|---------|
| File Watcher Daemon | /ganuda/services/research_file_watcher.py | research-file-watcher.service |
| Research Worker | /ganuda/services/research_worker.py | research-worker.service |
| Research Client | /ganuda/lib/research_client.py | (library) |
| VetAssist Research Endpoints | /ganuda/vetassist/backend/app/api/v1/endpoints/research.py | vetassist-backend.service |
| Dashboard Query | /ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py | vetassist-backend.service |

---

## Database Tables

### research_jobs (LLM Gateway)
- Tracks async research jobs from any source
- Fields: job_id, query, status, output_file, result_summary

### vetassist_research_results (VetAssist)
- Stores completed research for veteran dashboards
- Fields: veteran_id, session_id, job_id, question, answer, sources

---

## Key Configuration

| Setting | Value |
|---------|-------|
| Request min age | 5 seconds |
| Completion age threshold | 60 seconds |
| Max wait time | 600 seconds |
| Poll interval | 5 seconds |
| Max research steps | 5 (default) |

---

## Lessons Learned

### 1. SSE Event Type Mismatch
**Issue:** research_client.py looked for `type: "report"` but ii-researcher sends `type: "writing_report"`

**Fix:** Changed event type and field name in research_client.py:
- `event_type == "report"` → `event_type == "writing_report"`
- `data.content` → `data.final_report`

### 2. Jr Executor Limitation
**Issue:** Jr executor generates summaries but cannot edit files

**Impact:** Code changes required TPM direct implementation

**Future:** Need to enhance Jr executor with file-edit capability

### 3. File-Based Completion Detection
**Pattern:** File is considered complete when modified date is >= 60 seconds old

**Rationale:** Ensures file write is complete before reading

---

## Monitoring

```bash
# File watcher logs
journalctl -u research-file-watcher -f

# Research worker logs
journalctl -u research-worker -f

# Check pending requests
ls -la /ganuda/research/requests/

# Check completed research
ls -la /ganuda/research/completed/

# Query results table
psql -h 192.168.132.222 -U claude -d zammad_production \
  -c "SELECT job_id, question, created_at FROM vetassist_research_results ORDER BY created_at DESC LIMIT 5;"
```

---

## Rollback

```bash
# Stop services
sudo systemctl stop research-file-watcher
sudo systemctl stop research-worker

# Disable services
sudo systemctl disable research-file-watcher
sudo systemctl disable research-worker

# VetAssist will fall back gracefully (empty research_history)
```

---

## Related JR Instructions

- JR-II-RESEARCHER-ASYNC-PATTERN-JAN28-2026
- JR-VETASSIST-FILE-WATCHER-DAEMON-JAN28-2026
- JR-FIX-RESEARCH-CLIENT-SSE-PARSING-JAN28-2026

---

FOR SEVEN GENERATIONS
