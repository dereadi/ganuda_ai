# Jr Instruction: Add Missing Security Functions to VetAssist

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P0 (Blocking startup)
**Category:** Bug Fix
**From Review:** REVIEW-VETASSIST-20260126

---

## Problem

`/ganuda/vetassist/backend/app/services/auth_service.py` imports 6 functions from `app.core.security` that don't exist:

```python
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    hash_token,
    validate_email,
    validate_password_strength
)
```

This causes ImportError on startup.

---

## File to Modify

`/ganuda/vetassist/backend/app/core/security.py`

---

## Functions to Add

### 1. hash_password(password: str) -> str
Hash a plaintext password using bcrypt.
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)
```

### 2. verify_password(plain_password: str, hashed_password: str) -> bool
Verify a password against its hash.
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### 3. create_access_token(data: dict, expires_delta: timedelta = None) -> str
Create a JWT access token.
```python
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
```

### 4. hash_token(token: str) -> str
Hash a token for secure storage (e.g., refresh tokens).
```python
import hashlib

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
```

### 5. validate_email(email: str) -> bool
Validate email format.
```python
import re

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
```

### 6. validate_password_strength(password: str) -> tuple[bool, str]
Check password meets requirements (min 8 chars, has number, has letter).
```python
def validate_password_strength(password: str) -> tuple:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter"
    return True, "Password meets requirements"
```

---

## Required Imports at Top of security.py

```python
from fastapi import Request, Header, Depends, HTTPException, status
from typing import Optional
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import hashlib
import re
from app.core.config import settings
```

---

## Do NOT

- Change existing functions (decode_access_token, get_current_user, etc.)
- Add any database calls to security.py
- Hardcode the SECRET_KEY (must come from settings)

---

## Success Criteria

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
python -c "from app.core.security import hash_password, verify_password, create_access_token, hash_token, validate_email, validate_password_strength; print('All security functions imported successfully')"
```

Then test full app:
```bash
python -c "from app.main import app; print('App imports OK')"
```
