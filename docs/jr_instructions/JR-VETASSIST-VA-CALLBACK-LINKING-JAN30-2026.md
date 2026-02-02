# JR-VETASSIST-VA-CALLBACK-LINKING-JAN30-2026

## Metadata
- **Priority:** P1
- **Jr Type:** Backend / Python
- **Target Node:** bluefin (192.168.132.222)
- **Depends On:** JR-VETASSIST-VA-LINK-ENDPOINT-JAN30-2026 (Phase 2)
- **Blocks:** JR-VETASSIST-VA-LINK-FRONTEND-JAN30-2026 (Phase 4)
- **Files to Modify:**
  - `/ganuda/vetassist/backend/app/api/v1/endpoints/va_auth.py`
  - `/ganuda/vetassist/backend/app/services/va_session_service.py`

## Context

The current VA OAuth callback (`va_callback` in `va_auth.py`) has one mode: standalone VA login. It creates a `vetassist_users` record and issues a VA-format JWT (signed with `VETASSIST_JWT_SECRET`).

We need two new behaviors:

1. **Linking mode** — User is already logged in via email/password and wants to link their VA account. The OAuth flow was initiated from the settings page with the user's current session token in the `session_id` parameter. After token exchange, redirect to frontend with `linking=true` so the frontend can call `POST /auth/link-va`.

2. **Linked-login mode** — User has previously linked their accounts and is now logging in via VA.gov. The callback detects the ICN is already in the `users` table and issues an email-format JWT (signed with `SECRET_KEY`), creating a `user_sessions` row. This lets the user log in via VA.gov and land in the same session as if they'd used email/password.

## Current Code Reference

**`va_auth.py`** — The `va_callback()` function currently (lines 35-84):
1. Exchanges authorization code for VA tokens
2. Fetches veteran info from VA API
3. Creates a VA session via `session_service.create_session_from_va_auth()`
4. Redirects to `https://vetassist.ganuda.us/va-success?token={jwt}&expires={expires_at}`

**`va_session_service.py`** — The `create_session_from_va_auth()` method:
- Extracts ICN from VA claims
- Finds or creates user in `vetassist_users` table (NOT `users` table)
- Stores encrypted VA tokens
- Issues JWT signed with `VETASSIST_JWT_SECRET`

**`va_oauth_service.py`** — The `get_authorization_url(session_id)` method:
- Already accepts `session_id` parameter
- Stores it in the state dict alongside the CSRF state token
- The state is passed through the OAuth redirect and returned in the callback

---

## Step 1: Modify va_auth.py — Add Linking + Linked-Login Logic

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/va_auth.py`

Replace the entire `va_callback` function with the version below. The `va_login` and `va_refresh_token` endpoints remain unchanged.

### Add imports at top of file

```python
import os
import hashlib
from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session as SASession

