# Jr Instruction: SAG API Key Authentication Guard (v2)

**Task ID:** SAG-AUTH-GUARD-v2
**Kanban:** #1852
**Priority:** 2
**Assigned Jr:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

Create API key authentication middleware for the SAG dashboard and apply it to all API endpoints. The vision routes already import `require_api_key` (line 27 of vision_routes.py) but auth.py doesn't exist yet — SAG will crash on import until this is created.

---

## Step 1: Create the auth middleware module

Create `/ganuda/sag/routes/auth.py`

```python
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
```

---

## Step 2: Add @require_api_key to vision route endpoints

File: `/ganuda/sag/routes/vision_routes.py`

Note: The import `from sag.routes.auth import require_api_key` already exists at line 27.

```python
<<<<<<< SEARCH
@vision_bp.route("/cameras", methods=["GET"])
def camera_status():
=======
@vision_bp.route("/cameras", methods=["GET"])
@require_api_key
def camera_status():
>>>>>>> REPLACE
```

```python
<<<<<<< SEARCH
@vision_bp.route("/speed/recent", methods=["GET"])
def speed_recent():
=======
@vision_bp.route("/speed/recent", methods=["GET"])
@require_api_key
def speed_recent():
>>>>>>> REPLACE
```

```python
<<<<<<< SEARCH
@vision_bp.route("/speed/stats", methods=["GET"])
def speed_stats():
=======
@vision_bp.route("/speed/stats", methods=["GET"])
@require_api_key
def speed_stats():
>>>>>>> REPLACE
```

```python
<<<<<<< SEARCH
@vision_bp.route("/calibration", methods=["GET"])
def calibration_status():
=======
@vision_bp.route("/calibration", methods=["GET"])
@require_api_key
def calibration_status():
>>>>>>> REPLACE
```

```python
<<<<<<< SEARCH
@vision_bp.route("/snapshot/<camera_id>", methods=["GET"])
def camera_snapshot(camera_id):
=======
@vision_bp.route("/snapshot/<camera_id>", methods=["GET"])
@require_api_key
def camera_snapshot(camera_id):
>>>>>>> REPLACE
```

---

## Step 3: Add auth to config route endpoints

File: `/ganuda/sag/routes/config_routes.py`

```python
<<<<<<< SEARCH
from flask import Blueprint, jsonify, render_template
=======
from flask import Blueprint, jsonify, render_template
from sag.routes.auth import require_api_key
>>>>>>> REPLACE
```

```python
<<<<<<< SEARCH
@config_bp.route("/api/config/services")
def api_services() -> dict:
=======
@config_bp.route("/api/config/services")
@require_api_key
def api_services() -> dict:
>>>>>>> REPLACE
```

```python
<<<<<<< SEARCH
@config_bp.route("/api/config/env-status")
def api_env_status() -> dict:
=======
@config_bp.route("/api/config/env-status")
@require_api_key
def api_env_status() -> dict:
>>>>>>> REPLACE
```

---

## Step 4: Add auth to VLM route endpoints

File: `/ganuda/sag/routes/vlm_routes.py`

```python
<<<<<<< SEARCH
from flask import Blueprint, request, jsonify
import httpx
import os

vlm_bp = Blueprint('vlm', __name__, url_prefix='/api/vlm')
=======
from flask import Blueprint, request, jsonify
from sag.routes.auth import require_api_key
import httpx
import os

vlm_bp = Blueprint('vlm', __name__, url_prefix='/api/vlm')
>>>>>>> REPLACE
```

```python
<<<<<<< SEARCH
@vlm_bp.route('/describe', methods=['POST'])
def describe() -> dict:
=======
@vlm_bp.route('/describe', methods=['POST'])
@require_api_key
def describe() -> dict:
>>>>>>> REPLACE
```

```python
<<<<<<< SEARCH
@vlm_bp.route('/analyze', methods=['POST'])
def analyze() -> dict:
=======
@vlm_bp.route('/analyze', methods=['POST'])
@require_api_key
def analyze() -> dict:
>>>>>>> REPLACE
```

```python
<<<<<<< SEARCH
@vlm_bp.route('/ask', methods=['POST'])
def ask() -> dict:
=======
@vlm_bp.route('/ask', methods=['POST'])
@require_api_key
def ask() -> dict:
>>>>>>> REPLACE
```

---

## Verification

```text
cd /ganuda && python3 -c "from sag.routes.auth import require_api_key; print('auth module OK')"
```

```text
cd /ganuda && python3 -c "from sag.routes.vision_routes import vision_bp; print('vision routes OK')"
```

```text
cd /ganuda && python3 -c "from sag.routes.config_routes import config_bp; print('config routes OK')"
```

```text
cd /ganuda && python3 -c "from sag.routes.vlm_routes import vlm_bp; print('vlm routes OK')"
```

## What NOT to Change

- Do NOT modify the /config page (HTML template render) — it's unauthenticated by design
- Do NOT modify the /health endpoint on VLM — keep it open for monitoring
- Do NOT add database dependencies to auth.py
- Do NOT change API key values or secrets

## Rollback

Unset `LLM_GATEWAY_API_KEY` env var — the decorator passes through when no key is configured.
