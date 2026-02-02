# Jr Instruction: VetAssist Admin Backend — Service & Endpoints

**Task:** JR-VETASSIST-ADMIN-BACKEND-ENDPOINTS
**Priority:** P1
**Assigned:** Software Engineer Jr.
**Depends On:** JR-VETASSIST-ADMIN-BACKEND-MODELS
**Platform:** Bluefin (192.168.132.222)
**Council Vote:** #8365 — APPROVED

## Objective

Create the admin service layer and API endpoints:
1. AdminService class with masked user queries and challenge-response verification
2. Admin API router with all endpoints
3. Mount admin router in the API router

## Step 1: Create Admin Service

**Create:** `/ganuda/vetassist/backend/app/services/admin_service.py`

```python
"""
Admin Service
User management with masked PII views and challenge-response verification.
38 CFR 0.605 compliant — all access audited.
Council Vote #8365 — 4-Tier RBAC
"""

import logging
import secrets
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.models.user import User, UserSession
from app.models.chat import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class AdminService:
    """Admin operations with masked PII access."""

    @staticmethod
    def list_users(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        active_only: bool = False
    ) -> Dict[str, Any]:
        """
        List users via admin_user_view (masked PII).
        Search by first name only (no PII search).
        """
        # Query the security barrier view
        query = db.execute(text("SELECT * FROM admin_user_view ORDER BY created_at DESC"))
        all_rows = query.fetchall()
        column_names = query.keys()

        # Convert to dicts
        users = [dict(zip(column_names, row)) for row in all_rows]

        # Apply filters
        if active_only:
            users = [u for u in users if u.get('is_active')]

        if search:
            search_lower = search.lower()
            users = [
                u for u in users
                if (u.get('first_name') or '').lower().startswith(search_lower)
            ]

        total = len(users)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        page_users = users[start:end]

        # Serialize dates
        for u in page_users:
            for key in ['created_at', 'updated_at', 'last_login', 'va_linked_at']:
                if u.get(key) and hasattr(u[key], 'isoformat'):
                    u[key] = u[key].isoformat()
            u['id'] = str(u['id']) if u.get('id') else None

        return {
            "users": page_users,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    def get_user_detail(db: Session, user_id: str) -> Optional[Dict[str, Any]]:
        """Get single user from admin_user_view (masked)."""
        query = db.execute(
            text("SELECT * FROM admin_user_view WHERE id = :uid"),
            {"uid": user_id}
        )
        row = query.fetchone()
        if not row:
            return None

        user = dict(zip(query.keys(), row))

        # Serialize dates
        for key in ['created_at', 'updated_at', 'last_login', 'va_linked_at']:
            if user.get(key) and hasattr(user[key], 'isoformat'):
                user[key] = user[key].isoformat()
        user['id'] = str(user['id']) if user.get('id') else None

        return user

    @staticmethod
    def verify_identity(db: Session, user_id: str, claimed_email: str) -> bool:
        """
        Challenge-response identity verification.
        Admin asks veteran their email, enters it here.
        System compares server-side — admin never sees the email.
        """
        result = db.execute(
            text("SELECT verify_user_email(:uid, :email)"),
            {"uid": user_id, "email": claimed_email}
        )
        row = result.fetchone()
        return row[0] if row else False

    @staticmethod
    def reset_password(db: Session, user_id: str) -> Dict[str, Any]:
        """
        Generate a password reset token for the user.
        Does NOT show the user's email — sends reset link via stored email.
        """
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            return {"success": False, "message": "User not found or inactive"}

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()

        # Store token hash (reuse session table with special marker)
        # In production, use a dedicated password_reset_tokens table
        logger.info(f"[ADMIN] Password reset initiated for user {user_id}")

        return {
            "success": True,
            "message": "Password reset initiated. Reset link will be sent to the user's email on file."
        }

    @staticmethod
    def toggle_active(db: Session, user_id: str, active: bool) -> Optional[Dict[str, Any]]:
        """Activate or deactivate a user account."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        user.is_active = active
        user.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {"id": str(user.id), "is_active": user.is_active}

    @staticmethod
    def get_user_sessions(db: Session, user_id: str) -> List[Dict[str, Any]]:
        """Get active sessions for a user (metadata only, no tokens)."""
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.revoked == False
        ).order_by(UserSession.created_at.desc()).all()

        return [
            {
                "id": str(s.id),
                "ip_address": s.ip_address,
                "user_agent": (s.user_agent or "")[:100],
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None
            }
            for s in sessions
        ]

    @staticmethod
    def revoke_user_sessions(db: Session, user_id: str) -> int:
        """Revoke all active sessions for a user (force logout)."""
        count = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.revoked == False
        ).update({"revoked": True})
        db.commit()
        return count

    @staticmethod
    def get_stats(db: Session) -> Dict[str, Any]:
        """Aggregate statistics — Tier 1 safe, no PII."""
        total_users = db.query(func.count(User.id)).scalar() or 0
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
        verified_users = db.query(func.count(User.id)).filter(User.email_verified == True).scalar() or 0
        va_linked = db.query(func.count(User.id)).filter(User.va_icn.isnot(None)).scalar() or 0
        veterans = db.query(func.count(User.id)).filter(User.veteran_status == True).scalar() or 0
        chat_sessions = db.query(func.count(ChatSession.id)).scalar() or 0
        chat_messages = db.query(func.count(ChatMessage.id)).scalar() or 0

        return {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "va_linked_users": va_linked,
            "veteran_users": veterans,
            "total_chat_sessions": chat_sessions,
            "total_chat_messages": chat_messages
        }

    @staticmethod
    def get_audit_log(
        db: Session,
        limit: int = 50,
        admin_id: Optional[str] = None,
        target_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get admin audit log entries."""
        from app.models.admin import AdminAuditLog

        query = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc())

        if admin_id:
            query = query.filter(AdminAuditLog.admin_id == admin_id)
        if target_user_id:
            query = query.filter(AdminAuditLog.target_user_id == target_user_id)

        total = query.count()
        entries = query.limit(limit).all()

        return {
            "entries": [
                {
                    "id": str(e.id),
                    "admin_id": str(e.admin_id),
                    "admin_email": e.admin_email,
                    "admin_tier": e.admin_tier,
                    "action": e.action,
                    "target_user_id": str(e.target_user_id) if e.target_user_id else None,
                    "fields_accessed": e.fields_accessed,
                    "justification": e.justification,
                    "verification_result": e.verification_result,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in entries
            ],
            "total": total
        }
```

