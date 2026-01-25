# Jr Instruction: VetAssist VA OAuth Callback Endpoint
## Task ID: VetAssist Sprint 4 - Task 2
## Priority: P1
## Estimated Complexity: Medium

---

## Objective

Implement VA.gov OAuth login flow so veterans can authenticate with their VA credentials and check their claim status through VetAssist.

---

## Background

The VA Benefits Claims API requires veteran authentication via OAuth 2.0. Veterans log in using:
- ID.me
- Login.gov
- DS Logon (legacy)

After login, VA redirects to our callback URL with an authorization code. We exchange this code for an access token, then use that token to call VA APIs on the veteran's behalf.

---

## Prerequisites

Environment variables already configured in `/ganuda/vetassist/backend/.env`:
```
VA_OAUTH_CLIENT_ID=0oa19441es2SkUgu32p8
VA_OAUTH_CLIENT_SECRET=VPoIz3QHyoKzdAJBlYnfKxdtEzjsk-PEyfIy0V-ySctEEnmZ1UIBItnXijDi7u3k
VA_OAUTH_REDIRECT_URI=https://vetassist.ganuda.us/api/v1/auth/va/callback
VA_OAUTH_AUTH_URL=https://sandbox-api.va.gov/oauth2/authorization
VA_OAUTH_TOKEN_URL=https://sandbox-api.va.gov/oauth2/token
```

---

## Implementation Steps

### Step 1: Create VA OAuth Service

Create `/ganuda/vetassist/backend/app/services/va_oauth_service.py`:

```python
"""
VA OAuth Service
Handles VA.gov authentication for veterans
Cherokee AI Federation - For Seven Generations
"""
import os
import httpx
import secrets
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

# OAuth Configuration from environment
VA_CLIENT_ID = os.environ.get('VA_OAUTH_CLIENT_ID', '')
VA_CLIENT_SECRET = os.environ.get('VA_OAUTH_CLIENT_SECRET', '')
VA_REDIRECT_URI = os.environ.get('VA_OAUTH_REDIRECT_URI', '')
VA_AUTH_URL = os.environ.get('VA_OAUTH_AUTH_URL', 'https://sandbox-api.va.gov/oauth2/authorization')
VA_TOKEN_URL = os.environ.get('VA_OAUTH_TOKEN_URL', 'https://sandbox-api.va.gov/oauth2/token')

# Scopes needed for Benefits Claims API
VA_SCOPES = [
    'openid',
    'profile',
    'claim.read',
    'claim.write'
]


class VAOAuthService:
    """Service for VA.gov OAuth authentication"""

    def __init__(self):
        if not VA_CLIENT_ID:
            logger.warning("VA_OAUTH_CLIENT_ID not set")
        self._state_store: Dict[str, str] = {}  # In production, use Redis

    def get_authorization_url(self, session_id: Optional[str] = None) -> Dict[str, str]:
        """
        Generate VA authorization URL for veteran login.

        Returns:
            dict with 'url' and 'state' (save state for verification)
        """
        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state with session if provided
        if session_id:
            self._state_store[state] = session_id

        params = {
            'client_id': VA_CLIENT_ID,
            'redirect_uri': VA_REDIRECT_URI,
            'response_type': 'code',
            'scope': ' '.join(VA_SCOPES),
            'state': state
        }

        url = f"{VA_AUTH_URL}?{urlencode(params)}"

        return {
            'url': url,
            'state': state
        }

    async def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from VA callback
            state: State parameter for verification

        Returns:
            Token response with access_token, refresh_token, etc.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                VA_TOKEN_URL,
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': VA_REDIRECT_URI,
                    'client_id': VA_CLIENT_ID,
                    'client_secret': VA_CLIENT_SECRET
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )

            if response.status_code != 200:
                logger.error(f"VA token exchange failed: {response.status_code} - {response.text}")
                raise VAOAuthError(f"Token exchange failed: {response.status_code}")

            token_data = response.json()

            # Get session_id if we stored it with state
            session_id = self._state_store.pop(state, None)
            token_data['vetassist_session_id'] = session_id

            return token_data

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired access token"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                VA_TOKEN_URL,
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                    'client_id': VA_CLIENT_ID,
                    'client_secret': VA_CLIENT_SECRET
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )

            if response.status_code != 200:
                raise VAOAuthError(f"Token refresh failed: {response.status_code}")

            return response.json()

    async def get_veteran_info(self, access_token: str) -> Dict[str, Any]:
        """Get veteran profile info using access token"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                'https://sandbox-api.va.gov/services/veteran_verification/v1/status',
                headers={
                    'Authorization': f'Bearer {access_token}'
                }
            )

            if response.status_code != 200:
                raise VAOAuthError(f"Failed to get veteran info: {response.status_code}")

            return response.json()

    def verify_state(self, state: str) -> bool:
        """Verify state parameter to prevent CSRF"""
        return state in self._state_store


class VAOAuthError(Exception):
    """Exception for VA OAuth errors"""
    pass


# Singleton instance
va_oauth_service = VAOAuthService()
```

