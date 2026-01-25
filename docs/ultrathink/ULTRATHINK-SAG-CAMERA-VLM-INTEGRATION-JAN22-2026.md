# ULTRATHINK: SAG Camera Tab VLM Integration

**Created**: January 22, 2026
**TPM**: Claude Opus 4.5
**Council Audit Hash**: 36c8b402ffe658fe
**Confidence**: 0.822 (high-medium)
**Concerns Raised**: 3 (Raven-Strategy, Crawdad-Security, Turtle-7GEN)

---

## Executive Summary

Integrate the SAG Camera UI tab with VLM (Vision Language Model) endpoints to enable AI-powered security camera analysis. This requires frontend modifications, API integration patterns, test infrastructure, and careful attention to security and ethical considerations raised by the Council.

---

## Council Deliberation Analysis

### Concerns Requiring TPM Attention

| Specialist | Concern | Key Point |
|------------|---------|-----------|
| **Raven** | STRATEGY | Ethical/privacy concerns must be proactively managed for long-term trust |
| **Crawdad** | SECURITY | All data between nodes must be encrypted; strict auth/authz required |
| **Turtle** | 7GEN | Surveillance AI must prioritize community well-being over short-term gains |

### Council Consensus Points

All 7 specialists agreed on:

1. **RESTful API Integration** - Use gateway endpoints, not direct bluefin access
2. **Async Frontend Calls** - Non-blocking UI with proper loading states
3. **Dual Image Handling** - Support both upload AND path methods
4. **Encryption Required** - TLS for transit, encryption at rest
5. **Authentication** - API key or OAuth required for all VLM calls
6. **Audit Logging** - Track all camera analysis requests

### Specialist-Specific Insights

**Gecko (Technical)**:
- Optimize image size/format before upload
- Implement retries for transient failures
- Evaluate latency vs throughput tradeoffs

**Eagle Eye (Monitoring)**:
- WebSockets for real-time video streams
- Balance real-time responsiveness with system load
- Pre-uploaded images can use path reference

**Spider (Integration)**:
- Ensure alignment with Cherokee values of respect
- Community engagement on data collection transparency
- Robust error handling for user experience

**Peace Chief (Coordination)**:
- Queue system for batch processing
- Stakeholder discussions on benefits vs risks
- Build trust through responsible use

---

## Technical Architecture

### Current State

```
┌─────────────────┐
│   SAG UI        │  Camera tab exists but not wired
│   (redfin:4000) │  to VLM endpoints
└─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  LLM Gateway    │────▶│  VLM Service    │  VLM ready, needs
│  (redfin:8080)  │     │  (bluefin:8090) │  frontend integration
└─────────────────┘     └─────────────────┘
```

### Target State

```
┌─────────────────────────────────────────────────────────────────┐
│                        SAG UI (redfin:4000)                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │ Dashboard │  │  Kanban   │  │  Council  │  │  CAMERA   │    │
│  └───────────┘  └───────────┘  └───────────┘  └─────┬─────┘    │
│                                                      │          │
│  ┌──────────────────────────────────────────────────┴────────┐ │
│  │                    Camera Analysis Panel                   │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │ │
│  │  │ Upload/Path │  │  Analysis   │  │  Q&A Panel  │       │ │
│  │  │   Picker    │  │   Results   │  │  (Ask VLM)  │       │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │ │
│  └───────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼ (via API key auth)
┌─────────────────────────────────────────────────────────────────┐
│                   LLM Gateway (redfin:8080)                     │
│  POST /v1/vlm/describe  │  POST /v1/vlm/analyze                 │
│  POST /v1/vlm/ask       │  GET /v1/vlm/health                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (internal network)
┌─────────────────────────────────────────────────────────────────┐
│                   VLM Service (bluefin:8090)                    │
│  Qwen2-VL-7B-Instruct  │  RTX 5070  │  ~17s inference          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Strategy

### Phase 1: Frontend Integration (SAG Camera Tab)

**1.1 Camera Tab Component Structure**

```
sag/templates/camera.html (or camera tab in main template)
├── Image Input Section
│   ├── File Upload (drag-drop + button)
│   ├── Path Input (for server-side images)
│   └── Camera Selector (camera_id dropdown)
├── Analysis Controls
│   ├── "Describe" button → /v1/vlm/describe
│   ├── "Analyze" button → /v1/vlm/analyze
│   └── "Ask" button + text input → /v1/vlm/ask
├── Results Display
│   ├── Description panel (text)
│   ├── Anomaly assessment (normal/concerning/critical badge)
│   └── Q&A history
└── Status Indicators
    ├── VLM health indicator
    ├── Loading spinners
    └── Error messages