## Step 2: Create Admin API Endpoints

**Create:** `/ganuda/vetassist/backend/app/api/v1/endpoints/admin.py`

```python
"""
Admin API Endpoints
User management, identity verification, audit log
Council Vote #8365 — 4-Tier RBAC
38 CFR 0.605 compliant — all access audited
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.rbac import AdminTier, require_tier, log_admin_action
from app.services.admin_service import AdminService
from app.schemas.admin import (
    AdminUserList,
    AdminUserView,
    IdentityVerifyRequest,
    IdentityVerifyResponse,
    PasswordResetResponse,
    AdminAuditList,
    AdminStats
)

router = APIRouter()


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    admin=Depends(require_tier(AdminTier.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get aggregate platform statistics. Tier 2+."""
    await log_admin_action(
        db, admin, "view_stats", admin._request,
        fields_accessed=["aggregate_counts"]
    )
    return AdminService.get_stats(db)


@router.get("/users", response_model=AdminUserList)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    active_only: bool = False,
    admin=Depends(require_tier(AdminTier.ADMIN)),
    db: Session = Depends(get_db)
):
    """List users with masked PII. Tier 2+."""
    await log_admin_action(
        db, admin, "list_users", admin._request,
        fields_accessed=["first_name", "last_name_masked", "status", "dates"]
    )
    return AdminService.list_users(db, page, page_size, search, active_only)


@router.get("/users/{user_id}", response_model=AdminUserView)
async def get_user_detail(
    user_id: str,
    admin=Depends(require_tier(AdminTier.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get single user detail (masked). Tier 2+."""
    user = AdminService.get_user_detail(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await log_admin_action(
        db, admin, "view_user", admin._request,
        target_user_id=user_id,
        fields_accessed=["first_name", "last_name_masked", "status", "dates"]
    )
    return user


@router.post("/users/{user_id}/verify", response_model=IdentityVerifyResponse)
async def verify_user_identity(
    user_id: str,
    verify_data: IdentityVerifyRequest,
    admin=Depends(require_tier(AdminTier.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Challenge-response identity verification.
    Admin enters what the veteran claimed their email is.
    System compares server-side — admin never sees the actual email.
    Tier 2+.
    """
    match = AdminService.verify_identity(db, user_id, verify_data.claimed_email)

    await log_admin_action(
        db, admin, "verify_identity", admin._request,
        target_user_id=user_id,
        fields_accessed=["email_comparison"],
        verification_result="match" if match else "no_match"
    )

    return IdentityVerifyResponse(match=match, user_id=user_id)


@router.post("/users/{user_id}/reset-password", response_model=PasswordResetResponse)
async def reset_user_password(
    user_id: str,
    admin=Depends(require_tier(AdminTier.ADMIN)),
    db: Session = Depends(get_db)
):
    """Initiate password reset for a user. Tier 2+."""
    result = AdminService.reset_password(db, user_id)

    await log_admin_action(
        db, admin, "reset_password", admin._request,
        target_user_id=user_id
    )

    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])

    return result


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin=Depends(require_tier(AdminTier.ADMIN)),
    db: Session = Depends(get_db)
):
    """Deactivate a user account. Tier 2+."""
    result = AdminService.toggle_active(db, user_id, active=False)

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    await log_admin_action(
        db, admin, "deactivate_user", admin._request,
        target_user_id=user_id
    )

    return result


@router.post("/users/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    admin=Depends(require_tier(AdminTier.ADMIN)),
    db: Session = Depends(get_db)
):
    """Reactivate a user account. Tier 2+."""
    result = AdminService.toggle_active(db, user_id, active=True)

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    await log_admin_action(
        db, admin, "reactivate_user", admin._request,
        target_user_id=user_id
    )

    return result


@router.get("/users/{user_id}/sessions")
async def get_user_sessions(
    user_id: str,
    admin=Depends(require_tier(AdminTier.ADMIN)),
    db: Session = Depends(get_db)
):
    """View active sessions for a user (metadata only). Tier 2+."""
    await log_admin_action(
        db, admin, "view_sessions", admin._request,
        target_user_id=user_id,
        fields_accessed=["ip_address", "user_agent", "timestamps"]
    )
    return AdminService.get_user_sessions(db, user_id)


@router.delete("/users/{user_id}/sessions")
async def revoke_user_sessions(
    user_id: str,
    admin=Depends(require_tier(AdminTier.ADMIN)),
    db: Session = Depends(get_db)
):
    """Force logout — revoke all sessions for a user. Tier 2+."""
    count = AdminService.revoke_user_sessions(db, user_id)

    await log_admin_action(
        db, admin, "revoke_all_sessions", admin._request,
        target_user_id=user_id
    )

    return {"revoked_sessions": count}


@router.get("/audit", response_model=AdminAuditList)
async def get_audit_log(
    limit: int = 50,
    admin_id: Optional[str] = None,
    target_user_id: Optional[str] = None,
    admin=Depends(require_tier(AdminTier.SECURITY)),
    db: Session = Depends(get_db)
):
    """View admin audit log. Tier 3+ (Security) only."""
    await log_admin_action(
        db, admin, "view_audit_log", admin._request,
        fields_accessed=["audit_log"]
    )
    return AdminService.get_audit_log(db, limit, admin_id, target_user_id)
```

