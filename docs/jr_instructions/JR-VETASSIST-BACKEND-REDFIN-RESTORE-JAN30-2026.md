# JR-VETASSIST-BACKEND-REDFIN-RESTORE-JAN30-2026
## Restore Backend to Redfin + Add Missing Endpoints + Fix Frontend Auth

**Priority:** P0 - Blocking all user testing
**Target Node:** redfin (backend + frontend)
**Estimated Scope:** 3 files modified, 1 Caddy config revert, 1 frontend rebuild

### Background

The VetAssist backend v1.0 runs on redfin alongside the frontend. During a previous session, a v2.0 backend was built on bluefin with additional endpoints. Caddy was changed to proxy API calls to bluefin:8001 instead of localhost:8001.

This is wrong. The backend belongs on redfin with the frontend. The v1.0 codebase is mature (auth, rate limiting, config, CORS, 20+ endpoint modules) — it just needs 2 missing endpoints added. We should NOT replace v1.0 with v2.0.

### What's Working (v1.0 on redfin)

- Auth (register, login, logout, profile) via `python-jose` + `passlib`
- Calculator (combined rating calculation)
- Chat (LLM Gateway integration)
- Dashboard GET `/{veteran_id}` — loads scratchpad, files, claims, research
- Dashboard PUT `/{veteran_id}/scratchpad` — auto-save scratchpad
- Dashboard GET `/claims` — list user claims
- Dashboard GET `/stats` — aggregate stats
- Dashboard DELETE `/claims/{session_id}` — soft delete
- Wizard (session-based form filling)
- Research, Content, Evidence, RAG, Documents, Conditions, Claims
- Proper config via `.env` + pydantic Settings
- Rate limiting via slowapi
- CORS configured for vetassist.ganuda.us

### What's MISSING (causes "Not Found")

The dashboard page's FileDropZone calls two endpoints that don't exist in v1.0:

1. `POST /api/v1/dashboard/{veteran_id}/files` — upload evidence file
2. `DELETE /api/v1/dashboard/{veteran_id}/files/{file_id}` — delete evidence file

