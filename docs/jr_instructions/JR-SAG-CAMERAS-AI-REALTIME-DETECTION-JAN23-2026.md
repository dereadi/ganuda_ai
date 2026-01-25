# Jr Instruction: SAG Cameras Real-Time AI Detection Enhancement

**Task ID:** SAG-CAMERAS-AI-001
**Priority:** P1
**Date:** January 23, 2026
**Estimated Effort:** 4-6 hours total

## Objective

Enhance the SAG Cameras page (http://192.168.132.223:4000/ → Cameras view) with:
1. Real-time AI object detection with bounding boxes
2. MQTT-based live detection events
3. Stereo vision depth estimation using Ring doorbell + Amcrest traffic camera
4. Zero-shot detection via YOLO-World (detect custom objects by text prompt)

## Current Architecture

**SAG UI Location:** `/ganuda/home/dereadi/sag_unified_interface/`
- `app.py` - Flask application (port 4000)
- `static/js/control-room.js` - Camera view logic (lines 1226-1790)
- `static/js/unified.js` - Main UI framework

**Existing Camera API Endpoints:**
- `GET /api/cameras` - List cameras
- `GET /api/cameras/stats` - Camera statistics
- `GET /api/cameras/detections` - Recent detections
- `GET /api/cameras/{id}/snapshot` - Camera snapshot
- `GET /api/cameras/frame/{filename}` - Saved frame image

**Vision Services (bluefin):**
- VLM Service: `/ganuda/services/vision/vlm_service.py` (port 8093)
- YOLO-World: `/ganuda/services/vision/yolo_world_service.py` (port 8091) - NOT YET DEPLOYED

**Available Cameras:**
| Camera | IP | RTSP | Purpose |
|--------|----|----|---------|
| Traffic (Amcrest) | 192.168.132.182 | :554 | Street view, motion detection |
| Office (Amcrest) | 192.168.132.181 | :554 | Office monitoring |
| Ring Doorbell | via ring-mqtt | :8554 | Front door, stereo partner |

**MQTT Broker:** EMQX on bluefin:1883

---

## Phase 1: Deploy YOLO-World Service

**File:** `/ganuda/services/vision/yolo_world_service.py`
**Port:** 8091

### 1.1 Create systemd service

Create `/ganuda/services/vision/yolo-world.service`:

```ini
[Unit]
Description=YOLO-World Zero-Shot Detection Service
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/vision
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/dereadi/cherokee_venv/bin/python3 -u yolo_world_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 1.2 Fix YOLO-World service code

The current service needs enhancement. Update `/ganuda/services/vision/yolo_world_service.py`:

```python
# Add after model load:
model.set_classes(TRIBAL_PROMPTS)

# Add endpoint for custom prompts:
@app.route('/detect_custom', methods=['POST'])
def detect_custom():
    """Detect with custom prompts."""
    data = request.json
    image_path = data.get('image_path')
    custom_prompts = data.get('prompts', TRIBAL_PROMPTS)

    # Temporarily set custom classes
    model.set_classes(custom_prompts)
    results = model(image_path)
    model.set_classes(TRIBAL_PROMPTS)  # Reset

    detections = []
    for result in results:
        boxes = result.boxes.cpu().numpy()
        for box in boxes:
            detections.append({
                'class': custom_prompts[int(box.cls[0])],
                'confidence': float(box.conf[0]),
                'bbox': box.xyxy[0].astype(int).tolist()
            })
    return jsonify(detections)
```

### 1.3 Deploy and start

```bash
sudo cp /ganuda/services/vision/yolo-world.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable yolo-world
sudo systemctl start yolo-world
```

---

## Phase 2: SAG Backend API Enhancements

**File:** `/ganuda/home/dereadi/sag_unified_interface/app.py`

### 2.1 Add YOLO detection endpoint

```python
@app.route('/api/cameras/<camera_id>/detect', methods=['POST'])
def detect_objects(camera_id):
    """Run YOLO-World detection on camera frame."""
    import requests

    # Get latest frame
    frame_path = get_latest_frame(camera_id)
    if not frame_path:
        return jsonify({'error': 'No frame available'}), 404

    # Call YOLO-World service
    try:
        resp = requests.post(
            'http://192.168.132.222:8091/detect',
            json={'image_path': frame_path},
            timeout=30
        )
        detections = resp.json()

        return jsonify({
            'camera_id': camera_id,
            'frame_path': frame_path,
            'detections': detections,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>/annotate', methods=['POST'])
def annotate_frame(camera_id):
    """Return frame with bounding boxes drawn."""
    import requests

    frame_path = get_latest_frame(camera_id)
    if not frame_path:
        return jsonify({'error': 'No frame available'}), 404

    resp = requests.post(
        'http://192.168.132.222:8091/annotate',
        json={'image_path': frame_path},
        timeout=30
    )
    return jsonify(resp.json())
```

### 2.2 Add WebSocket for real-time events

```python
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt

socketio = SocketIO(app, cors_allowed_origins="*")

# MQTT → WebSocket bridge
def on_mqtt_message(client, userdata, msg):
    """Forward MQTT detection events to WebSocket clients."""
    try:
        payload = json.loads(msg.payload.decode())
        socketio.emit('detection', payload)
    except:
        pass

mqtt_client = mqtt.Client()
mqtt_client.on_message = on_mqtt_message
mqtt_client.connect('192.168.132.222', 1883)
mqtt_client.subscribe('ganuda/vision/detections')
mqtt_client.loop_start()
```

---

## Phase 3: Frontend Enhancement

**File:** `/ganuda/home/dereadi/sag_unified_interface/static/js/control-room.js`

### 3.1 Add bounding box overlay to camera cards

Add after line ~1315 (camera-preview div):

```javascript
// Add canvas overlay for bounding boxes
html += '<canvas class="detection-overlay" id="overlay-' + cam.id + '"></canvas>';
```

### 3.2 Create detection overlay renderer

Add new function:

```javascript
function drawDetectionBoxes(cameraId, detections) {
    var canvas = document.getElementById('overlay-' + cameraId);
    var img = canvas.previousElementSibling; // The camera image
    if (!canvas || !img) return;

    // Match canvas size to image
    canvas.width = img.naturalWidth || img.width;
    canvas.height = img.naturalHeight || img.height;

    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Color map for object types
    var colors = {
        'person': '#00ff00',
        'car': '#0088ff',
        'truck': '#ff8800',
        'delivery truck': '#ff00ff',
        'cat': '#ffff00',
        'dog': '#ff0088',
        'default': '#00ffff'
    };

    detections.forEach(function(det) {
        var bbox = det.bbox;
        var color = colors[det.class] || colors['default'];

        // Draw box
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]);

        // Draw label background
        var label = det.class + ' ' + (det.confidence * 100).toFixed(0) + '%';
        ctx.font = 'bold 14px Arial';
        var textWidth = ctx.measureText(label).width;
        ctx.fillStyle = color;
        ctx.fillRect(bbox[0], bbox[1] - 20, textWidth + 10, 20);

        // Draw label text
        ctx.fillStyle = '#000';
        ctx.fillText(label, bbox[0] + 5, bbox[1] - 5);
    });
}

function runDetection(cameraId) {
    fetch('/api/cameras/' + cameraId + '/detect', { method: 'POST' })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.detections) {
                drawDetectionBoxes(cameraId, data.detections);
                addDetectionToFeed(cameraId, data.detections);
            }
        })
        .catch(function(err) {
            console.error('Detection failed:', err);
        });
}
```

### 3.3 Add WebSocket for real-time updates

```javascript
// Connect to WebSocket for live detections
var socket = io();