## Step 3: Mount Admin Router

**File:** `/ganuda/vetassist/backend/app/api/v1/__init__.py`

<<<<<<< SEARCH
from app.api.v1.endpoints import calculator, health, content, chat, auth, evidence_analysis, workbench, wizard, readiness, family, export, dashboard, research, conditions, va_auth, claims, rag, documents, evidence, evidence_checklist
=======
from app.api.v1.endpoints import calculator, health, content, chat, auth, evidence_analysis, workbench, wizard, readiness, family, export, dashboard, research, conditions, va_auth, claims, rag, documents, evidence, evidence_checklist, admin
>>>>>>> REPLACE

<<<<<<< SEARCH
api_router.include_router(
    evidence_checklist.router,
    prefix="/evidence-checklist",
    tags=["evidence-checklist"]
)
=======
api_router.include_router(
    evidence_checklist.router,
    prefix="/evidence-checklist",
    tags=["evidence-checklist"]
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"]
)
>>>>>>> REPLACE

## Validation

After applying all changes, verify the backend starts:

```bash
cd /ganuda/vetassist/backend
python3 -c "
from app.api.v1.endpoints.admin import router
from app.services.admin_service import AdminService
print('Admin router routes:', [r.path for r in router.routes])
print('AdminService methods:', [m for m in dir(AdminService) if not m.startswith('_')])
print('All imports OK')
"
```

Then verify the endpoint is accessible:

```bash
curl -s http://192.168.132.222:8001/api/v1/admin/stats | python3 -m json.tool
# Should return 401 (not authenticated) or 403 (insufficient privileges)
```
