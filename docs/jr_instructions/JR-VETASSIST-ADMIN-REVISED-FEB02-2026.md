# JR-VETASSIST-ADMIN-REVISED-FEB02-2026

## Task: VetAssist Admin Panel — Dependencies, RBAC, Service, Schemas, Endpoints

**Priority:** P1
**Assigned:** Software Engineer Jr
**Replaces:** Failed tasks #526 (partial), #527, #528
**Date:** 2026-02-02

---

## Background

Tasks #526-528 attempted to build the VetAssist admin panel in three phases. Results:
- **#526 SQL migration**: Succeeded. Tables `admin_audit_log` and `admin_user_view` already exist. Column `users.admin_tier` (integer, default 0) already exists. **Do NOT recreate any database objects.**
- **#527 Backend models + RBAC**: Failed — executor ran outside the virtualenv.
- **#528 Backend endpoints**: Catastrophically overwrote `v1/__init__.py` instead of creating a new file. TPM restored `__init__.py`.

This single instruction creates all five missing Python files. It does NOT touch `v1/__init__.py`. It does NOT recreate any SQL objects.

---

## Existing Infrastructure (Do Not Recreate)

**Database objects already present (confirmed via psql):**
- `users` table with `admin_tier INTEGER DEFAULT 0` column
- `admin_audit_log` table (id, admin_id, admin_email, admin_tier, action, target_user_id, target_table, fields_accessed, justification, ip_address, user_agent, session_id, verification_result, created_at)
- `admin_user_view` view (id, first_name, last_name, veteran_status, is_active, email_verified, va_linked, va_linked_at, admin_tier, created_at, updated_at, last_login, disability_rating)
- `user_sessions` table (id, user_id, token_hash, ip_address, user_agent, created_at, expires_at, revoked)

**Existing Python modules referenced by the new code:**
- `app.core.database.get_db` — SQLAlchemy session generator (yields Session)
- `app.core.security.get_current_user` — async, takes `authorization: str = Header(...)`, returns `{"user_id": ..., "email": ...}`
- `app.core.database_config.get_db_connection` — returns psycopg2 connection
- `app.core.database_config.get_dict_cursor` — returns RealDictCursor
- `app.core.config.settings` — Pydantic settings singleton
- `app.models.user.User` — SQLAlchemy model for `users` table
- `app.models.user.UserSession` — SQLAlchemy model for `user_sessions` table

**Tier values:**
- 0 = Regular user (no admin access)
- 1 = VIEWER (read-only admin, can view user list and stats)
- 2 = SUPPORT (can view user details, verify identity, view sessions)
- 3 = ADMIN (can reset passwords, toggle active status, revoke sessions)
- 4 = SECURITY (full access including audit log and verification results)

---

## CRITICAL EXECUTOR RULES

1. **NO search/replace blocks** — the executor cannot process them.
2. **Use bash heredoc** (`cat << 'PYEOF' > filepath`) for all file creation.
3. **All psql commands** must include `PGPASSWORD=jawaseatlasers2`.
4. **All Python validation** must use `/ganuda/vetassist/backend/venv/bin/python`.
5. **NEVER write to** `app/api/v1/__init__.py` — that file is off limits.
6. **All file paths are absolute**, rooted at `/ganuda/vetassist/backend/`.

---

## Step 1: Create dependencies.py (thin re-export module)

This file unblocks both `audit.py` and `workbench_documents.py`, which import from `app.api.dependencies` (relative as `..dependencies`). The `audit.py` endpoint at `app/api/v1/endpoints/audit.py` does `from app.api.dependencies import get_current_user`. The `workbench_documents.py` does `from ..dependencies import get_db, get_current_user`.

Since both files are under `app/api/v1/endpoints/`, the `..dependencies` relative import resolves to `app/api/v1/dependencies`. We create that module as a thin re-export.

