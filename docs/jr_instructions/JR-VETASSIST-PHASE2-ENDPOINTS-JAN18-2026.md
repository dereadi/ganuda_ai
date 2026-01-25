# JR INSTRUCTION: VetAssist Phase 2 Backend Endpoints

## Document Control
```yaml
jr_instruction_id: JR-VETASSIST-PHASE2-ENDPOINTS
created: 2026-01-18
author: TPM Claude (Opus 4.5)
assigned_jr: it_triad_jr
priority: HIGH
estimated_duration: 4_hours
dependencies:
  - Consciousness daemon running (COMPLETE)
  - RLM executor prompt fixed (COMPLETE)
```

---

## Objective

Create 5 backend endpoint files for VetAssist Phase 2 functionality. These endpoints power the veteran claim workbench, guided wizards, and export capabilities.

---

## Technical Context

**Base Path:** `/ganuda/vetassist/backend/app/api/v1/endpoints/`

**Existing Files to Reference:**
- `chat.py` - Example endpoint structure
- `calculator.py` - Rating calculation patterns

**Database:** PostgreSQL on bluefin (192.168.132.222)
- Connection: `user=claude, password=jawaseatlasers2, db=zammad_production`

**Framework:** FastAPI with Pydantic models

---

## Files to Create

### 1. `/ganuda/vetassist/backend/app/api/v1/endpoints/workbench.py`

**Purpose:** Veteran claim workbench - tracks claim progress and checklist items

**Endpoints:**
```python
POST /workbench/claims - Create new claim draft
GET /workbench/claims/{claim_id} - Get claim with progress
PUT /workbench/claims/{claim_id} - Update claim
GET /workbench/claims/{claim_id}/checklist - Get evidence checklist
PUT /workbench/claims/{claim_id}/checklist/{item_id} - Update checklist item
GET /workbench/claims/{claim_id}/timeline - Get claim timeline events
```

**Database Tables Needed:**
- `vetassist_claims` (id, veteran_id, status, created_at, updated_at)
- `vetassist_checklist_items` (id, claim_id, item_type, description, completed, evidence_path)
- `vetassist_timeline_events` (id, claim_id, event_type, description, created_at)

---

### 2. `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

**Purpose:** Guided form completion wizards for complex VA forms

**Endpoints:**
```python
POST /wizard/start - Start new wizard session
GET /wizard/{session_id}/step/{step_num} - Get current step
POST /wizard/{session_id}/step/{step_num} - Submit step answers
GET /wizard/{session_id}/summary - Get completed wizard summary
POST /wizard/{session_id}/complete - Finalize and generate form
```

**Wizard Types:**
- `21-526EZ` - Disability Compensation claim
- `21-0995` - Supplemental Claim
- `20-0996` - Higher-Level Review
- `10182` - Board of Veterans Appeals

---

### 3. `/ganuda/vetassist/backend/app/api/v1/endpoints/readiness.py`

**Purpose:** Claim submission readiness assessment

**Endpoints:**
```python
GET /readiness/{claim_id} - Get overall readiness score
GET /readiness/{claim_id}/conditions - Per-condition readiness
GET /readiness/{claim_id}/evidence - Evidence completeness check
GET /readiness/{claim_id}/blockers - List blocking issues
POST /readiness/{claim_id}/validate - Run full validation
```

**Readiness Criteria:**
- All required forms completed
- DBQ for each claimed condition
- Service treatment records uploaded
- Nexus letter present (if applicable)
- Personal statement drafted

---

### 4. `/ganuda/vetassist/backend/app/api/v1/endpoints/family.py`

**Purpose:** Dependent management for SMC-S and family benefits

**Endpoints:**
```python
GET /family/{veteran_id}/dependents - List all dependents
POST /family/{veteran_id}/dependents - Add dependent
PUT /family/{veteran_id}/dependents/{dep_id} - Update dependent
DELETE /family/{veteran_id}/dependents/{dep_id} - Remove dependent
GET /family/{veteran_id}/benefits - Calculate family benefits impact
POST /family/validate-documents - Validate dependent documents
```

**Dependent Types:**
- Spouse
- Child (under 18 or full-time student 18-23)
- Helpless child
- Parent (if veteran 30%+ rated)

---

### 5. `/ganuda/vetassist/backend/app/api/v1/endpoints/export.py`

