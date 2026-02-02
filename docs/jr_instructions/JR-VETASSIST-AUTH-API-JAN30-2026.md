# JR-VETASSIST-AUTH-API-JAN30-2026
## Build VetAssist Authentication API Module

**Priority:** P0 - Critical (all other endpoints depend on auth)
**Target Node:** bluefin (192.168.132.222)
**File to Create:** `/ganuda/vetassist/backend/app/api/auth_routes.py`
**Wire into:** `/ganuda/vetassist/backend/main.py`

### Context

The VetAssist frontend (Next.js) expects a complete auth API. The database tables already exist:

**`users` table** (UUID primary key):
- id (uuid), email (varchar), password_hash (varchar)
- first_name, last_name, phone (varchar)
- veteran_status (boolean), service_branch (varchar)
- service_start_date, service_end_date (date)
- disability_rating (integer)
- created_at, updated_at, last_login (timestamptz)
- email_verified (boolean), is_active (boolean)

**`user_sessions` table** (UUID primary key):
- id (uuid), user_id (uuid FK->users), token_hash (varchar)
- ip_address (varchar), user_agent (text)
- created_at (timestamptz), expires_at (timestamptz), revoked (boolean)

### Dependencies

```bash
pip install bcrypt pyjwt python-jose[cryptography]
```

### Endpoints to Implement

#### 1. POST /api/v1/auth/register
**Request:**
```json
{
  "email": "veteran@example.com",
  "password": "securePassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "555-0123",
  "veteran_status": true,
  "service_branch": "Army",
  "service_start_date": "2005-06-15",
  "service_end_date": "2015-08-20"
}
```
**Response (201):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": { ... user object ... }
}
```
**Logic:**
1. Validate email uniqueness (query users WHERE email = ?)
2. Hash password with bcrypt
3. INSERT into users table (generate UUID)
4. Create session in user_sessions (generate token, hash for storage)
5. Return JWT token + user object

#### 2. POST /api/v1/auth/login
**Request:**
```json
{
  "email": "veteran@example.com",
  "password": "securePassword123",
  "remember_me": false
}
```
**Response (200):** Same as register response
**Logic:**
1. SELECT user by email
2. Verify password with bcrypt
3. UPDATE last_login timestamp
4. Create session in user_sessions
5. Return JWT token + user object
6. `remember_me` = true: 30-day expiry; false: 24-hour expiry

#### 3. POST /api/v1/auth/logout
**Headers:** `Authorization: Bearer <token>`
**Response (200):** `{"message": "Logged out successfully"}`
**Logic:**
1. Extract token from Authorization header
2. Hash token, find in user_sessions
3. SET revoked = true
4. Return success

#### 4. GET /api/v1/auth/me
**Headers:** `Authorization: Bearer <token>`
**Response (200):** Full user object (no password_hash)
**Logic:**
1. Extract and validate JWT token
2. Look up user by ID from token claims
3. Verify session not revoked
4. Return user object

#### 5. PATCH /api/v1/auth/profile
**Headers:** `Authorization: Bearer <token>`
**Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "555-0123",
  "veteran_status": true,
  "service_branch": "Army",
  "disability_rating": 70
}
```
**Response (200):** Updated user object
**Logic:**
1. Authenticate via token
2. UPDATE users SET ... WHERE id = user_id
3. Return updated user

#### 6. POST /api/v1/auth/forgot-password
**Request:** `{"email": "veteran@example.com"}`
**Response (200):** `{"message": "If account exists, reset email sent"}`
**Logic:** For MVP, log the request. Full email integration later.

### Implementation Pattern

Use `database_config.py` for all DB connections:
```python
from app.core.database_config import get_db_connection, get_dict_cursor
```

JWT configuration:
```python
JWT_SECRET = os.environ.get("JWT_SECRET", "vetassist-jwt-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24
JWT_EXPIRY_HOURS_REMEMBER = 720  # 30 days
```

### Auth Dependency (reusable)

Create `/ganuda/vetassist/backend/app/core/auth.py`:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Decode JWT and return user dict. Use as FastAPI dependency."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Look up user from DB
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    cur.execute("SELECT * FROM users WHERE id = %s AND is_active = true", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

### Wire into main.py

Add to imports in `/ganuda/vetassist/backend/main.py`:
```python
from app.api.auth_routes import router as auth_router
```

Add to router includes:
```python
app.include_router(auth_router)
```

### Security Notes (Crawdad review)

- NEVER return password_hash in any response
- Hash tokens before storing in user_sessions (use SHA-256)
- Rate-limit login attempts (5 per minute per IP) — can defer to Phase 2
- All PII fields route through goldfin tunnel (port 5433) when PII vault is active
- JWT_SECRET must be rotated to a proper secret before production

### Verification

```bash
# Register
curl -X POST http://192.168.132.222:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","first_name":"Test","veteran_status":true}'

# Login
curl -X POST http://192.168.132.222:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'

# Get profile (use token from login)
curl http://192.168.132.222:8001/api/v1/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```