```

**1.2 JavaScript API Integration**

```javascript
// Key patterns for VLM API calls
const VLM_API = '/api/vlm';  // Proxy through SAG backend to gateway

async function describeFrame(imagePath, cameraId) {
    const response = await fetch(`${VLM_API}/describe`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({image_path: imagePath, camera_id: cameraId})
    });
    return response.json();
}

async function analyzeFrame(imagePath, cameraId) {
    const response = await fetch(`${VLM_API}/analyze`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({image_path: imagePath, camera_id: cameraId})
    });
    return response.json();
}

async function askAboutFrame(imagePath, question, cameraId) {
    const response = await fetch(`${VLM_API}/ask`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            image_path: imagePath,
            question: question,
            camera_id: cameraId
        })
    });
    return response.json();
}
```

**1.3 SAG Backend Routes (Python/Flask)**

```python
# sag/app.py - Add VLM proxy routes

@app.route('/api/vlm/<endpoint>', methods=['POST'])
def vlm_proxy(endpoint):
    """Proxy VLM requests to gateway with API key."""
    import httpx

    GATEWAY_URL = "http://localhost:8080"  # Local on redfin
    API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

    try:
        response = httpx.post(
            f"{GATEWAY_URL}/v1/vlm/{endpoint}",
            json=request.json,
            headers={"X-API-Key": API_KEY},
            timeout=120.0
        )
        return jsonify(response.json())
    except httpx.TimeoutException:
        return jsonify({"error": "VLM timeout"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route('/api/vlm/health', methods=['GET'])
def vlm_health():
    """Check VLM service health."""
    import httpx
    try:
        response = httpx.get(
            "http://localhost:8080/v1/vlm/health",
            timeout=5.0
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)})
```

### Phase 2: Image Handling

**2.1 Upload Method (Base64)**

For images not on bluefin filesystem, need upload endpoint:

```python
# Add to VLM API on bluefin - /v1/vlm/upload
@app.route('/v1/vlm/upload', methods=['POST'])
def upload_frame():
    """Upload image and return server path."""
    import base64
    from datetime import datetime

    data = request.json
    if 'image_base64' not in data:
        return jsonify({"error": "image_base64 required"}), 400

    # Decode and save
    image_data = base64.b64decode(data['image_base64'])
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    camera_id = data.get('camera_id', 'upload')
    filename = f"{camera_id}_{timestamp}.jpg"
    filepath = f"/ganuda/data/vision/frames/{filename}"

    with open(filepath, 'wb') as f:
        f.write(image_data)

    return jsonify({
        "success": True,
        "image_path": filepath,
        "filename": filename
    })
```

**2.2 Path Method (Server-side)**

For images already on bluefin (e.g., from camera capture daemons):

```
/ganuda/data/vision/frames/
├── front_door/
│   ├── 20260122_103000.jpg
│   └── 20260122_103100.jpg
├── backyard/
│   └── 20260122_103000.jpg
└── driveway/
    └── 20260122_103000.jpg
```

### Phase 3: Test Image Infrastructure

**3.1 Test Image Requirements**

Need sample images for development and testing:

| Category | Description | Count |
|----------|-------------|-------|
| Normal | Empty scenes, routine activity | 5 |
| People | Various counts, activities | 5 |
| Vehicles | Cars, trucks, deliveries | 3 |
| Anomalies | Suspicious activity simulated | 3 |
| Edge Cases | Low light, obstructions | 4 |

**3.2 Test Image Generation Script**

```bash
#!/bin/bash
# /ganuda/scripts/generate_test_frames.sh

FRAME_DIR="/ganuda/data/vision/frames"
mkdir -p "$FRAME_DIR/test"

# Option 1: Download sample security camera images (public domain)
# Option 2: Generate synthetic images with stable diffusion
# Option 3: Capture from actual cameras if available

echo "Test frame directory: $FRAME_DIR/test"
echo "Place test images here for VLM testing"
```

**3.3 Test Harness**

```python
# /ganuda/scripts/test_vlm_integration.py
"""Test VLM endpoints with sample images."""

import httpx
import json
from pathlib import Path

GATEWAY = "http://192.168.132.223:8080"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"
TEST_DIR = Path("/ganuda/data/vision/frames/test")

def test_describe(image_path: str):
    response = httpx.post(
        f"{GATEWAY}/v1/vlm/describe",
        json={"image_path": image_path, "camera_id": "test"},
        headers={"X-API-Key": API_KEY},
        timeout=120.0
    )
    print(f"DESCRIBE: {response.json()}")

