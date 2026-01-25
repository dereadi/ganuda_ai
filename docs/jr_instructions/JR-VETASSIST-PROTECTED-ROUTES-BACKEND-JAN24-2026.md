# Jr Instruction: VetAssist Protected Routes - Backend

**Task ID:** VETASSIST-PROTECTED-BACKEND
**Priority:** P1
**Date:** January 24, 2026
**Phase:** Auth Hardening (2 of 3)

## Objective

Add authentication dependency to sensitive backend endpoints (wizard, dashboard).

## Files to Modify (3 files)

1. `/ganuda/vetassist/backend/app/core/security.py`
2. `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`
3. `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`

## Required Changes

### 1. security.py - Add `get_current_user_optional`

Add this function after `decode_access_token`:

```python
from fastapi import Request, Header, Depends, HTTPException, status
from typing import Optional

async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """
    Get current user from JWT token if present.
    Returns None if no token (allows anonymous access).
    Use for endpoints that work both authenticated and unauthenticated.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        return None

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email")
    }
```

### 2. wizard.py - Add auth requirement

**Remove hardcoded DB_CONFIG** and use centralized config:

```python
# REMOVE:
DB_CONFIG = {
    "host": "192.168.132.222",
    ...
    "password": "jawaseatlasers2"
}

# ADD at top:
from app.core.database_config import get_db_connection, get_dict_cursor
from app.api.v1.endpoints.auth import get_current_user
from fastapi import Depends

# Replace get_db_conn():
def get_db_conn():
    return get_db_connection()
```

**Add auth to start_wizard endpoint:**
```python
@router.post("/start", status_code=status.HTTP_201_CREATED)
def start_wizard(
    request: WizardStartRequest,
    current_user = Depends(get_current_user)
):
    """Start a new wizard session"""
    # Use current_user.id instead of request.veteran_id if not provided
    veteran_id = request.veteran_id or str(current_user.id)
    ...
```

### 3. dashboard.py - Fix imports and auth

**Add missing imports:**
```python
from psycopg2.extras import RealDictCursor
from app.core.database_config import get_db_connection

# Add WIZARD_FORMS import
from .wizard import WIZARD_FORMS

def get_db_conn():
    return get_db_connection()
```

**Update get_current_user usage:**

The dashboard already uses `get_current_user`, but we need to extract user_id properly:

```python
@router.get("/claims", response_model=List[ClaimSummary])
def list_user_claims(
    status: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    user_id = str(current_user.id)  # Extract user ID from user object
    ...
```

## Output

Generate each modified file completely.

## Success Criteria

- [ ] No hardcoded passwords in wizard.py
- [ ] Wizard endpoints require authentication
- [ ] Dashboard imports are fixed
- [ ] All endpoints use centralized database config
