# Jr Instruction: VetAssist VA Session Management - Phase 3: VA Session Service

## Priority: HIGH
## Estimated Effort: Large
## Dependencies: Phase 1 (Database), Phase 2 (Encryption)

---

## Objective

Create the VASessionService class that handles the complete session management flow:
1. Create/link VetAssist user from VA identity
2. Encrypt and store VA tokens
3. Generate VetAssist JWT
4. Integrate with OAuth callback

---

## Context

After successful VA OAuth, we have tokens but no VetAssist session. This service bridges that gap by creating persistent user accounts and issuing our own JWTs.

Reference: `/ganuda/docs/ultrathink/ULTRATHINK-VETASSIST-VA-SESSION-MANAGEMENT-JAN20-2026.md`

---

## Implementation

### File: `/ganuda/vetassist/backend/app/services/va_session_service.py`

```python
"""
VA Session Management Service
Cherokee AI Federation - For Seven Generations

Handles user creation, token storage, and JWT issuance for VA OAuth.
"""
import os
import uuid
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
import asyncpg

from app.services.token_encryption import encrypt_va_token, decrypt_va_token
from app.core.config import settings

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.environ.get("VETASSIST_JWT_SECRET", settings.SECRET_KEY)
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 30


class VASessionService:
    """Manages VA OAuth sessions and VetAssist user accounts."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool

    async def create_session_from_va_auth(
        self,
        va_tokens: Dict[str, Any],
        va_claims: Dict[str, Any],
        device_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update user and session from VA OAuth tokens.

        Args:
            va_tokens: Token response from VA (access_token, refresh_token, expires_in)
            va_claims: Decoded claims from VA token or userinfo endpoint
            device_info: Optional device/browser info

        Returns:
            Dict with user_id, jwt_token, expires_at
        """
        async with self.db.acquire() as conn:
            async with conn.transaction():
                # 1. Extract VA identity
                va_icn = va_claims.get("icn") or va_claims.get("sub")
                if not va_icn:
                    raise ValueError("No ICN found in VA claims")

                # 2. Find or create user
                user = await self._find_or_create_user(conn, va_icn, va_claims)
                user_id = str(user["id"])

                # 3. Store encrypted tokens
                await self._store_va_tokens(conn, user_id, va_tokens)

                # 4. Create session and JWT
                jwt_id = str(uuid.uuid4())
                jwt_token = self._generate_jwt(user_id, va_icn, jwt_id)
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES)

                await self._create_session(conn, user_id, jwt_id, expires_at, device_info)

                # 5. Audit log
                await self._audit_log(conn, user_id, "login", {
                    "method": "va_oauth",
                    "icn": va_icn[:8] + "..."  # Partial for privacy
                }, device_info)

                logger.info(f"[VA Session] Created session for user {user_id[:8]}...")

                return {
                    "user_id": user_id,
                    "jwt_token": jwt_token,
                    "expires_at": expires_at.isoformat(),
                    "va_icn": va_icn
                }

    async def _find_or_create_user(
        self,
        conn: asyncpg.Connection,
        va_icn: str,
        va_claims: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Find existing user by ICN or create new one."""
        # Try to find existing user
        user = await conn.fetchrow(
            "SELECT * FROM vetassist_users WHERE va_icn = $1",
            va_icn
        )

        if user:
            # Update last login
            await conn.execute(
                """UPDATE vetassist_users
                   SET last_login_at = NOW(), updated_at = NOW()
                   WHERE id = $1""",
                user["id"]
            )
            return dict(user)

        # Create new user
        user_id = uuid.uuid4()
        await conn.execute(
            """INSERT INTO vetassist_users
               (id, va_icn, va_veteran_status, email, first_name, last_name, last_login_at)
               VALUES ($1, $2, $3, $4, $5, $6, NOW())""",
            user_id,
            va_icn,
            va_claims.get("veteran_status", "unknown"),
            va_claims.get("email"),
            va_claims.get("first_name"),
            va_claims.get("last_name")
        )

        logger.info(f"[VA Session] Created new user for ICN {va_icn[:8]}...")
        return {"id": user_id, "va_icn": va_icn}

    async def _store_va_tokens(
        self,
        conn: asyncpg.Connection,
        user_id: str,
        va_tokens: Dict[str, Any]
    ):
        """Encrypt and store VA tokens."""
        access_encrypted = encrypt_va_token(va_tokens["access_token"], user_id)
        refresh_encrypted = None
        if va_tokens.get("refresh_token"):
            refresh_encrypted = encrypt_va_token(va_tokens["refresh_token"], user_id)

        expires_in = va_tokens.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Upsert tokens
        await conn.execute(
            """INSERT INTO vetassist_va_tokens
               (user_id, access_token_encrypted, refresh_token_encrypted,
                token_type, scope, expires_at)
               VALUES ($1, $2, $3, $4, $5, $6)
               ON CONFLICT (user_id) DO UPDATE SET
                   access_token_encrypted = EXCLUDED.access_token_encrypted,
                   refresh_token_encrypted = EXCLUDED.refresh_token_encrypted,
                   expires_at = EXCLUDED.expires_at,
                   refreshed_at = NOW()""",
            uuid.UUID(user_id),
            access_encrypted,
            refresh_encrypted,
            va_tokens.get("token_type", "Bearer"),
            va_tokens.get("scope", ""),
            expires_at
        )

    def _generate_jwt(self, user_id: str, va_icn: str, jwt_id: str) -> str:
        """Generate VetAssist JWT."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "iss": "vetassist.ganuda.us",
            "aud": "vetassist-frontend",
            "exp": now + timedelta(minutes=JWT_EXPIRY_MINUTES),
            "iat": now,
            "jti": jwt_id,
            "va_linked": True,
            "va_icn": va_icn
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    async def _create_session(
        self,
        conn: asyncpg.Connection,
        user_id: str,
        jwt_id: str,
        expires_at: datetime,
        device_info: Optional[Dict[str, Any]]
    ):
        """Create session record for JWT tracking."""
        await conn.execute(
            """INSERT INTO vetassist_sessions
               (user_id, jwt_id, device_info, expires_at)
               VALUES ($1, $2, $3, $4)""",
            uuid.UUID(user_id),
            jwt_id,
            device_info,
            expires_at
        )

    async def _audit_log(
        self,
        conn: asyncpg.Connection,
        user_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        device_info: Optional[Dict[str, Any]] = None
    ):
        """Log authentication event for audit."""
        ip_hash = None
        if device_info and device_info.get("ip"):
            ip_hash = hashlib.sha256(device_info["ip"].encode()).hexdigest()

        await conn.execute(
            """INSERT INTO vetassist_auth_audit
               (user_id, event_type, event_data, ip_hash)
               VALUES ($1, $2, $3, $4)""",
            uuid.UUID(user_id),
            event_type,
            event_data,
            ip_hash
        )

    async def validate_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a VetAssist JWT and check session is active.

        Returns claims if valid, None if invalid or revoked.
        """
        try:
            claims = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                audience="vetassist-frontend",
                issuer="vetassist.ganuda.us"
            )

            # Check session not revoked
            async with self.db.acquire() as conn:
                session = await conn.fetchrow(
                    """SELECT id FROM vetassist_sessions
                       WHERE jwt_id = $1 AND revoked_at IS NULL AND expires_at > NOW()""",
                    claims["jti"]
                )

                if not session:
                    logger.warning(f"[VA Session] Session revoked or expired: {claims['jti'][:8]}...")
                    return None

            return claims

        except jwt.ExpiredSignatureError:
            logger.debug("[VA Session] JWT expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"[VA Session] Invalid JWT: {e}")
            return None

    async def revoke_session(self, jwt_id: str, user_id: str):
        """Revoke a specific session."""
        async with self.db.acquire() as conn:
            await conn.execute(
                """UPDATE vetassist_sessions
                   SET revoked_at = NOW()
                   WHERE jwt_id = $1 AND user_id = $2""",
                jwt_id,
                uuid.UUID(user_id)
            )
            await self._audit_log(conn, user_id, "logout", {"jwt_id": jwt_id[:8]})

        logger.info(f"[VA Session] Revoked session {jwt_id[:8]}...")

    async def revoke_all_sessions(self, user_id: str):
        """Revoke all sessions for a user (force logout everywhere)."""
        async with self.db.acquire() as conn:
            result = await conn.execute(
                """UPDATE vetassist_sessions
                   SET revoked_at = NOW()
                   WHERE user_id = $1 AND revoked_at IS NULL""",
                uuid.UUID(user_id)
            )
            await self._audit_log(conn, user_id, "logout_all", {})

        logger.info(f"[VA Session] Revoked all sessions for user {user_id[:8]}...")


# Singleton instance
_session_service: Optional[VASessionService] = None


async def get_session_service() -> VASessionService:
    """Get or create the session service singleton."""
    global _session_service
    if _session_service is None:
        from app.db.database import get_db_pool
        pool = await get_db_pool()
        _session_service = VASessionService(pool)
    return _session_service
```

