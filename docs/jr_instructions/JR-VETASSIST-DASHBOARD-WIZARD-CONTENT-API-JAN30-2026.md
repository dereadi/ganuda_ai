# JR-VETASSIST-DASHBOARD-WIZARD-CONTENT-API-JAN30-2026
## Build Dashboard, Wizard Session, and Content API Modules

**Priority:** P1 - Feature Complete
**Target Node:** bluefin (192.168.132.222)
**Files to Create:**
- `/ganuda/vetassist/backend/app/api/dashboard_routes.py`
- `/ganuda/vetassist/backend/app/api/wizard_routes.py` (REPLACE existing)
- `/ganuda/vetassist/backend/app/api/content_routes.py`
- `/ganuda/vetassist/backend/app/api/research_routes.py`
**Wire into:** `/ganuda/vetassist/backend/main.py`
**Depends on:** Auth API (JR-VETASSIST-AUTH-API-JAN30-2026)

### Overview

Four API modules that complete the VetAssist backend. All database tables already exist.
All authenticated endpoints use `get_current_user` dependency from `app.core.auth`.

---

## Module 1: Dashboard API

**File:** `dashboard_routes.py`
**Prefix:** `/api/v1/dashboard`

### Database Tables Used
- `vetassist_claims` (id, veteran_id, status, claim_type, conditions jsonb, created_at, updated_at)
- `vetassist_user_files` (id, veteran_id, filename, file_type, file_size, storage_path, category, uploaded_at, description)
- `vetassist_scratchpads` (id, veteran_id, content, created_at, updated_at)
- `vetassist_research_results` (id, veteran_id, session_id, job_id, question, answer, sources jsonb, completed_at, created_at)

### Endpoints

#### GET /api/v1/dashboard/{veteran_id}
Returns aggregated dashboard data.
```json
{
  "veteran": { "id": "...", "first_name": "...", "disability_rating": 70 },
  "claims": [
    {"id": 1, "status": "in_progress", "claim_type": "increase", "conditions": [...], "created_at": "..."}
  ],
  "files": [
    {"id": 1, "filename": "dd214.pdf", "category": "service_records", "file_size": 245000, "uploaded_at": "..."}
  ],
  "research_history": [
    {"id": 1, "question": "PTSD rating criteria", "answer": "...", "completed_at": "..."}
  ],
  "scratchpad": {"content": "Notes here...", "updated_at": "..."},
  "quick_actions": [
    {"label": "Start New Claim", "url": "/wizard"},
    {"label": "Upload Evidence", "url": "/wizard"},
    {"label": "Chat with AI", "url": "/chat"}
  ]
}
```
**Logic:** Run parallel queries against claims, files, research_results, scratchpads tables. Join with users table for veteran info.

#### PUT /api/v1/dashboard/{veteran_id}/scratchpad
**Request:** `{"content": "My notes..."}`
**Logic:** UPSERT into vetassist_scratchpads (INSERT ON CONFLICT UPDATE)

#### POST /api/v1/dashboard/{veteran_id}/files
**Request:** FormData with `file` and `category` fields
**Logic:**
1. Save file to `/ganuda/vetassist/uploads/{veteran_id}/{uuid}_{filename}`
2. INSERT into vetassist_user_files
3. File size limit: 25 MB
4. Allowed types: pdf, jpg, jpeg, png, tiff, gif

#### DELETE /api/v1/dashboard/{veteran_id}/files/{file_id}
**Logic:** Soft delete — keep file on disk, mark as deleted in DB. Or hard delete both.

---

## Module 2: Wizard Session API (REPLACE existing wizard.py)

**File:** `wizard_routes.py` (completely replace `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`)
**Prefix:** `/api/v1/wizard`

The current wizard.py is a stub. Replace it with proper session-based wizard management.

### Database Tables Used
- `vetassist_wizard_sessions` (id, session_id uuid, wizard_type, veteran_id, current_step int, answers jsonb, status, created_at, completed_at, updated_at)
- `vetassist_wizard_files` (id, session_id, file_uuid, original_name, category, file_size, mime_type, file_path, deleted, deleted_at, created_at)