```bash
cat << 'PYEOF' > /ganuda/vetassist/backend/app/api/v1/dependencies.py
"""
Shared dependencies for API v1 endpoints.
Thin re-export module — imports from canonical locations in app.core.

Created: 2026-02-02 (JR-VETASSIST-ADMIN-REVISED)
Unblocks: audit.py, workbench_documents.py, admin.py
"""

from app.core.database import get_db
from app.core.security import get_current_user

__all__ = ["get_db", "get_current_user"]
PYEOF
```

**Validation:**

```bash
/ganuda/vetassist/backend/venv/bin/python -c "
import ast
ast.parse(open('/ganuda/vetassist/backend/app/api/v1/dependencies.py').read())
print('PASS: dependencies.py parses OK')
"
```

---

## Step 2: Create rbac.py (Role-Based Access Control)

```bash
cat << 'PYEOF' > /ganuda/vetassist/backend/app/core/rbac.py
"""
Role-Based Access Control (RBAC) for VetAssist Admin Panel.
4-tier system: VIEWER(1), SUPPORT(2), ADMIN(3), SECURITY(4).

Users with admin_tier=0 are regular users with no admin access.
The require_tier dependency factory returns a FastAPI dependency
that checks the caller's tier against the minimum required.

Created: 2026-02-02 (JR-VETASSIST-ADMIN-REVISED)
"""

import enum
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.database_config import get_db_connection
from app.models.user import User
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class AdminTier(int, enum.Enum):
    """Admin permission tiers. Higher number = more access."""
    NONE = 0
    VIEWER = 1
    SUPPORT = 2
    ADMIN = 3
    SECURITY = 4


def require_tier(minimum_tier: int):
    """
    FastAPI dependency factory. Returns a dependency that:
    1. Gets the current user from the DB via SQLAlchemy.
    2. Checks that user.admin_tier >= minimum_tier.
    3. Returns the User ORM object if authorized.
    4. Raises 403 if the user's tier is insufficient.
    5. Raises 401 if no valid user is found.

    Usage in an endpoint:
        @router.get("/users")
        def list_users(admin: User = Depends(require_tier(AdminTier.VIEWER))):
            ...
    """
    from app.api.v1.endpoints.auth import get_current_user as _get_auth_user

    async def _check_tier(
        request: Request,
        current_user: User = Depends(_get_auth_user),
    ) -> User:
        # current_user is a User ORM object from auth.py's get_current_user
        tier = getattr(current_user, "admin_tier", 0) or 0

        if tier < minimum_tier:
            logger.warning(
                "RBAC denied: user=%s tier=%d required=%d path=%s",
                current_user.email, tier, minimum_tier, request.url.path,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires admin tier {minimum_tier} ({AdminTier(minimum_tier).name}). Your tier: {tier}.",
            )

        return current_user

    return _check_tier


def log_admin_action(
    admin_user: User,
    action: str,
    request: Request,
    target_user_id: Optional[str] = None,
    target_table: Optional[str] = None,
    fields_accessed: Optional[list] = None,
    justification: Optional[str] = None,
    verification_result: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """
    Insert a row into admin_audit_log using raw psycopg2.

    This function never raises — failures are logged but swallowed
    so that the calling endpoint is not disrupted by audit issues.
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO admin_audit_log
                        (admin_id, admin_email, admin_tier, action,
                         target_user_id, target_table, fields_accessed,
                         justification, ip_address, user_agent,
                         session_id, verification_result)
                    VALUES
                        (%s, %s, %s, %s,
                         %s, %s, %s,
                         %s, %s, %s,
                         %s, %s)
                    """,
                    (
                        str(admin_user.id),
                        admin_user.email,
                        getattr(admin_user, "admin_tier", 0) or 0,
                        action,
                        target_user_id,
                        target_table,
                        fields_accessed,
                        justification,
                        request.client.host if request.client else None,
                        request.headers.get("user-agent"),
                        session_id,
                        verification_result,
                    ),
                )
                conn.commit()
        finally:
            conn.close()
    except Exception:
        logger.exception("Failed to write admin audit log for action=%s", action)
PYEOF
```

**Validation:**

