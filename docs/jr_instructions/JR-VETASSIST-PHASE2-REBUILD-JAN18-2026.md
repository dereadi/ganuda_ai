# JR Instruction: VetAssist Phase 2 Feature Rebuild

## Metadata
```yaml
task_id: vetassist_phase2_rebuild
priority: 1
assigned_to: it_triad_jr
estimated_effort: large
category: feature_development
created: 2026-01-18
reason: Previous tasks (109-123) marked complete but RLM executor bug prevented actual file creation
```

## Context

Tasks 109-123 were executed with a buggy RLM executor that generated text responses but never wrote files to disk. The bug has been fixed (see `/ganuda/lib/rlm_executor.py` fix on Jan 18, 2026). These features need to be properly built.

## Current VetAssist State

**Backend Endpoints Exist:**
- `/api/v1/auth/` - Authentication
- `/api/v1/calculator/` - Rating calculator
- `/api/v1/chat/` - AI chat with Council
- `/api/v1/content/` - Educational articles
- `/api/v1/evidence_analysis/` - Evidence analysis
- `/api/v1/health/` - Health check

**Missing (Need to Create):**
- `/api/v1/workbench/` - Claim workbench management
- `/api/v1/wizard/` - Form wizard framework
- `/api/v1/family/` - Family member management
- `/api/v1/readiness/` - Claim readiness scoring
- `/api/v1/export/` - PDF export

## Required Files to Create

### 1. Workbench Backend

**CREATE FILE: /ganuda/vetassist/backend/app/api/v1/endpoints/workbench.py**
```python
"""
VetAssist Claim Workbench Endpoints

Manages veteran claim projects with evidence tracking, status, and notes.
Cherokee AI Federation - For Seven Generations
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

router = APIRouter(prefix="/workbench", tags=["workbench"])

# Pydantic models
class ClaimProject(BaseModel):
    id: str
    veteran_id: str
    title: str
    status: str  # draft, in_progress, submitted, decided
    conditions: List[dict]
    evidence_items: List[dict]
    notes: List[dict]
    created_at: datetime
    updated_at: datetime

class CreateProject(BaseModel):
    title: str
    conditions: List[dict] = []

class AddEvidence(BaseModel):
    project_id: str
    evidence_type: str  # medical, buddy_statement, nexus_letter, service_record
    description: str
    file_path: Optional[str] = None

# In-memory storage (replace with database)
projects_db = {}

@router.post("/projects", response_model=ClaimProject)
async def create_project(data: CreateProject, user_id: str = "demo"):
    """Create a new claim project."""
    project = ClaimProject(
        id=str(uuid4()),
        veteran_id=user_id,
        title=data.title,
        status="draft",
        conditions=data.conditions,
        evidence_items=[],
        notes=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    projects_db[project.id] = project
    return project

@router.get("/projects", response_model=List[ClaimProject])
async def list_projects(user_id: str = "demo"):
    """List all projects for a veteran."""
    return [p for p in projects_db.values() if p.veteran_id == user_id]

@router.get("/projects/{project_id}", response_model=ClaimProject)
async def get_project(project_id: str):
    """Get a specific project."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects_db[project_id]

@router.post("/projects/{project_id}/evidence")
async def add_evidence(project_id: str, data: AddEvidence):
    """Add evidence to a project."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    evidence = {
        "id": str(uuid4()),
        "type": data.evidence_type,
        "description": data.description,
        "file_path": data.file_path,
        "added_at": datetime.now().isoformat()
    }
    projects_db[project_id].evidence_items.append(evidence)
    projects_db[project_id].updated_at = datetime.now()
    return evidence

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    del projects_db[project_id]
    return {"status": "deleted"}
```

### 2. Form Wizard Backend

