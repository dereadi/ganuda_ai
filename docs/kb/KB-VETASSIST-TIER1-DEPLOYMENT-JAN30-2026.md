# KB: VetAssist Tier 1 AI Enhancement Deployment

**Date:** January 30, 2026
**Council Vote:** 23589699dd7b4a97 (confidence 0.873, PROCEED WITH CAUTION)
**Author:** TPM
**Status:** Deployed, partially verified

## What Was Deployed

Four Tier 1 AI enhancements to the VetAssist backend (`/ganuda/vetassist/backend/`):

### 1. 38 CFR RAG with BM25 Retriever
- **Files:** `app/services/cfr_parser.py`, `app/services/cfr_retriever.py`, `app/api/v1/endpoints/rag.py` (modified), `app/services/council_chat.py` (modified)
- **Data:** `app/data/cfr_part4_sections.json` (267 sections from eCFR)
- **Endpoint:** `POST /api/v1/rag/regulations/search`
- **Status:** Working. BM25 text search returns relevant sections in <1ms.

### 2. C-SSRS Crisis Classifier (Three-Tier)
- **Files:** `app/services/crisis_classifier.py`
- **Database:** `crisis_detections` table on triad_federation
- **Tiers:** Lexicon screen (0ms) → LLM via local gateway (974ms) → Intervention routing
- **Status:** Working. Module-level tests pass. Backend needs restart to load corrected version.

### 3. Medical Record OCR with docling
- **Files:** `app/services/document_processor.py` (modified)
- **Dependencies:** docling (IBM, MIT license), torch 2.10.0, pydantic 2.12.5
- **Status:** Installed. Not end-to-end tested (pre-existing import bug in document_processor.py blocks it).

### 4. VA Form Auto-Fill with PyPDFForm
- **Files:** `app/services/va_form_filler.py`
- **Dependencies:** PyPDFForm (MIT license)
- **Status:** Module created. `get_supported_forms()` returns `['21-526EZ']`. No form templates downloaded yet.

## Lessons Learned

