# JR Instruction: SAG Camera Tab Integration

**Task ID**: SAG-CAMERA-TAB-001
**Priority**: P1 - High
**Assigned Domain**: Software Engineering Jr
**Created**: January 21, 2026
**TPM**: Claude Opus 4.5

## Objective

Add a "Cameras" tab to the SAG Control Room interface (http://192.168.132.223:4000/) that displays:
1. Live camera thumbnails with detection overlays
2. Recent detection events (faces, vehicles, plates)
3. Alert feed for unknown persons (CRAWDAD alerts)
4. Vehicle tracking history (Eagle Eye data)

## Background Context

The Tribal Vision service is already running on redfin:
- **Service**: `tribal-vision.service` (active, running)
- **Cameras**:
  - `office_pii` (192.168.132.181) - Face detection, person alerts
  - `traffic` (192.168.132.182) - Vehicle identification and tracking
- **Output Directory**: `/ganuda/data/vision/`
- **Frame Pattern**: `{camera_type}_{YYYYMMDD}_{HHMMSS}.jpg`

## Implementation Steps

### Step 1: Add Navigation Item

**File**: `/ganuda/home/dereadi/sag_unified_interface/templates/index.html`

Add to the SYSTEMS nav-section (after IoT Devices, before Home Hub):
```html
<a href="#" class="nav-item" data-view="cameras">Cameras</a>
```

### Step 2: Add Camera View Content

**File**: `/ganuda/home/dereadi/sag_unified_interface/templates/index.html`

Add new view-content div (after homehub-view):
```html
<!-- Camera View -->
<div id="cameras-view" class="view-content">
    <h2>Tribal Vision - Camera Intelligence</h2>
    <div class="camera-dashboard">
        <div class="camera-grid" id="camera-grid">
            <!-- Camera cards populated by JS -->
        </div>
        <div class="camera-events">
            <h3>Recent Detections</h3>
            <div id="detection-feed" class="event-feed"></div>
        </div>
        <div class="camera-alerts">
            <h3>Security Alerts</h3>
            <div id="alert-feed" class="alert-feed"></div>
        </div>
    </div>
</div>
```

### Step 3: Add Backend API Endpoints

**File**: `/ganuda/home/dereadi/sag_unified_interface/app.py`

Add these endpoints:

```python
import glob
from datetime import datetime, timedelta

@app.route('/api/cameras')
def api_cameras():
    """Get all camera status and latest frames."""
    cameras = [
        {
            'id': 'office_pii',
            'name': 'Office PII Monitor',
            'ip': '192.168.132.181',
            'purpose': 'Face Detection / Security',
            'specialist': 'Crawdad',
            'status': 'active'
        },
        {
            'id': 'traffic',
            'name': 'Traffic Monitor',
            'ip': '192.168.132.182',
            'purpose': 'Vehicle Identification',
            'specialist': 'Eagle Eye',
            'status': 'active'
        }
    ]

    # Get latest frame for each camera
    vision_dir = '/ganuda/data/vision'
    for cam in cameras:
        pattern = f"{vision_dir}/{cam['id']}_*.jpg"
        files = sorted(glob.glob(pattern), reverse=True)
        if files:
            cam['latest_frame'] = files[0]
            cam['last_capture'] = os.path.getmtime(files[0])
        else:
            cam['latest_frame'] = None
            cam['last_capture'] = None

    return jsonify({'cameras': cameras})


@app.route('/api/cameras/<camera_id>/frames')
def api_camera_frames(camera_id):
    """Get recent frames for a specific camera."""
    limit = request.args.get('limit', 10, type=int)
    vision_dir = '/ganuda/data/vision'
    pattern = f"{vision_dir}/{camera_id}_*.jpg"
    files = sorted(glob.glob(pattern), reverse=True)[:limit]

    frames = []
    for f in files:
        filename = os.path.basename(f)
        # Parse timestamp from filename: camera_YYYYMMDD_HHMMSS.jpg
        parts = filename.replace('.jpg', '').split('_')
        if len(parts) >= 3:
            timestamp = f"{parts[1]}_{parts[2]}"
        else:
            timestamp = "unknown"
        frames.append({
            'path': f,
            'filename': filename,
            'timestamp': timestamp,
            'size': os.path.getsize(f)
        })

    return jsonify({'camera_id': camera_id, 'frames': frames})


@app.route('/api/cameras/frame/<path:filename>')
def api_camera_frame_image(filename):
    """Serve a camera frame image."""
    from flask import send_from_directory
    return send_from_directory('/ganuda/data/vision', filename)


@app.route('/api/cameras/detections')
def api_camera_detections():
    """Get recent detection events from tribal vision logs."""
    # Read recent detections from service log
    import subprocess
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'tribal-vision', '-n', '50', '--no-pager', '-o', 'json'],
            capture_output=True, text=True, timeout=5
        )

        detections = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            try:
                entry = json.loads(line)
                msg = entry.get('MESSAGE', '')
                if 'face' in msg.lower() or 'alert' in msg.lower() or 'vehicle' in msg.lower():
                    detections.append({
                        'timestamp': entry.get('__REALTIME_TIMESTAMP', ''),
                        'message': msg
                    })
            except:
                pass

        return jsonify({'detections': detections[-20:]})
    except Exception as e:
        return jsonify({'error': str(e), 'detections': []})


@app.route('/api/cameras/alerts')
def api_camera_alerts():
    """Get security alerts (unknown persons, etc.)."""
    import subprocess
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'tribal-vision', '-n', '100', '--no-pager'],
            capture_output=True, text=True, timeout=5
        )

        alerts = []
        for line in result.stdout.strip().split('\n'):
            if 'CRAWDAD ALERT' in line or 'UNKNOWN' in line:
                alerts.append({
                    'timestamp': line[:19] if len(line) > 19 else '',
                    'message': line
                })

        return jsonify({'alerts': alerts[-10:]})
    except Exception as e:
        return jsonify({'error': str(e), 'alerts': []})
```

### Step 4: Add Frontend JavaScript

**File**: `/ganuda/home/dereadi/sag_unified_interface/static/js/unified.js`

Add camera view handlers:

```javascript
// Camera view functions
async function loadCameraView() {
    const grid = document.getElementById('camera-grid');
    const detectionFeed = document.getElementById('detection-feed');
    const alertFeed = document.getElementById('alert-feed');

    if (!grid) return;

    try {
        // Load cameras
        const camResponse = await fetch('/api/cameras');
        const camData = await camResponse.json();

        grid.innerHTML = camData.cameras.map(cam => `
            <div class="camera-card" data-camera="${cam.id}">
                <div class="camera-header">
                    <span class="camera-name">${cam.name}</span>
                    <span class="camera-status ${cam.status}">${cam.status}</span>
                </div>
                <div class="camera-preview">
                    ${cam.latest_frame ?
                        `<img src="/api/cameras/frame/${cam.latest_frame.split('/').pop()}" alt="${cam.name}" class="camera-thumb">` :
                        '<div class="no-frame">No recent frame</div>'
                    }
                </div>
                <div class="camera-info">
                    <div>IP: ${cam.ip}</div>
                    <div>Purpose: ${cam.purpose}</div>
                    <div>Specialist: ${cam.specialist}</div>
                </div>
            </div>
        `).join('');

        // Load detections
        const detResponse = await fetch('/api/cameras/detections');
        const detData = await detResponse.json();

        detectionFeed.innerHTML = detData.detections.map(d => `
            <div class="detection-item">
                <span class="det-time">${d.timestamp}</span>
                <span class="det-msg">${d.message}</span>
            </div>
        `).join('') || '<div class="no-data">No recent detections</div>';

        // Load alerts
        const alertResponse = await fetch('/api/cameras/alerts');
        const alertData = await alertResponse.json();

        alertFeed.innerHTML = alertData.alerts.map(a => `
            <div class="alert-item ${a.message.includes('UNKNOWN') ? 'critical' : ''}">
                <span class="alert-time">${a.timestamp}</span>
                <span class="alert-msg">${a.message}</span>
            </div>
        `).join('') || '<div class="no-data">No recent alerts</div>';

    } catch (error) {
        console.error('Error loading camera view:', error);
        grid.innerHTML = '<div class="error">Failed to load cameras</div>';
    }
}

// Add to view switcher
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function(e) {
        // ... existing view switch logic ...

        if (this.dataset.view === 'cameras') {
            loadCameraView();
        }
    });
});
```

### Step 5: Add CSS Styles

**File**: `/ganuda/home/dereadi/sag_unified_interface/static/css/unified.css`

Add camera styles:

```css
/* Camera Dashboard */
.camera-dashboard {
    display: grid;
    grid-template-columns: 2fr 1fr;
    grid-template-rows: auto auto;
    gap: 20px;
    padding: 20px;
}

.camera-grid {
    grid-column: 1;
    grid-row: 1 / 3;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;
}

.camera-card {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    overflow: hidden;
}

.camera-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    background: var(--color-surface-elevated);
    border-bottom: 1px solid var(--color-border);
}

.camera-name {
    font-weight: 600;
}

.camera-status {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
}

.camera-status.active {
    background: var(--color-success-bg);
    color: var(--color-success);
}

.camera-preview {
    aspect-ratio: 16/9;
    background: #000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.camera-thumb {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

.camera-info {
    padding: 12px;
    font-size: 13px;
    color: var(--color-text-muted);
}

.camera-events, .camera-alerts {
    grid-column: 2;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 16px;
    max-height: 400px;
    overflow-y: auto;
}

.camera-events h3, .camera-alerts h3 {
    margin: 0 0 12px 0;
    font-size: 14px;
    color: var(--color-text-muted);
}

.detection-item, .alert-item {
    padding: 8px;
    border-bottom: 1px solid var(--color-border);
    font-size: 12px;
}

.alert-item.critical {
    background: var(--color-danger-bg);
    border-left: 3px solid var(--color-danger);
}

.det-time, .alert-time {
    display: block;
    color: var(--color-text-muted);
    font-size: 11px;
}
```

## Testing Checklist

1. [ ] Navigate to Cameras tab - should load without errors
2. [ ] Camera cards display with latest thumbnail
3. [ ] Detection feed shows recent face/vehicle events
4. [ ] Alert feed shows CRAWDAD alerts for unknown persons
5. [ ] Images load correctly from `/api/cameras/frame/`
6. [ ] Auto-refresh works every 30 seconds

## Dependencies

- Tribal Vision service must be running: `systemctl status tribal-vision`
- Vision output directory must exist: `/ganuda/data/vision/`
- SAG service must be restarted after changes: `systemctl restart cherokee-sag`

## Notes

- The office_pii camera generates ~1.7MB frames (high resolution for face recognition)
- The traffic camera generates ~75KB frames (lower resolution for vehicle tracking)
- CRAWDAD alerts are generated when unknown persons are detected in PII area
- Consider adding websocket support for real-time updates in future enhancement

---
*Cherokee AI Federation - For Seven Generations*
