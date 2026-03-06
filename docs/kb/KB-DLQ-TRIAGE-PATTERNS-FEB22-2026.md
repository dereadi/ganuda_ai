# KB: DLQ Triage Patterns — Lessons from Feb 22 Audit

**Date:** 2026-02-22
**Author:** TPM
**Severity:** Operational
**Related:** KB-JR-EXECUTOR-SR-FIRST-EXTRACTION-FIX, KB-EXECUTOR-MIXED-STEP-TYPES-SKIP-BUG, KB-JR-INSTRUCTION-FORMAT-REGEX-COMPATIBILITY

---

## Problem

11 Jr tasks (IDs 791–815) from Feb 18-19 were stuck in DLQ with `in_progress` status. Root causes were compounding: nftables rate limiting on bluefin silently dropping DB connections (50/min limit exceeded by 5+ polling daemons), plus stale SEARCH strings in instructions written against outdated code.

## Root Causes Identified

### 1. nftables Rate Limiting (Infrastructure)
- Bluefin `pg_meter` was set to `rate 50/minute burst 75 packets`
- Federation has 5+ daemons polling PostgreSQL every 15-30 seconds
- At peak: Jr executor + thermal purge + embedding server + monitoring + gateway = 60+ connections/min
- Connections above threshold silently dropped — no error, no log
- **Fix:** Bumped to `rate 200/minute burst 300 packets`

### 2. Stale SEARCH Strings (Instruction Quality)
- Instructions were generated from documentation or LLM hallucination, NOT from reading actual files
- Common mismatches:
  - **Function names:** `get_cameras()` vs actual `camera_status()`, `describe_image()` vs `describe()`
  - **Variable names:** `lines` vs actual `digest_lines`, `logging.info` vs `logger.info`
  - **Architecture assumptions:** Instructions assumed raw psycopg2 but file uses FastAPI+SQLAlchemy
  - **Docstring text:** "Main ritual orchestration" vs actual "Main ritual cycle"
  - **Code structure:** Assumed inline switch/case but actual code delegates to component imports

### 3. Orphaned in_progress Tasks (Executor Design)
- `get_pending_tasks()` uses `FOR UPDATE SKIP LOCKED` and only picks up `pending` or `assigned`
- Tasks claimed before crash stay `in_progress` forever — no timeout/reaper
- **Workaround:** Manual `UPDATE SET status = 'pending' WHERE status = 'in_progress'`
- **Proper fix needed:** Add a reaper that resets tasks stuck in_progress > 10 minutes

### 4. telegram_notify.py Missing Import (Code Bug)
- `import os` was missing — `os.environ.get()` throws `NameError`
- Executor crashed on startup after restart
- Only surfaced because previous executor process had `os` imported from another module's side effect

### 5. Retry Duplication (Executor Behavior)
- Task #800 (CFR 4.10) retried 11 times, each appending the same text
- Result: 12x duplication of a paragraph in expand_articles.py line 455
- Task #833 (AutoSave) duplicated autoSave callback 13x in wizard session page
- **Root cause:** SR SEARCH block matches, REPLACE inserts before original, next retry matches again
- **Pattern:** Each retry's SEARCH hits the *first* occurrence (the newly inserted copy), prepends another
- **Fix needed:** Executor should check if REPLACE content already exists before applying
- **TPM workaround:** Manual deduplication via Edit tool

### 6. Calendar Seed Duplication (Missing Constraint)
- `federation_calendar` had no unique constraint on (event_date, event_name)
- Jr #830 inserted 9 events, then TPM migration inserted 9 more = 18 duplicates
- **Fix:** Added `CREATE UNIQUE INDEX idx_federation_calendar_unique ON federation_calendar (event_date, event_name)`

## Triage Methodology

For each stuck DLQ task:

1. **Read the instruction file** — identify all SEARCH/REPLACE blocks and Create blocks
2. **Read every target file** — get the actual content at the expected location
3. **Diff each SEARCH block** against actual content — identify exact mismatch
4. **Classify the failure:**
   - A) Stale SEARCH string (wrong function names, variable names, docstrings)
   - B) Architecture mismatch (file restructured, different framework)
   - C) Partial application (some steps succeeded, others didn't)
   - D) Mixed step types (Create + SR in same instruction — KB-EXECUTOR-MIXED-STEP-TYPES)
5. **Determine action:**
   - Partial: Write surgical instruction for remaining steps only
   - Stale: Rewrite with exact SEARCH strings from current file
   - Architecture mismatch: Full redesign of instruction
   - Already done: Mark completed

## Results (Feb 22)

| ID | Task | Status | Action |
|---|---|---|---|
| 791 | Ritual Calendar | Rewritten as #830 | **Completed** |
| 793 | VetAssist UserID | Already 100% done | **Marked completed** |
| 800 | CFR 4.10 | Corruption fixed, remaining steps deferred | TPM direct fix |
| 804 | Grafana | Deferred (lowest priority) | Needs full rewrite |
| 806 | Chat-Calculator | Deferred | Needs FormContext + layout wiring |
| 809 | Name Field Split | Rewritten as #832 (partial, OCR+PDF only) | **Queued** |
| 810 | PII Redaction | Deferred — pii_service.py already exists | Needs reconciliation with existing |
| 811 | Autosave UX | Rewritten as #833 (remaining steps only) | **Queued** |
| 813 | Consent | Deferred — FastAPI architecture mismatch | Needs full redesign |
| 814 | SAG Auth Guard | Rewritten as #831 | **Completed** + TPM finish |
| 815 | Feedback Widget | Deferred | Needs new files + router wiring |

## Prevention

1. **ALWAYS read target files before writing SEARCH strings** — never generate from memory or docs
2. **One instruction per edit type** — don't mix Create + SEARCH/REPLACE (KB-EXECUTOR-MIXED-STEP-TYPES)
3. **Set `use_rlm = false`** for well-structured instructions
4. **Add unique constraints** to any table that receives seed data
5. **Add a task reaper** to reset orphaned in_progress tasks after 10 minutes
6. **Monitor nftables counters** — `nft list counters` shows drops before they become silent failures
7. **SQL files not in executor whitelist** — `.sql` code blocks are skipped silently. TPM must run migrations manually via psql
8. **Executor language whitelist** — python, typescript, javascript, yaml, json, ini, toml, conf, cfg, text, env, properties. SQL, bash, shell, and service files are NOT processed