socket.on('detection', function(data) {
    // Update bounding boxes
    if (data.camera_id && data.detections) {
        drawDetectionBoxes(data.camera_id, data.detections);
    }

    // Add to detection feed
    addDetectionToFeed(data.camera_id, data.detections);

    // Flash the camera card
    var card = document.querySelector('.camera-card[data-camera="' + data.camera_id + '"]');
    if (card) {
        card.classList.add('detection-flash');
        setTimeout(function() { card.classList.remove('detection-flash'); }, 500);
    }
});

function addDetectionToFeed(cameraId, detections) {
    var feed = document.getElementById('detection-feed');
    if (!feed) return;

    detections.forEach(function(det) {
        var item = document.createElement('div');
        item.className = 'detection-item new';
        item.innerHTML = '<span class="det-time">' + new Date().toLocaleTimeString() + '</span>' +
            '<span class="det-icon">' + getDetectionIcon(det.class) + '</span>' +
            '<span class="det-label">' + det.class + '</span>' +
            '<span class="det-conf">' + (det.confidence * 100).toFixed(0) + '%</span>' +
            '<span class="det-cam">' + cameraId + '</span>';

        feed.insertBefore(item, feed.firstChild);

        // Remove 'new' class after animation
        setTimeout(function() { item.classList.remove('new'); }, 300);

        // Keep feed manageable
        while (feed.children.length > 50) {
            feed.removeChild(feed.lastChild);
        }
    });
}

function getDetectionIcon(cls) {
    var icons = {
        'person': '🚶', 'car': '🚗', 'truck': '🚛', 'pickup truck': '🛻',
        'delivery truck': '📦', 'FedEx truck': '📦', 'UPS truck': '📦',
        'cat': '🐱', 'dog': '🐕', 'bird': '🐦', 'squirrel': '🐿️'
    };
    return icons[cls] || '🎯';
}
```

### 3.4 Add CSS for detection overlay

**File:** `/ganuda/home/dereadi/sag_unified_interface/static/css/unified.css`

```css
/* Detection overlay styles */
.camera-preview {
    position: relative;
}

.detection-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
}

.camera-card.detection-flash {
    animation: flash 0.3s ease-out;
}