### Task 1: Add File Upload/Delete to Dashboard (Backend)

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`

Add these imports at the top (after existing imports):
```python
import os
import uuid
import shutil
from fastapi import UploadFile, File as FastAPIFile, Form
from app.core.config import settings
```

Add these two endpoints at the end of the file (before or after `delete_claim`):

```python
@router.post("/{veteran_id}/files")
async def upload_file(
    veteran_id: str,
    file: UploadFile = FastAPIFile(...),
    category: str = Form(default="other"),
    description: str = Form(default=""),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload an evidence file for a veteran's dashboard.
    Files are stored on disk and metadata saved to vetassist_wizard_files table.
    Max size: 25MB. Allowed types: PDF, JPEG, PNG, TIFF, GIF.
    """
    # Validate file size (25MB limit)
    MAX_SIZE = 25 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is 25MB.")

    # Validate file type
    allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff', 'image/gif']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed. Use PDF or image files.")

    # Generate unique filename
    ext = os.path.splitext(file.filename or "file")[1] or ".bin"
    stored_name = f"{uuid.uuid4()}{ext}"

    # Create upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, veteran_id)
    os.makedirs(upload_dir, exist_ok=True)

    # Save file to disk
    file_path = os.path.join(upload_dir, stored_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # Save metadata to database
    # Uses vetassist_wizard_files table (same table the dashboard GET reads from)
    # If no wizard session exists for direct uploads, create a "dashboard" pseudo-session
    try:
        conn = get_db_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Ensure a dashboard pseudo-session exists for direct uploads
            dashboard_session_id = f"dashboard-{veteran_id}"
            cur.execute("""
                INSERT INTO vetassist_wizard_sessions (session_id, veteran_id, wizard_type, status, current_step, answers)
                VALUES (%s, %s, 'dashboard', 'active', 0, '{}')
                ON CONFLICT (session_id) DO NOTHING
            """, (dashboard_session_id, veteran_id))

            # Insert file record
            cur.execute("""
                INSERT INTO vetassist_wizard_files
                    (session_id, original_name, stored_name, mime_type, file_size, category, file_path, deleted)
                VALUES (%s, %s, %s, %s, %s, %s, %s, false)
                RETURNING id, original_name as filename, mime_type as file_type, category,
                          created_at as uploaded_at, file_size
            """, (
                dashboard_session_id,
                file.filename,
                stored_name,
                file.content_type,
                len(content),
                category,
                file_path
            ))
            result = cur.fetchone()
            conn.commit()

        # Serialize datetime for JSON
        file_data = dict(result)
        if file_data.get('uploaded_at'):
            file_data['uploaded_at'] = str(file_data['uploaded_at'])

        return {"status": "uploaded", "file": file_data}
    except Exception as e:
        # Clean up file on database error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to save file metadata: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass


@router.delete("/{veteran_id}/files/{file_id}")
def delete_file(
    veteran_id: str,
    file_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Soft-delete an evidence file from the dashboard.
    Sets deleted=true in database. File remains on disk for recovery.
    """
    try:
        conn = get_db_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verify file belongs to this veteran (through session)
            cur.execute("""
                SELECT f.id, f.file_path
                FROM vetassist_wizard_files f
                INNER JOIN vetassist_wizard_sessions s ON f.session_id::text = s.session_id::text
                WHERE f.id = %s AND s.veteran_id = %s AND NOT f.deleted
            """, (file_id, veteran_id))
            file_record = cur.fetchone()

            if not file_record:
                raise HTTPException(status_code=404, detail="File not found")

            # Soft delete
            cur.execute("""
                UPDATE vetassist_wizard_files SET deleted = true WHERE id = %s
            """, (file_id,))
            conn.commit()

        return {"status": "deleted", "file_id": file_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass
```

Also ensure the upload directory exists:
```bash
sudo mkdir -p /ganuda/vetassist/uploads
sudo chown dereadi:dereadi /ganuda/vetassist/uploads
```

### Task 2: Revert Caddy Back to localhost:8001

File: `/etc/caddy/Caddyfile` on redfin

Change:
```
handle /api/* {
    reverse_proxy 192.168.132.222:8001
}
```

Back to:
```
handle /api/* {
    reverse_proxy localhost:8001
}
```

Then reload:
```bash
sudo systemctl reload caddy
```

### Task 3: Fix Frontend Dashboard Components Auth Headers

The dashboard child components use raw `fetch()` without Authorization headers. All three need the JWT token.

**File: `/ganuda/vetassist/frontend/components/dashboard/FileDropZone.tsx`**

Change the `onDrop` upload fetch (~line 59-63):
```typescript
// BEFORE:
const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files`, {
  method: 'POST',
  body: formData,
});

// AFTER:
const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files`, {
  method: 'POST',
  headers: {
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  },
  body: formData,
  // Do NOT set Content-Type — browser auto-sets multipart boundary for FormData
});
```

Change the `deleteFile` fetch (~line 88-92):
```typescript
// BEFORE:
const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files/${fileId}`, {
  method: 'DELETE',
});

// AFTER:
const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files/${fileId}`, {
  method: 'DELETE',
  headers: {
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  },
});
```

**File: `/ganuda/vetassist/frontend/components/dashboard/ScratchpadEditor.tsx`**

Change the `saveContent` fetch (~line 23-28):
```typescript
// BEFORE:
const response = await fetch(`${apiUrl}/dashboard/${veteranId}/scratchpad`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ content: textContent }),
});

// AFTER:
const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
const response = await fetch(`${apiUrl}/dashboard/${veteranId}/scratchpad`, {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  },
  body: JSON.stringify({ content: textContent }),
});
```

**File: `/ganuda/vetassist/frontend/components/dashboard/ResearchPanel.tsx`**

Change the `fetchResults` fetch (~line 36-38):
```typescript
// BEFORE:
const response = await fetch(`${apiUrl}/research/results/${sessionId}`);

// AFTER:
const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
const response = await fetch(`${apiUrl}/research/results/${sessionId}`, {
  headers: {
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  },
});
```

Change the `handleSubmit` fetch (~line 65-69):
```typescript
// BEFORE:
const response = await fetch(`${apiUrl}/research/trigger`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({...})
});

// AFTER:
const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
const response = await fetch(`${apiUrl}/research/trigger`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  },
  body: JSON.stringify({...})
});
```

### Task 4: Rebuild Frontend + Restart Backend

```bash
# 1. Restart backend with new endpoints
sudo systemctl restart vetassist-backend

# 2. Verify backend has file upload endpoint
curl -s http://localhost:8001/api/docs | grep -c "files"
# Should find the new endpoints in the Swagger docs

# 3. Rebuild frontend
cd /ganuda/vetassist/frontend
npm run build

# 4. Restart frontend
kill $(pgrep -f 'next-server')
nohup npm start -- -p 3000 > /ganuda/logs/vetassist_frontend.log 2>&1 &

# 5. Verify through Caddy
curl -sk --resolve vetassist.ganuda.us:443:127.0.0.1 https://vetassist.ganuda.us/health
# Should return v1.0.0 from redfin
```

### Task 5: Stop Bluefin v2.0 Backend (Cleanup)

On bluefin, the v2.0 backend was running as a nohup process:
```bash
# On bluefin - kill the v2.0 process
pkill -f "python.*main.*8001"
# Or find PID: ps aux | grep 8001
```

The v2.0 code on bluefin can stay as reference but should not serve traffic.

### Verification Checklist

- [ ] `curl http://localhost:8001/health` returns v1.0.0 from redfin
- [ ] `curl -sk --resolve vetassist.ganuda.us:443:127.0.0.1 https://vetassist.ganuda.us/health` returns from redfin
- [ ] Login as Marcus at `/login`
- [ ] Dashboard loads with greeting "Welcome back, Marcus"
- [ ] Scratchpad auto-saves (green checkmark appears)
- [ ] File upload works — select a PDF, see it appear in Evidence Files
- [ ] File delete works — click X on a file, it disappears
- [ ] Research question submits without error
- [ ] Browser DevTools Network tab shows `Authorization: Bearer ...` on all API calls

### Architecture After Fix

```
Browser → vetassist.ganuda.us → Caddy (redfin:443)
  → /api/*  → localhost:8001 (redfin v1.0 backend)  ← ALL API traffic
  → /*      → localhost:3000 (redfin Next.js frontend)

Backend → 192.168.132.222:5432 (bluefin PostgreSQL)  ← Database connection
Backend → 192.168.132.223:8080 (redfin LLM Gateway)  ← AI inference
```

Everything on one node. No cross-node proxy for API calls.

### Files Modified

| File | Node | Change |
|------|------|--------|
| `app/api/v1/endpoints/dashboard.py` | redfin | Add POST files + DELETE files endpoints |
| `/etc/caddy/Caddyfile` | redfin | Revert `/api/*` proxy to `localhost:8001` |
| `components/dashboard/FileDropZone.tsx` | redfin | Add Authorization header to upload/delete |
| `components/dashboard/ScratchpadEditor.tsx` | redfin | Add Authorization header to save |
| `components/dashboard/ResearchPanel.tsx` | redfin | Add Authorization header to fetch/trigger |

### Why NOT Replace v1.0 With v2.0

The v2.0 on bluefin was built as a parallel implementation using different libraries (`pyjwt` vs `python-jose`, raw `bcrypt` vs `passlib`, raw psycopg2 vs config-managed connections). Replacing v1.0 would:
- Break the existing auth system (different JWT library, different secret key)
- Lose rate limiting, proper error handling, config management
- Require re-registering all users (different password hashing)
- Introduce unnecessary risk to a working codebase

The v1.0 just needs 2 endpoints added. Ship the smallest change.
