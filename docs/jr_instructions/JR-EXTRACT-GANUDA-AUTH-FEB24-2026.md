# Jr Instruction: Extract ganuda_auth Package — Consolidated Auth Utilities

**Task ID**: EXTRACT-AUTH
**Kanban**: #1716
**Priority**: 2 (SFP 35, SP 5)
**Assigned Jr**: Software Engineer Jr.
**use_rlm**: false
**Target File**: `/ganuda/lib/ganuda_auth/__init__.py`

## Objective

Populate the `ganuda_auth` package stub with consolidated authentication utilities extracted from existing federation patterns:

- **API key validation** — from `/ganuda/sag/routes/auth.py` (`require_api_key` decorator using `hmac.compare_digest`)
- **Password hashing** — bcrypt via `passlib.context.CryptContext`
- **JWT tokens** — creation and verification via `python-jose` (`jose.jwt`)

The package becomes the single source of truth for auth across SAG, VetAssist, and any future Assist apps.

## Exports

| Function | Signature | Purpose |
|---|---|---|
| `require_api_key` | `(fn) -> fn` | Decorator; checks `X-API-Key` header against `CHEROKEE_API_KEY` env var |
| `hash_password` | `(password: str) -> str` | Returns bcrypt hash |
| `verify_password` | `(plain: str, hashed: str) -> bool` | Verifies plaintext against bcrypt hash |
| `create_access_token` | `(data: dict, expires_minutes: int = 60) -> str` | Returns signed JWT (HS256) |
| `decode_access_token` | `(token: str) -> dict` | Decodes and verifies JWT; raises `JWTError` on failure |

## Dependencies

- `passlib[bcrypt]` — password hashing (already in federation venv)
- `python-jose[cryptography]` — JWT encode/decode (already in federation venv)
- stdlib only otherwise (`os`, `functools`, `hmac`, `logging`, `datetime`)

## Implementation

Create `/ganuda/lib/ganuda_auth/__init__.py`

```python
"""
ganuda_auth: Core Authentication Library
Cherokee AI Federation — For the Seven Generations

CORE PACKAGE — Shared across all Assist applications

Features:
- API key validation decorator (extracted from SAG auth.py)
- JWT token creation and verification (HS256)
- Password hashing (bcrypt via passlib)

Usage:
    from ganuda_auth import hash_password, verify_password
    from ganuda_auth import create_access_token, decode_access_token
    from ganuda_auth import require_api_key
"""

__version__ = "1.0.0"

import os
import hmac
import functools
import logging
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
_API_KEY = os.environ.get("CHEROKEE_API_KEY", "")
_JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "")
_JWT_ALGORITHM = "HS256"

# ---------------------------------------------------------------------------
# Password hashing (bcrypt)
# ---------------------------------------------------------------------------
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Returns the bcrypt hash string suitable for database storage.
    """
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Returns True if the password matches, False otherwise.
    """
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_minutes: int = 60) -> str:
    """Create a signed JWT access token (HS256).

    Args:
        data: Claims to encode in the token payload.
        expires_minutes: Token lifetime in minutes (default 60).

    Returns:
        Encoded JWT string.

    Raises:
        ValueError: If JWT_SECRET_KEY environment variable is not set.
    """
    if not _JWT_SECRET:
        raise ValueError(
            "JWT_SECRET_KEY environment variable is not set. "
            "Cannot create access tokens without a signing key."
        )
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT access token.

    Args:
        token: The encoded JWT string.

    Returns:
        Decoded payload as a dictionary.

    Raises:
        ValueError: If JWT_SECRET_KEY environment variable is not set.
        jose.JWTError: If the token is invalid, expired, or tampered with.
    """
    if not _JWT_SECRET:
        raise ValueError(
            "JWT_SECRET_KEY environment variable is not set. "
            "Cannot decode access tokens without a signing key."
        )
    return jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])


# ---------------------------------------------------------------------------
# API key validation decorator
# ---------------------------------------------------------------------------

def require_api_key(fn):
    """Decorator to require a valid API key on incoming requests.

    Checks the X-API-Key header against the CHEROKEE_API_KEY env var.
    Uses hmac.compare_digest for constant-time comparison.

    If CHEROKEE_API_KEY is not configured, all requests are allowed
    (development mode).

    Works with Flask request context (imports flask.request internally
    so the package can be imported without Flask installed).
    """
    @functools.wraps(fn)
    def decorated(*args, **kwargs):
        if not _API_KEY:
            # No key configured — allow all (dev mode)
            return fn(*args, **kwargs)

        from flask import request, jsonify

        provided = request.headers.get("X-API-Key", "")
        if not provided:
            logger.warning("Auth: missing API key for %s", request.path)
            return jsonify({"error": "Missing X-API-Key header"}), 401

        if not hmac.compare_digest(provided, _API_KEY):
            logger.warning("Auth: invalid API key for %s", request.path)
            return jsonify({"error": "Invalid API key"}), 403

        return fn(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
__all__ = [
    "require_api_key",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "JWTError",
]
```

## Verification

After the file is written, confirm syntax and imports:

```text
python3 -c "import ast; ast.parse(open('/ganuda/lib/ganuda_auth/__init__.py').read()); print('SYNTAX OK')"
```

Then verify the public API is importable (run from redfin where cherokee_venv has passlib + python-jose):

```text
/ganuda/home/dereadi/cherokee_venv/bin/python3 -c "
from ganuda_auth import require_api_key, hash_password, verify_password, create_access_token, decode_access_token
print('require_api_key:', callable(require_api_key))
print('hash_password:', callable(hash_password))
print('verify_password:', callable(verify_password))
print('create_access_token:', callable(create_access_token))
print('decode_access_token:', callable(decode_access_token))
print('ALL EXPORTS OK')
"
```

Verify password round-trip:

```text
/ganuda/home/dereadi/cherokee_venv/bin/python3 -c "
import sys; sys.path.insert(0, '/ganuda/lib')
from ganuda_auth import hash_password, verify_password
h = hash_password('test123')
assert verify_password('test123', h), 'FAIL: correct password rejected'
assert not verify_password('wrong', h), 'FAIL: wrong password accepted'
print('PASSWORD ROUND-TRIP OK')
"
```

## Design Notes

- **Flask import is lazy** inside `require_api_key` so the package can be imported by non-Flask consumers (e.g., CLI scripts, VetAssist FastAPI) without requiring Flask as a dependency.
- **Environment variables** (`CHEROKEE_API_KEY`, `JWT_SECRET_KEY`) are read at module load time for performance. Services must set them before importing.
- **`JWTError` re-exported** so consumers can catch token errors without importing `jose` directly.
- **No database coupling** — this is a pure utility library. Session management and user lookup remain in the consuming application.
- **SAG routes/auth.py** can be refactored in a follow-up task to `from ganuda_auth import require_api_key` instead of its local copy.
