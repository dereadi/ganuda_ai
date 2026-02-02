# JR-VETASSIST-VA-LINK-ENDPOINT-JAN30-2026

## Metadata
- **Priority:** P1
- **Jr Type:** Backend / Python
- **Target Node:** bluefin (192.168.132.222)
- **Depends On:** JR-VETASSIST-VA-LINK-MIGRATION-JAN30-2026 (Phase 1 must complete first)
- **Blocks:** JR-VETASSIST-VA-CALLBACK-LINKING-JAN30-2026, JR-VETASSIST-VA-LINK-FRONTEND-JAN30-2026

## Context

After Phase 1 adds `va_icn` and `va_linked_at` columns to the `users` table, we need:
1. The SQLAlchemy `User` model to know about these columns
2. The `UserResponse` schema to expose `va_linked` (boolean, derived — never raw ICN)
3. A new `POST /auth/link-va` endpoint that bridges the two auth systems

The endpoint accepts a VA JWT (issued by `VASessionService` during VA OAuth), extracts the ICN from it, and links it to the caller's email-based account.

## Files to Modify

1. `/ganuda/vetassist/backend/app/models/user.py`
2. `/ganuda/vetassist/backend/app/schemas/auth.py`
3. `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`

---

## Step 1: Update User Model

**File:** `/ganuda/vetassist/backend/app/models/user.py`

Add two columns to the `User` class, after line 35 (`is_active` column):

```python
    # VA Account Linking
    va_icn = Column(String(50), unique=True, nullable=True)
    va_linked_at = Column(DateTime(timezone=True), nullable=True)
```

Update the `to_dict()` method to include a derived `va_linked` boolean. Add this to the return dict (after `is_active`):

```python
            "va_linked": self.va_icn is not None,
            "va_linked_at": self.va_linked_at.isoformat() if self.va_linked_at else None
```

**IMPORTANT:** Never include `va_icn` in `to_dict()`. It is PII and must not appear in API responses.

The complete `to_dict()` return should be:
```python
    def to_dict(self):
        """Convert user to dictionary for API responses (exclude password, va_icn)"""
        return {
            "id": str(self.id),
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "veteran_status": self.veteran_status,
            "service_branch": self.service_branch,
            "service_start_date": self.service_start_date.isoformat() if self.service_start_date else None,
            "service_end_date": self.service_end_date.isoformat() if self.service_end_date else None,
            "disability_rating": self.disability_rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "email_verified": self.email_verified,
            "is_active": self.is_active,
            "va_linked": self.va_icn is not None,
            "va_linked_at": self.va_linked_at.isoformat() if self.va_linked_at else None
        }
```

---

## Step 2: Update Pydantic Schemas

**File:** `/ganuda/vetassist/backend/app/schemas/auth.py`

### A) Add `va_linked` fields to `UserResponse`

After the `is_active` field (line 73), add:

```python
    va_linked: bool = False
    va_linked_at: Optional[str] = None
```

### B) Add request schema for the link endpoint

After the `MessageResponse` class (at the end of the file), add:

```python
class VALinkRequest(BaseModel):
    """Schema for linking a VA.gov account to an existing email-based account"""
    va_session_token: str = Field(..., description="JWT token from VA OAuth callback")
```

### C) Update the imports in `__init__` or wherever schemas are imported

The new `VALinkRequest` must be importable from `app.schemas.auth`.

---

