# Jr Instruction: VetAssist VA Session Management - Phase 6: Logout & Session Management

## Priority: MEDIUM
## Estimated Effort: Small
## Dependencies: Phase 1-5

---

## Objective

Implement logout functionality and session management endpoints:
1. Logout endpoint (revoke current session)
2. List active sessions
3. Force logout all sessions
4. Session activity viewing

---

## Context

Users need to be able to log out (revoking their JWT) and manage their active sessions. This is important for security when a device is lost or compromised.

Reference: `/ganuda/docs/ultrathink/ULTRATHINK-VETASSIST-VA-SESSION-MANAGEMENT-JAN20-2026.md`

---

## Implementation

### File: `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`

Add logout and session management endpoints:

```python
"""
Authentication Endpoints
Cherokee AI Federation - For Seven Generations
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.services.va_session_service import get_session_service, VASessionService
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class SessionInfo(BaseModel):
    """Session information for display."""
    id: str
    created_at: str
    expires_at: str
    device_info: Optional[dict]
    is_current: bool


class SessionListResponse(BaseModel):
    """Response for session list."""
    sessions: List[SessionInfo]
    total: int


# Dependency to get current user from JWT
async def get_current_user(
    request: Request,
    session_service: VASessionService = Depends(get_session_service)
):
    """Extract and validate user from JWT."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.split(" ")[1]
    claims = await session_service.validate_jwt(token)

    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"user_id": claims["sub"], "jwt_id": claims["jti"], "token": token}


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    session_service: VASessionService = Depends(get_session_service)
):
    """
    Logout current session.
    Revokes the JWT so it can no longer be used.
    """
    await session_service.revoke_session(
        jwt_id=current_user["jwt_id"],
        user_id=current_user["user_id"]
    )

    logger.info(f"[Auth] User {current_user['user_id'][:8]}... logged out")

    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all_sessions(
    current_user: dict = Depends(get_current_user),
    session_service: VASessionService = Depends(get_session_service)
):
    """
    Logout all sessions for current user.
    Use when device is lost/stolen or for security.
    """
    await session_service.revoke_all_sessions(current_user["user_id"])

    logger.info(f"[Auth] User {current_user['user_id'][:8]}... logged out of all sessions")

    return {"message": "Successfully logged out of all sessions"}


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    current_user: dict = Depends(get_current_user),
    session_service: VASessionService = Depends(get_session_service)
):
    """
    List all active sessions for current user.
    """
    async with session_service.db.acquire() as conn:
        sessions = await conn.fetch(
            """SELECT id, jwt_id, device_info, created_at, expires_at
               FROM vetassist_sessions
               WHERE user_id = $1 AND revoked_at IS NULL AND expires_at > NOW()
               ORDER BY created_at DESC""",
            current_user["user_id"]
        )

    session_list = [
        SessionInfo(
            id=str(s["id"]),
            created_at=s["created_at"].isoformat(),
            expires_at=s["expires_at"].isoformat(),
            device_info=s["device_info"],
            is_current=(s["jwt_id"] == current_user["jwt_id"])
        )
        for s in sessions
    ]

    return SessionListResponse(sessions=session_list, total=len(session_list))


@router.delete("/sessions/{session_id}")
async def revoke_specific_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    session_service: VASessionService = Depends(get_session_service)
):
    """
    Revoke a specific session by ID.
    """
    async with session_service.db.acquire() as conn:
        # Verify session belongs to user
        session = await conn.fetchrow(
            """SELECT jwt_id FROM vetassist_sessions
               WHERE id = $1 AND user_id = $2""",
            session_id,
            current_user["user_id"]
        )

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        await session_service.revoke_session(session["jwt_id"], current_user["user_id"])

    return {"message": "Session revoked"}


@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    session_service: VASessionService = Depends(get_session_service)
):
    """
    Get current user information.
    """
    async with session_service.db.acquire() as conn:
        user = await conn.fetchrow(
            """SELECT id, va_icn, va_veteran_status, email, first_name, last_name,
                      created_at, last_login_at
               FROM vetassist_users
               WHERE id = $1""",
            current_user["user_id"]
        )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user["id"]),
        "va_icn": user["va_icn"],
        "va_veteran_status": user["va_veteran_status"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "created_at": user["created_at"].isoformat() if user["created_at"] else None,
        "last_login_at": user["last_login_at"].isoformat() if user["last_login_at"] else None
    }
```