**CREATE FILE: /ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py**
```python
"""
VetAssist Form Wizard Endpoints

Provides step-by-step form guidance for ITF, New Claims, and Rating Increases.
Cherokee AI Federation - For Seven Generations
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from uuid import uuid4

router = APIRouter(prefix="/wizard", tags=["wizard"])

# Wizard definitions
WIZARD_DEFINITIONS = {
    "itf": {
        "name": "Intent to File (ITF)",
        "description": "Reserve your effective date while gathering evidence",
        "steps": [
            {"id": 1, "title": "Personal Information", "fields": ["name", "ssn_last4", "dob"]},
            {"id": 2, "title": "Contact Information", "fields": ["address", "phone", "email"]},
            {"id": 3, "title": "Claim Type", "fields": ["claim_types"]},
            {"id": 4, "title": "Review & Submit", "fields": []}
        ]
    },
    "new_claim": {
        "name": "New Disability Claim",
        "description": "File a claim for service-connected disability",
        "steps": [
            {"id": 1, "title": "Service Information", "fields": ["branch", "service_dates", "discharge_status"]},
            {"id": 2, "title": "Conditions", "fields": ["conditions", "in_service_events"]},
            {"id": 3, "title": "Evidence", "fields": ["medical_records", "buddy_statements"]},
            {"id": 4, "title": "Review & Submit", "fields": []}
        ]
    },
    "rating_increase": {
        "name": "Rating Increase",
        "description": "Request an increase for a worsening condition",
        "steps": [
            {"id": 1, "title": "Current Rating", "fields": ["current_conditions", "current_rating"]},
            {"id": 2, "title": "Worsening Details", "fields": ["worsened_condition", "symptoms"]},
            {"id": 3, "title": "New Evidence", "fields": ["recent_treatment", "impact_on_work"]},
            {"id": 4, "title": "Review & Submit", "fields": []}
        ]
    }
}

# Session storage
wizard_sessions = {}

class WizardSession(BaseModel):
    session_id: str
    wizard_type: str
    current_step: int
    data: Dict
    created_at: datetime
    completed: bool = False

class StartWizard(BaseModel):
    wizard_type: str

class UpdateStep(BaseModel):
    step_data: Dict

@router.get("/types")
async def list_wizard_types():
    """List available wizard types."""
    return [
        {"type": k, "name": v["name"], "description": v["description"]}
        for k, v in WIZARD_DEFINITIONS.items()
    ]

@router.get("/types/{wizard_type}")
async def get_wizard_definition(wizard_type: str):
    """Get wizard definition with all steps."""
    if wizard_type not in WIZARD_DEFINITIONS:
        raise HTTPException(status_code=404, detail="Wizard type not found")
    return WIZARD_DEFINITIONS[wizard_type]

@router.post("/start", response_model=WizardSession)
async def start_wizard(data: StartWizard):
    """Start a new wizard session."""
    if data.wizard_type not in WIZARD_DEFINITIONS:
        raise HTTPException(status_code=400, detail="Invalid wizard type")

    session = WizardSession(
        session_id=str(uuid4()),
        wizard_type=data.wizard_type,
        current_step=1,
        data={},
        created_at=datetime.now()
    )
    wizard_sessions[session.session_id] = session
    return session

@router.get("/session/{session_id}", response_model=WizardSession)
async def get_session(session_id: str):
    """Get wizard session state."""
    if session_id not in wizard_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return wizard_sessions[session_id]

@router.post("/session/{session_id}/step/{step_num}")
async def update_step(session_id: str, step_num: int, data: UpdateStep):
    """Update data for a wizard step."""
    if session_id not in wizard_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = wizard_sessions[session_id]
    session.data[f"step_{step_num}"] = data.step_data
    session.current_step = step_num + 1

    # Check if completed
    wizard_def = WIZARD_DEFINITIONS[session.wizard_type]
    if session.current_step > len(wizard_def["steps"]):
        session.completed = True

    return session

@router.post("/session/{session_id}/submit")
async def submit_wizard(session_id: str):
    """Submit completed wizard."""
    if session_id not in wizard_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = wizard_sessions[session_id]
    # In production: create claim project, send to VA, etc.
    return {
        "status": "submitted",
        "confirmation_number": f"VA-{str(uuid4())[:8].upper()}",
        "wizard_type": session.wizard_type,
        "submitted_at": datetime.now().isoformat()
    }
```

