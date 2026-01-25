# JR Instruction: Frigate + YOLO-World Hybrid Vision System

**Task ID:** HYBRID-VISION-001
**Priority:** P1
**Assigned Node:** bluefin (primary), redfin (SAG UI)
**Date:** January 23, 2026
**Council Vote:** Option D Approved (84.5% confidence)

## Objective

Deploy a hybrid real-time object detection system using:
1. **Frigate NVR** - Motion detection, RTSP management, MQTT events, WebRTC streams
2. **YOLO-World** - Zero-shot detection with text prompts (no retraining needed)
3. **Qwen2-VL** - Rich natural language descriptions
4. **SAG UI** - Real-time camera page with bounding boxes and timeline

## Architecture Summary

```
Cameras → Frigate (motion) → YOLO-World (detect) → Qwen2-VL (describe) → SAG UI
              ↓                    ↓                     ↓
         MQTT events         Bounding boxes        Natural language
```

## Prerequisites

- MQTT broker running (EMQX on bluefin:1883) ✅
- Ring doorbell integrated (ring-mqtt on bluefin:8554) ✅
- RTX 5070 GPU on bluefin ✅
- SAG UI running on redfin:4000 ✅

## Implementation Steps

### Step 1: Install YOLO-World on Bluefin

```bash
ssh bluefin

# Activate venv
source /home/dereadi/cherokee_venv/bin/activate

# Install ultralytics with YOLO-World support
pip install ultralytics

# Download YOLO-World model
python3 -c "from ultralytics import YOLOWorld; m = YOLOWorld('yolov8l-world.pt'); print('Model loaded')"
```

### Step 2: Create YOLO-World Detection Service

**File:** `/ganuda/services/vision/yolo_world_service.py`

```python
#!/usr/bin/env python3
"""
Cherokee Tribal Vision - YOLO-World Zero-Shot Detection Service
Bluefin Node - Port 8091
"""

from flask import Flask, request, jsonify
from ultralytics import YOLOWorld
import cv2
import base64
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Lazy load model
_model = None

# Cherokee tribal detection prompts
TRIBAL_PROMPTS = [
    # Vehicles
    "person", "car", "truck", "pickup truck", "SUV", "van",
    "delivery truck", "FedEx truck", "UPS truck", "Amazon van",
    "USPS truck", "mail truck", "motorcycle", "bicycle",
    # Wildlife
    "cat", "dog", "bird", "squirrel", "rabbit", "deer",
    # Objects
    "package", "box",
    # Calibration
    "Chevrolet Silverado", "white pickup truck"
]

def get_model():
    global _model
    if _model is None:
        logger.info("Loading YOLO-World model...")
        _model = YOLOWorld('yolov8l-world.pt')
        _model.set_classes(TRIBAL_PROMPTS)
        logger.info(f"Model loaded with {len(TRIBAL_PROMPTS)} prompts")
    return _model

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "yolo-world",
        "prompts": len(TRIBAL_PROMPTS),
        "cuda": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    })

@app.route('/detect', methods=['POST'])
def detect():
    """Detect objects with bounding boxes"""
    data = request.json
    if not data or 'image_path' not in data:
        return jsonify({"error": "image_path required"}), 400

    model = get_model()
    results = model(data['image_path'], verbose=False)

    detections = []
    for r in results:
        for box in r.boxes:
            cls_idx = int(box.cls)
            detections.append({
                "class": TRIBAL_PROMPTS[cls_idx] if cls_idx < len(TRIBAL_PROMPTS) else "unknown",
                "confidence": float(box.conf),
                "bbox": box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            })

    return jsonify({
        "image_path": data['image_path'],
        "detections": detections,
        "count": len(detections)
    })

@app.route('/detect_custom', methods=['POST'])
def detect_custom():
    """Detect with custom prompts (zero-shot)"""
    data = request.json
    if not data or 'image_path' not in data:
        return jsonify({"error": "image_path required"}), 400

    prompts = data.get('prompts', TRIBAL_PROMPTS)

    model = get_model()
    model.set_classes(prompts)
    results = model(data['image_path'], verbose=False)

    # Reset to default prompts
    model.set_classes(TRIBAL_PROMPTS)

    detections = []
    for r in results:
        for box in r.boxes:
            cls_idx = int(box.cls)
            detections.append({
                "class": prompts[cls_idx] if cls_idx < len(prompts) else "unknown",
                "confidence": float(box.conf),
                "bbox": box.xyxy[0].tolist()
            })

    return jsonify({
        "detections": detections,
        "prompts_used": prompts
    })

@app.route('/annotate', methods=['POST'])
def annotate():
    """Return annotated image with bounding boxes"""
    data = request.json
    if not data or 'image_path' not in data:
        return jsonify({"error": "image_path required"}), 400

    model = get_model()
    results = model(data['image_path'], verbose=False)

    # Draw boxes
    img = cv2.imread(data['image_path'])
    detections = []

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_idx = int(box.cls)
            cls_name = TRIBAL_PROMPTS[cls_idx] if cls_idx < len(TRIBAL_PROMPTS) else "unknown"
            conf = float(box.conf)

            # Green box
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Label background
            label = f"{cls_name} {conf:.0%}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(img, (x1, y1 - h - 10), (x1 + w, y1), (0, 255, 0), -1)
            cv2.putText(img, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

            detections.append({
                "class": cls_name,
                "confidence": conf,
                "bbox": [x1, y1, x2, y2]
            })

    # Encode to base64
    _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    return jsonify({
        "annotated_image": f"data:image/jpeg;base64,{img_base64}",
        "detections": detections
    })

@app.route('/prompts', methods=['GET'])
def get_prompts():
    """Get current detection prompts"""
    return jsonify({"prompts": TRIBAL_PROMPTS})

@app.route('/prompts', methods=['POST'])
def add_prompt():
    """Add a custom prompt"""
    data = request.json
    prompt = data.get('prompt')
    if prompt and prompt not in TRIBAL_PROMPTS:
        TRIBAL_PROMPTS.append(prompt)
        model = get_model()
        model.set_classes(TRIBAL_PROMPTS)
        return jsonify({"status": "added", "prompt": prompt, "total": len(TRIBAL_PROMPTS)})
    return jsonify({"status": "exists or invalid"})

if __name__ == '__main__':
    logger.info("Starting YOLO-World service on port 8091")
    app.run(host='0.0.0.0', port=8091)
```