```bash
/ganuda/vetassist/backend/venv/bin/python -c "
import ast
ast.parse(open('/ganuda/vetassist/backend/app/core/rbac.py').read())
print('PASS: rbac.py parses OK')
"
```

---

## Step 3: Create admin schemas

```bash
cat << 'PYEOF' > /ganuda/vetassist/backend/app/schemas/admin.py
"""
Pydantic schemas for VetAssist Admin API.

Created: 2026-02-02 (JR-VETASSIST-ADMIN-REVISED)
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --------------- Request Schemas ---------------

class ToggleActiveRequest(BaseModel):
    """Toggle a user's is_active flag."""
    is_active: bool
    justification: str = Field(..., min_length=10, max_length=500)


class ResetPasswordRequest(BaseModel):
    """Admin-initiated password reset."""
    new_password: str = Field(..., min_length=8)
    justification: str = Field(..., min_length=10, max_length=500)


class VerifyIdentityRequest(BaseModel):
    """Record identity verification outcome."""
    result: str = Field(..., pattern="^(verified|failed|inconclusive)$")
    justification: str = Field(..., min_length=10, max_length=500)


class AuditLogQuery(BaseModel):
    """Query params for audit log listing (used as query model)."""
    admin_id: Optional[str] = None
    target_user_id: Optional[str] = None
    action: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


# --------------- Response Schemas ---------------

class AdminUserSummary(BaseModel):
    """Row from admin_user_view — no PII like email or phone."""
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    veteran_status: Optional[bool] = None
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None
    va_linked: Optional[bool] = None
    va_linked_at: Optional[str] = None
    admin_tier: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_login: Optional[str] = None
    disability_rating: Optional[int] = None

    class Config:
        from_attributes = True


class AdminUserDetail(BaseModel):
    """Detailed user view for SUPPORT+ tier (includes email)."""
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    veteran_status: Optional[bool] = None
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None
    va_linked: Optional[bool] = None
    va_linked_at: Optional[str] = None
    admin_tier: Optional[int] = None
    service_branch: Optional[str] = None
    disability_rating: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_login: Optional[str] = None

    class Config:
        from_attributes = True


class UserSessionInfo(BaseModel):
    """Session record for admin inspection."""
    id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    revoked: bool = False


class AuditLogEntry(BaseModel):
    """Single row from admin_audit_log."""
    id: str
    admin_id: str
    admin_email: Optional[str] = None
    admin_tier: int
    action: str
    target_user_id: Optional[str] = None
    target_table: Optional[str] = None
    fields_accessed: Optional[List[str]] = None
    justification: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    verification_result: Optional[str] = None
    created_at: Optional[str] = None


class AdminStats(BaseModel):
    """Aggregate statistics for the admin dashboard."""
    total_users: int = 0
    active_users: int = 0
    inactive_users: int = 0
    verified_emails: int = 0
    va_linked_users: int = 0
    total_sessions: int = 0
    active_sessions: int = 0
    audit_entries_24h: int = 0


class PaginatedUsers(BaseModel):
    """Paginated user listing response."""
    users: List[AdminUserSummary]
    total: int
    limit: int
    offset: int


class MessageResponse(BaseModel):
    """Generic success message."""
    message: str
    detail: Optional[str] = None
PYEOF
```

**Validation:**

```bash
/ganuda/vetassist/backend/venv/bin/python -c "
import ast
ast.parse(open('/ganuda/vetassist/backend/app/schemas/admin.py').read())
print('PASS: admin schemas parse OK')
"
```

---

## Step 4: Create admin_service.py

