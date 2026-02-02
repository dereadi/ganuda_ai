# Jr Instruction: Mount Evidence Checklist Endpoint + Fix Routing Gaps

**Date:** January 31, 2026
**Priority:** High
**Assigned To:** Software Engineer Jr.
**Council Vote:** 30c3f0f3c835aa2a

## Problem

Three routing issues discovered during integration testing:

1. `app/api/v1/endpoints/evidence_checklist.py` exists (96 lines, 4 endpoints) but is NOT imported in the router
2. `/api/v1/wizard/forms` GET is caught by wildcard route, returning a UUID parse error
3. Evidence analysis and export endpoints use integer `claim_id` while rest of app uses UUIDs

## Required Changes

### Step 1 (python): Mount evidence_checklist router in /ganuda/vetassist/backend/app/api/v1/__init__.py

Add import of evidence_checklist at line 7 and mount it with a prefix. Add after the existing evidence import:

At the top of the file, modify the import line:
```python
from app.api.v1.endpoints import calculator, health, content, chat, auth, evidence_analysis, workbench, wizard, readiness, family, export, dashboard, research, conditions, va_auth, claims, rag, documents, evidence, evidence_checklist
```

Then add a new router include block after the evidence router (after line 124):
```python
api_router.include_router(
    evidence_checklist.router,
    prefix="/evidence-checklist",
    tags=["evidence-checklist"]
)
```

### Step 2 (bash): Verify evidence checklist endpoints respond

```bash
curl -s http://192.168.132.223:8001/api/v1/evidence-checklist/evidence/categories
curl -s -X POST http://192.168.132.223:8001/api/v1/evidence-checklist/evidence/checklist \
  -H "Content-Type: application/json" \
  -d '{"conditions": ["PTSD"], "service_branch": "Army"}'
```

Note: Backend restart required after code change.

### Step 3 (python): Fix wizard forms routing in /ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py

Check the file for a wildcard route like `@router.get("/{session_id}")` and add a literal `/forms` route ABOVE it:

```python
@router.get("/forms")
async def list_wizard_forms():
    """List available wizard form types."""
    return {
        "forms": [
            {"id": "21-526EZ", "name": "Application for Disability Compensation", "type": "initial"},
            {"id": "21-0995", "name": "Decision Review Request: Supplemental Claim", "type": "supplemental"},
            {"id": "20-0996", "name": "Decision Review Request: Higher-Level Review", "type": "review"},
            {"id": "10182", "name": "Decision Review Request: Board Appeal", "type": "appeal"}
        ]
    }
```

This must be placed BEFORE any `/{session_id}` wildcard route in the same file.

## Verification

After backend restart:
```bash
# Evidence checklist categories
curl -s http://192.168.132.223:8001/api/v1/evidence-checklist/evidence/categories

# Wizard forms list
curl -s http://192.168.132.223:8001/api/v1/wizard/forms
```

Both should return JSON arrays, not errors.

## Context

- Router file: `/ganuda/vetassist/backend/app/api/v1/__init__.py`
- Evidence checklist: `/ganuda/vetassist/backend/app/api/v1/endpoints/evidence_checklist.py`
- Wizard: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`
- See KB: `KB-VETASSIST-TIER2-INTEGRATION-TESTING-JAN31-2026.md`

---
*Cherokee AI Federation — For Seven Generations*
