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