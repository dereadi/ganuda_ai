# Jr Instruction: Add Ring Doorbell + Stereo Vision Features to SAG Cameras

**Task ID:** SAG-RING-STEREO-001
**Priority:** P1
**Date:** January 23, 2026

## Objective

1. Add Ring doorbell to SAG cameras page
2. Implement stereo vision features using Ring + Amcrest traffic camera

## Part 1: Add Ring to Camera Config

**File:** `/ganuda/home/dereadi/sag_unified_interface/app.py`

### 1.1 Update CAMERA_CONFIG

Add Ring doorbell to the config (around line 2635):

```python
CAMERA_CONFIG = {
    'office_pii': {
        'id': 'office_pii',
        'name': 'Office PII Monitor',
        'ip': '192.168.132.181',
        'purpose': 'Face Detection / Security',
        'specialist': 'Crawdad',
        'features': ['face_detection', 'person_alert', 'ai_detection', '5mp'],
        'type': 'amcrest',
    },
    'traffic': {
        'id': 'traffic',
        'name': 'Traffic Monitor',
        'ip': '192.168.132.182',
        'purpose': 'Vehicle Identification',
        'specialist': 'Eagle Eye',
        'features': ['vehicle_tracking', 'license_plate', 'ai_detection', '5mp'],
        'type': 'amcrest',
        'stereo_partner': 'ring_doorbell',  # For stereo vision
    },
    'ring_doorbell': {
        'id': 'ring_doorbell',
        'name': 'Ring Front Door',
        'ip': '192.168.132.222',  # bluefin (ring-mqtt host)
        'rtsp_url': 'rtsp://ring:tribal_vision_2026@192.168.132.222:8554/d436398fc2b8_live',
        'purpose': 'Entry Detection / Stereo Vision',
        'specialist': 'Eagle Eye',
        'features': ['doorbell', 'person_detection', 'stereo_vision', 'on_demand'],
        'type': 'ring',
        'stereo_partner': 'traffic',  # For stereo vision
        'on_demand': True,  # Ring streams on-demand only
    }
}
```

### 1.2 Add Ring snapshot endpoint

```python
@app.route('/api/cameras/ring_doorbell/snapshot')
def api_ring_snapshot():
    """Get Ring doorbell snapshot via ring-mqtt."""
    import subprocess
    import tempfile

    rtsp_url = 'rtsp://ring:tribal_vision_2026@192.168.132.222:8554/d436398fc2b8_live'

    try:
        # Capture single frame using ffmpeg
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name

        subprocess.run([
            'ffmpeg', '-y', '-rtsp_transport', 'tcp',
            '-i', rtsp_url,
            '-frames:v', '1',
            '-f', 'image2',
            tmp_path
        ], capture_output=True, timeout=10)

        with open(tmp_path, 'rb') as f:
            img_data = f.read()

        os.unlink(tmp_path)
        return Response(img_data, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 1.3 Update camera list endpoint

Modify `/api/cameras` to include Ring:

```python
@app.route('/api/cameras')
def api_cameras():
    cameras = []
    for cam_id, cfg in CAMERA_CONFIG.items():
        cam_data = {
            'id': cam_id,
            'name': cfg['name'],
            'ip': cfg['ip'],
            'status': 'active',
            'purpose': cfg.get('purpose', ''),
            'specialist': cfg.get('specialist', ''),
            'features': cfg.get('features', []),
            'type': cfg.get('type', 'unknown'),
            'on_demand': cfg.get('on_demand', False),
            'stereo_partner': cfg.get('stereo_partner'),
        }

        # Get latest frame if available
        if cfg.get('type') == 'ring':
            cam_data['latest_frame'] = None  # On-demand
            cam_data['last_capture'] = None
        else:
            # Existing Amcrest logic...
            pass

        cameras.append(cam_data)

    return jsonify({'cameras': cameras})
```

---

## Part 2: Stereo Vision Features

### 2.1 Depth-Aware Zoom

When you know the depth of an object, you can:
- Calculate optimal crop region
- Scale the zoom based on distance
- Show object at "virtual" distances

**New endpoint:** `/api/stereo/zoom`

```python
@app.route('/api/stereo/zoom', methods=['POST'])
def api_stereo_zoom():
    """
    Depth-aware zoom on detected object.
    Uses stereo disparity to calculate distance, then crops appropriately.
    """
    data = request.json
    object_bbox = data.get('bbox')  # [x1, y1, x2, y2]
    camera_id = data.get('camera_id')
    target_distance = data.get('target_distance', 10)  # feet

    # Get stereo partner
    cfg = CAMERA_CONFIG.get(camera_id)
    if not cfg or not cfg.get('stereo_partner'):
        return jsonify({'error': 'No stereo partner'}), 400

    partner_id = cfg['stereo_partner']

    # Get frames from both cameras
    frame1 = get_camera_frame(camera_id)
    frame2 = get_camera_frame(partner_id)

    # Calculate depth via stereo matching
    depth = calculate_stereo_depth(frame1, frame2, object_bbox)

    # Calculate zoom factor based on current vs target distance
    zoom_factor = depth['depth_feet'] / target_distance

    # Crop and scale
    zoomed = crop_and_zoom(frame1, object_bbox, zoom_factor)

    return jsonify({
        'image': base64.b64encode(zoomed).decode(),
        'actual_depth_feet': depth['depth_feet'],
        'zoom_factor': zoom_factor,
        'enhanced': True
    })