```bash
cat << 'PYEOF' > /ganuda/vetassist/backend/app/services/admin_service.py
"""
Admin service layer for VetAssist.
All database access uses raw psycopg2 via database_config for consistency
with the existing dashboard/wizard pattern.

Created: 2026-02-02 (JR-VETASSIST-ADMIN-REVISED)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from psycopg2.extras import RealDictCursor

from app.core.database_config import get_db_connection
from app.core.security import hash_password

logger = logging.getLogger(__name__)


class AdminService:
    """
    Service methods for admin operations.
    Every method opens and closes its own connection.
    """

    # ---- User listing (from admin_user_view) ----

    @staticmethod
    def list_users(
        limit: int = 50,
        offset: int = 0,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Return paginated rows from admin_user_view.
        Does NOT expose email or phone (view omits them).

        Returns:
            (rows, total_count)
        """
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                where_clauses = []
                params: list = []

                if is_active is not None:
                    where_clauses.append("is_active = %s")
                    params.append(is_active)

                if search:
                    where_clauses.append(
                        "(first_name ILIKE %s OR last_name ILIKE %s)"
                    )
                    like_val = f"%{search}%"
                    params.extend([like_val, like_val])

                where_sql = ""
                if where_clauses:
                    where_sql = "WHERE " + " AND ".join(where_clauses)

                # Count
                cur.execute(
                    f"SELECT COUNT(*) AS cnt FROM admin_user_view {where_sql}",
                    params,
                )
                total = cur.fetchone()["cnt"]

                # Rows
                cur.execute(
                    f"""
                    SELECT * FROM admin_user_view
                    {where_sql}
                    ORDER BY created_at DESC NULLS LAST
                    LIMIT %s OFFSET %s
                    """,
                    params + [limit, offset],
                )
                rows = cur.fetchall()

            return [_serialize_row(r) for r in rows], total
        finally:
            conn.close()

    # ---- User detail (from users table — SUPPORT+ only) ----

    @staticmethod
    def get_user_detail(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Full user record from users table (includes email, phone).
        Caller must be SUPPORT tier or above.
        """
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, email, first_name, last_name, phone,
                           veteran_status, is_active, email_verified,
                           (va_icn IS NOT NULL) AS va_linked,
                           va_linked_at, admin_tier, service_branch,
                           disability_rating, created_at, updated_at, last_login
                    FROM users
                    WHERE id = %s
                    """,
                    (user_id,),
                )
                row = cur.fetchone()
            if row is None:
                return None
            return _serialize_row(row)
        finally:
            conn.close()

    # ---- Identity verification ----

    @staticmethod
    def verify_identity(user_id: str, result: str) -> bool:
        """
        Record an identity verification outcome.
        Does not modify the users table — only writes to audit log
        (handled by the endpoint via log_admin_action).

        Returns True if user exists, False otherwise.
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE id = %s", (user_id,))
                return cur.fetchone() is not None
        finally:
            conn.close()

    # ---- Password reset ----

    @staticmethod
    def reset_password(user_id: str, new_password: str) -> bool:
        """
        Hash and set a new password for the target user.
        Also revokes all their sessions.

        Returns True if user found and updated, False otherwise.
        """
        hashed = hash_password(new_password)
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s RETURNING id",
                    (hashed, user_id),
                )
                if cur.fetchone() is None:
                    conn.rollback()
                    return False

                # Revoke all active sessions
                cur.execute(
                    "UPDATE user_sessions SET revoked = true WHERE user_id = %s AND revoked = false",
                    (user_id,),
                )
                conn.commit()
            return True
        except Exception:
            conn.rollback()
            logger.exception("Failed to reset password for user %s", user_id)
            return False
        finally:
            conn.close()

    # ---- Toggle active ----

    @staticmethod
    def toggle_active(user_id: str, is_active: bool) -> bool:
        """
        Set user.is_active. If deactivating, also revoke all sessions.

        Returns True if user found and updated.
        """
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET is_active = %s, updated_at = NOW() WHERE id = %s RETURNING id",
                    (is_active, user_id),
                )
                if cur.fetchone() is None:
                    conn.rollback()
                    return False

                if not is_active:
                    cur.execute(
                        "UPDATE user_sessions SET revoked = true WHERE user_id = %s AND revoked = false",
                        (user_id,),
                    )
                conn.commit()
            return True
        except Exception:
            conn.rollback()
            logger.exception("Failed to toggle active for user %s", user_id)
            return False
        finally:
            conn.close()

    # ---- Sessions ----

    @staticmethod
    def get_user_sessions(user_id: str) -> List[Dict[str, Any]]:
        """Return all sessions for a user, newest first."""
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, ip_address, user_agent, created_at,
                           expires_at, revoked
                    FROM user_sessions
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 100
                    """,
                    (user_id,),
                )
                rows = cur.fetchall()
            return [_serialize_row(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def revoke_user_sessions(user_id: str) -> int:
        """Revoke all active sessions for user. Returns count revoked."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE user_sessions
                    SET revoked = true
                    WHERE user_id = %s AND revoked = false
                    RETURNING id
                    """,
                    (user_id,),
                )
                count = cur.rowcount
                conn.commit()
            return count
        except Exception:
            conn.rollback()
            logger.exception("Failed to revoke sessions for user %s", user_id)
            return 0
        finally:
            conn.close()

    # ---- Audit log ----

    @staticmethod
    def get_audit_log(
        admin_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Query admin_audit_log with optional filters.
        Returns (rows, total_count).
        """
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                where_clauses = []
                params: list = []

                if admin_id:
                    where_clauses.append("admin_id = %s")
                    params.append(admin_id)
                if target_user_id:
                    where_clauses.append("target_user_id = %s")
                    params.append(target_user_id)
                if action:
                    where_clauses.append("action = %s")
                    params.append(action)

                where_sql = ""
                if where_clauses:
                    where_sql = "WHERE " + " AND ".join(where_clauses)

                cur.execute(
                    f"SELECT COUNT(*) AS cnt FROM admin_audit_log {where_sql}",
                    params,
                )
                total = cur.fetchone()["cnt"]

                cur.execute(
                    f"""
                    SELECT * FROM admin_audit_log
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    params + [limit, offset],
                )
                rows = cur.fetchall()

            return [_serialize_row(r) for r in rows], total
        finally:
            conn.close()

    # ---- Stats ----

    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """Aggregate stats for the admin dashboard."""
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        COUNT(*) AS total_users,
                        COUNT(*) FILTER (WHERE is_active = true) AS active_users,
                        COUNT(*) FILTER (WHERE is_active = false) AS inactive_users,
                        COUNT(*) FILTER (WHERE email_verified = true) AS verified_emails,
                        COUNT(*) FILTER (WHERE va_icn IS NOT NULL) AS va_linked_users
                    FROM users
                """)
                user_stats = cur.fetchone()

                cur.execute("""
                    SELECT
                        COUNT(*) AS total_sessions,
                        COUNT(*) FILTER (
                            WHERE revoked = false AND expires_at > NOW()
                        ) AS active_sessions
                    FROM user_sessions
                """)
                session_stats = cur.fetchone()

                cur.execute("""
                    SELECT COUNT(*) AS cnt
                    FROM admin_audit_log
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """)
                audit_stats = cur.fetchone()

            return {
                "total_users": user_stats["total_users"],
                "active_users": user_stats["active_users"],
                "inactive_users": user_stats["inactive_users"],
                "verified_emails": user_stats["verified_emails"],
                "va_linked_users": user_stats["va_linked_users"],
                "total_sessions": session_stats["total_sessions"],
                "active_sessions": session_stats["active_sessions"],
                "audit_entries_24h": audit_stats["cnt"],
            }
        finally:
            conn.close()


# ---- Helpers ----

def _serialize_row(row: dict) -> dict:
    """Convert a RealDictRow to a JSON-safe dict (stringify datetimes/uuids)."""
    out = {}
    for k, v in row.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        elif hasattr(v, "hex"):
            # UUID objects
            out[k] = str(v)
        else:
            out[k] = v
    return out
PYEOF
```

