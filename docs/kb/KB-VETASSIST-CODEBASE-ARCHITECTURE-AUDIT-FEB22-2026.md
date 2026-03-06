# KB: VetAssist Codebase Architecture — Current State (Feb 22 Audit)

**Date:** 2026-02-22
**Author:** TPM
**Purpose:** Prevent stale SEARCH strings by documenting actual code patterns
**Related:** KB-VETASSIST-WIZARD-IMPLEMENTATION, KB-VETASSIST-SPLIT-DATABASE-ARCHITECTURE

---

## Backend Architecture

### Two Parallel API Systems (IMPORTANT)

VetAssist backend has TWO API systems running simultaneously:

1. **routers.py** (`/ganuda/vetassist/backend/app/api/v1/routers.py`)
   - FastAPI + SQLAlchemy + Pydantic models
   - Uses `Session = Depends(get_db)` dependency injection
   - Handles: workbench, readiness, family, export, evidence_checklist
   - BUG: Line 8 calls `router.include_router()` BEFORE line 9 defines `router`

2. **wizard.py** (`/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`)
   - FastAPI + raw psycopg2 (NOT SQLAlchemy)
   - Uses `get_db_conn()` → `psycopg2.connect(**get_db_config())`
   - Handles: wizard sessions, step submission, document processing
   - Has its own `router = APIRouter(prefix="/wizard")`

**When writing SEARCH strings for wizard.py:** Use psycopg2 patterns (cursor, execute, fetchone).
**When writing SEARCH strings for routers.py:** Use SQLAlchemy patterns (Session, Depends).

### Key Backend Patterns

```python
# wizard.py connection pattern:
conn = get_db_conn()
with conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute("...", (params,))
    row = cur.fetchone()
    conn.commit()
conn.close()

# routers.py connection pattern:
def endpoint(db: Session = Depends(get_db)):
    return Service.method(db, data)
```

### Backend File Map

| File | Pattern | Purpose |
|---|---|---|
| wizard.py | psycopg2, 700+ lines | Wizard sessions, steps, document processing |
| auth.py | FastAPI, SQLAlchemy | Registration, login, token refresh |
| routers.py | FastAPI, SQLAlchemy | Workbench, readiness, export |
| evidence_service.py | Pure Python dicts | Evidence checklist categories (EVIDENCE_CATEGORIES dict) |
| pii_service.py | Presidio wrapper | PII detection + redaction (singleton: `pii_service`) |
| ocr_service.py | pytesseract + vLLM | OCR extraction with LLM structured data |
| pdf_service.py | reportlab + PyPDF2 | PDF form filling (FIELD_MAPPINGS dict) |

### Document Processing Pipeline (wizard.py)

```
Upload → Classify (vLLM) → OCR (tesseract) → Extract (vLLM) → Store (psycopg2)
```

The pipeline is in `_process_single_document()` (~lines 300-400). Key insertion point for PII redaction is between Extract and Store (Step 5 comment marker).

---

## Frontend Architecture

### Framework
- Next.js 14 App Router
- TypeScript
- Tailwind CSS
- react-hook-form + zod (calculator)
- axios (chat) + fetch (wizard)

### Key Frontend Patterns

| Page | State Mgmt | API Pattern | Key Feature |
|---|---|---|---|
| layout.tsx | AuthProvider context | — | Wraps all pages |
| wizard/page.tsx | useState | fetch | Form type selection, session creation |
| wizard/[sessionId]/page.tsx | useState, useRef, useCallback | fetch | Step rendering, auto-save (partial) |
| chat/page.tsx | useState, useRef | axios | Chat sessions, message history |
| calculator/page.tsx | react-hook-form + zod | axios | Combined rating calculator |

### Wizard Step Architecture

The wizard renders steps inline via `renderStepContent()` switch/case (NOT delegated to component imports, despite importing them). The imported step components (ConditionsStep, EvidenceStep, ReviewStep) are used for specific wizard types:

```
21-526EZ: case 1-2 inline, case 3 ConditionsStep, case 4 EvidenceStep, case 5 ReviewStep
21-0995: SupplementalClaimStep
20-0996: HigherLevelReviewStep
10182: BoardAppealStep
```

### Registration Page

`/ganuda/vetassist/frontend/app/(auth)/register/page.tsx`:
- Uses `register()` from auth-context (NOT raw fetch + JSON.stringify)
- Fields: `formData.email, .password, .first_name, .last_name, .veteran_status`
- Has `validationErrors` state and `passwordStrength` state (NOT `error`/`loading`)

---

## Database Architecture

### Split Database (KB-VETASSIST-SPLIT-DATABASE-ARCHITECTURE)

| Database | Host | Used By |
|---|---|---|
| triad_federation | bluefin:5432 | Auth, users, chat (via .env DATABASE_URL) |
| zammad_production | bluefin:5432 | Wizard, thermal memory, CMDB, feedback |

### Key Tables in zammad_production

| Table | Used By |
|---|---|
| vetassist_wizard_sessions | wizard.py |
| vetassist_documents | wizard.py (document processing) |
| vetassist_feedback | feedback.py (NEW, created Feb 22) |
| thermal_memory_archive | Everything |
| federation_calendar | ritual_review.py (NEW, created Feb 22) |

---

## Common Mistakes When Writing Instructions

1. **Don't assume function names** — Read the actual file first. Example: `get_cameras()` doesn't exist, it's `camera_status()`.
2. **Don't assume import patterns** — wizard.py uses `from app.services.va_api_service import va_api_service`, NOT `from app.services.ocr_service import OCRService`.
3. **Don't assume state variables** — The register page uses `validationErrors`, not `error` + `loading`.
4. **Don't mix Create + SEARCH/REPLACE** — Executor bug, only first Create executes. Split into separate instructions.
5. **evidence_service.py is a dict, not code with comments** — EVIDENCE_CATEGORIES is a nested dictionary. Insert new categories as dict keys, not comment blocks.
6. **pii_service.py already exists** — Use it, don't create a new one. Import: `from app.services.pii_service import pii_service`.
