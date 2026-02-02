# Jr Instruction: Fix VetAssist Circular Imports

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P0 (Blocking)
**Category:** Bug Fix
**From Review:** REVIEW-VETASSIST-20260126 - CRIT-002

---

## Problem

VetAssist backend is non-functional due to circular imports in the auth system.

Error chain:
1. `app/core/security.py` imports from auth endpoints
2. Auth endpoints import from security.py
3. Python fails at startup with ImportError

---

## Files to Modify

### `/ganuda/vetassist/backend/app/core/security.py`
- Should ONLY contain security utility functions
- NO imports from api/endpoints
- Functions needed: `decode_access_token`, `get_current_user`, `get_current_user_optional`

### `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`
- Should import FROM security.py
- NOT the other way around

### `/ganuda/vetassist/backend/app/services/auth_service.py`
- Imports `hash_password`, `verify_password` from security.py
- These functions don't exist - need to create them OR change imports

---

## Solution Steps

1. **Read current security.py** - Verify it has no circular imports
2. **Read auth_service.py** - Find the bad imports
3. **Create missing functions** in security.py:
   - `hash_password(password: str) -> str`
   - `verify_password(plain: str, hashed: str) -> bool`
4. **Verify no circular imports** - Each file should only import from lower-level modules
5. **Test startup** - `python -c "from app.main import app"`

---

## Do NOT

- Add new dependencies
- Change API contracts
- Modify database schema

---

## Success Criteria

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
python -c "from app.main import app; print('Import successful')"
```

Output: "Import successful"