### Step 2: Create OAuth Endpoints

Add to `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py` (or create new file `va_auth.py`):

```python
"""
VA OAuth Endpoints
Cherokee AI Federation - For Seven Generations
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from typing import Optional
import logging

from app.services.va_oauth_service import va_oauth_service, VAOAuthError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/va/login")
async def va_login(
    session_id: Optional[str] = Query(None, description="VetAssist session to link")
):
    """
    Initiate VA.gov OAuth login flow.

    Redirects veteran to VA.gov login page (ID.me, Login.gov, or DS Logon).
    After login, VA redirects back to /va/callback with auth code.

    Args:
        session_id: Optional VetAssist wizard session to link after login

    Returns:
        Redirect to VA.gov authorization page
    """
    try:
        auth_data = va_oauth_service.get_authorization_url(session_id)
        logger.info(f"[VA OAuth] Redirecting to VA login, state={auth_data['state'][:8]}...")
        return RedirectResponse(url=auth_data['url'])
    except Exception as e:
        logger.error(f"[VA OAuth] Login initiation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate VA login")


@router.get("/va/callback")
async def va_callback(
    code: str = Query(..., description="Authorization code from VA"),
    state: str = Query(..., description="State for CSRF verification")
):
    """
    Handle OAuth callback from VA.gov.

    VA redirects here after veteran logs in. We exchange the code for tokens,
    then redirect to VetAssist frontend with session info.

    Args:
        code: Authorization code from VA
        state: State parameter for CSRF protection

    Returns:
        Redirect to VetAssist frontend with tokens/session
    """
    try:
        # Exchange code for token
        token_data = await va_oauth_service.exchange_code_for_token(code, state)

        logger.info(f"[VA OAuth] Token exchange successful")

        # Get veteran info
        try:
            veteran_info = await va_oauth_service.get_veteran_info(token_data['access_token'])
            logger.info(f"[VA OAuth] Got veteran info")
        except Exception as e:
            logger.warning(f"[VA OAuth] Could not get veteran info: {e}")
            veteran_info = None

        # Store token in database for later use
        # TODO: Save to vetassist_va_tokens table

        # Redirect to frontend with success
        # In production, use secure cookie or session storage
        session_id = token_data.get('vetassist_session_id', '')
        frontend_url = f"https://vetassist.ganuda.us/auth/va-success?session={session_id}"

        return RedirectResponse(url=frontend_url)

    except VAOAuthError as e:
        logger.error(f"[VA OAuth] Callback error: {e}")
        return RedirectResponse(url="https://vetassist.ganuda.us/auth/va-error?error=token_exchange_failed")
    except Exception as e:
        logger.error(f"[VA OAuth] Unexpected error: {e}")
        return RedirectResponse(url="https://vetassist.ganuda.us/auth/va-error?error=unknown")


@router.post("/va/refresh")
async def va_refresh_token(refresh_token: str):
    """
    Refresh expired VA access token.

    Args:
        refresh_token: Refresh token from previous auth

    Returns:
        New token data
    """
    try:
        token_data = await va_oauth_service.refresh_token(refresh_token)
        return token_data
    except VAOAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
```

