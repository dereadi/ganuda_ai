# Jr Instruction: Wave 3 — SAG API Key Authentication Guard

**Task**: Add API key authentication to all SAG API endpoints (vision, config, VLM)
**Priority**: 1 (CRITICAL — camera IPs, speed detection data, and license plates currently exposed without auth)
**Source**: Council vote #5e286ebeabda8d47, Long Man Wave 3 DISCOVER/DELIBERATE
**Assigned Jr**: Software Engineer Jr.

## Context

The SAG dashboard has 3 route blueprints:
- `vision_bp` (/api/vision/*) — camera fleet status, speed detections with license plates, live snapshots
- `config_bp` (/api/config/*) — service health, env var status
- `vlm_bp` (/api/vlm/*) — VLM image analysis endpoints

ALL endpoints are currently publicly accessible with NO authentication. This means anyone on the network can:
- Query camera IP addresses and passwords
- Read license plate data from speed detections
- Access live camera snapshots
- Trigger VLM image analysis

`CHEROKEE_API_KEY` already exists in secrets.env. We just need to enforce it.

---

## Fix 1: Create auth middleware module

Create `/ganuda/sag/routes/auth.py`

```python
"""SAG API Key Authentication Middleware"""
import os
from functools import wraps
from flask import request, jsonify

SAG_API_KEY = os.environ.get('CHEROKEE_API_KEY', '')


def require_api_key(f):
    """Decorator to require API key for endpoint access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow health check endpoints without auth
        if request.path.endswith('/health'):
            return f(*args, **kwargs)

        # Check X-API-Key header
        api_key = request.headers.get('X-API-Key', '')
        if not api_key:
            # Also check query param for browser/curl convenience
            api_key = request.args.get('api_key', '')

        if not SAG_API_KEY:
            # If no key configured, log warning but allow (don't break during setup)
            print("[SAG AUTH] WARNING: CHEROKEE_API_KEY not set, allowing unauthenticated access")
            return f(*args, **kwargs)

        if api_key != SAG_API_KEY:
            return jsonify({"error": "Unauthorized", "message": "Valid X-API-Key header required"}), 401

        return f(*args, **kwargs)
    return decorated
```

---

## Fix 2: Apply auth to vision endpoints

File: `/ganuda/sag/routes/vision_routes.py`

Add import at top of file:

```
<<<<<<< SEARCH
from lib.secrets_loader import get_db_config
import psycopg2
=======
from lib.secrets_loader import get_db_config
from sag.routes.auth import require_api_key
import psycopg2
>>>>>>> REPLACE
```

Add decorator to each route:

```
<<<<<<< SEARCH
@vision_bp.route("/cameras", methods=["GET"])
def get_cameras():
=======
@vision_bp.route("/cameras", methods=["GET"])
@require_api_key
def get_cameras():
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
@vision_bp.route("/speed/recent", methods=["GET"])
def get_recent_speeds():
=======
@vision_bp.route("/speed/recent", methods=["GET"])
@require_api_key
def get_recent_speeds():
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
@vision_bp.route("/speed/stats", methods=["GET"])
def get_speed_stats():
=======
@vision_bp.route("/speed/stats", methods=["GET"])
@require_api_key
def get_speed_stats():
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
@vision_bp.route("/calibration", methods=["GET"])
def get_calibration():
=======
@vision_bp.route("/calibration", methods=["GET"])
@require_api_key
def get_calibration():
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
@vision_bp.route("/snapshot/<camera_id>", methods=["GET"])
def get_snapshot(camera_id):
=======
@vision_bp.route("/snapshot/<camera_id>", methods=["GET"])
@require_api_key
def get_snapshot(camera_id):
>>>>>>> REPLACE
```

---

## Fix 3: Apply auth to config endpoints

File: `/ganuda/sag/routes/config_routes.py`

Add import:

```
<<<<<<< SEARCH
from flask import Blueprint, jsonify, render_template
=======
from flask import Blueprint, jsonify, render_template
from sag.routes.auth import require_api_key
>>>>>>> REPLACE
```

Add decorator to API endpoints (NOT the HTML page render):

```
<<<<<<< SEARCH
@config_bp.route("/api/config/services")
def services_status():
=======
@config_bp.route("/api/config/services")
@require_api_key
def services_status():
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
@config_bp.route("/api/config/env-status")
def env_status():
=======
@config_bp.route("/api/config/env-status")
@require_api_key
def env_status():
>>>>>>> REPLACE
```

---

## Fix 4: Apply auth to VLM endpoints

File: `/ganuda/sag/routes/vlm_routes.py`

Add import after existing imports:

```
<<<<<<< SEARCH
vlm_bp = Blueprint('vlm', __name__, url_prefix='/api/vlm')
=======
from sag.routes.auth import require_api_key

vlm_bp = Blueprint('vlm', __name__, url_prefix='/api/vlm')
>>>>>>> REPLACE
```

Add decorator to sensitive endpoints (NOT /health):

```
<<<<<<< SEARCH
@vlm_bp.route('/describe', methods=['POST'])
def describe_image():
=======
@vlm_bp.route('/describe', methods=['POST'])
@require_api_key
def describe_image():
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
@vlm_bp.route('/analyze', methods=['POST'])
def analyze_image():
=======
@vlm_bp.route('/analyze', methods=['POST'])
@require_api_key
def analyze_image():
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
@vlm_bp.route('/ask', methods=['POST'])
def ask_about_image():
=======
@vlm_bp.route('/ask', methods=['POST'])
@require_api_key
def ask_about_image():
>>>>>>> REPLACE
```

---

## Verification

1. **Without API key**: `curl http://redfin:4000/api/vision/cameras` should return 401 Unauthorized
2. **With API key**: `curl -H "X-API-Key: $CHEROKEE_API_KEY" http://redfin:4000/api/vision/cameras` should return camera list
3. **Health endpoint**: `curl http://redfin:4000/api/vlm/health` should work WITHOUT key (health checks exempt)
4. **Config HTML page**: `http://redfin:4000/config` should still render (HTML page, not API)
5. **Query param fallback**: `curl "http://redfin:4000/api/vision/speed/recent?api_key=$CHEROKEE_API_KEY"` should work
