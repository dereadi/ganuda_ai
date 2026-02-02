# JR-VETASSIST-VA-LINKING-PHASE2-LINK-ENDPOINT-JAN31-2026

## Metadata
- **Priority:** P1
- **Jr Type:** Engineering
- **Target Node:** sasass2 (192.168.132.200)
- **Category:** VetAssist — VA Account Linking Phase 2 (Backend Endpoint)
- **Depends On:** JR-VETASSIST-VA-LINKING-PHASE1-MODEL-FIX-JAN31-2026
- **Council Vote:** ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026

## Objective

Add the `POST /auth/link-va` endpoint and supporting schema. This endpoint lets an authenticated email-based user link their VA.gov account by providing a VA session JWT.

## Pre-Flight Check

```bash
python3 -c "
import jwt
print('PASS: PyJWT is available')
"
```

## Step 1: Add VALinkRequest Schema

**File:** `/ganuda/vetassist/backend/app/schemas/auth.py`

<<<<<<< SEARCH
class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
=======
class VALinkRequest(BaseModel):
    """Schema for VA account linking request"""
    va_session_token: str


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
>>>>>>> REPLACE

## Step 2: Add va_linked to UserResponse Schema

**File:** `/ganuda/vetassist/backend/app/schemas/auth.py`

<<<<<<< SEARCH
    email_verified: bool
    is_active: bool

    class Config:
        from_attributes = True
=======
    email_verified: bool
    is_active: bool
    va_linked: bool = False
    va_linked_at: Optional[str] = None

    class Config:
        from_attributes = True
>>>>>>> REPLACE

## Step 3: Add Imports to auth.py

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`

<<<<<<< SEARCH
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    UserProfileUpdate,
    MessageResponse
)
=======
from app.services.auth_service import AuthService
from app.models.user import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    UserProfileUpdate,
    MessageResponse,
    VALinkRequest
)
>>>>>>> REPLACE

## Step 4: Add POST /auth/link-va Endpoint

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`

<<<<<<< SEARCH
@router.post("/logout", response_model=MessageResponse)
async def logout(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
=======
@router.post("/link-va", response_model=UserResponse)
@limiter.limit("2/minute")
async def link_va_account(
    request: Request,
    link_data: VALinkRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Link a VA.gov account to the current email-based account.
    Requires active email-based authentication.
    """
    import jwt
    import os
    import hashlib
    import logging
    from datetime import datetime, timezone

    va_jwt_secret = os.getenv("VETASSIST_JWT_SECRET", "vetassist-jwt-secret-change-me")

    # Decode VA JWT to extract ICN
    try:
        va_payload = jwt.decode(link_data.va_session_token, va_jwt_secret, algorithms=["HS256"])
        va_icn = va_payload.get("va_icn")
        if not va_icn:
            raise HTTPException(status_code=400, detail="VA token missing ICN")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="VA session token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid VA session token")

    # Check ICN not already linked to another user
    existing = db.query(User).filter(User.va_icn == va_icn, User.id != current_user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="This VA account is already linked to another user")

    # Check caller not already linked to a different ICN
    if current_user.va_icn and current_user.va_icn != va_icn:
        raise HTTPException(status_code=409, detail="Your account is already linked to a different VA account")

    # Link the account
    current_user.va_icn = va_icn
    current_user.va_linked_at = datetime.now(timezone.utc)
    current_user.veteran_status = True

    # Backfill name from VA claims if local fields are empty
    va_first = va_payload.get("first_name")
    va_last = va_payload.get("last_name")
    if va_first and not current_user.first_name:
        current_user.first_name = va_first
    if va_last and not current_user.last_name:
        current_user.last_name = va_last

    db.commit()
    db.refresh(current_user)

    # Log linking event (truncated ICN hash for PII safety)
    icn_hash = hashlib.sha256(va_icn.encode()).hexdigest()[:12]
    logging.getLogger(__name__).info(f"[VA Link] User {current_user.id} linked to ICN hash {icn_hash}")

    return UserResponse(**current_user.to_dict())


@router.post("/logout", response_model=MessageResponse)
async def logout(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
>>>>>>> REPLACE

## Step 5: Verify Syntax

```bash
python3 -c "
import py_compile
for f in ['/ganuda/vetassist/backend/app/schemas/auth.py', '/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py']:
    try:
        py_compile.compile(f, doraise=True)
        print(f'PASS: {f} syntax valid')
    except py_compile.PyCompileError as e:
        print(f'FAIL: {e}')
"
```

## Rollback

To undo, restore from search-replace backups:
  ls -la /ganuda/vetassist/backend/app/schemas/auth.py.sr_backup_*
  ls -la /ganuda/vetassist/backend/app/api/v1/endpoints/auth.py.sr_backup_*
Restore the most recent backup for each file.
