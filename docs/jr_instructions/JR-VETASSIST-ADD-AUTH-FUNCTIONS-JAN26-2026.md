# Jr Instruction: Add Missing Auth Functions to VetAssist security.py

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P0
**Category:** Bug Fix

---

## Problem

`/ganuda/vetassist/backend/app/core/security.py` is missing three authentication functions that other modules depend on.

---

## Functions to Add

Append the following functions to the END of `/ganuda/vetassist/backend/app/core/security.py`:

```python
async def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode JWT access token.
    Returns payload if valid, otherwise None.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        return None

async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """
    Get current user from JWT token if present.
    Returns None if no token (allows anonymous access).
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]
    payload = await decode_access_token(token)
    if not payload:
        return None

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email")
    }

async def get_current_user(
    authorization: str = Header(..., description="JWT token")
) -> dict:
    """
    Get current user from JWT token.
    Raises HTTPException if token is invalid or missing.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]
    payload = await decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email")
    }
```

---

## Implementation

Use cat to append the functions:

```bash
cat >> /ganuda/vetassist/backend/app/core/security.py << 'ENDOFFILE'

async def decode_access_token(token: str) -> Optional[dict]:
    """Decode JWT access token. Returns payload if valid, otherwise None."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        return None

async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """Get current user from JWT token if present. Returns None if no token."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    payload = await decode_access_token(token)
    if not payload:
        return None
    return {"user_id": payload.get("sub"), "email": payload.get("email")}

async def get_current_user(
    authorization: str = Header(..., description="JWT token")
) -> dict:
    """Get current user from JWT token. Raises HTTPException if invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ")[1]
    payload = await decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user_id": payload.get("sub"), "email": payload.get("email")}
ENDOFFILE
```

---

## Verify

```bash
grep -c "def.*get_current_user" /ganuda/vetassist/backend/app/core/security.py
```

Should return: 2 (for get_current_user_optional and get_current_user)
