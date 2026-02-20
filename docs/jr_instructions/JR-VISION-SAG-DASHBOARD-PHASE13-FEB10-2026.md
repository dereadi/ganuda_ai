# Jr Instruction: SAG Vision Dashboard — Phase 1.3

**Task ID:** VISION-DASH-001
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Kanban:** #1745
**Date:** February 10, 2026
**Ultrathink:** ULTRATHINK-STEREO-CALIBRATION-LORA-VISION-PIPELINE-FEB10-2026.md

## Background

The SAG Unified Interface (redfin:4000) is the Federation's ITSM frontend. It currently has a camera section (`/ganuda/sag/templates/camera.html`) that calls the optic nerve endpoint (bluefin:8093). We need to extend this with a Vision dashboard showing live camera status, speed detections, calibration data, and training progress.

**Existing SAG structure:**
- Templates: `/ganuda/sag/templates/`
- Routes: `/ganuda/sag/routes/`
- Static: `/ganuda/sag/static/`

**Data sources:**
- Camera feeds: digest auth via `/ganuda/lib/amcrest_camera.py`
- Speed detections: `stereo_speed_detections` table on bluefin (192.168.132.222)
- Calibration status: `/ganuda/config/calibration/*.json`
- Camera registry: `/ganuda/config/camera_registry.yaml`

## Edit 1: Create vision API routes

Create `/ganuda/sag/routes/vision_routes.py`

