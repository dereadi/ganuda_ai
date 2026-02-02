# JR-VETASSIST-DASHBOARD-AUTH-FIX-JAN30-2026
## Fix Dashboard Components to Send Auth Tokens

**Priority:** P0 - Blocking user testing
**Target Node:** redfin (frontend build) + bluefin (backend verification)
**Bug Report:** User logged in as Marcus, dashboard loads, note saves, but file upload shows "Not Found" in red

### Root Cause Analysis

The dashboard page (`app/dashboard/page.tsx`) correctly uses `useAuth()` and sends JWT tokens in its own fetch call. However, the child components use **raw `fetch()` without Authorization headers**:

| Component | File | API Call | Auth Header |
|-----------|------|----------|-------------|
| Dashboard page | `app/dashboard/page.tsx:67` | GET `/dashboard/{id}` | YES (Bearer token) |
| FileDropZone | `components/dashboard/FileDropZone.tsx:60` | POST `/dashboard/{id}/files` | **NO** |
| FileDropZone | `components/dashboard/FileDropZone.tsx:90` | DELETE `/dashboard/{id}/files/{fid}` | **NO** |
| ScratchpadEditor | `components/dashboard/ScratchpadEditor.tsx:24` | PUT `/dashboard/{id}/scratchpad` | **NO** |
| ResearchPanel | `components/dashboard/ResearchPanel.tsx:37` | GET `/research/results/{id}` | **NO** |
| ResearchPanel | `components/dashboard/ResearchPanel.tsx:65` | POST `/research/trigger` | **NO** |

Without the Authorization header, the bluefin v2.0 backend returns `401 Not authenticated`. If requests somehow reach the redfin v1.0 backend (localhost:8001), it returns `404 Not Found` because the dashboard file endpoints don't exist in v1.0.

### Secondary Issue: Dual Backend Conflict

There is an OLD v1.0 backend running on redfin (port 8001):
```
vetassist-backend.service → /ganuda/vetassist/backend/venv/bin/python -m uvicorn app.main:app --port 8001
Version: 1.0.0 | Using: /ganuda/vetassist/backend/venv/ | RAM: 1GB
```

The NEW v2.0 backend runs on bluefin (port 8001):
```
Version: 2.0.0 | Using: /home/dereadi/cherokee_venv/ | RAM: varies
Has all 39 endpoints including dashboard, auth, calculator, chat, wizard, etc.
```

Caddy on redfin correctly proxies `/api/*` to `192.168.132.222:8001` (bluefin). The redfin backend is NOT used by Caddy but wastes 1GB RAM.

### Fix 1: Add Auth Headers to Dashboard Components

Each component needs to read the JWT from localStorage and include it in all fetch calls.

**Option A (Recommended): Pass token as prop from dashboard page**

In `app/dashboard/page.tsx`, the token is already available:
```typescript
const token = localStorage.getItem('auth_token');
```

Pass it to child components:
```typescript
<FileDropZone veteranId={veteranId} existingFiles={data?.files || []} authToken={token} />
<ScratchpadEditor veteranId={veteranId} initialContent={...} authToken={token} />
<ResearchPanel sessionId={veteranId} veteranId={veteranId} authToken={token} />
```

**Option B: Read token directly in each component**

Each component reads `localStorage.getItem('auth_token')` and adds to fetch:
```typescript
const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
```

### Fix 2: FileDropZone.tsx Changes

File: `/ganuda/vetassist/frontend/components/dashboard/FileDropZone.tsx`

**Add `authToken` prop:**
```typescript
interface FileDropZoneProps {
  veteranId: string;
  authToken?: string | null;   // ADD THIS
  onUploadComplete?: (file: UploadedFile) => void;
  existingFiles?: UploadedFile[];
}
```

**Update upload fetch (line 60):**
```typescript
// BEFORE:
const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files`, {
  method: 'POST',
  body: formData,
});

// AFTER:
const token = authToken || localStorage.getItem('auth_token');
const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files`, {
  method: 'POST',
  headers: {
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  },
  body: formData,
  // NOTE: Do NOT set Content-Type for FormData — browser sets it with boundary
});
```

**Update delete fetch (line 90):**
```typescript
// BEFORE:
const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files/${fileId}`, {
  method: 'DELETE',
});

// AFTER:
const token = authToken || localStorage.getItem('auth_token');
const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files/${fileId}`, {
  method: 'DELETE',
  headers: {
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  },
});
```

### Fix 3: ScratchpadEditor.tsx Changes

File: `/ganuda/vetassist/frontend/components/dashboard/ScratchpadEditor.tsx`

**Add `authToken` prop and update fetch (line 24):**
```typescript
// BEFORE:
const response = await fetch(`${apiUrl}/dashboard/${veteranId}/scratchpad`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ content: textContent }),
});

// AFTER:
const token = authToken || localStorage.getItem('auth_token');
const response = await fetch(`${apiUrl}/dashboard/${veteranId}/scratchpad`, {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  },
  body: JSON.stringify({ content: textContent }),
});
```

### Fix 4: ResearchPanel.tsx Changes

File: `/ganuda/vetassist/frontend/components/dashboard/ResearchPanel.tsx`

**Update both fetch calls (lines 37 and 65) to include auth headers:**

```typescript
const token = authToken || localStorage.getItem('auth_token');

// GET results (line 37):
const response = await fetch(`${apiUrl}/research/results/${sessionId}`, {
  headers: {
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  },
});

// POST trigger (line 65):
const response = await fetch(`${apiUrl}/research/trigger`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  },
  body: JSON.stringify({...}),
});
```

### Fix 5: Stop Old Backend on Redfin

On redfin, the old v1.0 backend is wasting 1GB RAM:
```bash
sudo systemctl stop vetassist-backend
sudo systemctl disable vetassist-backend
```

This prevents any accidental routing to the old backend and frees 1GB RAM for the GPU inference workloads.

### After Changes

Rebuild the frontend on redfin:
```bash
cd /ganuda/vetassist/frontend
npm run build
# Restart Next.js (kill old process, start new one)
kill $(pgrep -f 'next-server')
nohup npm start -- -p 3000 > /ganuda/logs/vetassist_frontend.log 2>&1 &
```

### Verification

1. Login at `/login` with Marcus (test1@vetassist.test)
2. Navigate to `/dashboard`
3. Try uploading a file in Evidence Files — should succeed (not "Not Found")
4. Edit scratchpad and wait for auto-save — should show green checkmark
5. Submit a research question — should submit without error
6. Check browser DevTools Network tab — all `/api/v1/` requests should have `Authorization: Bearer ...` header

### Files Modified

| File | Change |
|------|--------|
| `app/dashboard/page.tsx` | Pass `authToken` prop to child components |
| `components/dashboard/FileDropZone.tsx` | Add authToken prop, include Bearer header in upload/delete |
| `components/dashboard/ScratchpadEditor.tsx` | Add authToken prop, include Bearer header in save |
| `components/dashboard/ResearchPanel.tsx` | Add authToken prop, include Bearer header in fetch/trigger |