```

### 2.2 3D Object Localization

**New endpoint:** `/api/stereo/locate`

```python
@app.route('/api/stereo/locate', methods=['POST'])
def api_stereo_locate():
    """
    Calculate real-world 3D position of detected object.
    Returns X, Y, Z coordinates relative to a reference point.
    """
    data = request.json
    bbox_traffic = data.get('traffic_bbox')
    bbox_ring = data.get('ring_bbox')

    # Camera positions (calibrated)
    TRAFFIC_CAM_POS = {'x': 0, 'y': 0, 'z': 8}  # feet from reference
    RING_CAM_POS = {'x': -15, 'y': 10, 'z': 3}  # feet from reference

    # Triangulate
    position = triangulate_position(
        bbox_traffic, TRAFFIC_CAM_POS,
        bbox_ring, RING_CAM_POS
    )

    return jsonify({
        'position': position,  # {'x': 45, 'y': 12, 'z': 0}
        'from_driveway': f"{position['x']} feet",
        'from_door': f"{calculate_distance(position, RING_CAM_POS):.1f} feet",
        'zone': classify_zone(position)  # 'driveway', 'sidewalk', 'porch'
    })
```

### 2.3 Multi-View Composite

**New endpoint:** `/api/stereo/composite`

```python
@app.route('/api/stereo/composite', methods=['POST'])
def api_stereo_composite():
    """
    Create a composite view combining both camera angles.
    Options: side-by-side, overlay, birdseye-synth
    """
    data = request.json
    mode = data.get('mode', 'side_by_side')  # side_by_side, overlay, birdseye

    frame_traffic = get_camera_frame('traffic')
    frame_ring = get_camera_frame('ring_doorbell')

    if mode == 'side_by_side':
        composite = np.hstack([frame_traffic, frame_ring])

    elif mode == 'overlay':
        # Perspective transform Ring to match Traffic angle
        composite = overlay_frames(frame_traffic, frame_ring)

    elif mode == 'birdseye':
        # Synthesize top-down view using depth data
        composite = create_birdseye(frame_traffic, frame_ring)

    _, buffer = cv2.imencode('.jpg', composite)
    return jsonify({
        'image': base64.b64encode(buffer).decode(),
        'mode': mode
    })
```

---

## Part 3: Frontend Stereo Controls

**File:** `/ganuda/home/dereadi/sag_unified_interface/static/js/control-room.js`

### 3.1 Add stereo view toggle

```javascript
// In camera card HTML
html += '<div class="camera-stereo-controls">';
if (cam.stereo_partner) {
    html += '<button onclick="showStereoView(\'' + cam.id + '\')" class="btn-stereo">Stereo View</button>';
    html += '<button onclick="locateObject(\'' + cam.id + '\')" class="btn-locate">3D Locate</button>';
}
html += '</div>';
```

### 3.2 Stereo view modal

```javascript
function showStereoView(cameraId) {
    var modal = document.createElement('div');
    modal.className = 'stereo-modal';
    modal.innerHTML = `
        <div class="stereo-container">
            <div class="stereo-header">
                <h3>Stereo Vision - ${cameraId}</h3>
                <select id="stereo-mode" onchange="updateStereoMode('${cameraId}')">
                    <option value="side_by_side">Side by Side</option>
                    <option value="overlay">Overlay</option>
                    <option value="birdseye">Bird's Eye</option>
                </select>
                <button onclick="closeStereoModal()">×</button>
            </div>
            <div class="stereo-view">
                <img id="stereo-image" src="/api/stereo/composite?camera_id=${cameraId}&mode=side_by_side">
            </div>
            <div class="stereo-info">
                <div id="depth-display">Click on object for depth</div>
                <div id="position-display"></div>
            </div>
            <div class="stereo-controls">
                <label>Virtual Zoom Distance: <input type="range" id="zoom-distance" min="5" max="100" value="20"> <span id="zoom-value">20</span> ft</label>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function depthAwareZoom(cameraId, bbox) {
    var targetDist = document.getElementById('zoom-distance').value;

    fetch('/api/stereo/zoom', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            camera_id: cameraId,
            bbox: bbox,
            target_distance: parseFloat(targetDist)
        })
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('stereo-image').src = 'data:image/jpeg;base64,' + data.image;
        document.getElementById('depth-display').textContent =
            `Object at ${data.actual_depth_feet.toFixed(1)} ft (${data.zoom_factor.toFixed(1)}x zoom)`;
    });
}
```

---

## Part 4: CSS for Stereo Features

```css
.stereo-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.9);
    z-index: 1000;
    display: flex;
    justify-content: center;
    align-items: center;
}

.stereo-container {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 20px;
    max-width: 90vw;
    max-height: 90vh;
}

.stereo-view img {
    max-width: 100%;
    border-radius: 8px;
}

.stereo-controls {
    margin-top: 15px;
    padding: 10px;
    background: rgba(0,0,0,0.3);
    border-radius: 8px;
}

.btn-stereo, .btn-locate {
    background: linear-gradient(135deg, #00ff88, #00ccff);
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8em;
    margin: 2px;
}

.camera-stereo-controls {
    margin-top: 8px;
    display: flex;
    gap: 5px;
}
```

---

## Testing Checklist

- [ ] Ring doorbell shows in camera grid
- [ ] Ring snapshot loads (may take 3-4s due to cloud delay)
- [ ] Stereo View button appears on traffic camera
- [ ] Side-by-side composite works
- [ ] Depth calculation returns reasonable values (10-100ft)
- [ ] Zoom slider changes perspective
- [ ] 3D locate returns position

---

**FOR SEVEN GENERATIONS** - Two eyes see depth, two cameras see truth.