from app.core.database import get_db
from app.core.security import create_access_token, hash_token
from app.core.config import settings
from app.models.user import User, UserSession
from app.services.auth_service import AuthService
```

### Replace `va_callback` function

```python
@router.get("/va/callback")
async def va_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from VA"),
    state: str = Query(..., description="State for CSRF verification")
):
    """
    Handle OAuth callback from VA.gov.

    Three modes:
    1. Linking mode: session_id present in state → redirect with linking=true
    2. Linked-login mode: ICN found in users table → issue email-format JWT
    3. Default mode: standalone VA login (existing behavior)
    """
    try:
        # Exchange code for tokens
        token_data = await va_oauth_service.exchange_code_for_token(code, state)
        logger.info(f"[VA OAuth] Token exchange successful")

        # Get veteran info for claims
        va_claims = {}
        try:
            veteran_info = await va_oauth_service.get_veteran_info(token_data['access_token'])
            va_claims = veteran_info
            logger.info(f"[VA OAuth] Got veteran info")
        except Exception as e:
            logger.warning(f"[VA OAuth] Could not get veteran info: {e}")
            va_claims = {"icn": token_data.get("id_token_claims", {}).get("sub", "unknown")}

        # Extract ICN
        va_icn = va_claims.get("icn") or va_claims.get("sub")

        # Check if state contains a session_id (linking mode)
        state_data = va_oauth_service.get_state_data(state) if hasattr(va_oauth_service, 'get_state_data') else {}
        session_id = state_data.get("session_id") if state_data else None

        # ---- MODE 1: LINKING MODE ----
        # User initiated from settings page while logged in
        if session_id:
            logger.info(f"[VA OAuth] Linking mode detected, session_id present")

            # Create the VA session (still stores encrypted tokens in vetassist_va_tokens)
            session_service = get_session_service()
            device_info = {
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "")
            }
            session = await session_service.create_session_from_va_auth(
                va_tokens=token_data,
                va_claims=va_claims,
                device_info=device_info
            )

            # Redirect with linking=true so frontend calls POST /auth/link-va
            frontend_url = (
                f"https://vetassist.ganuda.us/va-success"
                f"?linking=true"
                f"&token={session['jwt_token']}"
            )
            return RedirectResponse(url=frontend_url)

        # ---- MODE 2: LINKED-LOGIN MODE ----
        # Check if this ICN is already linked to a users table account
        if va_icn:
            db_gen = get_db()
            db: SASession = next(db_gen)
            try:
                linked_user = db.query(User).filter(
                    User.va_icn == va_icn,
                    User.is_active == True
                ).first()

                if linked_user:
                    logger.info(
                        f"[VA OAuth] Linked-login: ICN {va_icn[:8]}... "
                        f"→ user {str(linked_user.id)[:8]}..."
                    )

                    # Issue email-format JWT (signed with SECRET_KEY)
                    token_payload = {
                        "sub": str(linked_user.id),
                        "email": linked_user.email
                    }
                    access_token = create_access_token(
                        data=token_payload,
                        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                    )

                    # Create user_sessions row (same as email login)
                    client_ip = request.client.host if request.client else None
                    user_agent = request.headers.get("user-agent")
                    AuthService.create_session(
                        db=db,
                        user=linked_user,
                        token=access_token,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        remember_me=False
                    )

                    # Update last_login
                    linked_user.last_login = datetime.now(timezone.utc)
                    db.commit()

                    # Also store VA tokens for this session (encrypted)
                    session_service = get_session_service()
                    device_info = {
                        "ip": client_ip or "unknown",
                        "user_agent": user_agent or ""
                    }
                    try:
                        await session_service.create_session_from_va_auth(
                            va_tokens=token_data,
                            va_claims=va_claims,
                            device_info=device_info
                        )
                    except Exception as e:
                        # Non-fatal: VA token storage is secondary
                        logger.warning(f"[VA OAuth] VA token storage failed (non-fatal): {e}")

                    # Audit log
                    ip_hash = hashlib.sha256((client_ip or "unknown").encode()).hexdigest()
                    logger.info(
                        f"[VA OAuth] Linked-login success: user={str(linked_user.id)[:8]}... "
                        f"ip_hash={ip_hash[:16]}..."
                    )

                    # Redirect with email-auth JWT and linked=true flag
                    frontend_url = (
                        f"https://vetassist.ganuda.us/va-success"
                        f"?token={access_token}"
                        f"&linked=true"
                    )
                    return RedirectResponse(url=frontend_url)
            finally:
                try:
                    next(db_gen, None)  # Close generator
                except StopIteration:
                    pass

        # ---- MODE 3: DEFAULT (standalone VA login) ----
        # Existing behavior: create vetassist_users record, issue VA-format JWT
        session_service = get_session_service()
        device_info = {
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "")
        }

        session = await session_service.create_session_from_va_auth(
            va_tokens=token_data,
            va_claims=va_claims,
            device_info=device_info
        )

        logger.info(f"[VA OAuth] Session created for user {session['user_id'][:8]}...")

        frontend_url = (
            f"https://vetassist.ganuda.us/va-success"
            f"?token={session['jwt_token']}"
            f"&expires={session['expires_at']}"
        )
        return RedirectResponse(url=frontend_url)

    except VAOAuthError as e:
        logger.error(f"[VA OAuth] Callback error: {e}")
        return RedirectResponse(url="https://vetassist.ganuda.us/va-error?error=token_exchange_failed")
    except Exception as e:
        logger.error(f"[VA OAuth] Unexpected error: {e}", exc_info=True)
        return RedirectResponse(url="https://vetassist.ganuda.us/va-error?error=unknown")
