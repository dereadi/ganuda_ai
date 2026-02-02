# Jr Instruction: VetAssist Admin Backend — Models, RBAC, Schemas

**Task:** JR-VETASSIST-ADMIN-BACKEND-MODELS
**Priority:** P1
**Assigned:** Software Engineer Jr.
**Depends On:** JR-VETASSIST-ADMIN-SQL-MIGRATION
**Platform:** Bluefin (192.168.132.222)
**Council Vote:** #8365 — APPROVED

## Objective

Add admin infrastructure to the backend:
1. Add `admin_tier` column to User SQLAlchemy model
2. Create AdminAuditLog model
3. Create RBAC middleware (require_tier dependency)
4. Create admin Pydantic schemas
5. Update `to_dict()` to include admin fields

## Step 1: Update User Model

**File:** `/ganuda/vetassist/backend/app/models/user.py`

<<<<<<< SEARCH
from sqlalchemy import Column, String, Boolean, Date, Integer, DateTime, ForeignKey, Text
=======
from sqlalchemy import Column, String, Boolean, Date, Integer, DateTime, ForeignKey, Text, ARRAY
>>>>>>> REPLACE

<<<<<<< SEARCH
    # VA Account Linking
    va_icn = Column(String(50), unique=True, nullable=True)
    va_linked_at = Column(DateTime(timezone=True), nullable=True)
=======
    # VA Account Linking
    va_icn = Column(String(50), unique=True, nullable=True)
    va_linked_at = Column(DateTime(timezone=True), nullable=True)

    # Admin RBAC (Council Vote #8365)
    # Tier 0=user, 1=public, 2=admin, 3=security, 4=system
    admin_tier = Column(Integer, default=0)
>>>>>>> REPLACE

<<<<<<< SEARCH
            "va_linked": self.va_icn is not None,
            "va_linked_at": self.va_linked_at.isoformat() if self.va_linked_at else None
        }
=======
            "va_linked": self.va_icn is not None,
            "va_linked_at": self.va_linked_at.isoformat() if self.va_linked_at else None,
            "admin_tier": self.admin_tier or 0,
            "is_admin": (self.admin_tier or 0) >= 2
        }
>>>>>>> REPLACE

## Step 2: Create AdminAuditLog Model

**Create:** `/ganuda/vetassist/backend/app/models/admin.py`

```python
"""
Admin Audit Log model
Tracks all admin access to PII for 38 CFR 0.605 compliance
Council Vote #8365
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
import uuid

from app.core.database import Base
from app.core.types import PortableUUID


class AdminAuditLog(Base):
    """Audit log for admin PII access — 38 CFR 0.605 principle 9"""

    __tablename__ = "admin_audit_log"

    id = Column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    admin_id = Column(PortableUUID(), nullable=False)
    admin_email = Column(String(255))
    admin_tier = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    target_user_id = Column(PortableUUID(), nullable=True)
    target_table = Column(String(100), nullable=True)
    fields_accessed = Column(ARRAY(Text), nullable=True)
    justification = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(PortableUUID(), nullable=True)
    verification_result = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AdminAudit {self.action} by {self.admin_id} at {self.created_at}>"
```

## Step 3: Create RBAC Middleware

**Create:** `/ganuda/vetassist/backend/app/core/rbac.py`