### 3. Claim Readiness Scoring

**CREATE FILE: /ganuda/vetassist/backend/app/api/v1/endpoints/readiness.py**
```python
"""
VetAssist Claim Readiness Scoring

AI-powered assessment of claim strength based on evidence completeness.
Cherokee AI Federation - For Seven Generations
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict

router = APIRouter(prefix="/readiness", tags=["readiness"])

# Evidence requirements by condition category
EVIDENCE_REQUIREMENTS = {
    "ptsd": {
        "required": ["stressor_statement", "diagnosis", "nexus_letter"],
        "recommended": ["buddy_statements", "service_records", "treatment_records"],
        "weights": {"diagnosis": 30, "nexus_letter": 25, "stressor_statement": 20,
                   "treatment_records": 15, "buddy_statements": 5, "service_records": 5}
    },
    "musculoskeletal": {
        "required": ["diagnosis", "medical_records"],
        "recommended": ["nexus_letter", "service_records", "impact_statement"],
        "weights": {"diagnosis": 30, "medical_records": 25, "nexus_letter": 20,
                   "service_records": 15, "impact_statement": 10}
    },
    "hearing_loss": {
        "required": ["audiogram", "diagnosis"],
        "recommended": ["noise_exposure_evidence", "nexus_letter", "buddy_statements"],
        "weights": {"audiogram": 35, "diagnosis": 25, "nexus_letter": 20,
                   "noise_exposure_evidence": 15, "buddy_statements": 5}
    },
    "default": {
        "required": ["diagnosis", "medical_records"],
        "recommended": ["nexus_letter", "service_records"],
        "weights": {"diagnosis": 35, "medical_records": 30, "nexus_letter": 20, "service_records": 15}
    }
}

class ReadinessRequest(BaseModel):
    condition_category: str
    evidence_present: List[str]

class ReadinessResponse(BaseModel):
    score: int
    grade: str
    missing_required: List[str]
    missing_recommended: List[str]
    suggestions: List[str]

def calculate_grade(score: int) -> str:
    if score >= 90: return "A"
    if score >= 80: return "B"
    if score >= 70: return "C"
    if score >= 60: return "D"
    return "F"

@router.post("/score", response_model=ReadinessResponse)
async def calculate_readiness(data: ReadinessRequest):
    """Calculate claim readiness score."""
    category = data.condition_category.lower()
    if category not in EVIDENCE_REQUIREMENTS:
        category = "default"

    requirements = EVIDENCE_REQUIREMENTS[category]
    weights = requirements["weights"]

    # Calculate score
    score = 0
    for evidence in data.evidence_present:
        if evidence in weights:
            score += weights[evidence]

    # Identify missing evidence
    missing_required = [e for e in requirements["required"] if e not in data.evidence_present]
    missing_recommended = [e for e in requirements["recommended"] if e not in data.evidence_present]

    # Generate suggestions
    suggestions = []
    if missing_required:
        suggestions.append(f"Missing required evidence: {', '.join(missing_required)}")
    if "nexus_letter" in missing_recommended:
        suggestions.append("Consider obtaining a nexus letter from a medical professional")
    if "buddy_statements" in missing_recommended:
        suggestions.append("Buddy statements from fellow service members can strengthen your claim")
    if score < 70:
        suggestions.append("Your claim may benefit from additional evidence gathering")

    return ReadinessResponse(
        score=min(score, 100),
        grade=calculate_grade(score),
        missing_required=missing_required,
        missing_recommended=missing_recommended,
        suggestions=suggestions
    )

@router.get("/requirements/{condition_category}")
async def get_requirements(condition_category: str):
    """Get evidence requirements for a condition category."""
    category = condition_category.lower()
    if category not in EVIDENCE_REQUIREMENTS:
        category = "default"
    return EVIDENCE_REQUIREMENTS[category]

@router.get("/categories")
async def list_categories():
    """List supported condition categories."""
    return list(EVIDENCE_REQUIREMENTS.keys())
```

