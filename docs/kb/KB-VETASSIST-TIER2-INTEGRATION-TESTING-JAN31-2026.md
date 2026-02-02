# KB: VetAssist Tier 2 Integration Testing Results

**Date:** January 31, 2026
**Council Vote:** 30c3f0f3c835aa2a (confidence 0.822, REVIEW REQUIRED: 3 concerns)
**Author:** TPM
**Status:** Testing complete, gaps identified

## Context

After Tier 1 deployment (verified Jan 31), codebase exploration revealed Tier 2 features were already ~92% implemented. Council recommended frontend-backend integration testing (option D). This KB documents the endpoint-by-endpoint test results.

## Discovery: Tier 2 Already Implemented

| Feature | Service Files | Lines | Status |
|---------|--------------|-------|--------|
| Evidence Gap Analysis | evidence_gap_analyzer.py, evidence_service.py | 596 | Functional |
| Medical NER | medical_document_processor.py, vlm_document_extractor.py | 568 | Functional |
| Diagnostic Code Lookup | conditions.py, calculator.py, rating_predictor.py | 611 | Functional |
| PDF Export/Form Fill | pdf_service.py, export.py | 300 | Partial |

## Endpoint Test Matrix

### Working Endpoints

| Endpoint | Method | Result | Key Data |
|----------|--------|--------|----------|
| `/api/v1/conditions/map` | POST | **PASS** | "PTSD from combat" → DC 9411, full rating criteria 0-100%, evidence requirements, DBQ form |
| `/api/v1/conditions/body-systems` | GET | **PASS** | 11 systems: Auditory, Cardiovascular, Digestive, Endocrine, Eye, Genitourinary, Mental Disorders, Musculoskeletal, Neurological, Respiratory, Skin |
| `/api/v1/evidence/checklist/{id}` | GET | **PASS** | Returns checklist structure (empty data, no claims in test) |
| `/api/v1/chat/sessions` | POST | **PASS** | Creates session (requires valid user_id FK) |
| `/api/v1/chat/message` | POST | **PASS** | Council chat + CFR RAG + crisis detection + PII redaction |
| `/api/v1/rag/regulations/search` | POST | **PASS** | BM25 CFR Part 4 search, 267 sections |
| `/api/v1/rag/sources` | GET | **PASS** | 4 source types listed |
| `/health` | GET | **PASS** | Service healthy |

### Partial/Broken Endpoints

| Endpoint | Method | Issue | Fix Required |
|----------|--------|-------|-------------|
| `/api/v1/calculator/calculate` | POST | Combined rating calculation works (70+10+30=80%), but `va_compensation_rates` table doesn't exist — fails when looking up dollar amounts | Create table + seed with VA 2025/2026 compensation rates |
| `/api/v1/conditions/9411` | GET | Returns empty for valid diagnostic code | Investigate — the /map endpoint finds it, but direct lookup fails |
| `/api/v1/sessions/{id}/evidence-gaps` | GET | Returns empty response | May need evidence data in DB or different session format |
| `/api/v1/evidence/analyze/{id}` | POST | `claim_id` expects integer, not UUID | Schema mismatch — rest of app uses UUIDs |
| `/api/v1/export/{id}/json` | GET | Same integer claim_id issue | Same schema mismatch |
| `/api/v1/dashboard/stats` | GET | Requires `Authorization` header | Expected — protected endpoint |
| `/api/v1/wizard/forms` | GET | "forms" interpreted as UUID session_id parameter | Routing conflict — wildcard route catches before literal route |
| `/api/v1/documents/` | GET | 404 Not Found | Documents router exists but root GET may not be defined |
| `/api/v1/research/` | GET | Empty response | Same as documents |

### Not Mounted in Router

| File | Feature | Notes |
|------|---------|-------|
| `evidence_checklist.py` | Personalized evidence checklists | File exists at 96 lines, endpoints defined, but NOT imported in `__init__.py` |

## Key Issues Found

### 1. Missing `va_compensation_rates` Table
The calculator correctly computes the VA combined bilateral rating formula (38 CFR 4.25) but then fails when querying for dollar compensation amounts.

**Impact:** Calculator returns error instead of monthly benefit estimates.
**Fix:** Create table and seed with current VA compensation rate schedule (available from VA website as flat data).

### 2. Integer vs UUID Schema Mismatch
`evidence_analysis.py` and `export.py` use integer `claim_id` parameters, while the rest of the app (chat, sessions, auth) uses UUIDs.

**Impact:** Frontend can't pass consistent identifiers across endpoints.
**Fix:** Align on UUID throughout, or add integer lookup aliases.

### 3. Wizard Forms Routing Conflict
`/api/v1/wizard/forms` gets caught by a wildcard route like `/wizard/{session_id}`, treating "forms" as a session UUID.

**Impact:** Frontend can't list available wizard forms.
**Fix:** Add literal route before wildcard, or use different prefix.

### 4. Evidence Checklist Not Mounted
`app/api/v1/endpoints/evidence_checklist.py` exists with 4 endpoints but is not imported in `app/api/v1/__init__.py`.

**Impact:** Evidence checklist feature inaccessible via API.
**Fix:** Add import and router registration in `__init__.py`.

## Council Concerns (30c3f0f3c835aa2a)

| Specialist | Concern | Implication |
|------------|---------|-------------|
| Raven (Strategy) | Which features maximize veteran impact first? | Calculator + evidence checklist = highest veteran value |
| Crawdad (Security) | Auth coverage on Tier 2 endpoints | Dashboard requires auth, but evidence/export endpoints don't — need auth review |
| Eagle Eye (Visibility) | Monitoring gaps in new features | Need logging/metrics for all Tier 2 endpoints |

## Recommended Priority (Next Jr Tasks)

1. **Create `va_compensation_rates` table** — unblocks calculator dollar estimates
2. **Mount evidence_checklist.py in router** — 1-line fix, unlocks 4 endpoints
3. **Fix wizard forms routing conflict** — critical for frontend wizard flow
4. **Align claim_id types** (integer → UUID) in evidence_analysis.py and export.py

---
*Cherokee AI Federation — For Seven Generations*