**Validation:**

```bash
/ganuda/vetassist/backend/venv/bin/python -c "
import ast
ast.parse(open('/ganuda/vetassist/backend/app/services/admin_service.py').read())
print('PASS: admin_service.py parses OK')
"
```

---

## Step 5: Create admin.py endpoint file

This goes in `app/api/v1/endpoints/admin.py` — a NEW file. We do **NOT** modify `__init__.py`.

```bash
cat << 'PYEOF' > /ganuda/vetassist/backend/app/api/v1/endpoints/admin.py
"""
VetAssist Admin API Endpoints.

All endpoints require admin_tier >= 1 (VIEWER).
Write operations require tier 3+ (ADMIN).
Audit log access requires tier 4 (SECURITY).

Router prefix: /admin (to be wired by human admin in __init__.py)
Created: 2026-02-02 (JR-VETASSIST-ADMIN-REVISED)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import AdminTier, log_admin_action, require_tier
from app.models.user import User
from app.services.admin_service import AdminService
from app.schemas.admin import (
    AdminStats,
    AdminUserDetail,
    AdminUserSummary,
    AuditLogEntry,
    MessageResponse,
    PaginatedUsers,
    ResetPasswordRequest,
    ToggleActiveRequest,
    UserSessionInfo,
    VerifyIdentityRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])


# ------------------------------------------------------------------ #
#  User Listing & Detail
# ------------------------------------------------------------------ #

@router.get("/users", response_model=PaginatedUsers)
def list_users(
    request: Request,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    is_active: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=100),
    admin: User = Depends(require_tier(AdminTier.VIEWER)),
):
    """
    List users from admin_user_view (no email/phone exposed).
    Requires: VIEWER (tier 1+).
    """
    rows, total = AdminService.list_users(
        limit=limit, offset=offset, is_active=is_active, search=search
    )

    log_admin_action(
        admin_user=admin,
        action="list_users",
        request=request,
        target_table="admin_user_view",
        fields_accessed=["id", "first_name", "last_name", "is_active"],
    )

    return PaginatedUsers(users=rows, total=total, limit=limit, offset=offset)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def get_user_detail(
    user_id: str,
    request: Request,
    admin: User = Depends(require_tier(AdminTier.SUPPORT)),
):
    """
    Full user detail including email/phone.
    Requires: SUPPORT (tier 2+).
    """
    detail = AdminService.get_user_detail(user_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="User not found")

    log_admin_action(
        admin_user=admin,
        action="view_user_detail",
        request=request,
        target_user_id=user_id,
        target_table="users",
        fields_accessed=["email", "phone", "service_branch", "disability_rating"],
    )

    return detail


# ------------------------------------------------------------------ #
#  Identity Verification
# ------------------------------------------------------------------ #

@router.post("/users/{user_id}/verify", response_model=MessageResponse)
def verify_identity(
    user_id: str,
    body: VerifyIdentityRequest,
    request: Request,
    admin: User = Depends(require_tier(AdminTier.SUPPORT)),
):
    """
    Record identity verification result for a user.
    Requires: SUPPORT (tier 2+).
    """
    exists = AdminService.verify_identity(user_id, body.result)
    if not exists:
        raise HTTPException(status_code=404, detail="User not found")

    log_admin_action(
        admin_user=admin,
        action="verify_identity",
        request=request,
        target_user_id=user_id,
        justification=body.justification,
        verification_result=body.result,
    )

    return MessageResponse(
        message=f"Identity verification recorded: {body.result}",
        detail=body.justification,
    )


# ------------------------------------------------------------------ #
#  Password Reset
# ------------------------------------------------------------------ #

@router.post("/users/{user_id}/reset-password", response_model=MessageResponse)
def reset_password(
    user_id: str,
    body: ResetPasswordRequest,
    request: Request,
    admin: User = Depends(require_tier(AdminTier.ADMIN)),
):
    """
    Admin-initiated password reset. Revokes all user sessions.
    Requires: ADMIN (tier 3+).
    """
    success = AdminService.reset_password(user_id, body.new_password)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or update failed")

    log_admin_action(
        admin_user=admin,
        action="reset_password",
        request=request,
        target_user_id=user_id,
        justification=body.justification,
    )

    return MessageResponse(
        message="Password reset successful. All sessions revoked.",
        detail=body.justification,
    )


# ------------------------------------------------------------------ #
#  Toggle Active
# ------------------------------------------------------------------ #

@router.post("/users/{user_id}/toggle-active", response_model=MessageResponse)
def toggle_active(
    user_id: str,
    body: ToggleActiveRequest,
    request: Request,
    admin: User = Depends(require_tier(AdminTier.ADMIN)),
):
    """
    Enable or disable a user account. Deactivation revokes all sessions.
    Requires: ADMIN (tier 3+).
    """
    # Prevent self-deactivation
    if str(admin.id) == user_id and not body.is_active:
        raise HTTPException(
            status_code=400, detail="Cannot deactivate your own account"
        )

    success = AdminService.toggle_active(user_id, body.is_active)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or update failed")

    action_word = "activated" if body.is_active else "deactivated"
    log_admin_action(
        admin_user=admin,
        action=f"toggle_active_{action_word}",
        request=request,
        target_user_id=user_id,
        justification=body.justification,
    )

    return MessageResponse(
        message=f"User {action_word} successfully.",
        detail=body.justification,
    )


# ------------------------------------------------------------------ #
#  Sessions
# ------------------------------------------------------------------ #

@router.get("/users/{user_id}/sessions")
def get_user_sessions(
    user_id: str,
    request: Request,
    admin: User = Depends(require_tier(AdminTier.SUPPORT)),
):
    """
    List all sessions for a user.
    Requires: SUPPORT (tier 2+).
    """
    sessions = AdminService.get_user_sessions(user_id)

    log_admin_action(
        admin_user=admin,
        action="view_user_sessions",
        request=request,
        target_user_id=user_id,
        target_table="user_sessions",
    )

    return {"user_id": user_id, "sessions": sessions, "total": len(sessions)}


@router.post("/users/{user_id}/revoke-sessions", response_model=MessageResponse)
def revoke_user_sessions(
    user_id: str,
    request: Request,
    admin: User = Depends(require_tier(AdminTier.ADMIN)),
):
    """
    Revoke all active sessions for a user (force logout).
    Requires: ADMIN (tier 3+).
    """
    count = AdminService.revoke_user_sessions(user_id)

    log_admin_action(
        admin_user=admin,
        action="revoke_all_sessions",
        request=request,
        target_user_id=user_id,
        target_table="user_sessions",
    )

    return MessageResponse(message=f"Revoked {count} active session(s).")


# ------------------------------------------------------------------ #
#  Audit Log
# ------------------------------------------------------------------ #

@router.get("/audit-log")
def get_audit_log(
    request: Request,
    admin_id: Optional[str] = Query(default=None),
    target_user_id: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(require_tier(AdminTier.SECURITY)),
):
    """
    Query the admin audit log.
    Requires: SECURITY (tier 4).
    """
    rows, total = AdminService.get_audit_log(
        admin_id=admin_id,
        target_user_id=target_user_id,
        action=action,
        limit=limit,
        offset=offset,
    )

    log_admin_action(
        admin_user=admin,
        action="view_audit_log",
        request=request,
        target_table="admin_audit_log",
    )

    return {"entries": rows, "total": total, "limit": limit, "offset": offset}


# ------------------------------------------------------------------ #
#  Stats
# ------------------------------------------------------------------ #

@router.get("/stats", response_model=AdminStats)
def get_admin_stats(
    request: Request,
    admin: User = Depends(require_tier(AdminTier.VIEWER)),
):
    """
    Aggregate statistics for admin dashboard.
    Requires: VIEWER (tier 1+).
    """
    stats = AdminService.get_stats()

    log_admin_action(
        admin_user=admin,
        action="view_stats",
        request=request,
    )

    return AdminStats(**stats)
PYEOF
```

