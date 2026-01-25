# JR Instruction: VetAssist Claim Workbench & Form Wizards

## Metadata
```yaml
task_id: vetassist_claim_workbench
priority: 1
assigned_to: IT Triad Jr
target: /ganuda/vetassist
estimated_effort: high
use_rlm: true
sacred_fire_priority: true
dependencies:
  - VetAssist backend running (COMPLETE)
  - VetAssist auth system (COMPLETE)
  - PII protection via Presidio (COMPLETE)
  - goldfin PII vault access (COMPLETE)
```

## Overview

Build a comprehensive **Claim Workbench** that gives veterans a personal workspace to:
1. Organize their disability claim projects
2. Store and categorize supporting documents
3. Track evidence checklists per condition
4. Take notes and track progress
5. Use guided Form Wizards to understand the claims process

**This is NOT filing claims for them** - it's an educational tool to help them prepare and organize.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     VetAssist Claim Workbench                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Claims    │  │  Documents  │  │    Form Wizards         │ │
│  │  Projects   │  │   Storage   │  │                         │ │
│  │             │  │             │  │  • Intent to File (ITF) │ │
│  │  • Active   │  │  • Upload   │  │  • New Claim Prep       │ │
│  │  • Draft    │  │  • Organize │  │  • Rating Increase      │ │
│  │  • Archived │  │  • Tag      │  │  • Secondary Conditions │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Evidence Checklist                        ││
│  │  ☐ Service Treatment Records (STRs)                         ││
│  │  ☐ VA Medical Records                                        ││
│  │  ☐ Private Medical Records                                   ││
│  │  ☐ Buddy Statements                                          ││
│  │  ☐ Nexus Letter                                              ││
│  │  ☐ DBQ (Disability Benefits Questionnaire)                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                       Notes & Timeline                       ││
│  │  [Scratch pad for each claim project]                       ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

Create on **bluefin** (zammad_production):

```sql
-- Claim Projects (scratch area for organizing a claim)
CREATE TABLE IF NOT EXISTS vetassist_claim_projects (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES vetassist_users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft',  -- draft, active, submitted, archived
    claim_type VARCHAR(50),  -- new_claim, increase, secondary, appeal
    target_conditions JSONB DEFAULT '[]',  -- list of conditions being claimed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Evidence Checklist Items
CREATE TABLE IF NOT EXISTS vetassist_evidence_checklist (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES vetassist_claim_projects(id) ON DELETE CASCADE,
    condition_name VARCHAR(255),  -- e.g., "PTSD", "Tinnitus"
    evidence_type VARCHAR(100) NOT NULL,  -- str, va_records, private_records, buddy_statement, nexus, dbq
    description TEXT,
    is_completed BOOLEAN DEFAULT FALSE,
    document_id INTEGER,  -- link to uploaded document
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Document Metadata (actual files on goldfin)
CREATE TABLE IF NOT EXISTS vetassist_documents (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES vetassist_users(id),
    project_id INTEGER REFERENCES vetassist_claim_projects(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_type VARCHAR(50),  -- pdf, jpg, png, doc
    file_size INTEGER,
    storage_path VARCHAR(512),  -- path on goldfin: /vetassist/documents/{user_id}/{uuid}
    category VARCHAR(100),  -- medical, military, personal, legal
    tags JSONB DEFAULT '[]',
    description TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    is_sensitive BOOLEAN DEFAULT TRUE  -- PII flag
);

-- Notes / Scratch Pad
CREATE TABLE IF NOT EXISTS vetassist_notes (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES vetassist_users(id),
    project_id INTEGER REFERENCES vetassist_claim_projects(id) ON DELETE CASCADE,
    title VARCHAR(255),
    content TEXT NOT NULL,
    note_type VARCHAR(50) DEFAULT 'general',  -- general, timeline, evidence, reminder
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Form Wizard Progress
CREATE TABLE IF NOT EXISTS vetassist_wizard_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES vetassist_users(id),
    wizard_type VARCHAR(50) NOT NULL,  -- itf, new_claim, increase, secondary
    current_step INTEGER DEFAULT 1,
    total_steps INTEGER,
    answers JSONB DEFAULT '{}',  -- wizard responses
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, wizard_type)
);

-- Indexes
CREATE INDEX idx_claim_projects_user ON vetassist_claim_projects(user_id);
CREATE INDEX idx_documents_user ON vetassist_documents(user_id);
CREATE INDEX idx_documents_project ON vetassist_documents(project_id);
CREATE INDEX idx_notes_project ON vetassist_notes(project_id);
CREATE INDEX idx_checklist_project ON vetassist_evidence_checklist(project_id);
```