```python
"""
Role-Based Access Control middleware
4-Tier RBAC per Council Vote #8365

Tier 0: Regular user
Tier 1: Public (aggregate stats only)
Tier 2: Admin (masked PII, user management)
Tier 3: Security (full PII, time-limited, logged)
Tier 4: System (credential material, automated only)
"""

from enum import IntEnum
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.admin import AdminAuditLog

logger = logging.getLogger(__name__)


class AdminTier(IntEnum):
    USER = 0
    PUBLIC = 1
    ADMIN = 2
    SECURITY = 3
    SYSTEM = 4


def require_tier(minimum_tier: AdminTier):
    """
    FastAPI dependency that checks admin tier level.
    Logs the access attempt to admin_audit_log.

    Usage:
        @router.get("/admin/users")
        async def list_users(admin = Depends(require_tier(AdminTier.ADMIN))):
            ...
    """
    async def checker(
        request: Request,
        current_user = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        user_tier = getattr(current_user, 'admin_tier', 0) or 0

        if user_tier < minimum_tier:
            logger.warning(
                f"Admin access denied: user {current_user.id} "
                f"(tier {user_tier}) attempted tier {minimum_tier} action"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient admin privileges"
            )

        # Return user with request context for audit logging
        current_user._request = request
        current_user._db = db
        return current_user

    return checker


async def log_admin_action(
    db: Session,
    admin_user,
    action: str,
    request: Request,
    target_user_id=None,
    target_table: str = None,
    fields_accessed: list = None,
    justification: str = None,
    verification_result: str = None
):
    """
    Log an admin action to the audit trail.
    Required by 38 CFR 0.605 principle 9: accounting of disclosures.
    """
    audit_entry = AdminAuditLog(
        admin_id=admin_user.id,
        admin_email=admin_user.email,
        admin_tier=getattr(admin_user, 'admin_tier', 0) or 0,
        action=action,
        target_user_id=target_user_id,
        target_table=target_table,
        fields_accessed=fields_accessed,
        justification=justification,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        verification_result=verification_result
    )
    db.add(audit_entry)
    db.commit()

    logger.info(
        f"[ADMIN AUDIT] {action} by admin {admin_user.id} "
        f"(tier {admin_user.admin_tier}) target={target_user_id}"
    )
```

## Step 4: Create Admin Schemas

**Create:** `/ganuda/vetassist/backend/app/schemas/admin.py`

```python
"""
Pydantic schemas for admin endpoints
Masked user views and audit log entries
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AdminUserView(BaseModel):
    """Tier 2 admin view of a user — masked PII"""
    id: str
    first_name: Optional[str]
    last_name: str  # Masked: "D***"
    veteran_status: bool
    is_active: bool
    email_verified: bool
    va_linked: bool
    va_linked_at: Optional[str] = None
    admin_tier: int = 0
    created_at: str
    updated_at: Optional[str] = None
    last_login: Optional[str] = None
    disability_rating: Optional[int] = None

    class Config:
        from_attributes = True


class AdminUserList(BaseModel):
    """Paginated list of admin user views"""
    users: List[AdminUserView]
    total: int
    page: int
    page_size: int


class IdentityVerifyRequest(BaseModel):
    """Challenge-response identity verification"""
    claimed_email: str


class IdentityVerifyResponse(BaseModel):
    """Result of identity verification"""
    match: bool
    user_id: str


class PasswordResetResponse(BaseModel):
    """Result of password reset trigger"""
    success: bool
    message: str


class AdminAuditEntry(BaseModel):
    """Single admin audit log entry"""
    id: str
    admin_id: str
    admin_email: Optional[str]
    admin_tier: int
    action: str
    target_user_id: Optional[str]
    fields_accessed: Optional[List[str]]
    justification: Optional[str]
    verification_result: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class AdminAuditList(BaseModel):
    """Paginated audit log"""
    entries: List[AdminAuditEntry]
    total: int


class AdminStats(BaseModel):
    """Aggregate statistics — Tier 1 safe"""
    total_users: int
    active_users: int
    verified_users: int
    va_linked_users: int
    veteran_users: int
    total_chat_sessions: int
    total_chat_messages: int
```

## Step 5: Update Auth Schemas — Add admin fields to UserResponse

**File:** `/ganuda/vetassist/backend/app/schemas/auth.py`

<<<<<<< SEARCH
    va_linked: bool = False
    va_linked_at: Optional[str] = None

    class Config:
        from_attributes = True
=======
    va_linked: bool = False
    va_linked_at: Optional[str] = None
    admin_tier: int = 0
    is_admin: bool = False

    class Config:
        from_attributes = True
>>>>>>> REPLACE

## Validation

After applying all changes:

```bash
cd /ganuda/vetassist/backend
python3 -c "
from app.models.user import User
from app.models.admin import AdminAuditLog
from app.core.rbac import AdminTier, require_tier
from app.schemas.admin import AdminUserView, AdminStats
print('User admin_tier:', hasattr(User, 'admin_tier'))
print('AdminAuditLog table:', AdminAuditLog.__tablename__)
print('AdminTier.ADMIN:', AdminTier.ADMIN)
print('All imports OK')
"
```