@keyframes flash {
    0% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0.7); }
    100% { box-shadow: 0 0 20px 10px rgba(0, 255, 0, 0); }
}

.detection-item.new {
    animation: slideIn 0.3s ease-out;
    background: rgba(0, 255, 0, 0.1);
}

@keyframes slideIn {
    from { transform: translateX(-20px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

.det-icon {
    font-size: 1.2em;
    margin-right: 8px;
}
```

---

## Phase 4: Stereo Vision Integration

### 4.1 Create stereo depth service

**File:** `/ganuda/services/vision/stereo_depth.py`

```python
"""
Stereo vision depth estimation using Ring + Amcrest cameras.
Ring is ~15 feet from Amcrest, giving good baseline for triangulation.
"""

import numpy as np
from flask import Flask, request, jsonify
import cv2

app = Flask(__name__)

# Camera baseline (distance between cameras in meters)
BASELINE = 4.5  # ~15 feet

# Approximate focal lengths (need calibration for accuracy)
FOCAL_LENGTH_PX = 1000

@app.route('/depth', methods=['POST'])
def estimate_depth():
    """
    Estimate depth of detected object using stereo disparity.
    Requires detection bbox from both cameras for same object.
    """
    data = request.json

    # Get center points of detection in both frames
    amcrest_bbox = data.get('amcrest_bbox')  # [x1, y1, x2, y2]
    ring_bbox = data.get('ring_bbox')

    if not amcrest_bbox or not ring_bbox:
        return jsonify({'error': 'Need bbox from both cameras'}), 400

    # Calculate center x of each detection
    amcrest_cx = (amcrest_bbox[0] + amcrest_bbox[2]) / 2
    ring_cx = (ring_bbox[0] + ring_bbox[2]) / 2

    # Disparity (difference in x position)
    disparity = abs(amcrest_cx - ring_cx)

    if disparity < 1:
        return jsonify({'error': 'Object too far or same position'}), 400

    # Depth = (baseline * focal_length) / disparity
    depth_m = (BASELINE * FOCAL_LENGTH_PX) / disparity

    return jsonify({
        'depth_meters': round(depth_m, 2),
        'depth_feet': round(depth_m * 3.28084, 1),
        'disparity_px': round(disparity, 1),
        'confidence': 'high' if disparity > 50 else 'medium' if disparity > 20 else 'low'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8092)
```

### 4.2 Trigger Ring on Amcrest motion

**File:** `/ganuda/services/vision/stereo_trigger.py`

```python
"""
When Amcrest detects motion, trigger Ring snapshot for stereo matching.
"""

import paho.mqtt.client as mqtt
import requests
import time

MQTT_BROKER = 'localhost'
RING_RTSP = 'rtsp://ring:tribal_vision_2026@localhost:8554/d436398fc2b8_live'

def on_motion(client, userdata, msg):
    """Handle Amcrest motion event."""
    # Trigger Ring snapshot
    # Ring-mqtt publishes to: ring/d436398fc2b8/snapshot/image
    client.publish('ring/d436398fc2b8/snapshot/command', 'true')

    # Wait for Ring to respond (cloud delay ~3-4s)
    time.sleep(4)

    # Get frames from both cameras and run stereo matching
    # ...

client = mqtt.Client()
client.connect(MQTT_BROKER, 1883)
client.subscribe('ganuda/vision/motion')
client.on_message = on_motion
client.loop_forever()
```

---

## Phase 5: Custom Detection UI

### 5.1 Add custom prompt input

Add to cameras view sidebar:

```html
<div class="custom-detection">
    <h4>Custom Detection</h4>
    <input type="text" id="custom-prompt" placeholder="e.g., orange cat, FedEx truck">
    <button onclick="runCustomDetection()">Detect</button>
</div>
```

```javascript
function runCustomDetection() {
    var prompt = document.getElementById('custom-prompt').value;
    if (!prompt) return;

    var prompts = prompt.split(',').map(function(p) { return p.trim(); });

    // Run on all cameras
    document.querySelectorAll('.camera-card').forEach(function(card) {
        var camId = card.dataset.camera;
        fetch('/api/cameras/' + camId + '/detect_custom', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ prompts: prompts })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.detections) {
                drawDetectionBoxes(camId, data.detections);
            }
        });
    });
}
```

---

## Testing Checklist

- [ ] YOLO-World service starts and responds on :8091
- [ ] `/api/cameras/{id}/detect` returns detections with bboxes
- [ ] Bounding boxes render correctly on camera previews
- [ ] Detection feed updates in real-time via WebSocket
- [ ] Custom prompt detection works
- [ ] Stereo depth estimation returns reasonable values (10-100 feet for street)

## Dependencies

- `ultralytics` (YOLO-World)
- `flask-socketio` (WebSocket)
- `paho-mqtt` (MQTT client)
- `opencv-python` (image processing)

---

**FOR SEVEN GENERATIONS** - The tribe sees all, understands all.