def test_analyze(image_path: str):
    response = httpx.post(
        f"{GATEWAY}/v1/vlm/analyze",
        json={"image_path": image_path, "camera_id": "test"},
        headers={"X-API-Key": API_KEY},
        timeout=120.0
    )
    print(f"ANALYZE: {response.json()}")

def test_ask(image_path: str, question: str):
    response = httpx.post(
        f"{GATEWAY}/v1/vlm/ask",
        json={"image_path": image_path, "question": question, "camera_id": "test"},
        headers={"X-API-Key": API_KEY},
        timeout=120.0
    )
    print(f"ASK: {response.json()}")

if __name__ == "__main__":
    # Find first test image
    images = list(TEST_DIR.glob("*.jpg")) + list(TEST_DIR.glob("*.png"))
    if not images:
        print(f"No test images in {TEST_DIR}")
        exit(1)

    test_image = str(images[0])
    print(f"Testing with: {test_image}")

    test_describe(test_image)
    test_analyze(test_image)
    test_ask(test_image, "How many people are in this image?")
```

---

## Security Implementation (Crawdad Requirements)

### Authentication Flow

```
User → SAG UI → SAG Backend → Gateway → VLM
         │           │            │
         │           └── API Key ──┘
         └── Session Auth
```

### Security Checklist

- [ ] TLS for all external endpoints (Caddy handles)
- [ ] API key required for gateway VLM endpoints
- [ ] SAG backend proxies with server-side API key (never expose to browser)
- [ ] Audit logging for all VLM requests
- [ ] Rate limiting to prevent abuse
- [ ] Input validation on image paths (no path traversal)
- [ ] Image size limits (prevent DoS)

### Path Traversal Prevention

```python
import os

def validate_image_path(path: str) -> bool:
    """Ensure path is within allowed directory."""
    ALLOWED_BASE = "/ganuda/data/vision/frames"
    real_path = os.path.realpath(path)
    return real_path.startswith(ALLOWED_BASE)
```

---

## Seven Generations Considerations (Turtle Requirements)

### Ethical Framework

1. **Transparency**: Users must know when AI is analyzing camera feeds
2. **Consent**: Property owners/administrators approve camera AI usage
3. **Purpose Limitation**: Only use for stated security purposes
4. **Data Minimization**: Don't store analysis longer than needed
5. **Human Oversight**: Critical alerts require human review

### Implementation

```python
# Add to VLM responses
{
    "ai_disclosure": "Analysis performed by Qwen2-VL-7B AI model",
    "retention_policy": "Results retained for 30 days",
    "human_review_required": true  # For critical assessments
}
```

### Cultural Sovereignty

- Camera coverage decisions made by tribal administration
- AI recommendations are advisory, not autonomous
- Opt-out mechanisms for community members
- Regular community review of surveillance policies

---

## File Inventory

### Files to Create

| File | Node | Purpose |
|------|------|---------|
| `sag/templates/camera_tab.html` | redfin | Camera UI component |
| `sag/static/js/vlm-client.js` | redfin | VLM API JavaScript client |
| `sag/routes/vlm_routes.py` | redfin | SAG backend VLM proxy |
| `scripts/generate_test_frames.sh` | bluefin | Test image setup |
| `scripts/test_vlm_integration.py` | redfin | Integration test harness |

### Files to Modify

| File | Node | Changes |
|------|------|---------|
| `sag/app.py` | redfin | Register VLM routes |
| `sag/templates/base.html` | redfin | Add Camera nav link |
| `services/vision/vlm_api.py` | bluefin | Add upload endpoint |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| VLM timeout on large images | Medium | Low | Resize before upload |
| GPU OOM with concurrent requests | Low | Medium | Queue system |
| Path traversal attack | Low | High | Strict validation |
| Unauthorized access to feeds | Medium | High | API key + auth |
| Community pushback on surveillance | Medium | High | Transparency + engagement |

---

## Success Metrics

1. **Functional**: All 3 VLM endpoints callable from SAG UI
2. **Performance**: < 20s response time for analysis
3. **Security**: Zero unauthorized access attempts succeed
4. **Reliability**: > 99% uptime during testing
5. **Usability**: < 3 clicks to analyze an image

---

## TPM Decision

**APPROVED WITH CONDITIONS**

The Council's concerns are valid and must be addressed:

1. **Security (Crawdad)**: Implement server-side API key proxy, path validation
2. **Strategy (Raven)**: Add privacy policy to camera tab, audit logging
3. **7GEN (Turtle)**: Include AI disclosure in responses, human review for critical

Proceed with implementation via JR instruction.

---

*Cherokee AI Federation - For Seven Generations*
*Ultrathink Complete: 2026-01-22*