---

### Register Router

Add to `/ganuda/vetassist/backend/app/api/v1/__init__.py`:

```python
from app.api.v1.endpoints import auth

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
```

---

### Frontend Logout Component

Add to `/ganuda/vetassist/frontend/app/components/UserMenu.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';

export function UserMenu() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    await logout();
    router.push('/');
  };

  if (!user) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 text-gray-700 hover:text-gray-900"
      >
        <span>{user.vaLinked ? 'VA Verified' : 'User'}</span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10">
          <a
            href="/sessions"
            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
          >
            Manage Sessions
          </a>
          <button
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
          >
            {isLoggingOut ? 'Signing out...' : 'Sign out'}
          </button>
        </div>
      )}
    </div>
  );
}
```

---

### Sessions Management Page

### File: `/ganuda/vetassist/frontend/app/(protected)/sessions/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import { fetchWithAuth } from '../../lib/api';

interface Session {
  id: string;
  created_at: string;
  expires_at: string;
  device_info: { user_agent?: string; ip?: string } | null;
  is_current: boolean;
}

export default function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const res = await fetchWithAuth('/api/v1/auth/sessions');
      const data = await res.json();
      setSessions(data.sessions);
    } catch (e) {
      console.error('Failed to load sessions:', e);
    } finally {
      setLoading(false);
    }
  };

  const revokeSession = async (sessionId: string) => {
    try {
      await fetchWithAuth(`/api/v1/auth/sessions/${sessionId}`, { method: 'DELETE' });
      loadSessions();
    } catch (e) {
      console.error('Failed to revoke session:', e);
    }
  };

  const revokeAll = async () => {
    if (!confirm('This will sign you out of all devices. Continue?')) return;
    try {
      await fetchWithAuth('/api/v1/auth/logout-all', { method: 'POST' });
      window.location.href = '/';
    } catch (e) {
      console.error('Failed to revoke all sessions:', e);
    }
  };

  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Active Sessions</h1>
          <button
            onClick={revokeAll}
            className="px-4 py-2 text-red-600 border border-red-600 rounded-md hover:bg-red-50"
          >
            Sign out everywhere
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : (
          <div className="space-y-4">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`p-4 border rounded-lg ${session.is_current ? 'border-green-500 bg-green-50' : 'border-gray-200'}`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium">
                      {session.is_current && (
                        <span className="text-green-600 mr-2">Current session</span>
                      )}
                      {session.device_info?.user_agent?.slice(0, 50) || 'Unknown device'}
                    </div>
                    <div className="text-sm text-gray-500">
                      Created: {new Date(session.created_at).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-500">
                      Expires: {new Date(session.expires_at).toLocaleString()}
                    </div>
                  </div>
                  {!session.is_current && (
                    <button
                      onClick={() => revokeSession(session.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Revoke
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
```

---

## Verification

1. Test logout:
- Login via VA.gov
- Click logout
- Verify redirect to home
- Verify token cleared from localStorage

2. Test session list:
- Login from multiple browsers/devices
- Check /sessions page shows all sessions
- Verify current session marked

3. Test session revocation:
- Revoke session from another device
- Verify that device's token no longer works

4. Test logout-all:
- Login from multiple devices
- Click "Sign out everywhere"
- Verify all devices logged out

---

## Success Criteria

- [ ] Logout endpoint working
- [ ] Session list endpoint working
- [ ] Session revocation working
- [ ] Logout-all working
- [ ] Frontend logout component
- [ ] Sessions management page

---

*Cherokee AI Federation - For Seven Generations*
