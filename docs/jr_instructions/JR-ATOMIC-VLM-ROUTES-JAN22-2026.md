# Jr Task: Create SAG VLM Routes

Create the VLM proxy routes for SAG backend.

**File:** `/ganuda/sag/routes/vlm_routes.py`

```python
from flask import Blueprint, request, jsonify
import httpx
import os

vlm_bp = Blueprint('vlm', __name__, url_prefix='/api/vlm')
GATEWAY = os.getenv('LLM_GATEWAY_URL', 'http://localhost:8080')
API_KEY = os.getenv('LLM_API_KEY', 'REDACTED_USE_ENV_VAR')

@vlm_bp.route('/health', methods=['GET'])
def health():
    try:
        r = httpx.get(f"{GATEWAY}/v1/vlm/health", timeout=5.0)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@vlm_bp.route('/describe', methods=['POST'])
def describe():
    data = request.json or {}
    r = httpx.post(f"{GATEWAY}/v1/vlm/describe", json=data, headers={"X-API-Key": API_KEY}, timeout=120.0)
    return jsonify(r.json())

@vlm_bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.json or {}
    r = httpx.post(f"{GATEWAY}/v1/vlm/analyze", json=data, headers={"X-API-Key": API_KEY}, timeout=120.0)
    return jsonify(r.json())

@vlm_bp.route('/ask', methods=['POST'])
def ask():
    data = request.json or {}
    r = httpx.post(f"{GATEWAY}/v1/vlm/ask", json=data, headers={"X-API-Key": API_KEY}, timeout=120.0)
    return jsonify(r.json())
```

Create directory first: `mkdir -p /ganuda/sag/routes`
