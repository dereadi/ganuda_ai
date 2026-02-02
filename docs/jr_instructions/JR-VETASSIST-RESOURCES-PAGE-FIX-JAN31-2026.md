# Jr Instruction: Fix VetAssist Resources Page Crash + Backend Tags Bug

**Task ID:** VETASSIST-RESOURCES-FIX-001
**Assigned To:** Software Engineer Jr
**Priority:** P0 — Page is down, user-facing
**Created:** January 31, 2026
**Depends On:** None
**Estimated Steps:** 4

---

## Objective

Fix the VetAssist resources page which is crashing with a client-side error. The page shows "Loading resources..." spinner that never resolves because React crashes when trying to call `.slice()` on null `tags` field.

---

## Root Cause

The `educational_content` table stores `tags` as a `text` column containing JSON-serialized arrays (e.g., `'["claims", "basics"]'`). The backend `to_dict()` method returns this raw string. The frontend TypeScript expects `tags: string[]` (a real array). When tags is null OR a string, calling `item.tags.slice(0, 3)` crashes React.

Additional null fields: `difficulty_level`, `estimated_read_time`, `view_count` are all nullable and the frontend doesn't guard against null.

---

## Steps

### Step 1: Fix backend tags serialization in content model

**File:** `/ganuda/vetassist/backend/app/models/content.py`

In the `to_dict()` method, the `tags` field must be deserialized from JSON string to a Python list before returning. Find the line that returns tags and wrap it:

```
<<<<<<< SEARCH
            'tags': self.tags,
=======
            'tags': json.loads(self.tags) if self.tags else [],
>>>>>>> REPLACE
```

Also add `import json` at the top of the file if not already present:

```
<<<<<<< SEARCH
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime
=======
import json
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime
>>>>>>> REPLACE
```

### Step 2: Fix backend default values in to_dict()

**File:** `/ganuda/vetassist/backend/app/models/content.py`

Ensure nullable fields return safe defaults:

```
<<<<<<< SEARCH
            'difficulty_level': self.difficulty_level,
            'estimated_read_time': self.estimated_read_time,
=======
            'difficulty_level': self.difficulty_level or 'beginner',
            'estimated_read_time': self.estimated_read_time or 5,
>>>>>>> REPLACE
```

And for view_count:

```
<<<<<<< SEARCH
            'view_count': self.view_count,
=======
            'view_count': self.view_count or 0,
>>>>>>> REPLACE
```

### Step 3: Fix frontend null safety in resources page

**File:** `/ganuda/vetassist/frontend/app/resources/page.tsx`

Even though the backend will now return safe defaults, add defensive null guards in the frontend:

**Line ~260-264** — Guard difficulty_level:
```
<<<<<<< SEARCH
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold border capitalize ${getDifficultyColor(
                        item.difficulty_level
                      )}`}
                    >
                      {item.difficulty_level}
                    </span>
=======
                    {item.difficulty_level && (
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold border capitalize ${getDifficultyColor(
                        item.difficulty_level
                      )}`}
                    >
                      {item.difficulty_level}
                    </span>
                    )}
>>>>>>> REPLACE
```

**Line ~266-268** — Guard estimated_read_time:
```
<<<<<<< SEARCH
                    <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-700 border border-gray-300">
                      {item.estimated_read_time} min read
                    </span>
=======
                    {item.estimated_read_time && (
                    <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-700 border border-gray-300">
                      {item.estimated_read_time} min read
                    </span>
                    )}
>>>>>>> REPLACE
```

**Line ~281** — Guard tags.slice():
```
<<<<<<< SEARCH
                    {item.tags.slice(0, 3).map((tag) => (
=======
                    {(Array.isArray(item.tags) ? item.tags : []).slice(0, 3).map((tag) => (
>>>>>>> REPLACE
```

**Line ~289** — Guard tags.length:
```
<<<<<<< SEARCH
                    {item.tags.length > 3 && (
=======
                    {Array.isArray(item.tags) && item.tags.length > 3 && (
>>>>>>> REPLACE
```

**Line ~298** — Guard view_count:
```
<<<<<<< SEARCH
                    <span>{item.view_count} views</span>
=======
                    <span>{item.view_count || 0} views</span>
>>>>>>> REPLACE
```

### Step 4: Rebuild frontend and restart backend

```bash
# Restart backend to pick up model changes
sudo systemctl restart vetassist-backend

# Rebuild frontend
cd /ganuda/vetassist/frontend
npm run build
cp -r .next/static .next/standalone/.next/static
pkill -f 'next-server' || true
sleep 2
cd /ganuda/vetassist/frontend && nohup npm start -- -p 3000 > /ganuda/logs/vetassist_frontend.log 2>&1 &

# Verify backend health
curl -s http://localhost:8001/health

# Verify content endpoint returns tags as array
curl -s http://localhost:8001/api/v1/content?limit=1 | python3 -m json.tool | head -20
```

---

## Success Criteria

- Backend `/api/v1/content` returns `tags` as a JSON array (not a string)
- Backend returns safe defaults for `difficulty_level`, `estimated_read_time`, `view_count`
- Frontend resources page loads without crashing, even with null/missing fields
- Page shows articles (or "No articles found" message) instead of stuck spinner

---

## Security Notes

- No new credentials or endpoints
- No PII changes
- Frontend changes are display-only null guards