### Wizard Types
- `21-526EZ` — Application for Disability Compensation (new claim)
- `21-0995` — Decision Review Request: Supplemental Claim
- `20-0996` — Decision Review Request: Higher-Level Review
- `10182` — Decision Review Request: Board Appeal

### Endpoints

#### POST /api/v1/wizard/start
**Request:** `{"wizard_type": "21-526EZ", "veteran_id": "uuid"}`
**Response:** `{"session_id": "uuid", "wizard_type": "21-526EZ", "current_step": 1, "total_steps": 6}`
**Logic:** INSERT new session with UUID, status='active', current_step=1, answers='{}'

Steps for 21-526EZ:
1. Personal Information (pre-filled from user profile)
2. Service History
3. Conditions & Disabilities
4. Evidence Upload
5. Review & Confirm
6. Submit

#### GET /api/v1/wizard/{session_id}
**Response:**
```json
{
  "session_id": "uuid",
  "wizard_type": "21-526EZ",
  "current_step": 3,
  "total_steps": 6,
  "step_data": { ... answers for current step ... },
  "completed_steps": [1, 2],
  "status": "active"
}
```
**Logic:** SELECT from vetassist_wizard_sessions. Extract completed_steps from answers jsonb.

#### POST /api/v1/wizard/{session_id}/step/{step_number}
**Request:** `{"answers": {"condition_name": "PTSD", "onset_date": "2015-03-01"}}`
**Response:** `{"completed": false, "next_step": 4}`
**Logic:** UPDATE answers jsonb — merge step answers into existing answers object. Advance current_step.

#### POST /api/v1/wizard/{session_id}/upload
**Query param:** `category` (medical_records, service_records, nexus_letter, buddy_statement, other)
**Request:** FormData with `file`
**Response:** `{"file": {"id": "uuid", "original_name": "...", "category": "...", "file_size": 123456}}`
**Logic:** Save to `/ganuda/vetassist/uploads/wizard/{session_id}/{uuid}_{filename}`. INSERT into vetassist_wizard_files.

#### GET /api/v1/wizard/{session_id}/files
**Response:** `{"files": [...]}`

#### DELETE /api/v1/wizard/{session_id}/files/{file_id}
**Logic:** SET deleted = true, deleted_at = now()

#### POST /api/v1/wizard/{session_id}/complete
**Response:**
```json
{
  "session_id": "uuid",
  "wizard_type": "21-526EZ",
  "status": "completed",
  "form_data": { ... all answers merged ... },
  "files_count": 3,
  "next_steps": [
    "Review your completed form",
    "Download the pre-filled PDF",
    "Submit via eBenefits or mail"
  ]
}
```
**Logic:** UPDATE status='completed', completed_at=now(). Return aggregated data.

#### GET /api/v1/wizard/{session_id}/summary
Same response as complete but for retrieval.

#### GET /api/v1/wizard/{session_id}/export
**Response:** PDF file download (for Phase 2 — for now return JSON form data)

---

## Module 3: Content/Resources API

**File:** `content_routes.py`
**Prefix:** `/api/v1/content`

### Database Table Used
- `educational_content` (id varchar, title, slug, content_type, content text, summary, video_url, difficulty_level, estimated_read_time, tags text, view_count int, created_at, updated_at, is_published boolean)

### Endpoints

#### GET /api/v1/content
**Query params:** `limit` (default 50), `tag` (optional), `difficulty` (optional)
**Response:**
```json
{
  "items": [
    {
      "id": "ptsd-claims-guide",
      "title": "Understanding PTSD Claims",
      "slug": "ptsd-claims-guide",
      "content_type": "article",
      "summary": "A comprehensive guide...",
      "difficulty_level": "beginner",
      "estimated_read_time": 8,
      "tags": ["ptsd", "claims", "mental-health"],
      "view_count": 42,
      "created_at": "2026-01-15T00:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 50
}
```
**Logic:** SELECT from educational_content WHERE is_published = true. Filter by tag (LIKE on tags text field) and difficulty_level if provided. Don't return full content in list view — only summary.