### Step 3: Deploy Frigate NVR

**File:** `/ganuda/services/frigate/config.yml`

```yaml
mqtt:
  enabled: true
  host: localhost
  port: 1883
  topic_prefix: frigate
  client_id: frigate

detectors:
  # Use YOLO-World via HTTP (custom integration)
  default:
    type: cpu  # Fallback, we'll use YOLO-World API

cameras:
  traffic:
    enabled: true
    ffmpeg:
      inputs:
        - path: rtsp://admin:jawaseatlasers2@192.168.132.182:554/cam/realmonitor?channel=1&subtype=1
          roles:
            - detect
            - record
            - rtmp
    detect:
      enabled: true
      width: 1280
      height: 720
      fps: 5
    motion:
      threshold: 25
      contour_area: 100
    objects:
      track:
        - person
        - car
        - truck
        - cat
        - dog
        - bird
    record:
      enabled: true
      retain:
        days: 7
        mode: motion
      events:
        retain:
          default: 14
          mode: active_objects

  office:
    enabled: true
    ffmpeg:
      inputs:
        - path: rtsp://admin:jawaseatlasers2@192.168.132.181:554/cam/realmonitor?channel=1&subtype=0
          roles:
            - detect
    detect:
      enabled: true
      width: 1280
      height: 720
      fps: 5
    objects:
      track:
        - person

  ring_doorbell:
    enabled: true
    ffmpeg:
      inputs:
        - path: rtsp://ring:tribal_vision_2026@localhost:8554/d436398fc2b8_live
          roles:
            - detect
    detect:
      enabled: false  # On-demand - enable via API when needed

go2rtc:
  streams:
    traffic:
      - rtsp://admin:jawaseatlasers2@192.168.132.182:554/cam/realmonitor?channel=1&subtype=1
    office:
      - rtsp://admin:jawaseatlasers2@192.168.132.181:554/cam/realmonitor?channel=1&subtype=0
    ring_doorbell:
      - rtsp://ring:tribal_vision_2026@localhost:8554/d436398fc2b8_live

# WebRTC for low-latency viewing
live:
  height: 720
  quality: 8
```

**Start Frigate:**