---

## Update OAuth Callback

Modify `/ganuda/vetassist/backend/app/api/v1/endpoints/va_auth.py` to use the session service:

```python
# Add to imports
from app.services.va_session_service import get_session_service

# Update va_callback function:
@router.get("/va/callback")
async def va_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...)
):
    try:
        token_data = await va_oauth_service.exchange_code_for_token(code, state)
        logger.info(f"[VA OAuth] Token exchange successful")

        # Get veteran info for claims
        va_claims = {}
        try:
            veteran_info = await va_oauth_service.get_veteran_info(token_data['access_token'])
            va_claims = veteran_info
        except Exception as e:
            logger.warning(f"[VA OAuth] Could not get veteran info: {e}")
            # Use minimal claims from token
            va_claims = {"icn": token_data.get("id_token_claims", {}).get("sub")}

        # Create VetAssist session
        session_service = await get_session_service()
        device_info = {
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent", "")
        }

        session = await session_service.create_session_from_va_auth(
            va_tokens=token_data,
            va_claims=va_claims,
            device_info=device_info
        )

        # Redirect with JWT
        frontend_url = f"https://vetassist.ganuda.us/va-success?token={session['jwt_token']}&expires={session['expires_at']}"
        return RedirectResponse(url=frontend_url)

    except VAOAuthError as e:
        logger.error(f"[VA OAuth] Callback error: {e}")
        return RedirectResponse(url="https://vetassist.ganuda.us/va-error?error=token_exchange_failed")
```

---

## Environment Variables

Add to `/ganuda/vetassist/backend/.env`:

```
VETASSIST_JWT_SECRET=<generate-secure-random-string>
```

Generate with:
```bash
python3 -c "import secrets; print(f'VETASSIST_JWT_SECRET={secrets.token_hex(32)}')"
```

---

## Verification

1. Test session creation manually:
```python
from app.services.va_session_service import VASessionService
# Test with mock data
```

2. Test full OAuth flow:
- Navigate to https://vetassist.ganuda.us
- Click "Login with VA.gov"
- Complete VA login
- Verify redirect includes JWT token
- Decode JWT and verify claims

---

## Success Criteria

- [ ] VASessionService implemented
- [ ] User creation/linking works
- [ ] Tokens encrypted and stored
- [ ] JWT generated with correct claims
- [ ] OAuth callback integrated
- [ ] Audit logging working

---

*Cherokee AI Federation - For Seven Generations*