### Step 3: Register Router (if created new file)

If you created `va_auth.py`, add to `/ganuda/vetassist/backend/app/api/v1/__init__.py`:

```python
from app.api.v1.endpoints import va_auth

api_router.include_router(
    va_auth.router,
    prefix="/auth",
    tags=["va-auth"]
)
```

### Step 4: Create Database Table for Tokens

```sql
CREATE TABLE IF NOT EXISTS vetassist_va_tokens (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(100),
    session_id UUID REFERENCES vetassist_wizard_sessions(session_id),

    -- OAuth tokens
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP,
    scope TEXT,

    -- Veteran info from VA
    va_icn VARCHAR(50),  -- Integration Control Number

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP
);

CREATE INDEX idx_va_tokens_session ON vetassist_va_tokens(session_id);
CREATE INDEX idx_va_tokens_veteran ON vetassist_va_tokens(veteran_id);
```

---

## Testing

### Test Login Flow

```bash
# 1. Get login URL
curl "https://vetassist.ganuda.us/api/v1/auth/va/login?session_id=test-session"
# Should redirect to VA.gov login page

# 2. After login, VA redirects to callback
# https://vetassist.ganuda.us/api/v1/auth/va/callback?code=XXXXX&state=YYYYY

# 3. Callback exchanges code for token and redirects to frontend
```

### Test with Sandbox Credentials

VA sandbox provides test user credentials:
- Check email from VA for sandbox test account info
- Use ID.me sandbox for testing

---

## Verification (Required before marking complete)

```bash
# 1. Check service file exists
ls -la /ganuda/vetassist/backend/app/services/va_oauth_service.py

# 2. Check endpoints exist
grep -n "va/login\|va/callback" /ganuda/vetassist/backend/app/api/v1/endpoints/*.py

# 3. Test login redirect
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/api/v1/auth/va/login"
# Should return 307 (redirect)

# 4. Check database table
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "\d vetassist_va_tokens"
```

---

## Security Notes

1. **State parameter** prevents CSRF attacks
2. **Client secret** stored in environment, never in code
3. **Tokens** should be encrypted at rest in production
4. **HTTPS only** - never transmit tokens over HTTP
5. **Token expiry** - access tokens expire, always check and refresh

---

## Flow Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   VetAssist     │     │    VA.gov       │     │   VetAssist     │
│   Frontend      │     │    OAuth        │     │   Backend       │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │  Click "Login with VA"                        │
         │──────────────────────────────────────────────>│
         │                       │                       │
         │                       │  Redirect to VA login │
         │<──────────────────────────────────────────────│
         │                       │                       │
         │  Enter credentials    │                       │
         │──────────────────────>│                       │
         │                       │                       │
         │  Redirect with code   │                       │
         │<──────────────────────│                       │
         │                       │                       │
         │  /va/callback?code=X  │                       │
         │──────────────────────────────────────────────>│
         │                       │                       │
         │                       │  Exchange code        │
         │                       │<──────────────────────│
         │                       │                       │
         │                       │  Return tokens        │
         │                       │──────────────────────>│
         │                       │                       │
         │  Redirect to success  │                       │
         │<──────────────────────────────────────────────│
         │                       │                       │
```

---

## Acceptance Criteria

1. [ ] `va_oauth_service.py` created with OAuth flow
2. [ ] `/auth/va/login` endpoint redirects to VA
3. [ ] `/auth/va/callback` endpoint exchanges code for token
4. [ ] `/auth/va/refresh` endpoint refreshes tokens
5. [ ] `vetassist_va_tokens` table created
6. [ ] State parameter used for CSRF protection
7. [ ] Tokens stored securely

---

*Cherokee AI Federation - For Seven Generations*