## Backend API Endpoints

Add to `/ganuda/vetassist/backend/app/api/v1/endpoints/`:

### `workbench.py`

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import os

router = APIRouter(prefix="/workbench", tags=["workbench"])

# --- Models ---

class ClaimProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    claim_type: str  # new_claim, increase, secondary, appeal
    target_conditions: List[str] = []

class ClaimProjectResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    claim_type: str
    target_conditions: List[str]
    created_at: datetime

class EvidenceItemCreate(BaseModel):
    condition_name: str
    evidence_type: str
    description: Optional[str] = None

class NoteCreate(BaseModel):
    title: Optional[str] = None
    content: str
    note_type: str = "general"

# --- Endpoints ---

@router.get("/projects")
async def list_projects(user_id: str = Depends(get_current_user)):
    """List all claim projects for the current user."""
    # Implementation: SELECT * FROM vetassist_claim_projects WHERE user_id = ?
    pass

@router.post("/projects")
async def create_project(project: ClaimProjectCreate, user_id: str = Depends(get_current_user)):
    """Create a new claim project (scratch area)."""
    pass

@router.get("/projects/{project_id}")
async def get_project(project_id: int, user_id: str = Depends(get_current_user)):
    """Get project details with checklist and notes."""
    pass

@router.put("/projects/{project_id}")
async def update_project(project_id: int, project: ClaimProjectCreate):
    """Update project details."""
    pass

@router.delete("/projects/{project_id}")
async def archive_project(project_id: int):
    """Archive (soft delete) a project."""
    pass

# --- Evidence Checklist ---

@router.get("/projects/{project_id}/checklist")
async def get_checklist(project_id: int):
    """Get evidence checklist for a project."""
    pass

@router.post("/projects/{project_id}/checklist")
async def add_checklist_item(project_id: int, item: EvidenceItemCreate):
    """Add item to evidence checklist."""
    pass

@router.put("/checklist/{item_id}/complete")
async def toggle_checklist_item(item_id: int, completed: bool):
    """Mark checklist item as complete/incomplete."""
    pass

# --- Documents ---

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    project_id: Optional[int] = None,
    category: str = "general",
    user_id: str = Depends(get_current_user)
):
    """
    Upload document to goldfin storage.

    Files are stored at: /vetassist/documents/{user_id}/{uuid}.{ext}
    Only metadata stored in bluefin database.
    """
    # 1. Generate secure filename
    file_uuid = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    secure_filename = f"{file_uuid}{ext}"

    # 2. Store on goldfin (via NFS or API)
    storage_path = f"/vetassist/documents/{user_id}/{secure_filename}"

    # 3. Save metadata to database
    pass

@router.get("/documents")
async def list_documents(
    project_id: Optional[int] = None,
    category: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """List user's documents, optionally filtered."""
    pass

@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: int, user_id: str = Depends(get_current_user)):
    """Download a document from goldfin."""
    pass

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int):
    """Delete document from goldfin and database."""
    pass

# --- Notes ---

@router.get("/projects/{project_id}/notes")
async def list_notes(project_id: int):
    """Get all notes for a project."""
    pass

