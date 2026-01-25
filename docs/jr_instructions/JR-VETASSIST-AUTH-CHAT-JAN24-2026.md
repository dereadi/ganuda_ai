# Jr Instruction: VetAssist Chat Auth Integration

**Task ID:** VETASSIST-AUTH-CHAT
**Priority:** P1
**Date:** January 24, 2026
**Phase:** Auth Hardening (1 of 3)

## Objective

Remove hardcoded user ID from chat endpoint. Get user from JWT session.

## Files to Modify (2 files)

1. `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

## Current Problem

```python
# BAD - hardcoded user
user_id = "demo-user"
```

## Required Changes

### chat.py

1. **Add auth import at top:**
```python
from fastapi import Depends
from app.core.security import get_current_user_optional
```

2. **Update endpoint signature:**
```python
@router.post("/message")
async def send_message(
    message: ChatMessage,
    current_user: dict = Depends(get_current_user_optional)
):
```

3. **Get user_id from session:**
```python
# Get user from session, fallback to anonymous for unauthenticated
user_id = current_user.get("user_id") if current_user else f"anon-{request.client.host}"
```

4. **If no security.py exists, create minimal version:**
```python
# /ganuda/vetassist/backend/app/core/security.py
from fastapi import Request, HTTPException
from typing import Optional
import jwt

SECRET_KEY = "your-secret-key"  # TODO: Move to env

async def get_current_user_optional(request: Request) -> Optional[dict]:
    """Get current user from JWT token if present. Returns None if no token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"user_id": payload.get("sub"), "email": payload.get("email")}
    except jwt.PyJWTError:
        return None
```

## Output

Generate the complete modified chat.py file.

## Success Criteria

- [ ] No hardcoded "demo-user" string
- [ ] User ID from JWT or anonymous fallback
- [ ] Existing chat functionality preserved