```bash
mkdir -p /ganuda/services/frigate /ganuda/data/frigate

podman run -d \
  --name frigate \
  --network host \
  --shm-size=256m \
  -v /ganuda/services/frigate/config.yml:/config/config.yml:ro \
  -v /ganuda/data/frigate:/media/frigate \
  --restart unless-stopped \
  ghcr.io/blakeblackshear/frigate:stable
```

### Step 4: Create Motion-to-Detection Bridge

**File:** `/ganuda/services/vision/motion_detection_bridge.py`

```python
#!/usr/bin/env python3
"""
Bridge Frigate motion events to YOLO-World detection
Subscribes to MQTT, triggers YOLO-World, publishes results
"""

import json
import httpx
import paho.mqtt.client as mqtt
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MQTT_HOST = "localhost"
MQTT_PORT = 1883
YOLO_WORLD_URL = "http://localhost:8091"
VLM_URL = "http://localhost:8090"

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    logger.info(f"Connected to MQTT with result code {rc}")
    client.subscribe("frigate/+/motion")
    client.subscribe("frigate/events")

def on_motion(client, userdata, msg):
    """Handle motion events from Frigate"""
    try:
        payload = msg.payload.decode()
        camera = msg.topic.split('/')[1]

        if payload == "ON":
            logger.info(f"[{camera}] Motion detected, triggering YOLO-World")

            # Get snapshot from Frigate
            snapshot_url = f"http://localhost:5000/api/{camera}/latest.jpg"
            snapshot_path = f"/ganuda/data/vision/frames/{camera}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

            # Download snapshot
            resp = httpx.get(snapshot_url, timeout=5)
            if resp.status_code == 200:
                with open(snapshot_path, 'wb') as f:
                    f.write(resp.content)

                # YOLO-World detection
                detect_resp = httpx.post(f"{YOLO_WORLD_URL}/detect",
                    json={"image_path": snapshot_path},
                    timeout=30)
                detections = detect_resp.json()

                if detections.get('detections'):
                    # Get VLM description
                    vlm_resp = httpx.post(f"{VLM_URL}/v1/vlm/describe",
                        json={
                            "image_path": snapshot_path,
                            "camera_id": camera
                        },
                        timeout=60)
                    description = vlm_resp.json()

                    # Publish enriched event
                    event = {
                        "camera": camera,
                        "timestamp": datetime.now().isoformat(),
                        "detections": detections['detections'],
                        "description": description.get('description', ''),
                        "snapshot": snapshot_path
                    }

                    client.publish(f"tribal/vision/{camera}/detection",
                                 json.dumps(event))

                    logger.info(f"[{camera}] Published {len(detections['detections'])} detections")

    except Exception as e:
        logger.error(f"Error processing motion: {e}")

def on_message(client, userdata, msg):
    if "motion" in msg.topic:
        on_motion(client, userdata, msg)

client.on_connect = on_connect
client.on_message = on_message

if __name__ == '__main__':
    logger.info("Starting Motion-Detection Bridge")
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()
```

### Step 5: SAG UI Cameras Page Updates

**File:** `/ganuda/sag/routes/cameras_routes.py` (add endpoints)

