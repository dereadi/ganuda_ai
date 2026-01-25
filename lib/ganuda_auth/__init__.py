"""
ganuda-auth: Core Authentication Library
Cherokee AI Federation - For the Seven Generations

CORE PACKAGE - Shared across all Assist applications

Features:
- JWT token creation and verification
- Password hashing (bcrypt)
- FastAPI authentication middleware
- FreeIPA integration helpers (silverfin)

Usage:
    from ganuda_auth import hash_password, verify_password
    from ganuda_auth import create_access_token, verify_token
    from ganuda_auth.middleware import require_auth
"""

__version__ = "1.0.0"

# TODO: Extract from /ganuda/vetassist/backend/app/core/security.py
# Placeholder exports - implement in security.py