### 1. Jr File Modification Corrupts Files
**Problem:** Jr task 468 modified `council_chat.py` and injected ` ```python ` markdown fencing at line 1 and truncated the file at line 249 (lost `get_specialist_badge_color()` ending and `ask_va_question()` function).
**Root cause:** Jr's code generation wraps output in markdown code blocks. The file-write guardrail catches >50% content reduction but not fencing injection or minor truncation.
**Fix:** Always verify Jr-modified files for:
- Markdown fencing at line 1 or end of file
- File truncation (compare line count before/after)
- Missing closing functions
**Recommendation:** Add post-write validation to Jr executor that strips markdown fencing and compares function count.

### 2. Jr Step Extraction Fails on Plain-Text Instructions
**Problem:** Tasks 469, 471, 474, 475 all failed with "No executable steps found."
**Root cause:** Jr's SmartExtract regex requires `Step N (type):` format. Plain-text instructions and SQL DDL/bash tasks don't match.
**Fix:** Infrastructure operations (SQL DDL, pip install) should be executed directly by TPM, not queued to Jr work queue.
**Recommendation:** Add `type: infrastructure` to Jr work queue that bypasses step extraction and runs directly.

### 3. Jr Created File Instead of Directory
**Problem:** Jr task 464 created `/ganuda/vetassist/backend/app/data` as a Python file instead of a directory. Later, `cfr_parser.py` failed with `FileExistsError` when trying `os.makedirs('data')`.
**Fix:** Renamed file to `data_old_file` and created directory.
**Recommendation:** Jr instructions for "create directory" need explicit `mkdir -p` step, not file creation.

### 4. eCFR API Renderer Returns 404
**Problem:** The documented eCFR API endpoint (`/api/renderer/v1/content/enhanced/...`) returns 404 for Part 4.
**Fix:** Use direct HTML page URL with browser User-Agent headers:
```
URL: https://www.ecfr.gov/current/title-38/chapter-I/part-4/subpart-B
Headers: User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36
```
Returns 868KB HTML, parses to 267 sections.

### 5. Diagnostic Code Extraction is Incomplete
**Problem:** Only 67/267 CFR sections have diagnostic codes parsed. The regex `\b(\d{4})\b` only catches standalone 4-digit numbers 5000-9999 in cleaned text. Many codes are in HTML tables/attributes stripped during cleaning.
**Status:** Open. Needs Jr instruction to improve parser.

### 6. crisis_classifier.py Required Complete Rewrite
**Problem:** Jr's implementation deviated significantly from specification — used SQLAlchemy ORM, imported non-existent models, wrong API format, no proper C-SSRS scale.
**Fix:** TPM rewrote entire file (272 lines) with correct psycopg2-based implementation.
**Lesson:** Complex safety-critical modules should NOT be delegated to Jr. The C-SSRS crisis classifier touches clinical scales, intervention routing, and never-store-content requirements — too nuanced for Jr step extraction.

### 7. docling Installation Upgrades Core Dependencies
**Problem:** `pip install docling` upgraded pydantic 2.1→2.12.5 and torch 2.9.1→2.10.0.
**Verification:** FastAPI + pydantic + pydantic-settings all import correctly post-upgrade.
**Lesson:** Always check dependency version changes after installing large packages. Pin versions in requirements.txt.

### 8. Chat Session Creation Fails — FK Constraint, Not Missing Tables
**Problem:** `POST /api/v1/chat/sessions` returns 500 internal server error.
**Root cause:** The `chat_sessions.user_id` column has a FK to `users.id`. Test UUID `00000000-0000-0000-0000-000000000001` does not exist in the users table. Tables `chat_sessions`, `chat_messages`, `council_validations`, `users` all exist.
**Fix:** Use a valid user_id from the `users` table (e.g., `aa549d11-e4f5-4022-9b62-8c127b6a6213`).
**Verified:** Full end-to-end Council chat works — PTSD query returns Raven specialist citing 38 CFR 4.130 DC 9411. Crisis detection triggers correctly (ML model, `crisis_detected: true`). PII redaction active (PTSD → `<REDACTED>` in stored message).

## Open Issues

| # | Issue | Severity | Jr Instruction | Status |
|---|-------|----------|----------------|--------|
| 1 | Diagnostic code parser needs improvement | Medium | Task #477 queued | Jr queued |
| 2 | ~~Chat DB tables need migration~~ | ~~High~~ | N/A — FK constraint, tables exist | **RESOLVED** |
| 3 | ~~Backend restart for crisis_classifier.py~~ | ~~Low~~ | Manual | **RESOLVED** |
| 4 | Wire C-SSRS into chat.py | Medium | Task #478 queued | Jr queued |
| 5 | document_processor.py import bug (`extract_medical_eras`) | Low | Pre-existing | Open |
| 6 | VA form templates not downloaded | Medium | Needs Jr instruction | Open |

## End-to-End Verification (Jan 31 2026)

| Test | Result | Details |
|------|--------|---------|
| Council Chat + CFR RAG | **PASS** | Specialist: Raven, cites 38 CFR 4.130 DC 9411, ~9.6s |
| Crisis Detection in Chat | **PASS** | `crisis_detected: true`, `ml_detected`, 988 shown, 40ms |
| PII Redaction | **PASS** | "PTSD" → `<REDACTED>` in stored user message |
| CFR BM25 Search | **PASS** | §4.87, §4.130 for tinnitus query |
| VA Form Filler | **PASS** | `get_supported_forms()` → `['21-526EZ']` |

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `app/services/cfr_parser.py` | Created (Jr) + fixed URL (TPM) | 118 |
| `app/services/cfr_retriever.py` | Created (Jr) | 141 |
| `app/services/crisis_classifier.py` | Created (Jr) + rewritten (TPM) | 272 |
| `app/services/va_form_filler.py` | Created (Jr) | 72 |
| `app/services/document_processor.py` | Modified (Jr) | 198 |
| `app/services/council_chat.py` | Modified (Jr) + fixed corruption (TPM) | 265 |
| `app/api/v1/endpoints/rag.py` | Modified (Jr) | 186 |
| `app/data/cfr_part4_sections.json` | Generated by parser | 267 sections |
| DB: `crisis_detections` table | Created (TPM) | — |

---
*Cherokee AI Federation — For Seven Generations*
