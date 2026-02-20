# Jr Instruction: VetAssist Backend Memory Leak Fix

**Kanban:** #1776
**Council Vote:** #fadf71ec28884489 (PROCEED, 0.89)
**Priority:** 2
**Assigned Jr:** Software Engineer Jr.
**Long Man Phase:** BUILD

---

## Overview

Fix 3 database connection leaks in VetAssist backend causing memory creep from 1.2GB to 2GB. The critical path is `validate_jwt()` which leaks on EVERY authenticated request.

---

## Step 1: Fix validate_jwt — add finally block for connection cleanup

File: `/ganuda/vetassist/backend/app/services/va_session_service.py`

<<<<<<< SEARCH
    async def validate_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a VetAssist JWT and check session is active."""
        try:
            claims = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                audience="vetassist-frontend",
                issuer="vetassist.ganuda.us"
            )

            # Check session not revoked
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """SELECT id FROM vetassist_sessions
                   WHERE jwt_id = %s AND revoked_at IS NULL AND expires_at > NOW()""",
                (claims["jti"],)
            )
            session = cur.fetchone()
            cur.close()

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
=======
    async def validate_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a VetAssist JWT and check session is active."""
        conn = None
        try:
            claims = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                audience="vetassist-frontend",
                issuer="vetassist.ganuda.us"
            )

            # Check session not revoked
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """SELECT id FROM vetassist_sessions
                   WHERE jwt_id = %s AND revoked_at IS NULL AND expires_at > NOW()""",
                (claims["jti"],)
            )
            session = cur.fetchone()
            cur.close()

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
        finally:
            if conn:
                conn.close()
>>>>>>> REPLACE

---

## Step 2: Fix revoke_session — add conn.close()

File: `/ganuda/vetassist/backend/app/services/va_session_service.py`

<<<<<<< SEARCH
    async def revoke_session(self, jwt_id: str, user_id: str):
        """Revoke a specific session."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """UPDATE vetassist_sessions SET revoked_at = NOW()
               WHERE jwt_id = %s AND user_id = %s""",
            (jwt_id, user_id)
        )
        cur.execute(
            """INSERT INTO vetassist_auth_audit (user_id, event_type, event_data)
               VALUES (%s, 'logout', %s)""",
            (user_id, f'{{"jwt_id": "{jwt_id[:8]}..."}}')
        )
        conn.commit()
        cur.close()
        logger.info(f"[VA Session] Revoked session {jwt_id[:8]}...")
=======
    async def revoke_session(self, jwt_id: str, user_id: str):
        """Revoke a specific session."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """UPDATE vetassist_sessions SET revoked_at = NOW()
                   WHERE jwt_id = %s AND user_id = %s""",
                (jwt_id, user_id)
            )
            cur.execute(
                """INSERT INTO vetassist_auth_audit (user_id, event_type, event_data)
                   VALUES (%s, 'logout', %s)""",
                (user_id, f'{{"jwt_id": "{jwt_id[:8]}..."}}')
            )
            conn.commit()
            cur.close()
            logger.info(f"[VA Session] Revoked session {jwt_id[:8]}...")
        finally:
            conn.close()
>>>>>>> REPLACE

---

## Step 3: Fix get_research_status — connection already closed but early returns bypass it

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py`

The `conn.close()` at line 151 is actually fine — it runs after the `with` block. The real issue is that `conn` is created and closed correctly, but exception handling at the bottom re-raises without cleanup if the connection fails mid-query. The `with conn.cursor()` context manager handles the cursor, and `conn.close()` runs before the returns. This one is actually NOT a leak — the explorer over-reported. Skip this step.

---

## Manual Steps (TPM)

After Jr completes the code changes, restart the VetAssist backend on redfin:

```text
sudo systemctl restart vetassist-backend
```

Monitor memory over the next 24 hours to confirm the leak is resolved.

---

## Acceptance Criteria

- [ ] `validate_jwt()` has `conn = None` before try and `finally: if conn: conn.close()`
- [ ] `revoke_session()` wraps body in `try/finally` with `conn.close()`
- [ ] No functional changes to return values or error handling
- [ ] Backend starts cleanly after changes
