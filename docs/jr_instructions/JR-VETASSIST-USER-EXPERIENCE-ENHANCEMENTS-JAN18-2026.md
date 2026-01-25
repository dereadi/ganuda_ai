# JR INSTRUCTION: VetAssist User Experience Enhancements

## Document Control
```yaml
jr_instruction_id: JR-VETASSIST-UX-ENHANCEMENTS
created: 2026-01-18
author: TPM Claude (Opus 4.5)
priority: HIGH
assigned_jr: it_triad_jr
category: product_enhancement
user_feedback: Direct from Darrell testing
```

---

## Executive Summary

After user testing, three critical enhancement areas were identified:

1. **Deep Research on Questions** - Jr-powered web research for veteran questions
2. **VA API Integrations** - Connect to official VA Lighthouse APIs
3. **Personalized User Dashboard** - Scratchpad, file uploads, custom home page

---

## Enhancement 1: Deep Research Feature

### Problem
When a veteran asks a question about their condition or claim, the AI gives a good answer but the user wants MORE - research from authoritative sources, related articles, current VA policies.

### Solution
Trigger a Jr research task when the AI detects:
- A novel/complex question
- A question about specific conditions
- A request for "more information" or "research this"

### Implementation

#### Backend: `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py`

```python
"""
VetAssist Deep Research Endpoint
Triggers Jr web research for veteran questions
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

router = APIRouter()

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

class ResearchRequest(BaseModel):
    session_id: str
    question: str
    condition: Optional[str] = None
    search_sources: List[str] = ["va.gov", "cck-law.com", "vaclaimsinsider.com"]


@router.post("/trigger")
async def trigger_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Queue a deep research task for the Jr workers"""
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Create research task in jr_work_queue
        cur.execute("""
            INSERT INTO jr_work_queue (
                title, description, instruction_content, parameters,
                status, priority, assigned_jr, use_rlm
            ) VALUES (
                %s, %s, %s, %s, 'pending', 3, 'it_triad_jr', false
            ) RETURNING id, task_id
        """, (
            f"VetAssist Research: {request.question[:50]}...",
            f"Deep research for veteran question about {request.condition or 'VA benefits'}",
            f"""Research this veteran question thoroughly:

QUESTION: {request.question}
CONDITION: {request.condition or 'General VA benefits'}

Search these authoritative sources:
1. VA.gov official guidance
2. 38 CFR regulations
3. BVA decisions
4. Veteran advocacy sites (CCK Law, VA Claims Insider)

Return:
- Key findings (bullet points)
- Relevant VA regulations cited
- Links to authoritative sources
- Recommended next steps for the veteran
""",
            json.dumps({
                "session_id": request.session_id,
                "question": request.question,
                "sources": request.search_sources,
                "research_type": "veteran_question"
            })
        ))
        task = cur.fetchone()
        conn.commit()
    conn.close()

    return {
        "status": "research_queued",
        "task_id": task['task_id'],
        "message": "A Jr researcher is looking into this. Results will appear in your dashboard."
    }


@router.get("/results/{session_id}")
async def get_research_results(session_id: str):
    """Get completed research results for a session"""
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, title, status, result, completed_at
            FROM jr_work_queue
            WHERE parameters->>'session_id' = %s
            AND parameters->>'research_type' = 'veteran_question'
            ORDER BY created_at DESC
            LIMIT 5
        """, (session_id,))
        results = cur.fetchall()
    conn.close()

    return {"session_id": session_id, "research_tasks": results}
```

#### Frontend Component: Research Results Panel

Add to chat interface - when research completes, show expandable panel with:
- Key findings
- Source links (clickable)
- "Save to scratchpad" button

---

## Enhancement 2: VA Lighthouse API Integration

### Available APIs (from developer.va.gov)

| API | Purpose | Use Case |
|-----|---------|----------|
| Benefits Claims API | Submit/check claim status | Show real claim status |
| Benefits Intake API | Upload documents to VBMS | Direct file submission |
| Appeals Status API | Check appeal status | Track appeals |
| Veteran Verification API | Verify veteran status | Account validation |

### Implementation Plan