@router.post("/projects/{project_id}/notes")
async def create_note(project_id: int, note: NoteCreate):
    """Add a note to a project."""
    pass

@router.put("/notes/{note_id}")
async def update_note(note_id: int, note: NoteCreate):
    """Update a note."""
    pass

@router.delete("/notes/{note_id}")
async def delete_note(note_id: int):
    """Delete a note."""
    pass
```

### `wizards.py`

```python
from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from pydantic import BaseModel

router = APIRouter(prefix="/wizards", tags=["wizards"])

# --- Form Wizard Definitions ---

WIZARDS = {
    "itf": {
        "name": "Intent to File (ITF)",
        "description": "Protect your effective date while gathering evidence",
        "steps": [
            {
                "id": 1,
                "title": "What is an Intent to File?",
                "content": "An ITF establishes an effective date for your claim...",
                "type": "education"
            },
            {
                "id": 2,
                "title": "When Should You File an ITF?",
                "content": "File an ITF when you...",
                "type": "education",
                "checklist": [
                    "You have a condition you believe is service-connected",
                    "You need time to gather evidence",
                    "You want to protect your effective date"
                ]
            },
            {
                "id": 3,
                "title": "How to File an ITF",
                "content": "You can file through eBenefits, VA.gov, or by calling...",
                "type": "action_guide",
                "links": [
                    {"text": "VA.gov ITF Page", "url": "https://www.va.gov/claim-or-appeal-status/"}
                ]
            },
            {
                "id": 4,
                "title": "After Filing",
                "content": "You have 1 year from your ITF date to file your claim...",
                "type": "education"
            }
        ]
    },
    "new_claim": {
        "name": "New Disability Claim",
        "description": "Step-by-step guide to preparing your first claim",
        "steps": [
            {
                "id": 1,
                "title": "Identify Your Conditions",
                "content": "List all conditions you believe are service-connected...",
                "type": "interactive",
                "input": "condition_list"
            },
            {
                "id": 2,
                "title": "Gather Service Treatment Records",
                "content": "Your STRs are critical evidence...",
                "type": "checklist",
                "items": [
                    "Request STRs from National Personnel Records Center",
                    "Check for in-service treatment of your conditions",
                    "Note dates and descriptions of treatments"
                ]
            },
            {
                "id": 3,
                "title": "Obtain Medical Evidence",
                "content": "Current medical records showing diagnosis and severity...",
                "type": "checklist",
                "items": [
                    "VA medical records (request via MyHealtheVet)",
                    "Private medical records",
                    "Specialist evaluations"
                ]
            },
            {
                "id": 4,
                "title": "Consider a Nexus Letter",
                "content": "A nexus letter connects your current condition to service...",
                "type": "education"
            },
            {
                "id": 5,
                "title": "Buddy Statements",
                "content": "Statements from fellow service members or family...",
                "type": "education",
                "template": "buddy_statement_template"
            },
            {
                "id": 6,
                "title": "Review & Prepare",
                "content": "Before filing, ensure you have...",
                "type": "final_checklist"
            }
        ]
    },
    "increase": {
        "name": "Rating Increase Request",
        "description": "How to request an increase for a service-connected condition",
        "steps": [
            # ... similar structure
        ]
    },
    "secondary": {
        "name": "Secondary Condition Claim",
        "description": "Claim conditions caused by your service-connected disabilities",
        "steps": [
            # ... similar structure
        ]
    }
}

class WizardProgress(BaseModel):
    current_step: int
    answers: Dict[str, Any] = {}

@router.get("/")
async def list_wizards():
    """List all available form wizards."""
    return [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in WIZARDS.items()
    ]

@router.get("/{wizard_type}")
async def get_wizard(wizard_type: str):
    """Get full wizard definition."""
    if wizard_type not in WIZARDS:
        raise HTTPException(404, "Wizard not found")
    return WIZARDS[wizard_type]