**Purpose:** Document generation and export

**Endpoints:**
```python
GET /export/{claim_id}/pdf - Generate complete claim packet PDF
GET /export/{claim_id}/forms/{form_id} - Export specific filled form
GET /export/{claim_id}/checklist - Export evidence checklist
GET /export/{claim_id}/timeline - Export claim timeline
POST /export/{claim_id}/ftp - Upload to VA secure FTP (future)
```

**Export Formats:**
- PDF (primary)
- JSON (for interoperability)
- VA XML format (for eBenefits integration)

---

## Implementation Pattern

Each endpoint file should follow this structure:

```python
"""
VetAssist API v1 - [Name] Endpoint
Cherokee AI Federation - For Seven Generations
Created: January 2026
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter(prefix="/[name]", tags=["[name]"])

# Database connection
DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

# Pydantic models
class [ModelName](BaseModel):
    field: type

# Endpoints
@router.get("/endpoint")
async def endpoint_name():
    pass
```

---

## Database Schema SQL

Create these tables in zammad_production:

```sql
-- Run on bluefin (192.168.132.222)

-- Claims table
CREATE TABLE IF NOT EXISTS vetassist_claims (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    claim_type VARCHAR(50),
    conditions JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Checklist items
CREATE TABLE IF NOT EXISTS vetassist_checklist_items (
    id SERIAL PRIMARY KEY,
    claim_id INTEGER REFERENCES vetassist_claims(id),
    item_type VARCHAR(50),
    description TEXT,
    required BOOLEAN DEFAULT true,
    completed BOOLEAN DEFAULT false,
    evidence_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Timeline events
CREATE TABLE IF NOT EXISTS vetassist_timeline_events (
    id SERIAL PRIMARY KEY,
    claim_id INTEGER REFERENCES vetassist_claims(id),
    event_type VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Wizard sessions
CREATE TABLE IF NOT EXISTS vetassist_wizard_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID DEFAULT gen_random_uuid(),
    wizard_type VARCHAR(50),
    veteran_id VARCHAR(50),
    current_step INTEGER DEFAULT 1,
    answers JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'in_progress',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Dependents
CREATE TABLE IF NOT EXISTS vetassist_dependents (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(50) NOT NULL,
    dependent_type VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_of_birth DATE,
    relationship VARCHAR(50),
    documents JSONB,
    verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_claims_veteran ON vetassist_claims(veteran_id);
CREATE INDEX IF NOT EXISTS idx_checklist_claim ON vetassist_checklist_items(claim_id);
CREATE INDEX IF NOT EXISTS idx_timeline_claim ON vetassist_timeline_events(claim_id);
CREATE INDEX IF NOT EXISTS idx_wizard_session ON vetassist_wizard_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_dependents_veteran ON vetassist_dependents(veteran_id);
```

---

## Router Registration

After creating endpoints, update `/ganuda/vetassist/backend/app/api/v1/__init__.py`:

```python
from .endpoints import workbench, wizard, readiness, family, export

# Add to router includes
api_router.include_router(workbench.router)
api_router.include_router(wizard.router)
api_router.include_router(readiness.router)
api_router.include_router(family.router)
api_router.include_router(export.router)
```

---

## Acceptance Criteria

1. All 5 endpoint files created and syntactically valid
2. Database tables created on bluefin
3. Endpoints registered in API router
4. Basic CRUD operations working for each endpoint
5. Pydantic models defined for request/response schemas

---

## Testing Commands

```bash
# After implementation, test endpoints:
curl http://localhost:8001/api/v1/workbench/claims -X POST -H "Content-Type: application/json" -d '{"veteran_id": "test123"}'
curl http://localhost:8001/api/v1/wizard/start -X POST -H "Content-Type: application/json" -d '{"wizard_type": "21-526EZ", "veteran_id": "test123"}'
curl http://localhost:8001/api/v1/readiness/1
curl http://localhost:8001/api/v1/family/test123/dependents
curl http://localhost:8001/api/v1/export/1/pdf
```

---

## Notes for Jr

- Reference existing `chat.py` and `calculator.py` for patterns
- Use asyncpg if async DB needed, otherwise psycopg2 is fine
- All PII fields should be handled carefully - use vetassist_pii table patterns
- Log important operations to council for auditability
- Test locally before marking complete

**For Seven Generations**