```python
from flask import Blueprint, jsonify, request, send_file
import httpx
from pathlib import Path

cameras_bp = Blueprint('cameras', __name__, url_prefix='/api/cameras')

YOLO_WORLD = "http://192.168.132.222:8091"
FRIGATE = "http://192.168.132.222:5000"

CAMERAS = {
    "traffic": {
        "id": "traffic",
        "name": "Traffic Monitor",
        "ip": "192.168.132.182",
        "purpose": "Vehicle & Wildlife Detection",
        "specialist": "Eagle Eye",
        "continuous": True
    },
    "office": {
        "id": "office",
        "name": "Office Monitor",
        "ip": "192.168.132.181",
        "purpose": "Security / PII",
        "specialist": "Crawdad",
        "continuous": True
    },
    "ring_doorbell": {
        "id": "ring_doorbell",
        "name": "Ring Doorbell",
        "ip": "cloud",
        "purpose": "Front Door / Stereo Depth",
        "specialist": "Eagle Eye",
        "continuous": False,
        "stereo_pair": "traffic"
    }
}

@cameras_bp.route('/')
def list_cameras():
    return jsonify({"cameras": list(CAMERAS.values())})

@cameras_bp.route('/<camera_id>/snapshot')
def get_snapshot(camera_id):
    """Get latest snapshot from Frigate"""
    resp = httpx.get(f"{FRIGATE}/api/{camera_id}/latest.jpg", timeout=5)
    if resp.status_code == 200:
        return resp.content, 200, {'Content-Type': 'image/jpeg'}
    return jsonify({"error": "Snapshot unavailable"}), 404

@cameras_bp.route('/<camera_id>/detect', methods=['POST'])
def detect_objects(camera_id):
    """Detect objects in latest snapshot"""
    # Get snapshot
    snapshot_resp = httpx.get(f"{FRIGATE}/api/{camera_id}/latest.jpg", timeout=5)
    if snapshot_resp.status_code != 200:
        return jsonify({"error": "Snapshot unavailable"}), 404

    # Save temp file
    snap_path = f"/ganuda/data/vision/frames/{camera_id}_detect.jpg"
    with open(snap_path, 'wb') as f:
        f.write(snapshot_resp.content)

    # YOLO-World detection
    detect_resp = httpx.post(f"{YOLO_WORLD}/detect",
        json={"image_path": snap_path},
        timeout=30)

    return jsonify(detect_resp.json())

@cameras_bp.route('/<camera_id>/annotated')
def get_annotated(camera_id):
    """Get annotated snapshot with bounding boxes"""
    # Get snapshot
    snapshot_resp = httpx.get(f"{FRIGATE}/api/{camera_id}/latest.jpg", timeout=5)
    if snapshot_resp.status_code != 200:
        return jsonify({"error": "Snapshot unavailable"}), 404

    snap_path = f"/ganuda/data/vision/frames/{camera_id}_annotate.jpg"
    with open(snap_path, 'wb') as f:
        f.write(snapshot_resp.content)

    # YOLO-World annotate
    annotate_resp = httpx.post(f"{YOLO_WORLD}/annotate",
        json={"image_path": snap_path},
        timeout=30)

    return jsonify(annotate_resp.json())

@cameras_bp.route('/prompts', methods=['GET', 'POST'])
def manage_prompts():
    """Get or add detection prompts"""
    if request.method == 'GET':
        resp = httpx.get(f"{YOLO_WORLD}/prompts", timeout=5)
        return jsonify(resp.json())
    else:
        data = request.json
        resp = httpx.post(f"{YOLO_WORLD}/prompts",
            json=data, timeout=5)
        return jsonify(resp.json())
```

### Step 6: Create Systemd Services

**File:** `/ganuda/scripts/systemd/yolo-world.service`

```ini
[Unit]
Description=YOLO-World Detection Service
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/vision
Environment="PATH=/home/dereadi/cherokee_venv/bin"
ExecStart=/home/dereadi/cherokee_venv/bin/python3 yolo_world_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

**File:** `/ganuda/scripts/systemd/motion-bridge.service`

```ini
[Unit]
Description=Motion-Detection Bridge
After=network.target yolo-world.service

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/vision
Environment="PATH=/home/dereadi/cherokee_venv/bin"
ExecStart=/home/dereadi/cherokee_venv/bin/python3 motion_detection_bridge.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

## Verification Commands

```bash
# 1. Test YOLO-World health
curl http://bluefin:8091/health

# 2. Test detection
curl -X POST http://bluefin:8091/detect \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/ganuda/data/vision/frames/motion_20260123_123100.jpg"}'

# 3. Test annotated image
curl -X POST http://bluefin:8091/annotate \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/ganuda/data/vision/frames/motion_20260123_123100.jpg"}' \
  | jq '.detections'

# 4. Check Frigate
curl http://bluefin:5000/api/stats

# 5. Check MQTT events
mosquitto_sub -h bluefin -t "tribal/vision/#" -v

# 6. SAG UI cameras endpoint
curl http://redfin:4000/api/cameras
```

## Success Criteria

- [ ] YOLO-World service running on bluefin:8091
- [ ] Frigate NVR running with all 3 cameras
- [ ] Motion-detection bridge publishing enriched events
- [ ] SAG cameras page shows live feeds
- [ ] Real-time bounding boxes on detection
- [ ] Timeline shows motion events with descriptions
- [ ] Ring doorbell activates on-demand for stereo

## Dependencies

```
ultralytics>=8.0.0
flask>=2.0.0
httpx>=0.24.0
paho-mqtt>=1.6.0
opencv-python-headless>=4.8.0
torch>=2.0.0
```

---

**Council Approved:** Option D - Hybrid (Frigate + YOLO-World)
**FOR SEVEN GENERATIONS**