#### 1. Register for API Access
- Apply at https://developer.va.gov/
- Email: api@va.gov for VSO partnership inquiry
- Sandbox access is immediate; production requires demo

#### 2. Create VA API Service: `/ganuda/vetassist/backend/app/services/va_api.py`

```python
"""
VA Lighthouse API Integration Service
Cherokee AI Federation - For Seven Generations
"""
import httpx
from typing import Optional, Dict
import os

VA_API_BASE = "https://sandbox-api.va.gov"  # Change to api.va.gov for production
VA_API_KEY = os.getenv("VA_API_KEY", "sandbox-key")

class VALighthouseService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=VA_API_BASE,
            headers={"apikey": VA_API_KEY}
        )

    async def verify_veteran(self, ssn: str, first_name: str, last_name: str, birth_date: str):
        """Verify veteran status via VA API"""
        # Requires OAuth - veteran must authorize
        pass

    async def get_claim_status(self, veteran_id: str, claim_id: str):
        """Get status of a submitted claim"""
        response = await self.client.get(
            f"/services/claims/v1/claims/{claim_id}",
            headers={"X-VA-SSN": veteran_id}  # Requires proper auth
        )
        return response.json()

    async def submit_document(self, file_data: bytes, metadata: Dict):
        """Submit document to Benefits Intake API"""
        # For scanned PDFs to VBMS
        pass
```

#### 3. Create database table for API credentials

```sql
CREATE TABLE IF NOT EXISTS vetassist_va_connections (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(50) NOT NULL,
    va_api_token TEXT,  -- Encrypted
    token_expires TIMESTAMP,
    scopes TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP
);
```

---

## Enhancement 3: Personalized User Dashboard

### Requirements

1. **Scratchpad** - Text area for notes, auto-saves
2. **File Drop Zone** - Upload evidence documents
3. **My Claims** - List of tracked claims with progress
4. **Research History** - Past AI conversations and research results
5. **Quick Actions** - Calculator, new wizard, chat shortcuts

### Database Schema

```sql
-- User scratchpad
CREATE TABLE IF NOT EXISTS vetassist_user_scratchpad (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(50) NOT NULL,
    content TEXT,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(veteran_id)
);

-- User files
CREATE TABLE IF NOT EXISTS vetassist_user_files (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(50) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    storage_path TEXT,  -- Path in secure storage
    category VARCHAR(50),  -- medical, service_records, buddy_statement, etc
    uploaded_at TIMESTAMP DEFAULT NOW(),
    description TEXT
);

-- User dashboard preferences
CREATE TABLE IF NOT EXISTS vetassist_user_preferences (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(50) NOT NULL UNIQUE,
    dashboard_layout JSONB DEFAULT '{}',
    notification_prefs JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_scratchpad_veteran ON vetassist_user_scratchpad(veteran_id);
CREATE INDEX IF NOT EXISTS idx_files_veteran ON vetassist_user_files(veteran_id);
```

### Backend Endpoints: `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`