#### GET /api/v1/content/search
**Query params:** `q` (search query), `limit` (default 50)
**Logic:** SELECT WHERE title ILIKE %q% OR content ILIKE %q% OR summary ILIKE %q%

#### GET /api/v1/content/tags/list
**Response:** `{"tags": [{"tag": "ptsd", "count": 5}, {"tag": "claims", "count": 12}]}`
**Logic:** Parse tags from all published content. The tags field is text (comma-separated). Split and aggregate.

#### GET /api/v1/content/{article_id}
**Response:** Full article object including content text
**Logic:** SELECT by id. INCREMENT view_count.

#### GET /api/v1/content/{article_id}/related
**Response:** `{"items": [... up to 3 related articles ...]}`
**Logic:** Find articles with overlapping tags. ORDER BY tag overlap count DESC LIMIT 3.

---

## Module 4: Research API

**File:** `research_routes.py`
**Prefix:** `/api/v1/research`

### Database Table Used
- `vetassist_research_results` (id, veteran_id, session_id, job_id, question, answer, sources jsonb, completed_at, created_at)

### Endpoints

#### POST /api/v1/research/trigger
**Request:**
```json
{
  "session_id": "dashboard-session-id",
  "question": "What evidence do I need for a PTSD increase?",
  "condition": "PTSD",
  "search_sources": ["va.gov", "38cfr", "bva_decisions"]
}
```
**Response:** `{"job_id": "uuid", "status": "pending"}`
**Logic:**
1. INSERT into vetassist_research_results with status info in sources jsonb
2. Call LLM Gateway with research prompt (or queue as Jr task)
3. Return job_id for polling

For MVP: Call LLM Gateway synchronously with RAG context. Store answer immediately.

#### GET /api/v1/research/results/{session_id}
**Response:**
```json
{
  "results": [
    {
      "research_id": "uuid",
      "question": "What evidence do I need for a PTSD increase?",
      "condition": "PTSD",
      "status": "completed",
      "summary": "To support a PTSD increase claim...",
      "full_result": { ... },
      "created_at": "2026-01-30T10:00:00Z",
      "completed_at": "2026-01-30T10:00:08Z"
    }
  ]
}
```
**Logic:** SELECT from vetassist_research_results WHERE session_id = ? ORDER BY created_at DESC

---

## Wire All Into main.py

Add these imports and include_router calls:

```python
from app.api.dashboard_routes import router as dashboard_router
from app.api.wizard_routes import router as wizard_router  # replaces old v1 wizard
from app.api.content_routes import router as content_router
from app.api.research_routes import router as research_router

app.include_router(dashboard_router)
app.include_router(wizard_router)
app.include_router(content_router)
app.include_router(research_router)
```

Remove the old wizard import:
```python
# REMOVE this line:
# from app.api.v1.endpoints.wizard import router as wizard_router
```

## File Upload Directory

Create on bluefin:
```bash
mkdir -p /ganuda/vetassist/uploads/wizard
mkdir -p /ganuda/vetassist/uploads/dashboard
chown -R dereadi:dereadi /ganuda/vetassist/uploads
```

## Dependencies

```bash
pip install python-multipart  # for file uploads in FastAPI
pip install aiofiles           # for async file operations
```

## Verification

```bash
# Dashboard
curl http://192.168.132.222:8001/api/v1/dashboard/<VETERAN_ID> \
  -H "Authorization: Bearer <TOKEN>"

# Start wizard
curl -X POST http://192.168.132.222:8001/api/v1/wizard/start \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"wizard_type":"21-526EZ","veteran_id":"<UUID>"}'

# Content list
curl http://192.168.132.222:8001/api/v1/content?limit=10

# Research trigger
curl -X POST http://192.168.132.222:8001/api/v1/research/trigger \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","question":"PTSD rating criteria","condition":"PTSD","search_sources":["38cfr"]}'
```