```

---

## Step 2: Add `get_state_data()` to VA OAuth Service

**File:** `/ganuda/vetassist/backend/app/services/va_oauth_service.py`

The `va_oauth_service` stores state in an in-memory dict during `get_authorization_url()`. We need a method to retrieve the stored data (including `session_id`) given the state token.

Add this method to the `VAOAuthService` class:

```python
    def get_state_data(self, state: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored data for an OAuth state token.
        Returns the state data dict or None if not found/expired.
        """
        return self._state_store.get(state)
```

**Note:** Check what the state store attribute is actually named in the class. It may be `_state_store`, `state_store`, or `_states`. Match the existing naming. The `get_authorization_url()` method stores state like:

```python
self._state_store[state] = {"session_id": session_id, "created_at": ...}
```

If the attribute name differs, adjust accordingly.

---

## Flow Summary

### Linking Mode (User clicks "Link VA Account" from settings page)

```
Settings page → GET /auth/va/login?session_id=<email-jwt>
  → VA.gov OAuth → callback with state containing session_id
  → Callback detects session_id → creates VA session for token storage
  → Redirects to /va-success?linking=true&token=<va-jwt>
  → Frontend calls POST /auth/link-va with the va-jwt
  → Backend links va_icn to users row
```

### Linked-Login Mode (User clicks "Login with VA.gov" after linking)

```
Login page → GET /auth/va/login (no session_id)
  → VA.gov OAuth → callback
  → Callback queries: SELECT id FROM users WHERE va_icn = ?
  → Match found → issues email-format JWT, creates user_sessions row
  → Redirects to /va-success?token=<email-jwt>&linked=true
  → Frontend stores token as auth_token, redirects to dashboard
```

### Default Mode (User clicks "Login with VA.gov" without linking)

```
Login page → GET /auth/va/login (no session_id)
  → VA.gov OAuth → callback
  → No linked user found → existing behavior
  → Creates vetassist_users record, issues VA-format JWT
  → Redirects to /va-success?token=<va-jwt>&expires=<time>
```

---

## Verification

### Test 1: Linking mode redirect

```bash
# Initiate OAuth with session_id
curl -v "https://vetassist.ganuda.us/api/v1/auth/va/login?session_id=test-session-123"
# Should redirect to VA.gov with state containing session_id

# After OAuth completes, the callback should redirect to:
# https://vetassist.ganuda.us/va-success?linking=true&token=<va-jwt>
# NOT the default URL pattern
```

### Test 2: Linked-login mode

```bash
# Pre-requisite: Link a user's account (Phase 2 must be done first)
# Then initiate a VA login WITHOUT session_id
curl -v "https://vetassist.ganuda.us/api/v1/auth/va/login"

# After OAuth, callback should detect the linked ICN and redirect to:
# https://vetassist.ganuda.us/va-success?token=<email-jwt>&linked=true

# Verify the token is an email-format JWT (decodable with SECRET_KEY)
```

### Test 3: Default mode unchanged

```bash
# For unlinked users, the existing flow should be unchanged
# Callback should redirect to:
# https://vetassist.ganuda.us/va-success?token=<va-jwt>&expires=<time>
```

## Security Notes

- **Linked-login mode** creates a full email-format session. This means a VA-authenticated user gets the same access as if they'd logged in with email/password.
- The `user_sessions` row tracks the session for revocation.
- VA token storage (in `vetassist_va_tokens`) happens in both linking and linked-login modes, so the user's VA access tokens are always available for claim.read/claim.write API calls.
- The database generator cleanup in Mode 2 uses a `try/finally` pattern to ensure the SQLAlchemy session is properly closed.
