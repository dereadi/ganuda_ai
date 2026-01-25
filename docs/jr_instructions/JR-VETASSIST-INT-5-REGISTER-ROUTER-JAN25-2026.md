# JR Instruction: VetAssist Integration Part 5 - Register Evidence Router

**Task ID:** VETASSIST-INT-ROUTER-001
**Priority:** P1
**Type:** backend
**Assigned:** Software Engineer Jr.

---

## Objective

Register the new evidence.py endpoints in the FastAPI router configuration.

---

## Deliverable

Modify this file:

File: `/ganuda/vetassist/backend/app/api/v1/__init__.py`

Add the evidence router import and registration.

### Step 1: Add import

Find this line:
```python
from app.api.v1.endpoints import calculator, health, content, chat, auth, evidence_analysis, workbench, wizard, readiness, family, export, dashboard, research, conditions, va_auth, claims, rag, documents
```

Change to:
```python
from app.api.v1.endpoints import calculator, health, content, chat, auth, evidence_analysis, workbench, wizard, readiness, family, export, dashboard, research, conditions, va_auth, claims, rag, documents, evidence
```

### Step 2: Add router registration

After this block:
```python
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)
```

Add:
```python

api_router.include_router(
    evidence.router,
    prefix="/sessions",
    tags=["evidence"]
)
```

---

## Success Criteria

- File modified at `/ganuda/vetassist/backend/app/api/v1/__init__.py`
- Import statement includes `evidence`
- Router registration added with prefix `/sessions`

---

## For Seven Generations

Proper API registration ensures veterans can access evidence gap analysis through the wizard.