### 4. Family Member Management

**CREATE FILE: /ganuda/vetassist/backend/app/api/v1/endpoints/family.py**
```python
"""
VetAssist Family Member Management

Allows veterans to invite family members as caregivers with limited access.
Cherokee AI Federation - For Seven Generations
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import uuid4

router = APIRouter(prefix="/family", tags=["family"])

# Role permissions
ROLE_PERMISSIONS = {
    "caregiver": ["view_projects", "add_notes", "view_readiness"],
    "dependent": ["view_benefits_info"],
    "vso": ["view_projects", "add_notes", "view_readiness", "submit_forms"]
}

# Storage
invitations = {}
family_members = {}

class Invitation(BaseModel):
    id: str
    veteran_id: str
    email: str
    role: str
    created_at: datetime
    expires_at: datetime
    accepted: bool = False

class FamilyMember(BaseModel):
    id: str
    veteran_id: str
    user_id: str
    name: str
    role: str
    permissions: List[str]
    added_at: datetime

class CreateInvitation(BaseModel):
    email: str
    role: str
    name: Optional[str] = None

@router.post("/invite", response_model=Invitation)
async def create_invitation(data: CreateInvitation, veteran_id: str = "demo"):
    """Invite a family member."""
    if data.role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {list(ROLE_PERMISSIONS.keys())}")

    invitation = Invitation(
        id=str(uuid4()),
        veteran_id=veteran_id,
        email=data.email,
        role=data.role,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=7)
    )
    invitations[invitation.id] = invitation
    # In production: send email with invitation link
    return invitation

@router.get("/invitations", response_model=List[Invitation])
async def list_invitations(veteran_id: str = "demo"):
    """List pending invitations."""
    return [i for i in invitations.values() if i.veteran_id == veteran_id and not i.accepted]

@router.post("/accept/{invitation_id}")
async def accept_invitation(invitation_id: str, user_id: str, name: str):
    """Accept a family invitation."""
    if invitation_id not in invitations:
        raise HTTPException(status_code=404, detail="Invitation not found")

    inv = invitations[invitation_id]
    if inv.accepted:
        raise HTTPException(status_code=400, detail="Invitation already accepted")
    if datetime.now() > inv.expires_at:
        raise HTTPException(status_code=400, detail="Invitation expired")

    member = FamilyMember(
        id=str(uuid4()),
        veteran_id=inv.veteran_id,
        user_id=user_id,
        name=name,
        role=inv.role,
        permissions=ROLE_PERMISSIONS[inv.role],
        added_at=datetime.now()
    )
    family_members[member.id] = member
    inv.accepted = True
    return member

@router.get("/members", response_model=List[FamilyMember])
async def list_members(veteran_id: str = "demo"):
    """List family members."""
    return [m for m in family_members.values() if m.veteran_id == veteran_id]

@router.delete("/members/{member_id}")
async def remove_member(member_id: str):
    """Remove a family member."""
    if member_id not in family_members:
        raise HTTPException(status_code=404, detail="Member not found")
    del family_members[member_id]
    return {"status": "removed"}

@router.get("/roles")
async def list_roles():
    """List available roles and permissions."""
    return ROLE_PERMISSIONS
```

### 5. PDF Export