@router.get("/{wizard_type}/progress")
async def get_progress(wizard_type: str, user_id: str = Depends(get_current_user)):
    """Get user's progress in a wizard."""
    pass

@router.post("/{wizard_type}/progress")
async def save_progress(wizard_type: str, progress: WizardProgress, user_id: str = Depends(get_current_user)):
    """Save user's progress in a wizard."""
    pass

@router.post("/{wizard_type}/complete")
async def complete_wizard(wizard_type: str, user_id: str = Depends(get_current_user)):
    """Mark wizard as completed."""
    pass
```

## Frontend Pages

Create in `/ganuda/vetassist/frontend/app/`:

### `/workbench/page.tsx` - Main Workbench Dashboard

```tsx
// Claim projects list, quick actions, recent documents
```

### `/workbench/projects/[id]/page.tsx` - Project Detail

```tsx
// Project overview, evidence checklist, notes, documents
```

### `/workbench/documents/page.tsx` - Document Manager

```tsx
// Upload, organize, tag documents
```

### `/wizards/page.tsx` - Form Wizard Selection

```tsx
// List of available wizards with descriptions
```

### `/wizards/[type]/page.tsx` - Wizard Steps

```tsx
// Step-by-step wizard interface
```

## Evidence Checklist Templates

Pre-populate checklists based on common conditions:

```python
EVIDENCE_TEMPLATES = {
    "ptsd": [
        {"type": "str", "desc": "Service Treatment Records showing mental health treatment"},
        {"type": "stressor", "desc": "Stressor statement describing traumatic event(s)"},
        {"type": "va_records", "desc": "VA mental health treatment records"},
        {"type": "nexus", "desc": "Nexus letter from psychiatrist/psychologist"},
        {"type": "buddy", "desc": "Buddy statements about behavioral changes"},
        {"type": "dbq", "desc": "PTSD DBQ from qualified provider"}
    ],
    "tinnitus": [
        {"type": "str", "desc": "Service records showing noise exposure"},
        {"type": "audiogram", "desc": "Current audiogram showing hearing loss"},
        {"type": "nexus", "desc": "Nexus letter connecting tinnitus to service"},
        {"type": "buddy", "desc": "Buddy statements about noise exposure"}
    ],
    "back_condition": [
        {"type": "str", "desc": "Service records showing back injury/treatment"},
        {"type": "va_records", "desc": "Current VA treatment records"},
        {"type": "mri", "desc": "MRI or X-ray results"},
        {"type": "nexus", "desc": "Nexus letter from orthopedist"},
        {"type": "dbq", "desc": "Back conditions DBQ"}
    ]
    # ... more condition templates
}
```

## Security Considerations

1. **Document Storage**: Files stored on goldfin with restricted access
2. **PII Detection**: Run Presidio on document text extraction
3. **Encryption**: Documents encrypted at rest on goldfin
4. **Access Control**: Users can only access their own projects/documents
5. **Audit Trail**: Log all document access and modifications

## Success Criteria

- [ ] Database tables created on bluefin
- [ ] Backend API endpoints functional
- [ ] Frontend workbench page with project list
- [ ] Document upload working to goldfin
- [ ] Evidence checklist with condition templates
- [ ] Notes/scratch pad per project
- [ ] At least 2 Form Wizards complete (ITF, New Claim)
- [ ] Mobile responsive design
- [ ] All data properly associated with authenticated user

## Testing

```bash
# Test API endpoints
curl -X POST http://localhost:8001/api/v1/workbench/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "PTSD Claim", "claim_type": "new_claim", "target_conditions": ["PTSD"]}'

# Test document upload
curl -X POST http://localhost:8001/api/v1/workbench/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@medical_records.pdf" \
  -F "category=medical"
```

---

*Cherokee AI Federation - For the Seven Generations*
*"Helping veterans organize their path to the benefits they've earned."*