```python
#!/usr/bin/env python3
"""
Vision API Routes — Cherokee AI Federation SAG Dashboard

Provides REST endpoints for camera status, speed detections,
calibration data, and live snapshots.

For Seven Generations
"""

import os
import sys
import json
import yaml
import time
import logging
import io
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, jsonify, request, send_file

sys.path.insert(0, "/ganuda")
sys.path.insert(0, "/ganuda/lib")

from lib.secrets_loader import get_db_config
import psycopg2

logger = logging.getLogger(__name__)

vision_bp = Blueprint("vision", __name__, url_prefix="/api/vision")

REGISTRY_PATH = "/ganuda/config/camera_registry.yaml"
CALIBRATION_DIR = "/ganuda/config/calibration"
SNAPSHOT_CACHE = {}  # camera_id -> (timestamp, bytes)
SNAPSHOT_TTL = 30  # seconds


def _get_db():
    return psycopg2.connect(**get_db_config())


def _load_registry():
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)


@vision_bp.route("/cameras", methods=["GET"])
def camera_status():
    """Camera fleet status with connection info."""
    registry = _load_registry()
    cameras = []
    for cam_id, cam in registry.get("cameras", {}).items():
        cal_file = Path(CALIBRATION_DIR) / f"{cam_id}_intrinsics.json"
        cameras.append({
            "id": cam_id,
            "model": cam.get("model"),
            "ip": cam.get("ip"),
            "location": cam.get("location"),
            "purpose": cam.get("purpose"),
            "mount_height_ft": cam.get("mount_height_ft"),
            "stereo_role": cam.get("stereo_role"),
            "resolution_main": cam.get("resolution_main"),
            "resolution_sub": cam.get("resolution_sub"),
            "fps": cam.get("fps"),
            "calibrated": cal_file.exists(),
        })

    stereo = registry.get("stereo_pairs", {})
    return jsonify({
        "cameras": cameras,
        "stereo_pairs": stereo,
        "timestamp": datetime.now().isoformat(),
    })


@vision_bp.route("/speed/recent", methods=["GET"])
def speed_recent():
    """Last N speed detections."""
    limit = request.args.get("limit", 50, type=int)
    try:
        conn = _get_db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, timestamp, track_id, speed_mph, position_x,
                       position_y, confidence, camera_pair,
                       plate_text, plate_confidence, vehicle_type
                FROM stereo_speed_detections
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
        conn.close()

        detections = []
        for row in rows:
            detections.append({
                "id": row[0],
                "timestamp": row[1].isoformat() if row[1] else None,
                "track_id": row[2],
                "speed_mph": float(row[3]) if row[3] else None,
                "position_x": float(row[4]) if row[4] else None,
                "position_y": float(row[5]) if row[5] else None,
                "confidence": float(row[6]) if row[6] else None,
                "camera": row[7],
                "plate_text": row[8],
                "plate_confidence": float(row[9]) if row[9] else None,
                "vehicle_type": row[10],
            })

        return jsonify({"detections": detections, "count": len(detections)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@vision_bp.route("/speed/stats", methods=["GET"])
def speed_stats():
    """Aggregated speed statistics for the last 24 hours."""
    try:
        conn = _get_db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    ROUND(AVG(speed_mph)::numeric, 1) as avg_speed,
                    MAX(speed_mph) as max_speed,
                    COUNT(CASE WHEN speed_mph > 25 THEN 1 END) as alerts,
                    COUNT(DISTINCT track_id) as unique_vehicles,
                    COUNT(CASE WHEN plate_text IS NOT NULL THEN 1 END) as plates_read
                FROM stereo_speed_detections
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """)
            row = cur.fetchone()

            # Hourly breakdown
            cur.execute("""
                SELECT
                    date_trunc('hour', timestamp) as hour,
                    COUNT(*) as detections,
                    ROUND(AVG(speed_mph)::numeric, 1) as avg_speed,
                    MAX(speed_mph) as max_speed
                FROM stereo_speed_detections
                WHERE timestamp > NOW() - INTERVAL '24 hours'
                GROUP BY hour
                ORDER BY hour
            """)
            hourly = cur.fetchall()
        conn.close()

        return jsonify({
            "period": "24h",
            "total_detections": row[0],
            "avg_speed_mph": float(row[1]) if row[1] else 0,
            "max_speed_mph": float(row[2]) if row[2] else 0,
            "speed_alerts": row[3],
            "unique_vehicles": row[4],
            "plates_read": row[5],
            "hourly": [
                {
                    "hour": h[0].isoformat() if h[0] else None,
                    "detections": h[1],
                    "avg_speed": float(h[2]) if h[2] else 0,
                    "max_speed": float(h[3]) if h[3] else 0,
                }
                for h in hourly
            ],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@vision_bp.route("/calibration", methods=["GET"])
def calibration_status():
    """Calibration status for all cameras."""
    registry = _load_registry()
    status = {}

    for cam_id in registry.get("cameras", {}):
        cal_file = Path(CALIBRATION_DIR) / f"{cam_id}_intrinsics.json"
        if cal_file.exists():
            with open(cal_file) as f:
                cal_data = json.load(f)
            status[cam_id] = {
                "calibrated": True,
                "file": str(cal_file),
                "mount_height_ft": cal_data.get("mount_height_ft"),
                "lens_mm": cal_data.get("lens_mm"),
                "hfov_deg": cal_data.get("hfov_deg"),
                "has_K": cal_data.get("K") is not None,
                "has_distortion": cal_data.get("dist_coeffs") is not None,
            }
        else:
            status[cam_id] = {"calibrated": False}

    # Stereo pair status
    stereo = registry.get("stereo_pairs", {})
    stereo_file = Path(CALIBRATION_DIR) / "stereo_extrinsics.json"

    return jsonify({
        "cameras": status,
        "stereo_calibrated": stereo_file.exists(),
        "stereo_pairs": stereo,
    })


@vision_bp.route("/snapshot/<camera_id>", methods=["GET"])
def camera_snapshot(camera_id):
    """Live snapshot from a camera (cached for 30s)."""
    import requests
    from requests.auth import HTTPDigestAuth

    registry = _load_registry()
    cam = registry.get("cameras", {}).get(camera_id)
    if not cam:
        return jsonify({"error": f"Unknown camera: {camera_id}"}), 404

    # Check cache
    cached = SNAPSHOT_CACHE.get(camera_id)
    if cached and time.time() - cached[0] < SNAPSHOT_TTL:
        return send_file(
            io.BytesIO(cached[1]),
            mimetype="image/jpeg",
            download_name=f"{camera_id}.jpg",
        )

    # Get password from env
    pw_env = cam.get("password_env", "")
    password = os.environ.get(pw_env, "")
    username = cam.get("username", "admin")

    # Build snapshot URL
    if cam.get("tunnel_http_port"):
        host = cam["tunnel_host"]
        port = cam["tunnel_http_port"]
    else:
        host = cam["ip"]
        port = 80
    url = f"http://{host}:{port}/cgi-bin/snapshot.cgi?channel=1"

    try:
        resp = requests.get(
            url,
            auth=HTTPDigestAuth(username, password),
            timeout=10,
        )
        if resp.status_code == 200:
            SNAPSHOT_CACHE[camera_id] = (time.time(), resp.content)
            return send_file(
                io.BytesIO(resp.content),
                mimetype="image/jpeg",
                download_name=f"{camera_id}.jpg",
            )
        return jsonify({"error": f"Camera returned {resp.status_code}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 502
```

## Edit 2: Create vision dashboard template

