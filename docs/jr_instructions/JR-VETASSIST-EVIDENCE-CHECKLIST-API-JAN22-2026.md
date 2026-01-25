# JR Instruction: VetAssist Evidence Checklist API Endpoint

**Priority:** P2
**Assigned To:** Software Engineer Jr
**Date:** January 22, 2026

## Problem Statement

The `EvidenceService` in `/ganuda/vetassist/backend/app/services/evidence_service.py` can generate personalized evidence checklists based on conditions, but there's no API endpoint to expose this functionality directly.

Currently `/workbench/checklist/{claim_id}` requires an existing claim, but we need an endpoint that can generate a checklist from just a list of conditions for veterans exploring their options.

## Required Implementation

Add a new endpoint `/api/v1/evidence/checklist` that generates a personalized evidence checklist based on conditions.

## Implementation Steps

### Step 1: Create evidence API endpoint file

**File:** /ganuda/vetassist/backend/app/api/v1/endpoints/evidence_checklist.py

```python
"""
VetAssist Evidence Checklist API
Cherokee AI Federation - For Seven Generations
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.evidence_service import evidence_service

router = APIRouter(prefix="/evidence", tags=["evidence"])


class ChecklistRequest(BaseModel):
    conditions: List[str]
    session_id: Optional[str] = None


class EvidenceItem(BaseModel):
    id: str
    name: str
    description: str
    how_to_obtain: str
    required: bool
    condition_specific: Optional[str] = None


class EvidenceCategory(BaseModel):
    name: str
    description: str
    priority: int
    items: List[EvidenceItem]


class ChecklistResponse(BaseModel):
    session_id: str
    conditions: List[str]
    categories: Dict[str, EvidenceCategory]
    statistics: Dict[str, int]


@router.post("/checklist", response_model=ChecklistResponse)
def generate_checklist(request: ChecklistRequest):
    """
    Generate personalized evidence checklist based on claimed conditions.

    No authentication required - this helps veterans understand
    what evidence they'll need before starting a claim.
    """
    if not request.conditions:
        raise HTTPException(status_code=400, detail="At least one condition required")

    # Generate session ID if not provided
    import uuid
    session_id = request.session_id or str(uuid.uuid4())[:8]

    checklist = evidence_service.generate_checklist(session_id, request.conditions)

    return ChecklistResponse(
        session_id=checklist["session_id"],
        conditions=checklist["conditions"],
        categories=checklist["categories"],
        statistics=checklist["statistics"]
    )


@router.post("/checklist/save/{session_id}")
def save_checklist(session_id: str, request: ChecklistRequest):
    """Save a generated checklist to the database for later use."""
    checklist = evidence_service.generate_checklist(session_id, request.conditions)
    checklist_id = evidence_service.save_checklist(session_id, checklist)
    return {"checklist_id": checklist_id, "session_id": session_id}


@router.patch("/checklist/{session_id}/item/{item_id}")
def update_item_status(session_id: str, item_id: str, completed: bool = True):
    """Update completion status for a checklist item."""
    success = evidence_service.update_completion(session_id, item_id, completed)
    if not success:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return {"success": True, "item_id": item_id, "completed": completed}


@router.get("/categories")
def get_evidence_categories():
    """Get all evidence categories and their descriptions."""
    from app.services.evidence_service import EVIDENCE_CATEGORIES
    return {
        cat_id: {
            "name": cat["name"],
            "description": cat["description"],
            "priority": cat["priority"],
            "item_count": len(cat["items"])
        }
        for cat_id, cat in EVIDENCE_CATEGORIES.items()
    }
```

### Step 2: Register the router

Edit `/ganuda/vetassist/backend/app/api/v1/routers.py` - add import and include:

After line 5 (`from .endpoints import workbench, wizard, readiness, family, export`), add:
```python
from .endpoints import evidence_checklist
```

After line 7 (after the router definition), add:
```python
router.include_router(evidence_checklist.router)
```

### Step 3: Add __init__.py entry if needed

Check if `/ganuda/vetassist/backend/app/api/v1/endpoints/__init__.py` needs updating.
Add `evidence_checklist` to the exports if using explicit exports.

## Test Cases

After implementation:

```bash
# Generate checklist for PTSD and knee pain
curl -X POST "http://localhost:8001/api/v1/evidence/checklist" \
  -H "Content-Type: application/json" \
  -d '{"conditions": ["PTSD", "knee pain"]}'

# Get all evidence categories
curl "http://localhost:8001/api/v1/evidence/categories"

# Save a checklist
curl -X POST "http://localhost:8001/api/v1/evidence/checklist/save/my-session" \
  -H "Content-Type: application/json" \
  -d '{"conditions": ["tinnitus", "back pain"]}'
```

## Expected Response

```json
{
  "session_id": "abc123",
  "conditions": ["PTSD", "knee pain"],
  "categories": {
    "service_connection": {
      "name": "Service Connection Evidence",
      "priority": 1,
      "items": [
        {"id": "dd214", "name": "DD-214", "required": true, ...},
        {"id": "stressor_statement", "name": "Stressor Statement", "required": true, "condition_specific": "PTSD"}
      ]
    }
  },
  "statistics": {
    "total_items": 15,
    "required_items": 8,
    "optional_items": 7
  }
}
```

## Completion Criteria

1. `/api/v1/evidence/checklist` returns checklist for given conditions
2. `/api/v1/evidence/categories` lists all categories
3. Condition-specific items (PTSD stressor, etc.) are included
4. Statistics are calculated correctly