## Step 3: Add POST /auth/link-va Endpoint

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`

### A) Add imports

At the top, add these imports:

```python
import os
import hashlib
import logging
from datetime import datetime, timezone
import jwt as pyjwt
```

Add `VALinkRequest` to the schema imports:

```python
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    UserProfileUpdate,
    MessageResponse,
    VALinkRequest
)
```

Add a logger:

```python
logger = logging.getLogger(__name__)
```

### B) Add the endpoint

Append this endpoint after the `update_profile` endpoint (after line 301):

```python
@router.post("/link-va", response_model=UserResponse)
@limiter.limit("2/minute")  # Strict rate limit — account linking is sensitive
async def link_va_account(
    request: Request,
    link_data: VALinkRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Link a VA.gov account to the current email-based account.

    Flow:
    1. User logs in with email/password
    2. User initiates VA OAuth from settings page
    3. VA OAuth callback returns a VA JWT
    4. Frontend sends that VA JWT here
    5. We extract the ICN and link it to the user's account
    """
    # 1. Decode the VA JWT to extract ICN
    va_jwt_secret = os.environ.get(
        "VETASSIST_JWT_SECRET",
        os.environ.get("SECRET_KEY", "dev-secret-change-me")
    )

    try:
        va_claims = pyjwt.decode(
            link_data.va_session_token,
            va_jwt_secret,
            algorithms=["HS256"],
            audience="vetassist-frontend",
            issuer="vetassist.ganuda.us"
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="VA session token has expired. Please re-authenticate with VA.gov."
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid VA session token"
        )

    va_icn = va_claims.get("va_icn")
    if not va_icn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="VA session token does not contain identity information"
        )

    # 2. Check if this ICN is already linked to ANOTHER user
    from app.models.user import User as UserModel
    existing_link = db.query(UserModel).filter(
        UserModel.va_icn == va_icn,
        UserModel.id != current_user.id
    ).first()

    if existing_link:
        logger.warning(
            f"[VA Link] ICN {va_icn[:8]}... already linked to user {str(existing_link.id)[:8]}..."
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This VA.gov account is already linked to a different VetAssist account"
        )

    # 3. Check if current user is already linked to a DIFFERENT ICN
    if current_user.va_icn and current_user.va_icn != va_icn:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Your account is already linked to a different VA.gov account"
        )

    # 4. Check if already linked to same ICN (idempotent)
    if current_user.va_icn == va_icn:
        return UserResponse(**current_user.to_dict())

    # 5. Link the accounts
    current_user.va_icn = va_icn
    current_user.va_linked_at = datetime.now(timezone.utc)
    current_user.veteran_status = True

    # 6. Backfill name from VA claims if local fields are empty
    va_first = va_claims.get("first_name")
    va_last = va_claims.get("last_name")
    if not current_user.first_name and va_first:
        current_user.first_name = va_first
    if not current_user.last_name and va_last:
        current_user.last_name = va_last

    db.commit()
    db.refresh(current_user)

    # 7. Audit log
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()
    logger.info(
        f"[VA Link] Account linked: user={str(current_user.id)[:8]}... "
        f"icn={va_icn[:8]}... ip_hash={ip_hash[:16]}..."
    )

    return UserResponse(**current_user.to_dict())
```

### Key Design Decisions

1. **Rate limit: 2/minute** — Account linking is sensitive. Prevent brute-force.
2. **Idempotent** — If already linked to the same ICN, returns success without error.
3. **409 on conflicts** — Two clear conflict cases: ICN taken by another user, or user already linked to different ICN.
4. **Backfill names** — Only if local fields are NULL. Never overwrites existing data.
5. **Never exposes ICN** — The `UserResponse` includes `va_linked: bool` and `va_linked_at`, but never the raw ICN.

---

## Verification

### Test 1: Link a VA account

```bash
# First, get an email-based JWT by logging in
EMAIL_TOKEN=$(curl -s -X POST https://vetassist.ganuda.us/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}' | jq -r '.access_token')

# Then, get a VA JWT (from a separate VA OAuth flow)
# Assume VA_TOKEN is the JWT from /va/callback

# Link them
curl -s -X POST https://vetassist.ganuda.us/api/v1/auth/link-va \
  -H "Authorization: Bearer $EMAIL_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"va_session_token\": \"$VA_TOKEN\"}"

# Expected: 200 with user profile showing va_linked: true
# Verify va_icn is NOT in the response
```

### Test 2: Duplicate ICN prevention

```bash
# Try linking same VA ICN to a different email account
EMAIL_TOKEN_2=$(curl -s -X POST https://vetassist.ganuda.us/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"other@example.com","password":"testpass123"}' | jq -r '.access_token')

curl -s -X POST https://vetassist.ganuda.us/api/v1/auth/link-va \
  -H "Authorization: Bearer $EMAIL_TOKEN_2" \
  -H "Content-Type: application/json" \
  -d "{\"va_session_token\": \"$VA_TOKEN\"}"

# Expected: 409 Conflict
```

### Test 3: PII check

```bash
# Verify ICN never appears in any response
curl -s -X GET https://vetassist.ganuda.us/api/v1/auth/me \
  -H "Authorization: Bearer $EMAIL_TOKEN" | jq .

# Should show va_linked: true, va_linked_at: "2026-01-30T..."
# Should NOT contain va_icn field
```

## Security Notes

- **Account takeover prevention:** Linking requires an active email-based session. The attacker would need both the user's email password AND a valid VA OAuth session.
- **PII:** `va_icn` is stored in the database but never serialized to API responses. The `to_dict()` method excludes it; the `UserResponse` schema does not define it.
- **Audit trail:** All link events are logged with hashed IP and truncated ICN.
- **Crawdad review required:** This endpoint handles PII linking between two identity systems.