```python
"""
VetAssist User Dashboard Endpoint
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
import uuid

router = APIRouter()

DB_CONFIG = {...}  # Same as other endpoints
UPLOAD_DIR = "/ganuda/vetassist/uploads"  # Secure, not web-accessible

class ScratchpadUpdate(BaseModel):
    content: str

@router.get("/{veteran_id}")
def get_dashboard(veteran_id: str):
    """Get complete dashboard data for a veteran"""
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get scratchpad
        cur.execute("SELECT content, last_updated FROM vetassist_user_scratchpad WHERE veteran_id = %s", (veteran_id,))
        scratchpad = cur.fetchone()

        # Get recent files
        cur.execute("""
            SELECT id, filename, file_type, category, uploaded_at, description
            FROM vetassist_user_files WHERE veteran_id = %s
            ORDER BY uploaded_at DESC LIMIT 10
        """, (veteran_id,))
        files = cur.fetchall()

        # Get active claims
        cur.execute("""
            SELECT id, claim_type, status, created_at
            FROM vetassist_claims WHERE veteran_id = %s
            ORDER BY created_at DESC
        """, (veteran_id,))
        claims = cur.fetchall()

        # Get recent research
        cur.execute("""
            SELECT title, status, completed_at, result->>'summary' as summary
            FROM jr_work_queue
            WHERE parameters->>'veteran_id' = %s
            AND parameters->>'research_type' = 'veteran_question'
            ORDER BY created_at DESC LIMIT 5
        """, (veteran_id,))
        research = cur.fetchall()
    conn.close()

    return {
        "veteran_id": veteran_id,
        "scratchpad": scratchpad,
        "files": files,
        "claims": claims,
        "research_history": research,
        "quick_actions": [
            {"label": "New Claim", "action": "/wizard/start", "icon": "file-plus"},
            {"label": "Calculator", "action": "/calculator", "icon": "calculator"},
            {"label": "Ask AI", "action": "/chat", "icon": "message-circle"},
            {"label": "Upload Evidence", "action": "/dashboard/upload", "icon": "upload"}
        ]
    }

@router.put("/{veteran_id}/scratchpad")
def update_scratchpad(veteran_id: str, data: ScratchpadUpdate):
    """Auto-save scratchpad content"""
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            INSERT INTO vetassist_user_scratchpad (veteran_id, content, last_updated)
            VALUES (%s, %s, NOW())
            ON CONFLICT (veteran_id)
            DO UPDATE SET content = %s, last_updated = NOW()
            RETURNING *
        """, (veteran_id, data.content, data.content))
        result = cur.fetchone()
        conn.commit()
    conn.close()
    return result

@router.post("/{veteran_id}/files")
async def upload_file(veteran_id: str, file: UploadFile = File(...), category: str = "general"):
    """Upload evidence file"""
    # Security: validate file type
    allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']
    if file.content_type not in allowed_types:
        raise HTTPException(400, "File type not allowed. Use PDF or images.")

    # Generate secure filename
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    secure_name = f"{veteran_id}_{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, veteran_id, secure_name)

    # Create directory
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Save file
    content = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content)

    # Record in database
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            INSERT INTO vetassist_user_files
            (veteran_id, filename, file_type, file_size, storage_path, category)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, filename, category, uploaded_at
        """, (veteran_id, file.filename, file.content_type, len(content), file_path, category))
        result = cur.fetchone()
        conn.commit()
    conn.close()

    return {"status": "uploaded", "file": result}
```

### Frontend: Dashboard Page (`/ganuda/vetassist/frontend/src/app/dashboard/page.tsx`)

Create React components:
1. `ScratchpadEditor` - Auto-saving text area with markdown support
2. `FileDropZone` - Drag-and-drop file upload
3. `ClaimsTracker` - Cards showing claim progress
4. `ResearchPanel` - Expandable research results
5. `QuickActions` - Icon buttons for common tasks

---

## Implementation Priority

1. **Phase 1 (Immediate)**: Scratchpad + File Upload
   - Database tables
   - Backend endpoints
   - Basic frontend

2. **Phase 2 (This Week)**: Deep Research
   - Research endpoint
   - Jr task integration
   - Results display

3. **Phase 3 (Next Week)**: VA API Integration
   - API registration
   - Sandbox testing
   - OAuth flow for veteran auth

---

## Testing Commands

```bash
# Test scratchpad
curl -X PUT http://localhost:8001/api/v1/dashboard/test123/scratchpad \
  -H "Content-Type: application/json" \
  -d '{"content": "My notes about PTSD claim..."}'

# Test file upload
curl -X POST http://localhost:8001/api/v1/dashboard/test123/files \
  -F "file=@/path/to/document.pdf" \
  -F "category=medical"

# Test research trigger
curl -X POST http://localhost:8001/api/v1/research/trigger \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc123", "question": "What evidence do I need for a PTSD secondary to tinnitus claim?", "condition": "PTSD"}'
```

---

## VA API Resources

- Developer Portal: https://developer.va.gov/explore
- GitHub: https://github.com/department-of-veterans-affairs/vets-api-clients
- Contact: api@va.gov

---

## Notes for Jr

- PII handling critical - use vetassist_pii patterns
- File storage must be secure (not web-accessible)
- Auto-save scratchpad every 5 seconds on frontend
- Research tasks should return within 2 minutes
- VA API requires OAuth - start with sandbox

**For Seven Generations**
