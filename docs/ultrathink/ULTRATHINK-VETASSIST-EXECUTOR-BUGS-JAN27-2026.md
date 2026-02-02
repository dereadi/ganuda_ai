# ULTRATHINK: VetAssist Jr Executor Bugs Analysis

**Date:** January 27, 2026
**TPM:** Claude Opus 4.5
**Classification:** Bug Analysis - Priority 2 (User-Facing Functionality)

---

## Executive Summary

Two critical bugs affecting VetAssist user experience:
1. **Research tasks auto-complete without doing actual research** - Tasks complete in ~5 seconds with stub results
2. **Scratchpad/notes not saving** - PUT endpoint missing from current dashboard.py

---

## Bug 1: Research Tasks Auto-Completing Without Work

### Symptom
- User asks "Can I claim rabies" via VetAssist research feature
- Task queued successfully to `jr_work_queue` (id=350)
- Task marked "completed" in 5 seconds
- Result is empty stub: `{"summary": "Task completed: VetAssist Research: Can I claim rabies...", "completed_at": "..."}`
- No actual research performed, no sources fetched

### Code Path Analysis

```
VetAssist Research Request
        │
        ▼
/ganuda/vetassist/backend/app/api/v1/endpoints/research.py
├── POST /trigger → Inserts to jr_work_queue
├── assigned_jr = 'it_triad_jr'
├── use_rlm = false
└── status = 'pending'
        │
        ▼
jr_work_queue (database table on bluefin)
        │
        ▼ (should be picked up by)
jr_queue_worker.py (daemon)
├── Polls for tasks matching assigned Jr name
├── Uses JrQueueClient to fetch pending tasks
└── Calls TaskExecutor.process_queue_task()
        │
        ▼
task_executor.py
├── is_research_task() → Should return True (title contains "Research")
└── ResearchTaskExecutor.execute_research_task()
        │
        ▼
research_task_executor.py
├── _extract_urls() → Finds 0 URLs (instructions don't contain URLs)
├── _extract_topics() → Finds 0 topics (patterns don't match "QUESTION: ...")
└── Returns success=False (0 sources fetched)
```

### Root Cause: Multiple Issues

**Issue 1A: No Worker Running for 'it_triad_jr'**
- VetAssist assigns research tasks to `assigned_jr='it_triad_jr'`
- jr_queue_worker.py filters by Jr name: `python3 jr_queue_worker.py "Software Engineer Jr."`
- If no worker is running with name `it_triad_jr`, task sits idle
- Something else then marks it complete with stub result

**Issue 1B: Research Executor Doesn't Generate URLs**
Even if the executor ran, ResearchTaskExecutor.execute_research_task() would fail because:
- `_extract_urls()` finds no URLs in the instruction text (it just says "Search these sources: 1. VA.gov...")
- `_extract_topics()` looks for patterns like "Research: X" but instructions use "QUESTION: X"
- Result: 0 URLs, 0 topics → empty summary report

**Issue 1C: Instruction-to-URL Gap**
The VetAssist research.py creates instructions that say:
```
Search these authoritative sources:
1. VA.gov official guidance and M21-1 manual
2. 38 CFR (Code of Federal Regulations)
...
```

But ResearchTaskExecutor expects actual URLs or ArXiv IDs, not source names.

### Evidence

Database query result:
```sql
SELECT id, title, status, result,
       EXTRACT(EPOCH FROM (completed_at - created_at)) as seconds
FROM jr_work_queue WHERE id = 350;
```
Result: `seconds = 5.0` (impossible for actual research)

---

## Bug 2: Scratchpad/Notes Not Saving

### Symptom
- User types notes in VetAssist scratchpad
- Notes disappear on page refresh
- Database shows empty scratchpad table

### Code Path Analysis

**Current dashboard.py (broken):**
- Line 76-86: Reads from `vetassist_scratchpads` table
- No PUT endpoint for saving

**Backup file (dashboard.py.backup_20260119_211848) has the fix:**
```python
@router.put("/{veteran_id}/scratchpad")
def update_scratchpad(veteran_id: str, data: ScratchpadUpdate):
    """Auto-save scratchpad content"""
    ...
    INSERT INTO vetassist_user_scratchpad (veteran_id, content, last_updated)
    ...
```

### Root Cause

**Issue 2A: Missing PUT Endpoint**
The scratchpad save endpoint was removed or never merged into current dashboard.py.

**Issue 2B: Table Name Mismatch**
- Backup uses: `vetassist_user_scratchpad`
- Current reads from: `vetassist_scratchpads`
- These may be different tables, causing read/write mismatch

**Issue 2C: Missing Pydantic Model**
The backup references `ScratchpadUpdate` model which may not exist in current code.

---

## Architectural Analysis

### Two Executor Systems (Complexity Issue)

The codebase has TWO separate task execution systems:

| System | Table | Executor | Used By |
|--------|-------|----------|---------|
| Contract Net | jr_task_announcements | jr_task_executor.py | Bidding-based tasks |
| Queue Worker | jr_work_queue | jr_queue_worker.py + task_executor.py | Direct-assigned tasks (VetAssist) |

This dual system creates confusion about which executor should handle what.

### Council Consultation Recommended

- **Gecko (Technical)**: Consolidate to single executor or document clear boundaries
- **Crawdad (Security)**: Ensure both paths have same security constraints
- **Turtle (7Gen)**: Choose sustainable architecture pattern

---

## Fix Recommendations

### Bug 1 Fix: Research Task Completion

**Priority Steps:**
1. Create URL generator for research sources
2. Fix topic extraction pattern to match "QUESTION:" format
3. Ensure worker daemon runs with correct Jr name
4. Add fallback: if no sources found, query Council instead of returning stub

**Code Changes Required:**
- `research_task_executor.py`: Add source-to-URL mapping
- `research.py`: Consider including actual URLs in instructions
- Systemd service for `jr_queue_worker.py` with `it_triad_jr`

### Bug 2 Fix: Scratchpad Save

**Priority Steps:**
1. Restore PUT endpoint from backup
2. Standardize table name: `vetassist_scratchpads` vs `vetassist_user_scratchpad`
3. Add ScratchpadUpdate Pydantic model
4. Create table if missing with migration script

---

## Files Affected

| File | Issue | Action |
|------|-------|--------|
| `/ganuda/jr_executor/research_task_executor.py` | URL extraction fails | Add source-to-URL mapping |
| `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py` | No URLs in instructions | Either add URLs or change strategy |
| `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py` | Missing PUT endpoint | Restore from backup |
| `/ganuda/scripts/systemd/` | No it_triad_jr worker | Add systemd service |

---

## Testing Plan

1. **Research Fix Verification:**
   - Queue test research task
   - Verify worker picks it up
   - Verify URLs are fetched
   - Verify meaningful result returned

2. **Scratchpad Fix Verification:**
   - Type notes in scratchpad
   - Refresh page
   - Verify notes persist
   - Check database for saved content

---

## JR Assignment

- **JR-VETASSIST-RESEARCH-EXECUTOR-FIX-JAN27-2026**: Fix research task execution path
- **JR-VETASSIST-SCRATCHPAD-SAVE-FIX-JAN27-2026**: Restore scratchpad save functionality

---

FOR SEVEN GENERATIONS