Create `/ganuda/sag/templates/vision_dashboard.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vision Dashboard — Cherokee AI Federation</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #c9d1d9; }
        .header { background: #161b22; padding: 16px 24px; border-bottom: 1px solid #30363d; display: flex; align-items: center; justify-content: space-between; }
        .header h1 { font-size: 20px; color: #58a6ff; }
        .header .status { font-size: 13px; color: #8b949e; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; padding: 16px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
        .card h2 { font-size: 15px; color: #58a6ff; margin-bottom: 12px; border-bottom: 1px solid #21262d; padding-bottom: 8px; }
        .camera-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
        .camera-thumb { position: relative; border-radius: 6px; overflow: hidden; background: #21262d; }
        .camera-thumb img { width: 100%; height: auto; display: block; }
        .camera-thumb .label { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.7); padding: 4px 8px; font-size: 12px; }
        .camera-thumb .badge { position: absolute; top: 6px; right: 6px; width: 10px; height: 10px; border-radius: 50%; }
        .badge-green { background: #3fb950; }
        .badge-red { background: #f85149; }
        .badge-yellow { background: #d29922; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { text-align: left; color: #8b949e; padding: 6px 8px; border-bottom: 1px solid #21262d; }
        td { padding: 6px 8px; border-bottom: 1px solid #21262d; }
        .speed-alert { color: #f85149; font-weight: 600; }
        .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #21262d; }
        .stat-label { color: #8b949e; }
        .stat-value { color: #f0f6fc; font-weight: 600; }
        .stat-value.alert { color: #f85149; }
        .cal-status { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; }
        .cal-ok { background: #238636; color: #fff; }
        .cal-pending { background: #9e6a03; color: #fff; }
        .refresh-btn { background: #21262d; border: 1px solid #30363d; color: #c9d1d9; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; }
        .refresh-btn:hover { background: #30363d; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Vision Dashboard</h1>
        <div>
            <span class="status" id="last-update">Loading...</span>
            <button class="refresh-btn" onclick="refreshAll()">Refresh</button>
        </div>
    </div>

    <div class="grid">
        <!-- Camera Feeds -->
        <div class="card" style="grid-column: span 2;">
            <h2>Camera Fleet</h2>
            <div class="camera-grid" id="camera-feeds"></div>
        </div>

        <!-- Speed Stats -->
        <div class="card">
            <h2>Speed Summary (24h)</h2>
            <div id="speed-stats">Loading...</div>
        </div>

        <!-- Calibration Status -->
        <div class="card">
            <h2>Calibration Status</h2>
            <div id="calibration-status">Loading...</div>
        </div>

        <!-- Recent Detections -->
        <div class="card" style="grid-column: span 2;">
            <h2>Recent Speed Detections</h2>
            <div style="max-height: 400px; overflow-y: auto;">
                <table id="speed-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Speed</th>
                            <th>Vehicle</th>
                            <th>Plate</th>
                            <th>Camera</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = '/api/vision';

        async function loadCameras() {
            try {
                const resp = await fetch(`${API_BASE}/cameras`);
                const data = await resp.json();
                const container = document.getElementById('camera-feeds');
                container.innerHTML = '';

                data.cameras.forEach(cam => {
                    const div = document.createElement('div');
                    div.className = 'camera-thumb';
                    div.innerHTML = `
                        <img src="${API_BASE}/snapshot/${cam.id}" alt="${cam.id}"
                             onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22320%22 height=%22180%22><rect fill=%22%2321262d%22 width=%22320%22 height=%22180%22/><text fill=%22%238b949e%22 x=%22160%22 y=%2295%22 text-anchor=%22middle%22 font-size=%2214%22>Offline</text></svg>'">
                        <div class="badge ${cam.calibrated ? 'badge-green' : 'badge-yellow'}"></div>
                        <div class="label">
                            ${cam.id} | ${cam.location || ''}<br>
                            ${cam.mount_height_ft ? cam.mount_height_ft + 'ft' : ''} ${cam.stereo_role || ''}
                        </div>
                    `;
                    container.appendChild(div);
                });
            } catch (e) {
                console.error('Camera load error:', e);
            }
        }

        async function loadSpeedStats() {
            try {
                const resp = await fetch(`${API_BASE}/speed/stats`);
                const data = await resp.json();
                const container = document.getElementById('speed-stats');
                container.innerHTML = `
                    <div class="stat-row"><span class="stat-label">Total Detections</span><span class="stat-value">${data.total_detections}</span></div>
                    <div class="stat-row"><span class="stat-label">Avg Speed</span><span class="stat-value">${data.avg_speed_mph} mph</span></div>
                    <div class="stat-row"><span class="stat-label">Max Speed</span><span class="stat-value ${data.max_speed_mph > 25 ? 'alert' : ''}">${data.max_speed_mph} mph</span></div>
                    <div class="stat-row"><span class="stat-label">Speed Alerts (&gt;25)</span><span class="stat-value ${data.speed_alerts > 0 ? 'alert' : ''}">${data.speed_alerts}</span></div>
                    <div class="stat-row"><span class="stat-label">Unique Vehicles</span><span class="stat-value">${data.unique_vehicles}</span></div>
                    <div class="stat-row"><span class="stat-label">Plates Read</span><span class="stat-value">${data.plates_read}</span></div>
                `;
            } catch (e) {
                document.getElementById('speed-stats').innerHTML = '<span style="color:#8b949e">No data</span>';
            }
        }

        async function loadCalibration() {
            try {
                const resp = await fetch(`${API_BASE}/calibration`);
                const data = await resp.json();
                const container = document.getElementById('calibration-status');
                let html = '';

                for (const [camId, status] of Object.entries(data.cameras)) {
                    const badge = status.calibrated ? 'cal-ok' : 'cal-pending';
                    const label = status.calibrated ? 'Calibrated' : 'Pending';
                    html += `<div class="stat-row">
                        <span class="stat-label">${camId}</span>
                        <span class="cal-status ${badge}">${label}</span>
                    </div>`;
                }

                html += `<div class="stat-row">
                    <span class="stat-label">Stereo Pair</span>
                    <span class="cal-status ${data.stereo_calibrated ? 'cal-ok' : 'cal-pending'}">
                        ${data.stereo_calibrated ? 'Calibrated' : 'Pending'}
                    </span>
                </div>`;

                container.innerHTML = html;
            } catch (e) {
                document.getElementById('calibration-status').innerHTML = '<span style="color:#8b949e">Error loading</span>';
            }
        }

        async function loadRecentDetections() {
            try {
                const resp = await fetch(`${API_BASE}/speed/recent?limit=30`);
                const data = await resp.json();
                const tbody = document.querySelector('#speed-table tbody');
                tbody.innerHTML = '';

                data.detections.forEach(d => {
                    const isAlert = d.speed_mph > 25;
                    const time = d.timestamp ? new Date(d.timestamp).toLocaleTimeString() : '-';
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${time}</td>
                        <td class="${isAlert ? 'speed-alert' : ''}">${d.speed_mph} mph</td>
                        <td>${d.vehicle_type || '-'}</td>
                        <td>${d.plate_text || '-'}</td>
                        <td>${d.camera || '-'}</td>
                        <td>${d.confidence ? (d.confidence * 100).toFixed(0) + '%' : '-'}</td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (e) {
                console.error('Detection load error:', e);
            }
        }

        function refreshAll() {
            loadCameras();
            loadSpeedStats();
            loadCalibration();
            loadRecentDetections();
            document.getElementById('last-update').textContent =
                'Updated: ' + new Date().toLocaleTimeString();
        }

        // Initial load + auto-refresh every 30s
        refreshAll();
        setInterval(refreshAll, 30000);
    </script>
</body>
</html>
```

