# Jr Instruction: VetAssist Authentication Integration

**Priority**: 1 of 3
**Council Audit**: 3b690ed593a16433
**Estimated Complexity**: Medium
**Parent ULTRATHINK**: ULTRATHINK-VETASSIST-SPRINT2-JAN20-2026.md

## Objective

Implement JWT-based authentication for VetAssist, replacing temporary user IDs with real user accounts.

## Prerequisites

- Access to PostgreSQL on 192.168.132.222
- VetAssist backend running on redfin (192.168.132.223)
- VetAssist frontend in /ganuda/vetassist/frontend

## Tasks

### Task 1: Database Schema

Create the users and sessions tables:

```sql
-- Run on 192.168.132.222, database: triad_federation

CREATE TABLE IF NOT EXISTS vetassist_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vetassist_auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES vetassist_users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_vetassist_users_email ON vetassist_users(email);
CREATE INDEX idx_vetassist_auth_sessions_user ON vetassist_auth_sessions(user_id);
CREATE INDEX idx_vetassist_auth_sessions_token ON vetassist_auth_sessions(token_hash);
```

### Task 2: Backend Auth Endpoints

Create `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`:

```python
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import uuid
import os

router = APIRouter(prefix="/auth", tags=["authentication"])

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str = None
    last_name: str = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str = None
    last_name: str = None

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(user_id: str) -> tuple[str, datetime]:
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expires,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, expires

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Endpoints
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister):
    """Register a new user"""
    # Implementation: Insert into vetassist_users, return user
    pass

@router.post("/login", response_model=Token)
def login(credentials: UserLogin):
    """Login and get JWT token"""
    # Implementation: Verify credentials, create token, return
    pass

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user_id: str = Depends(get_current_user)):
    """Logout and invalidate session"""
    # Implementation: Delete from vetassist_auth_sessions
    pass

@router.get("/me", response_model=UserResponse)
def get_me(user_id: str = Depends(get_current_user)):
    """Get current user profile"""
    # Implementation: Query vetassist_users by id
    pass
```

### Task 3: Install Dependencies

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
pip install python-jose[cryptography] passlib[bcrypt]
```

### Task 4: Register Auth Router

In `/ganuda/vetassist/backend/app/api/v1/__init__.py`, add:

```python
from .endpoints import auth
api_router.include_router(auth.router)
```

### Task 5: Frontend Auth Pages

Create login page at `/ganuda/vetassist/frontend/app/login/page.tsx`:
- Email/password form
- Submit to POST /api/v1/auth/login
- Store JWT in localStorage or httpOnly cookie
- Redirect to dashboard on success

Create register page at `/ganuda/vetassist/frontend/app/register/page.tsx`:
- Registration form with email, password, name
- Submit to POST /api/v1/auth/register
- Auto-login after registration

### Task 6: Auth Context/Provider

Create `/ganuda/vetassist/frontend/lib/auth-context.tsx`:
- React context for auth state
- `useAuth()` hook
- Token refresh logic
- Protected route wrapper

### Task 7: Update Wizard to Use Real User

Modify wizard session creation to use authenticated user_id instead of TEMP_USER_ID.

## Validation

1. Register new user - should return user object
2. Login - should return JWT token
3. Access /api/v1/auth/me with token - should return user
4. Create wizard session with real user_id
5. Token expiry after 24 hours

## Security Notes

- Never log passwords or tokens
- Use HTTPS in production
- Set secure cookie flags
- Implement rate limiting on login

## Files to Create/Modify

- `backend/app/api/v1/endpoints/auth.py` (NEW)
- `backend/app/api/v1/__init__.py` (MODIFY)
- `frontend/app/login/page.tsx` (EXISTS - enhance)
- `frontend/app/register/page.tsx` (EXISTS - enhance)
- `frontend/lib/auth-context.tsx` (NEW)

## Report Back

When complete, update the Jr work queue with:
- Endpoints implemented
- Test results
- Any blockers encountered
