# JR-VETASSIST-VA-LINKING-PHASE3-CALLBACK-JAN31-2026

## Metadata
- **Priority:** P1
- **Jr Type:** Engineering
- **Target Node:** sasass2 (192.168.132.200)
- **Category:** VetAssist — VA Account Linking Phase 3 (OAuth Callback)
- **Depends On:** JR-VETASSIST-VA-LINKING-PHASE1-MODEL-FIX-JAN31-2026
- **Council Vote:** ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026

## Objective

Modify the VA OAuth callback to detect when a veteran's ICN is already linked to a local user account. If linked, issue a standard auth JWT (signed with SECRET_KEY) instead of a VA-only JWT, enabling unified login.

## Step 1: Add Depends Import

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/va_auth.py`

<<<<<<< SEARCH
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
=======
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
>>>>>>> REPLACE

## Step 2: Add db Dependency to Callback Signature

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/va_auth.py`

<<<<<<< SEARCH
@router.get("/va/callback")
async def va_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from VA"),
    state: str = Query(..., description="State for CSRF verification")
):
=======
@router.get("/va/callback")
async def va_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from VA"),
    state: str = Query(..., description="State for CSRF verification"),
    db: SASession = Depends(get_db)
):
>>>>>>> REPLACE

## Step 3: Add Linked-Login Logic to Callback

Replace the session creation and redirect section with linked-login check.

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/va_auth.py`

<<<<<<< SEARCH
        # Create VetAssist session with encrypted token storage
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

        # Redirect with JWT token
        frontend_url = f"https://vetassist.ganuda.us/va-success?token={session['jwt_token']}&expires={session['expires_at']}"
        return RedirectResponse(url=frontend_url)
=======
        # Check if VA ICN is already linked to a local user account
        va_icn = va_claims.get("icn") or token_data.get("id_token_claims", {}).get("sub")
        device_info = {
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "")
        }

        if va_icn and va_icn != "unknown":
            linked_user = db.query(User).filter(
                User.va_icn == va_icn,
                User.is_active == True
            ).first()

            if linked_user:
                # ICN is linked — issue standard auth JWT for unified login
                auth_token_data = {"sub": str(linked_user.id), "email": linked_user.email}
                auth_token = create_access_token(
                    data=auth_token_data,
                    expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                )
                AuthService.create_session(
                    db=db, user=linked_user, token=auth_token,
                    ip_address=device_info.get("ip"),
                    user_agent=device_info.get("user_agent"),
                    remember_me=False
                )
                logger.info(f"[VA OAuth] Linked-login for user {linked_user.id}")
                frontend_url = f"https://vetassist.ganuda.us/va-success?token={auth_token}&linked=true"
                return RedirectResponse(url=frontend_url)

        # No linked account — create standard VA session
        session_service = get_session_service()
        session = await session_service.create_session_from_va_auth(
            va_tokens=token_data,
            va_claims=va_claims,
            device_info=device_info
        )

        logger.info(f"[VA OAuth] VA session created for user {session['user_id'][:8]}...")

        # Redirect with VA JWT token
        frontend_url = f"https://vetassist.ganuda.us/va-success?token={session['jwt_token']}&expires={session['expires_at']}"
        return RedirectResponse(url=frontend_url)
>>>>>>> REPLACE

## Step 4: Verify Syntax

```bash
python3 -c "
import py_compile
try:
    py_compile.compile('/ganuda/vetassist/backend/app/api/v1/endpoints/va_auth.py', doraise=True)
    print('PASS: va_auth.py syntax valid')
except py_compile.PyCompileError as e:
    print(f'FAIL: {e}')
"
```

## Rollback

To undo, restore from search-replace backups:
  ls -la /ganuda/vetassist/backend/app/api/v1/endpoints/va_auth.py.sr_backup_*
Restore the most recent backup.