## Edit 3: Register vision blueprint in SAG app

The vision routes blueprint needs to be registered in the main SAG Flask app. Find the main app file and add:

```python
from sag.routes.vision_routes import vision_bp
app.register_blueprint(vision_bp)
```

Also add a navigation link to the vision dashboard in the main template/navigation.

## Do NOT

- Do not modify existing SAG routes or templates
- Do not change database schema
- Do not store camera passwords in HTML or JavaScript
- Do not expose RTSP URLs in the API response
- Do not bypass digest authentication on camera snapshots

## Success Criteria

1. `/api/vision/cameras` returns all 3 cameras with status
2. `/api/vision/speed/recent` returns speed detection data
3. `/api/vision/speed/stats` returns 24h aggregates
4. `/api/vision/calibration` shows per-camera calibration state
5. `/api/vision/snapshot/garage` returns a JPEG image
6. Vision dashboard HTML loads and renders all panels
7. Auto-refresh updates every 30 seconds
8. Speed alerts highlighted in red
9. Calibrated cameras show green badge, pending show yellow
10. No passwords or RTSP URLs exposed in API responses

---
*Cherokee AI Federation — Vision Dashboard*
*ᎠᏂᎦᏔᎲᏍᎩ ᎤᏂᎪᎵᏰᏗ — Eyes that see, screen that shows*

FOR SEVEN GENERATIONS