**CREATE FILE: /ganuda/vetassist/backend/app/api/v1/endpoints/export.py**
```python
"""
VetAssist PDF Export

Generate PDF summaries of claim projects and evidence checklists.
Cherokee AI Federation - For Seven Generations
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import io

router = APIRouter(prefix="/export", tags=["export"])

# Note: In production, use reportlab or weasyprint for PDF generation
# This is a stub that returns plain text formatted as PDF-ready

class ExportRequest(BaseModel):
    project_id: str
    include_evidence: bool = True
    include_readiness: bool = True

@router.post("/pdf/claim-summary")
async def export_claim_summary(data: ExportRequest):
    """Export claim project as PDF summary."""
    # In production: fetch from database
    # Here we return a text representation

    content = f"""
VETASSIST CLAIM SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Project ID: {data.project_id}

================================================================================
CLAIM INFORMATION
================================================================================
This is a placeholder for the claim summary PDF.

In production, this endpoint would:
1. Fetch the project from the database
2. Generate a formatted PDF using reportlab or weasyprint
3. Include condition details, evidence checklist, and readiness score
4. Return the PDF as a downloadable file

================================================================================
DISCLAIMER
================================================================================
VetAssist provides educational information only. This is not legal advice.
Always consult with a VA-accredited representative for claims assistance.

Cherokee AI Federation - For Seven Generations
    """

    return Response(
        content=content.encode(),
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=claim_summary_{data.project_id}.txt"
        }
    )

@router.post("/pdf/evidence-checklist")
async def export_evidence_checklist(condition_category: str):
    """Export evidence checklist as PDF."""
    content = f"""
VETASSIST EVIDENCE CHECKLIST
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Condition Category: {condition_category}

================================================================================
REQUIRED EVIDENCE
================================================================================
[ ] Medical diagnosis
[ ] Treatment records
[ ] Nexus letter (if applicable)

================================================================================
RECOMMENDED EVIDENCE
================================================================================
[ ] Service records showing in-service event
[ ] Buddy statements
[ ] Personal impact statement

================================================================================
TIPS FOR STRONG EVIDENCE
================================================================================
1. Get a clear diagnosis from a medical professional
2. Obtain a nexus letter linking condition to service
3. Document how the condition affects daily life
4. Gather buddy statements from fellow service members

Cherokee AI Federation - For Seven Generations
    """

    return Response(
        content=content.encode(),
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=evidence_checklist_{condition_category}.txt"
        }
    )
```

### 6. Update Main Router

**MODIFY FILE: /ganuda/vetassist/backend/app/api/v1/__init__.py**

Add imports and include the new routers:
```python
from .endpoints import workbench, wizard, readiness, family, export

# Add to router includes:
router.include_router(workbench.router)
router.include_router(wizard.router)
router.include_router(readiness.router)
router.include_router(family.router)
router.include_router(export.router)
```

## Testing

After creating files, test each endpoint:

```bash
# Test workbench
curl -X POST http://localhost:8001/api/v1/workbench/projects \
  -H "Content-Type: application/json" \
  -d '{"title": "My PTSD Claim", "conditions": []}'

# Test wizard
curl http://localhost:8001/api/v1/wizard/types

# Test readiness
curl -X POST http://localhost:8001/api/v1/readiness/score \
  -H "Content-Type: application/json" \
  -d '{"condition_category": "ptsd", "evidence_present": ["diagnosis", "nexus_letter"]}'

# Test family
curl http://localhost:8001/api/v1/family/roles

# Test export
curl -X POST http://localhost:8001/api/v1/export/pdf/evidence-checklist?condition_category=ptsd
```

## Success Criteria

| Test | Expected |
|------|----------|
| Workbench CRUD | Create, list, get, delete projects |
| Wizard flow | Start, update steps, submit |
| Readiness scoring | Score calculation with suggestions |
| Family management | Invite, accept, list members |
| PDF export | Download claim summary |

## Cherokee Wisdom

> "The one who tells the stories rules the world."

These tools help veterans tell their stories effectively to the VA. Every feature should empower, not complicate.

---
**Priority**: HIGH - Core Phase 2 features for VetAssist beta
**Cherokee AI Federation - For Seven Generations**
