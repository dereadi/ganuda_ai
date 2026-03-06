"""
API Key Authentication Guard — Cherokee AI Federation SAG
Council Vote #1852 — Protect SAG API endpoints with API key validation.
"""

import os
import hashlib
import hmac
import functools
import logging
from flask import request, jsonify

logger = logging.getLogger(__name__)

# API key loaded from environment (same key as LLM Gateway)
SAG_API_KEY = os.environ.get("LLM_GATEWAY_API_KEY", "")


def require_api_key(f):
    """Decorator to require a valid API key for SAG API endpoints.
    Checks X-API-Key header against SAG_API_KEY environment variable.
    Skips auth if SAG_API_KEY is not configured (development mode)."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not SAG_API_KEY:
            # No key configured — allow all (dev mode)
            return f(*args, **kwargs)

        provided = request.headers.get("X-API-Key", "")
        if not provided:
            logger.warning(f"SAG auth: missing API key for {request.path}")
            return jsonify({"error": "Missing X-API-Key header"}), 401

        if not hmac.compare_digest(provided, SAG_API_KEY):
            logger.warning(f"SAG auth: invalid API key for {request.path}")
            return jsonify({"error": "Invalid API key"}), 403

        return f(*args, **kwargs)
    return decorated