**Validation:**

```bash
/ganuda/vetassist/backend/venv/bin/python -c "
import ast
ast.parse(open('/ganuda/vetassist/backend/app/api/v1/endpoints/admin.py').read())
print('PASS: admin.py endpoint parses OK')
"
```

---

## Step 6: Validate all files parse together

```bash
/ganuda/vetassist/backend/venv/bin/python -c "
import ast, sys
files = [
    '/ganuda/vetassist/backend/app/api/v1/dependencies.py',
    '/ganuda/vetassist/backend/app/core/rbac.py',
    '/ganuda/vetassist/backend/app/schemas/admin.py',
    '/ganuda/vetassist/backend/app/services/admin_service.py',
    '/ganuda/vetassist/backend/app/api/v1/endpoints/admin.py',
]
ok = True
for f in files:
    try:
        ast.parse(open(f).read())
        print(f'PASS: {f}')
    except SyntaxError as e:
        print(f'FAIL: {f} -> {e}')
        ok = False
if ok:
    print('ALL FILES PARSE OK')
else:
    print('SOME FILES FAILED')
    sys.exit(1)
"
```

---

## Step 7: Validate database objects still exist

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT 'admin_audit_log' AS tbl, count(*) FROM admin_audit_log
UNION ALL
SELECT 'admin_user_view', count(*) FROM admin_user_view
UNION ALL
SELECT 'user_sessions', count(*) FROM user_sessions
UNION ALL
SELECT 'users', count(*) FROM users;
"
```

Expected: Four rows with counts (may be zero for audit log). If any table is missing, STOP and notify TPM.

---

## Step 8: Smoke test imports (in virtualenv)

```bash
cd /ganuda/vetassist/backend && /ganuda/vetassist/backend/venv/bin/python -c "
from app.api.v1.dependencies import get_db, get_current_user
print('PASS: dependencies re-exports work')

