# Jr Instruction: VetAssist VA Session Management - Phase 4: Token Refresh

## Priority: MEDIUM
## Estimated Effort: Medium
## Dependencies: Phase 1-3

---

## Objective

Implement background token refresh to keep VA access tokens valid. Tokens should be refreshed before expiry to ensure uninterrupted VA API access.

---

## Context

VA access tokens expire after 1 hour. We need to refresh them proactively (5 min before expiry) using the refresh token. Failed refreshes should gracefully degrade to requiring re-authentication.

Reference: `/ganuda/docs/ultrathink/ULTRATHINK-VETASSIST-VA-SESSION-MANAGEMENT-JAN20-2026.md`

---

## Implementation

### File: `/ganuda/vetassist/backend/app/services/token_refresh_service.py`

```python
"""
VA Token Refresh Service
Cherokee AI Federation - For Seven Generations

Background service to refresh VA tokens before expiry.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import asyncpg

from app.services.token_encryption import encrypt_va_token, decrypt_va_token
from app.services.va_oauth_service import va_oauth_service

logger = logging.getLogger(__name__)

# Refresh tokens 5 minutes before expiry
REFRESH_BUFFER_MINUTES = 5
# Check for tokens to refresh every minute
CHECK_INTERVAL_SECONDS = 60


class TokenRefreshService:
    """Background service to refresh expiring VA tokens."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the background refresh loop."""
        if self._running:
            logger.warning("[Token Refresh] Already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._refresh_loop())
        logger.info("[Token Refresh] Background service started")

    async def stop(self):
        """Stop the background refresh loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[Token Refresh] Background service stopped")

    async def _refresh_loop(self):
        """Main refresh loop."""
        while self._running:
            try:
                await self._refresh_expiring_tokens()
            except Exception as e:
                logger.error(f"[Token Refresh] Error in refresh loop: {e}")

            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

    async def _refresh_expiring_tokens(self):
        """Find and refresh tokens that will expire soon."""
        threshold = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_BUFFER_MINUTES)

        async with self.db.acquire() as conn:
            # Find tokens expiring within threshold that have refresh tokens
            tokens = await conn.fetch(
                """SELECT t.id, t.user_id, t.refresh_token_encrypted, t.expires_at,
                          u.va_icn
                   FROM vetassist_va_tokens t
                   JOIN vetassist_users u ON t.user_id = u.id
                   WHERE t.expires_at < $1
                     AND t.refresh_token_encrypted IS NOT NULL
                     AND u.is_active = true""",
                threshold
            )

        if tokens:
            logger.info(f"[Token Refresh] Found {len(tokens)} tokens to refresh")

        for token_row in tokens:
            await self._refresh_single_token(token_row)

    async def _refresh_single_token(self, token_row: asyncpg.Record):
        """Refresh a single token."""
        user_id = str(token_row["user_id"])

        try:
            # Decrypt refresh token
            refresh_token = decrypt_va_token(
                bytes(token_row["refresh_token_encrypted"]),
                user_id
            )

            # Call VA to refresh
            new_tokens = await va_oauth_service.refresh_token(refresh_token)

            # Encrypt and store new tokens
            async with self.db.acquire() as conn:
                access_encrypted = encrypt_va_token(new_tokens["access_token"], user_id)

                refresh_encrypted = None
                if new_tokens.get("refresh_token"):
                    refresh_encrypted = encrypt_va_token(new_tokens["refresh_token"], user_id)

                expires_in = new_tokens.get("expires_in", 3600)
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

                await conn.execute(
                    """UPDATE vetassist_va_tokens
                       SET access_token_encrypted = $1,
                           refresh_token_encrypted = COALESCE($2, refresh_token_encrypted),
                           expires_at = $3,
                           refreshed_at = NOW()
                       WHERE id = $4""",
                    access_encrypted,
                    refresh_encrypted,
                    expires_at,
                    token_row["id"]
                )

                # Audit log
                await conn.execute(
                    """INSERT INTO vetassist_auth_audit
                       (user_id, event_type, event_data)
                       VALUES ($1, 'token_refresh', $2)""",
                    token_row["user_id"],
                    {"success": True}
                )

            logger.info(f"[Token Refresh] Refreshed token for user {user_id[:8]}...")

        except Exception as e:
            logger.error(f"[Token Refresh] Failed to refresh token for {user_id[:8]}...: {e}")

            # Log failure
            async with self.db.acquire() as conn:
                await conn.execute(
                    """INSERT INTO vetassist_auth_audit
                       (user_id, event_type, event_data)
                       VALUES ($1, 'token_refresh_failed', $2)""",
                    token_row["user_id"],
                    {"error": str(e)[:200]}
                )

    async def get_valid_access_token(self, user_id: str) -> Optional[str]:
        """
        Get a valid access token for a user, refreshing if needed.

        Returns None if no valid token available.
        """
        async with self.db.acquire() as conn:
            token_row = await conn.fetchrow(
                """SELECT access_token_encrypted, refresh_token_encrypted, expires_at
                   FROM vetassist_va_tokens
                   WHERE user_id = $1""",
                user_id
            )

        if not token_row:
            return None

        # Check if current token is still valid (with buffer)
        threshold = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_BUFFER_MINUTES)

        if token_row["expires_at"] > threshold:
            # Token still valid
            return decrypt_va_token(bytes(token_row["access_token_encrypted"]), user_id)

        # Need to refresh
        if token_row["refresh_token_encrypted"]:
            try:
                refresh_token = decrypt_va_token(
                    bytes(token_row["refresh_token_encrypted"]),
                    user_id
                )
                new_tokens = await va_oauth_service.refresh_token(refresh_token)

                # Store and return new token
                async with self.db.acquire() as conn:
                    access_encrypted = encrypt_va_token(new_tokens["access_token"], user_id)
                    expires_at = datetime.now(timezone.utc) + timedelta(
                        seconds=new_tokens.get("expires_in", 3600)
                    )

                    await conn.execute(
                        """UPDATE vetassist_va_tokens
                           SET access_token_encrypted = $1, expires_at = $2, refreshed_at = NOW()
                           WHERE user_id = $3""",
                        access_encrypted,
                        expires_at,
                        user_id
                    )

                return new_tokens["access_token"]

            except Exception as e:
                logger.error(f"[Token Refresh] On-demand refresh failed: {e}")

        return None


# Singleton instance
_refresh_service: Optional[TokenRefreshService] = None


async def get_refresh_service() -> TokenRefreshService:
    """Get or create the token refresh service singleton."""
    global _refresh_service
    if _refresh_service is None:
        from app.db.database import get_db_pool
        pool = await get_db_pool()
        _refresh_service = TokenRefreshService(pool)
    return _refresh_service


async def start_token_refresh_service():
    """Start the background token refresh service."""
    service = await get_refresh_service()
    await service.start()


async def stop_token_refresh_service():
    """Stop the background token refresh service."""
    global _refresh_service
    if _refresh_service:
        await _refresh_service.stop()
```

---

## Integration with App Startup

Add to `/ganuda/vetassist/backend/app/main.py`:

```python
from app.services.token_refresh_service import start_token_refresh_service, stop_token_refresh_service

@app.on_event("startup")
async def startup_event():
    # ... existing startup code ...
    await start_token_refresh_service()
    logger.info("Token refresh service started")

@app.on_event("shutdown")
async def shutdown_event():
    await stop_token_refresh_service()
    logger.info("Token refresh service stopped")
```

---

## Verification

1. Create a test token with short expiry:
```sql
UPDATE vetassist_va_tokens
SET expires_at = NOW() + INTERVAL '2 minutes'
WHERE user_id = '<test-user-id>';
```

2. Watch logs for refresh:
```bash
tail -f /ganuda/logs/vetassist.log | grep "Token Refresh"
```

3. Verify token was refreshed:
```sql
SELECT expires_at, refreshed_at
FROM vetassist_va_tokens
WHERE user_id = '<test-user-id>';
```

---

## Success Criteria

- [ ] Background refresh loop running
- [ ] Tokens refreshed before expiry
- [ ] Failed refreshes logged in audit
- [ ] On-demand refresh working
- [ ] Graceful degradation on failure

---

*Cherokee AI Federation - For Seven Generations*
