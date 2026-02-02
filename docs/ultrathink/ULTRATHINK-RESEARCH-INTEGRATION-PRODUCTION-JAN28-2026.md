# ULTRATHINK: Production Research Integration

**Date:** 2026-01-28
**TPM:** Claude Opus 4.5
**Council Vote:** Pending full architecture review

---

## Executive Summary

Build production-ready research integration where ANY user research question flows through ii-researcher with file-based completion detection and dashboard delivery.

---

## Current State Analysis

### What Works
| Component | Status | Location |
|-----------|--------|----------|
| ii-researcher | ✅ Running | Port 8090 |
| SearXNG | ✅ Running | Port 8888 |
| research-worker | ✅ Running | systemd service |
| research_jobs table | ✅ Created | bluefin/zammad_production |
| SSE parsing | ✅ Fixed | research_client.py |
| LLM Gateway endpoints | ✅ Working | /v1/research/async, /v1/research/status |

### What's Missing
| Component | Status | Blocker |
|-----------|--------|---------|
| VetAssist → ii-researcher | ❌ Uses old jr_work_queue | Code change needed |
| File watcher daemon | ❌ Not created | Code + systemd |
| Dashboard research_history | ❌ Returns [] | Code change needed |
| Telegram /research | ❌ Not created | Code change needed |
| Jr file-edit capability | ❌ Executor limitation | Architecture gap |

---

## Architecture Decision

### Option A: File-Watcher Pattern (User Preferred)
```
Request File → Watcher → ii-researcher → Output File (1 min old) → Dashboard
```
**Pros:** Decoupled, observable, debuggable
**Cons:** More moving parts, additional daemon

### Option B: Direct API Integration
```
VetAssist API → LLM Gateway → research_jobs → research-worker → Database → Dashboard
```
**Pros:** Simpler, fewer services
**Cons:** Less observable, tighter coupling

### Decision: **Option A - File-Watcher Pattern**
User explicitly requested file-based completion detection ("modified date at least a minute old").

---

## Component Breakdown

### 1. Research Request Handler (VetAssist Backend)
**Purpose:** Accept research requests, write request files
**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py`
**Changes:**
- Add POST `/request` endpoint
- Write JSON to `/ganuda/research/requests/`
- Return request_id immediately

### 2. File Watcher Daemon
**Purpose:** Monitor request files, trigger research, detect completion, post results
**File:** `/ganuda/services/research_file_watcher.py`
**Service:** `research-file-watcher.service`
**Logic:**
- Scan `/ganuda/research/requests/` every 5s
- Process files >5s old (fully written)
- Queue to `/v1/research/async`
- Monitor `/ganuda/research/completed/{job_id}.json`
- When file >60s old → POST to dashboard

### 3. Research Complete Handler (VetAssist Backend)
**Purpose:** Receive completed research, store for dashboard
**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py`
**Changes:**
- Add POST `/complete` endpoint
- Insert into `vetassist_research_results` table

### 4. Database Schema
**Table:** `vetassist_research_results`
**Columns:** veteran_id, session_id, job_id, question, answer, sources, completed_at

### 5. Dashboard Query
**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`
**Changes:**
- Query `vetassist_research_results` for veteran
- Populate `research_history` array (currently returns [])

### 6. Telegram Integration (Future)
**File:** `/ganuda/telegram_bot/telegram_chief.py`
**Changes:**
- Add `/research` command
- Write request file OR call API directly
- Register for callback notification

---

## Jr Executor Gap Analysis

**Problem:** Current Jr executor generates summaries, cannot edit files.

**Evidence:**
```
Task 'Fix research_client.py SSE parsing': 2/2 steps succeeded
Result: Generated summary document, did not modify target file
```

**Solution Options:**

### Option A: Enhance Jr Executor (Recommended)
Add file-editing capability to `/ganuda/jr_executor/task_executor.py`:
- Parse JR instruction for file paths
- Use Edit tool pattern
- Validate changes before applying

### Option B: Manual Application
TPM applies code changes directly when Jr instructions require file edits.

### Option C: Hybrid
Jr generates code snippets in result, human/TPM applies.

**Decision:** Implement Option A as separate JR, use Option B for immediate needs.

---

## Execution Plan

### Phase 1: Infrastructure (Immediate)
| Task | Assignee | Method |
|------|----------|--------|
| Create directories | Manual | mkdir commands |
| Create database table | Manual | SQL |
| Create file watcher daemon | Manual/TPM | Write file |
| Create systemd service | Manual/TPM | Write file |

### Phase 2: VetAssist Integration
| Task | Assignee | Method |
|------|----------|--------|
| Add /request endpoint | Software Jr. | Code edit |
| Add /complete endpoint | Software Jr. | Code edit |
| Update dashboard query | Software Jr. | Code edit |

### Phase 3: Testing & Validation
| Task | Assignee | Method |
|------|----------|--------|
| Drop test request file | Manual | echo command |
| Verify end-to-end flow | Manual | curl + logs |
| Validate dashboard display | Manual | Browser |

### Phase 4: Telegram Integration (Future)
| Task | Assignee | Method |
|------|----------|--------|
| Add /research command | Telegram Jr. | Code edit |
| Wire callback notification | Software Jr. | Code edit |

---

## Jr Dispatch Matrix

Given executor limitation (no file edits), dispatch as follows:

| JR ID | Type | Executable by Jr? | Alternative |
|-------|------|-------------------|-------------|
| JR-RESEARCH-FILE-WATCHER-DAEMON | New file creation | ❌ No | TPM creates |
| JR-VETASSIST-REQUEST-ENDPOINT | Code modification | ❌ No | TPM applies |
| JR-VETASSIST-COMPLETE-ENDPOINT | Code modification | ❌ No | TPM applies |
| JR-VETASSIST-DASHBOARD-QUERY | Code modification | ❌ No | TPM applies |
| JR-EXECUTOR-FILE-EDIT-CAPABILITY | New capability | ✅ Research | Jr researches, TPM implements |

---

## Immediate Actions

1. **TPM creates file watcher daemon** (can't wait for Jr)
2. **TPM creates systemd service**
3. **TPM creates database table**
4. **TPM modifies VetAssist endpoints**
5. **TPM modifies dashboard query**
6. **Queue Jr task for executor enhancement** (future capability)

---

## Success Criteria

- [ ] User asks research question in VetAssist
- [ ] Request file created in `/ganuda/research/requests/`
- [ ] File watcher picks up within 10s
- [ ] ii-researcher processes (3-5 min)
- [ ] Output file created in `/ganuda/research/completed/`
- [ ] After 60s, file watcher posts to dashboard
- [ ] Dashboard shows research result under "AI Research"

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| File watcher crashes | Medium | systemd restart, monitoring |
| ii-researcher timeout | Low | 5 min timeout, error handling |
| Dashboard doesn't update | Medium | Direct DB insert, no cache |
| Duplicate processing | Low | Move processed files, check job_id |

---

## Seven Generations Impact

This infrastructure enables:
- Veterans get authoritative research on claims
- Reduces dependency on external paid APIs
- Builds institutional knowledge in Cherokee AI
- Foundation for future AI-assisted services

---

FOR SEVEN GENERATIONS