from app.core.rbac import AdminTier, require_tier, log_admin_action
print('PASS: rbac imports work')

from app.schemas.admin import AdminStats, PaginatedUsers, AdminUserDetail
print('PASS: admin schemas import')

from app.services.admin_service import AdminService
print('PASS: admin service imports')

# Endpoint import last (depends on all the above)
from app.api.v1.endpoints.admin import router
print('PASS: admin endpoint router imports')
print('ALL IMPORTS OK')
"
```

---

## HUMAN ADMIN ACTION REQUIRED (Post-Execution)

After the Jr completes the five file creations and all validations pass, the **human admin** (Darrell) must manually update `app/api/v1/__init__.py` to wire up the new routers. Add these lines:

1. In the import block at the top, add:
   ```python
   from app.api.v1.endpoints import admin, audit, workbench_documents
   ```

2. After the existing `include_router` blocks, add:
   ```python
   api_router.include_router(
       admin.router,
       prefix="/admin",
       tags=["admin"]
   )

   api_router.include_router(
       audit.router,
       prefix="/audit",
       tags=["audit"]
   )

   api_router.include_router(
       workbench_documents.router,
       prefix="/workbench-documents",
       tags=["workbench-documents"]
   )
   ```

3. Remove the TODO comment block at lines 140-143 of `__init__.py`.

4. Restart the backend: `sudo systemctl restart vetassist-backend`

**The Jr executor must NOT perform this step.** The `__init__.py` is protected after the #528 incident.

---

## Rollback Plan

If anything breaks after wiring:

```bash
# Revert __init__.py to remove admin/audit/workbench_documents imports
# Then restart:
sudo systemctl restart vetassist-backend

# The five new files can be deleted if needed:
rm /ganuda/vetassist/backend/app/api/v1/dependencies.py
rm /ganuda/vetassist/backend/app/core/rbac.py
rm /ganuda/vetassist/backend/app/schemas/admin.py
rm /ganuda/vetassist/backend/app/services/admin_service.py
rm /ganuda/vetassist/backend/app/api/v1/endpoints/admin.py
```

---

## Completion Criteria

All of the following must be true:
- [ ] Five Python files created at the correct paths
- [ ] All five files pass `ast.parse` validation
- [ ] Database objects confirmed present via psql
- [ ] Import smoke test passes in virtualenv
- [ ] `__init__.py` was NOT modified by the executor
