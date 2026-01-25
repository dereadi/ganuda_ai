# JR Instruction: SAG Cameras Page with Real-Time AI Detection

**Task ID:** SAG-CAMERAS-001
**Priority:** P1
**Assigned Node:** redfin (SAG UI), bluefin (VLM/detection)
**Date:** January 23, 2026

## Objective

Enhance the SAG Cameras page (http://192.168.132.223:4000/) to display:
1. Live camera feeds with real-time AI-annotated bounding boxes
2. Ring doorbell integration
3. Motion detection event timeline with identified objects
4. VLM descriptions for each detection

## Current State

**Cameras API** (`/api/cameras`) returns:
```json
{
  "cameras": [
    {"id": "office_pii", "ip": "192.168.132.181", "name": "Office PII Monitor"},
    {"id": "traffic", "ip": "192.168.132.182", "name": "Traffic Monitor"}
  ]
}
```

**VLM API** (bluefin:8090) endpoints:
- `/v1/vlm/describe` - Describe frame contents
- `/v1/vlm/analyze` - Anomaly detection
- `/v1/vlm/ask` - Q&A about frame

**Missing:**
- Ring doorbell in camera registry
- Object detection with bounding boxes
- Annotated frame display
- Motion event timeline

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SAG UI (redfin:4000)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Cameras Page                       │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │ Traffic │  │  Office │  │  Ring   │   Live      │   │
│  │  │   🎯    │  │   🎯    │  │   🎯    │   Feeds     │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  │                                                     │   │
│  │  Detection Timeline                                 │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ 12:31 🚗 White pickup truck | Traffic        │  │   │
│  │  │ 12:18 🐱 Orange cat crossing | Traffic       │  │   │
│  │  │ 11:45 📦 FedEx truck | Traffic               │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Detection Service (bluefin)                     │
│                                                              │
│  Motion Detection ──► Object Detection ──► VLM Description  │
│  (OpenCV MOG2)        (YOLO/OWL-ViT)       (Qwen2-VL)       │
│                                                              │
│  Annotated Frame = Original + Bounding Boxes + Labels       │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Add Object Detection Endpoint to VLM API

**File:** `/ganuda/services/vision/vlm_api.py`

Add YOLO or Grounding DINO for bounding box detection:

```python
from ultralytics import YOLO

# Load YOLO model (one-time)
_yolo = None
def get_yolo():
    global _yolo
    if _yolo is None:
        _yolo = YOLO('yolov8n.pt')  # Or yolov8s.pt for better accuracy
    return _yolo

@app.route('/v1/vlm/detect', methods=['POST'])
def detect():
    """Detect objects with bounding boxes."""
    data = request.json
    if not data or 'image_path' not in data:
        return jsonify({"error": "image_path required"}), 400

    yolo = get_yolo()
    results = yolo(data['image_path'])

    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                "class": r.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy[0].tolist(),  # [x1, y1, x2, y2]
            })

    return jsonify({
        "image_path": data['image_path'],
        "detections": detections,
        "count": len(detections)
    })

@app.route('/v1/vlm/detect_and_describe', methods=['POST'])
def detect_and_describe():
    """Detect objects AND get VLM description."""
    data = request.json
    if not data or 'image_path' not in data:
        return jsonify({"error": "image_path required"}), 400

    # Get object detections
    yolo = get_yolo()
    results = yolo(data['image_path'])

    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                "class": r.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy[0].tolist(),
            })

    # Get VLM description
    vlm = get_vlm()
    description = vlm.describe_frame(data['image_path'], data.get('camera_id', 'unknown'))

    return jsonify({
        "image_path": data['image_path'],
        "detections": detections,
        "count": len(detections),
        "description": description
    })

@app.route('/v1/vlm/annotate', methods=['POST'])
def annotate():
    """Return annotated image with bounding boxes drawn."""
    import cv2
    import base64
    from io import BytesIO

    data = request.json
    if not data or 'image_path' not in data:
        return jsonify({"error": "image_path required"}), 400

    yolo = get_yolo()
    results = yolo(data['image_path'])

    # Draw boxes on image
    img = cv2.imread(data['image_path'])
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_name = r.names[int(box.cls)]
            conf = float(box.conf)

            # Draw rectangle
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Draw label
            label = f"{cls_name} {conf:.2f}"
            cv2.putText(img, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Encode to base64
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    return jsonify({
        "annotated_image": f"data:image/jpeg;base64,{img_base64}",
        "detections": len(results[0].boxes) if results else 0
    })
```

### Step 2: Add Ring Doorbell to Camera Registry

**File:** `/ganuda/sag/routes/cameras.py` (or wherever cameras API is defined)

```python
CAMERAS = {
    "traffic": {
        "id": "traffic",
        "name": "Traffic Monitor",
        "ip": "192.168.132.182",
        "rtsp": "rtsp://admin:jawaseatlasers2@192.168.132.182:554/cam/realmonitor?channel=1&subtype=1",
        "purpose": "Vehicle Identification",
        "specialist": "Eagle Eye",
        "continuous": True
    },
    "office_pii": {
        "id": "office_pii",
        "name": "Office PII Monitor",
        "ip": "192.168.132.181",
        "rtsp": "rtsp://admin:jawaseatlasers2@192.168.132.181:554/cam/realmonitor?channel=1&subtype=0",
        "purpose": "Face Detection / Security",
        "specialist": "Crawdad",
        "continuous": True
    },
    "ring_doorbell": {
        "id": "ring_doorbell",
        "name": "Ring Doorbell",
        "ip": "cloud",
        "rtsp": "rtsp://ring:tribal_vision_2026@bluefin:8554/d436398fc2b8_live",
        "purpose": "Front Door / Stereo Depth",
        "specialist": "Eagle Eye",
        "continuous": False,  # On-demand only
        "stereo_pair": "traffic"
    }
}
```

### Step 3: Create Cameras Page JavaScript

**File:** `/ganuda/sag/static/js/cameras.js`

```javascript
class CamerasView {
    constructor() {
        this.cameras = [];
        this.detections = [];
        this.refreshInterval = null;
    }

    async init() {
        await this.loadCameras();
        this.render();
        this.startAutoRefresh();
    }

    async loadCameras() {
        const resp = await fetch('/api/cameras');
        const data = await resp.json();
        this.cameras = data.cameras;
    }

    async captureAndDetect(cameraId) {
        // Capture frame
        const captureResp = await fetch(`/api/cameras/${cameraId}/capture`, {
            method: 'POST'
        });
        const captureData = await captureResp.json();

        // Detect objects
        const detectResp = await fetch('/api/vlm/detect_and_describe', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                image_path: captureData.frame_path,
                camera_id: cameraId
            })
        });
        return await detectResp.json();
    }

    async getAnnotatedFrame(cameraId) {
        const resp = await fetch(`/api/cameras/${cameraId}/annotated`);
        return await resp.json();
    }

    render() {
        const container = document.getElementById('cameras-view');
        container.innerHTML = `
            <div class="cameras-grid">
                ${this.cameras.map(cam => this.renderCameraCard(cam)).join('')}
            </div>
            <div class="detection-timeline">
                <h3>Detection Timeline</h3>
                <div id="timeline-events"></div>
            </div>
        `;
    }

    renderCameraCard(camera) {
        const isOnDemand = !camera.continuous;
        return `
            <div class="camera-card ${isOnDemand ? 'on-demand' : ''}" data-camera="${camera.id}">
                <div class="camera-header">
                    <span class="camera-name">${camera.name}</span>
                    <span class="camera-status ${camera.status}">${camera.status}</span>
                </div>
                <div class="camera-feed">
                    <img id="feed-${camera.id}" src="/api/cameras/${camera.id}/frame" alt="${camera.name}">
                    <canvas id="overlay-${camera.id}" class="detection-overlay"></canvas>
                </div>
                <div class="camera-controls">
                    <button onclick="camerasView.captureAndDetect('${camera.id}')">
                        🎯 Detect
                    </button>
                    ${isOnDemand ? `
                        <button onclick="camerasView.activateStream('${camera.id}')">
                            📹 Activate
                        </button>
                    ` : ''}
                </div>
                <div class="camera-info">
                    <span>Specialist: ${camera.specialist}</span>
                    <span>Purpose: ${camera.purpose}</span>
                </div>
            </div>
        `;
    }

    drawDetections(cameraId, detections) {
        const canvas = document.getElementById(`overlay-${cameraId}`);
        const img = document.getElementById(`feed-${cameraId}`);
        const ctx = canvas.getContext('2d');

        canvas.width = img.width;
        canvas.height = img.height;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        detections.forEach(det => {
            const [x1, y1, x2, y2] = det.bbox;
            const scaleX = canvas.width / img.naturalWidth;
            const scaleY = canvas.height / img.naturalHeight;

            ctx.strokeStyle = '#00ff00';
            ctx.lineWidth = 2;
            ctx.strokeRect(x1 * scaleX, y1 * scaleY,
                          (x2 - x1) * scaleX, (y2 - y1) * scaleY);

            ctx.fillStyle = '#00ff00';
            ctx.font = '14px monospace';
            ctx.fillText(`${det.class} ${(det.confidence * 100).toFixed(0)}%`,
                        x1 * scaleX, y1 * scaleY - 5);
        });
    }

    addToTimeline(event) {
        const timeline = document.getElementById('timeline-events');
        const eventEl = document.createElement('div');
        eventEl.className = 'timeline-event';
        eventEl.innerHTML = `
            <span class="event-time">${event.time}</span>
            <span class="event-icon">${event.icon}</span>
            <span class="event-desc">${event.description}</span>
            <span class="event-camera">${event.camera}</span>
        `;
        timeline.prepend(eventEl);
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(async () => {
            for (const cam of this.cameras) {
                if (cam.continuous) {
                    const img = document.getElementById(`feed-${cam.id}`);
                    if (img) {
                        img.src = `/api/cameras/${cam.id}/frame?t=${Date.now()}`;
                    }
                }
            }
        }, 5000);  // Refresh every 5 seconds
    }
}

const camerasView = new CamerasView();
document.addEventListener('DOMContentLoaded', () => camerasView.init());
```

### Step 4: Add Camera API Endpoints

**File:** `/ganuda/sag/routes/cameras_routes.py`

```python
from flask import Blueprint, jsonify, send_file
import httpx
import cv2
from pathlib import Path
from datetime import datetime

cameras_bp = Blueprint('cameras', __name__, url_prefix='/api/cameras')

FRAME_DIR = Path('/ganuda/data/vision/frames')
VLM_URL = 'http://192.168.132.222:8090'

@cameras_bp.route('/<camera_id>/frame')
def get_frame(camera_id):
    """Get latest frame for camera."""
    frames = sorted(FRAME_DIR.glob(f'{camera_id}_*.jpg'), reverse=True)
    if frames:
        return send_file(frames[0], mimetype='image/jpeg')
    return jsonify({"error": "No frames available"}), 404

@cameras_bp.route('/<camera_id>/capture', methods=['POST'])
def capture_frame(camera_id):
    """Capture new frame from camera."""
    camera = CAMERAS.get(camera_id)
    if not camera:
        return jsonify({"error": "Camera not found"}), 404

    cap = cv2.VideoCapture(camera['rtsp'])
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return jsonify({"error": "Failed to capture"}), 500

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    frame_path = FRAME_DIR / f'{camera_id}_{timestamp}.jpg'
    cv2.imwrite(str(frame_path), frame)

    return jsonify({
        "frame_path": str(frame_path),
        "timestamp": timestamp,
        "camera_id": camera_id
    })

@cameras_bp.route('/<camera_id>/annotated')
def get_annotated_frame(camera_id):
    """Get latest frame with detection annotations."""
    frames = sorted(FRAME_DIR.glob(f'{camera_id}_*.jpg'), reverse=True)
    if not frames:
        return jsonify({"error": "No frames available"}), 404

    resp = httpx.post(f'{VLM_URL}/v1/vlm/annotate',
                     json={"image_path": str(frames[0])},
                     timeout=30.0)
    return jsonify(resp.json())

@cameras_bp.route('/<camera_id>/detect', methods=['POST'])
def detect_objects(camera_id):
    """Detect objects in latest frame."""
    frames = sorted(FRAME_DIR.glob(f'{camera_id}_*.jpg'), reverse=True)
    if not frames:
        return jsonify({"error": "No frames available"}), 404

    resp = httpx.post(f'{VLM_URL}/v1/vlm/detect_and_describe',
                     json={
                         "image_path": str(frames[0]),
                         "camera_id": camera_id
                     },
                     timeout=60.0)
    return jsonify(resp.json())
```

### Step 5: Update delivery-watch for Detection Integration

Modify `/ganuda/lib/tribal_vision/quick_delivery_watch.py` to call detection API when motion is detected:

```python
def on_motion_detected(frame, frame_path):
    """Enhanced motion handler with detection."""
    # Call detection API
    try:
        resp = httpx.post(f"{VLM_URL}/v1/vlm/detect_and_describe",
            json={
                "image_path": str(frame_path),
                "camera_id": CAMERA_ID
            },
            timeout=60.0)
        detection_result = resp.json()

        # Log detections
        if detection_result.get('detections'):
            for det in detection_result['detections']:
                print(f"[DETECT] {det['class']} ({det['confidence']:.0%})")

        # Store event for timeline
        store_detection_event({
            "timestamp": datetime.now().isoformat(),
            "camera_id": CAMERA_ID,
            "detections": detection_result.get('detections', []),
            "description": detection_result.get('description', {})
        })

    except Exception as e:
        print(f"[DETECT] Error: {e}")
```

### Step 6: Install YOLO on Bluefin

```bash
ssh bluefin "source /home/dereadi/cherokee_venv/bin/activate && pip install ultralytics"
```

## CSS Styling (Optional)

**File:** `/ganuda/sag/static/css/cameras.css`

```css
.cameras-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
    padding: 20px;
}

.camera-card {
    background: var(--card-bg);
    border-radius: 8px;
    overflow: hidden;
}

.camera-card.on-demand {
    border: 2px dashed var(--accent-color);
}

.camera-feed {
    position: relative;
    width: 100%;
}

.camera-feed img {
    width: 100%;
    display: block;
}

.detection-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
}

.detection-timeline {
    margin-top: 20px;
    padding: 20px;
}

.timeline-event {
    display: flex;
    gap: 10px;
    padding: 10px;
    border-bottom: 1px solid var(--border-color);
}

.event-icon {
    font-size: 1.5em;
}
```

## Verification

```bash
# Test detection endpoint
curl -X POST http://192.168.132.222:8090/v1/vlm/detect \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/ganuda/data/vision/frames/motion_20260123_123100.jpg"}'

# Test annotated frame
curl -X POST http://192.168.132.222:8090/v1/vlm/annotate \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/ganuda/data/vision/frames/motion_20260123_123100.jpg"}' | jq '.detections'

# Check SAG cameras page
curl http://192.168.132.223:4000/api/cameras
```

## Success Criteria

- [ ] YOLO installed on bluefin
- [ ] `/v1/vlm/detect` endpoint returns bounding boxes
- [ ] `/v1/vlm/annotate` endpoint returns base64 annotated image
- [ ] Ring doorbell appears in cameras list
- [ ] Cameras page shows live feeds
- [ ] Detection overlay draws bounding boxes
- [ ] Timeline shows motion events with identified objects

## Icon Reference for Timeline

| Detection | Icon |
|-----------|------|
| car/truck | 🚗 |
| person | 🚶 |
| cat | 🐱 |
| dog | 🐕 |
| bird | 🐦 |
| delivery truck | 📦 |
| bicycle | 🚲 |

---

**FOR SEVEN GENERATIONS** - The tribe's eyes now see and understand.
