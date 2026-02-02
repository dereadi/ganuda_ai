# JR-VETASSIST-FIX-CLAIM-ID-TYPES-JAN30-2026

## Metadata
- **Priority:** P0 (Security — Crawdad flagged IDOR risk)
- **Jr Type:** Backend / Python
- **Target Node:** bluefin (192.168.132.222)
- **Depends On:** None
- **Blocks:** Tier 2 production readiness
- **Council Vote:** ULTRATHINK-VETASSIST-P0-SPRINT-AND-VA-LINKING-JAN30-2026 (7/7 approve)

## Problem

Four backend files use `claim_id: int` as path/query parameters. The rest of the codebase uses `str` or `uuid.UUID` for IDs. Integer IDs are sequentially guessable, creating an **Insecure Direct Object Reference (IDOR)** vulnerability — an attacker who knows one claim ID can enumerate others.

**Codebase standard:**
- `claims.py` and `va_claims_service.py` use `claim_id: str`
- Database models use `PortableUUID()` for primary keys
- Chat endpoints use `uuid.UUID`

**Affected files (19 functions total):**

| File | Functions Affected |
|------|-------------------|
| `app/api/v1/endpoints/evidence_analysis.py` | 2 |
| `app/api/v1/endpoints/export.py` | 5 |
| `app/api/v1/endpoints/workbench.py` | 7 |
| `app/api/v1/routers.py` | 5 |

## Fix

Change all `claim_id: int` parameters to `claim_id: str` to match the pattern in `claims.py` and `va_claims_service.py`. Using `str` (not `uuid.UUID`) because VA claim IDs from the external VA API may not be standard UUIDs.

### File 1: evidence_analysis.py

**Path:** `/ganuda/vetassist/backend/app/api/v1/endpoints/evidence_analysis.py`

Find and replace ALL occurrences of `claim_id: int` with `claim_id: str`.

Specifically:

```python
# BEFORE (line ~22):
class EvidenceAnalysisRequest(BaseModel):
    claim_id: int

# AFTER:
class EvidenceAnalysisRequest(BaseModel):
    claim_id: str
```

```python
# BEFORE (line ~28):
def analyze_evidence(claim_id: int, request: EvidenceAnalysisRequest):

# AFTER:
def analyze_evidence(claim_id: str, request: EvidenceAnalysisRequest):
```

```python
# BEFORE (line ~91):
def get_evidence_checklist(claim_id: int):

# AFTER:
def get_evidence_checklist(claim_id: str):
```

### File 2: export.py

**Path:** `/ganuda/vetassist/backend/app/api/v1/endpoints/export.py`

Find and replace ALL occurrences of `claim_id: int` with `claim_id: str`.

5 functions to change:
```python
# BEFORE:
def export_claim_json(claim_id: int):
def export_checklist(claim_id: int):
def export_timeline(claim_id: int):
def export_pdf(claim_id: int):
def export_va_xml(claim_id: int):

# AFTER:
def export_claim_json(claim_id: str):
def export_checklist(claim_id: str):
def export_timeline(claim_id: str):
def export_pdf(claim_id: str):
def export_va_xml(claim_id: str):
```

### File 3: workbench.py

**Path:** `/ganuda/vetassist/backend/app/api/v1/endpoints/workbench.py`

Find and replace ALL occurrences of `claim_id: int` with `claim_id: str`.

7 functions to change:
```python
# BEFORE:
def get_claim(claim_id: int):
def update_claim(claim_id: int, claim: ClaimUpdate):
def get_checklist(claim_id: int):
def add_checklist_item(claim_id: int, item: ChecklistItemCreate):
def update_checklist_item(claim_id: int, item_id: int, item: ChecklistItemUpdate):
def get_timeline(claim_id: int):
def add_timeline_event(claim_id: int, event: TimelineEventCreate):

# AFTER:
def get_claim(claim_id: str):
def update_claim(claim_id: str, claim: ClaimUpdate):
def get_checklist(claim_id: str):
def add_checklist_item(claim_id: str, item: ChecklistItemCreate):
def update_checklist_item(claim_id: str, item_id: str, item: ChecklistItemUpdate):
def get_timeline(claim_id: str):
def add_timeline_event(claim_id: str, event: TimelineEventCreate):
```

**NOTE:** Also change `item_id: int` to `item_id: str` in `update_checklist_item` if checklist items use UUID keys.

### File 4: routers.py

**Path:** `/ganuda/vetassist/backend/app/api/v1/routers.py`

Find and replace ALL occurrences of `claim_id: int` with `claim_id: str`.

5 functions to change:
```python
# BEFORE:
def update_claim(claim_id: int, ...):
def read_checklist(claim_id: int, ...):
def read_timeline(claim_id: int, ...):
def assess_readiness(claim_id: int, ...):
def export_document(claim_id: int, ...):

# AFTER:
def update_claim(claim_id: str, ...):
def read_checklist(claim_id: str, ...):
def read_timeline(claim_id: str, ...):
def assess_readiness(claim_id: str, ...):
def export_document(claim_id: str, ...):
```

## Implementation

The simplest approach — this is a find-and-replace across 4 files:

```bash
cd /ganuda/vetassist/backend

# evidence_analysis.py
sed -i 's/claim_id: int/claim_id: str/g' app/api/v1/endpoints/evidence_analysis.py

# export.py
sed -i 's/claim_id: int/claim_id: str/g' app/api/v1/endpoints/export.py

# workbench.py
sed -i 's/claim_id: int/claim_id: str/g' app/api/v1/endpoints/workbench.py

# routers.py
sed -i 's/claim_id: int/claim_id: str/g' app/api/v1/routers.py
```

Also fix `item_id` if applicable:
```bash
sed -i 's/item_id: int/item_id: str/g' app/api/v1/endpoints/workbench.py
```

## Verification

```bash
# 1. Confirm no remaining int claim_id parameters
grep -rn "claim_id: int" /ganuda/vetassist/backend/app/
# Expected: no output

# 2. Confirm the changes were applied
grep -rn "claim_id: str" /ganuda/vetassist/backend/app/ | head -20
# Expected: 19+ matches across the 4 files

# 3. Verify Python syntax is valid
cd /ganuda/vetassist/backend
python -c "from app.api.v1.endpoints import evidence_analysis, export, workbench"
# Expected: no ImportError

# 4. Verify FastAPI can build the routes
python -c "
from app.api.v1.endpoints.evidence_analysis import router as ea
from app.api.v1.endpoints.export import router as ex
from app.api.v1.endpoints.workbench import router as wb
print(f'evidence_analysis routes: {len(ea.routes)}')
print(f'export routes: {len(ex.routes)}')
print(f'workbench routes: {len(wb.routes)}')
"
# Expected: route counts printed without error
```

## Security Notes (Crawdad Review)

- **IDOR Remediation:** Integer path parameters allowed sequential enumeration. String parameters accept UUIDs, which are not guessable (2^122 entropy).
- **No authorization bypass:** This fix changes type validation only. Endpoint-level authorization (`get_current_user` dependency) must still be verified separately.
- **Backward compatibility:** Any frontend code sending integer claim IDs will still work — `str` accepts any path segment. But the type annotation now correctly signals that claim IDs are opaque strings, not enumerable integers.
