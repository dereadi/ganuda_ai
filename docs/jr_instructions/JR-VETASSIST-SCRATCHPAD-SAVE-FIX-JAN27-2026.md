# JR Instruction: VetAssist Scratchpad Save Fix

**JR ID:** JR-VETASSIST-SCRATCHPAD-SAVE-FIX-JAN27-2026
**Priority:** P2 - User-Facing Bug
**Assigned To:** Software Engineer Jr.
**Ultrathink:** ULTRATHINK-VETASSIST-EXECUTOR-BUGS-JAN27-2026.md

---

## Problem Statement

VetAssist scratchpad/notes are not being saved. Users type notes and they disappear on refresh.

**Root Cause:**
1. PUT endpoint for saving scratchpad is missing from current dashboard.py
2. Table name mismatch between read and write operations
3. Missing Pydantic model for scratchpad update

---

## Task 1: Add Pydantic Model for Scratchpad

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`

Add this import at the top (after existing imports, around line 5):

```python
from typing import List, Optional
```

Add this Pydantic model after the existing models (after `DashboardStats` class, around line 36):

```python
class ScratchpadUpdate(BaseModel):
    content: str
```

---

## Task 2: Standardize Table Name

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`

The current code queries `vetassist_scratchpads` but we need to use `vetassist_scratchpads` consistently. Update the read query (around line 76-86) to use consistent naming:

```python
            # Try to get scratchpad (table may not exist)
            try:
                cur.execute("""
                    SELECT content, updated_at as last_updated
                    FROM vetassist_scratchpads
                    WHERE veteran_id = %s
                """, (veteran_id,))
                scratchpad_row = cur.fetchone()
                if scratchpad_row:
                    scratchpad = {
                        "content": scratchpad_row["content"] or "",
                        "last_updated": str(scratchpad_row["last_updated"]) if scratchpad_row["last_updated"] else None
                    }
            except Exception:
                conn.rollback()  # Reset transaction state for next query
```

---

## Task 3: Add PUT Endpoint for Scratchpad Save

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`

Add this endpoint after the `get_dashboard_data` function (around line 152, before `list_user_claims`):

```python
@router.put("/{veteran_id}/scratchpad")
def update_scratchpad(veteran_id: str, data: ScratchpadUpdate, current_user: dict = Depends(get_current_user)):
    """
    Auto-save scratchpad content for a veteran.

    This endpoint supports auto-save functionality from the frontend.
    Content is upserted (inserted or updated) based on veteran_id.
    """
    try:
        conn = get_db_conn()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO vetassist_scratchpads (veteran_id, content, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (veteran_id)
                DO UPDATE SET content = EXCLUDED.content, updated_at = NOW()
                RETURNING veteran_id, content, updated_at
            """, (veteran_id, data.content))
            result = cur.fetchone()
            conn.commit()

        return {
            "status": "saved",
            "veteran_id": result['veteran_id'],
            "last_updated": result['updated_at'].isoformat() if result['updated_at'] else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save scratchpad: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass
```

---

## Task 4: Create Database Table Migration

**File:** `/ganuda/sql/vetassist_scratchpads_migration.sql`

Create this migration file:

```sql
-- VetAssist Scratchpads Table Migration
-- JR: JR-VETASSIST-SCRATCHPAD-SAVE-FIX-JAN27-2026
-- Date: 2026-01-27

-- Create scratchpads table if not exists
CREATE TABLE IF NOT EXISTS vetassist_scratchpads (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(128) NOT NULL UNIQUE,
    content TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index on veteran_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_vetassist_scratchpads_veteran_id
ON vetassist_scratchpads(veteran_id);

-- Add comment for documentation
COMMENT ON TABLE vetassist_scratchpads IS 'VetAssist user scratchpad/notes storage - auto-saved from frontend';
```

Run on bluefin:
```bash
psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/sql/vetassist_scratchpads_migration.sql
```

---

## Task 5: Add HTTPException Import (if missing)

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`

Ensure this import exists at the top:

```python
from fastapi import APIRouter, Depends, HTTPException
```

---

## Complete File Reference

After all changes, the top of dashboard.py should look like:

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import json
from psycopg2.extras import RealDictCursor

from app.core.database_config import get_db_connection
from app.core.security import get_current_user
from app.api.v1.endpoints.wizard import WIZARD_FORMS

router = APIRouter(tags=["dashboard"])

# Alias for compatibility
def get_db_conn():
    return get_db_connection()

class ClaimSummary(BaseModel):
    session_id: str
    wizard_type: str
    form_name: str
    status: str
    current_step: int
    total_steps: int
    created_at: datetime
    updated_at: Optional[datetime]
    conditions_count: int = 0
    files_count: int = 0

class DashboardStats(BaseModel):
    total_claims: int
    active_claims: int
    completed_claims: int
    total_conditions: int
    total_files: int

class ScratchpadUpdate(BaseModel):
    content: str
```

---

## Verification Steps

1. **Run database migration:**
   ```bash
   psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT * FROM vetassist_scratchpads LIMIT 1;"
   ```

2. **Restart VetAssist backend:**
   ```bash
   sudo systemctl restart vetassist-backend
   # or if running manually:
   # kill the uvicorn process and restart
   ```

3. **Test scratchpad save via curl:**
   ```bash
   curl -X PUT http://192.168.132.223:8001/api/v1/dashboard/test-veteran-123/scratchpad \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <token>" \
     -d '{"content": "Test note from curl"}'
   ```

4. **Verify in database:**
   ```bash
   psql -h 192.168.132.222 -U claude -d zammad_production -c \
     "SELECT * FROM vetassist_scratchpads WHERE veteran_id = 'test-veteran-123';"
   ```

5. **Test in UI:**
   - Log in as veteran
   - Type notes in scratchpad
   - Refresh page
   - Verify notes persist

---

## Frontend Considerations

The frontend should call this endpoint on:
- Debounced input (e.g., 1 second after user stops typing)
- Page unload / beforeunload event

Example frontend call:
```typescript
const saveScratchpad = async (content: string) => {
  await fetch(`/api/v1/dashboard/${veteranId}/scratchpad`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ content })
  });
};
```

---

## Rollback Plan

If issues occur:
```bash
# Restore from backup
cp /ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py.backup_20260119_211848 \
   /ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py

# Restart service
sudo systemctl restart vetassist-backend
```

---

## KB Article Reference

After completion, create: KB-VETASSIST-SCRATCHPAD-IMPLEMENTATION-JAN27-2026

---

FOR SEVEN GENERATIONS
