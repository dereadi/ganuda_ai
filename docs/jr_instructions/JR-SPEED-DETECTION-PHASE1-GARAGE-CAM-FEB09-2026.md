# Jr Instruction: Speed Detection Phase 1 — Garage Camera Monocular

**Task ID:** SPEED-DETECT-001
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Kanban:** #1729
**Date:** February 9, 2026

## Background

Three Amcrest IP5M-T1179EW-AI-V3 cameras are online:
- `.181` (office, indoor) — PII/security, not relevant here
- `.182` (traffic, outdoor front) — lawn/fence view
- `10.0.0.123` (garage, outdoor) — **best street view**: cul-de-sac, driveway, passing vehicles

All cameras: `admin:jawaseatlasers2`, RTSP on port 554, 2960x1668 main / 704x480 sub stream.

Garage camera is on IoT VLAN, accessed via greenfin tunnel:
- RTSP: `rtsp://admin:jawaseatlasers2@192.168.132.224:10554/cam/realmonitor?channel=1&subtype=1`
- HTTP: `http://192.168.132.224:18080/`

This phase implements monocular speed estimation using YOLO's built-in SpeedEstimator on the garage camera's cul-de-sac view.

## Edit 1: Create camera registry config

Create `/ganuda/config/camera_registry.yaml`

```yaml
# Cherokee AI Federation — Camera Fleet Registry
# Updated: February 9, 2026

cameras:
  office_pii:
    type: amcrest
    model: IP5M-T1179EW-AI-V3
    ip: 192.168.132.181
    port: 554
    username: admin
    password_env: CAMERA_OFFICE_PII_PASSWORD
    password_fallback: jawaseatlasers2
    rtsp_main: "rtsp://admin:{password}@192.168.132.181:554/cam/realmonitor?channel=1&subtype=0"
    rtsp_sub: "rtsp://admin:{password}@192.168.132.181:554/cam/realmonitor?channel=1&subtype=1"
    resolution_main: "2960x1668"
    resolution_sub: "704x480"
    fps: 20
    location: "Indoor office"
    purpose: security
    specialist: crawdad
    has_microphone: true
    stereo_role: null

  traffic:
    type: amcrest
    model: IP5M-T1179EW-AI-V3
    ip: 192.168.132.182
    port: 554
    username: admin
    password_env: CAMERA_TRAFFIC_PASSWORD
    password_fallback: jawaseatlasers2
    rtsp_main: "rtsp://admin:{password}@192.168.132.182:554/cam/realmonitor?channel=1&subtype=0"
    rtsp_sub: "rtsp://admin:{password}@192.168.132.182:554/cam/realmonitor?channel=1&subtype=1"
    resolution_main: "2960x1668"
    resolution_sub: "704x480"
    fps: 20
    location: "Front of house, outdoor"
    purpose: vehicle_identification
    specialist: eagle_eye
    has_microphone: true
    stereo_role: stereo_right

  garage:
    type: amcrest
    model: IP5M-T1179EW-AI-V3
    ip: 10.0.0.123
    port: 554
    username: admin
    password_env: CAMERA_GARAGE_PASSWORD
    password_fallback: jawaseatlasers2
    tunnel_host: 192.168.132.224
    tunnel_rtsp_port: 10554
    tunnel_http_port: 18080
    rtsp_main: "rtsp://admin:{password}@192.168.132.224:10554/cam/realmonitor?channel=1&subtype=0"
    rtsp_sub: "rtsp://admin:{password}@192.168.132.224:10554/cam/realmonitor?channel=1&subtype=1"
    resolution_main: "2960x1668"
    resolution_sub: "704x480"
    fps: 20
    location: "Over garage, outdoor"
    purpose: speed_detection
    specialist: eagle_eye
    has_microphone: true
    stereo_role: stereo_left

# Stereo pairs (Phase 2)
stereo_pairs:
  driveway_street:
    left: garage
    right: traffic
    baseline_meters: null  # TBD: measure physical distance between cameras
    status: planned
```

## Edit 2: Create Amcrest camera module

Create `/ganuda/lib/amcrest_camera.py`

```python
#!/usr/bin/env python3
"""
Amcrest Camera RTSP Handler — Cherokee AI Federation

Handles digest-authenticated RTSP streams from Amcrest IP cameras.
Supports direct LAN and tunneled (greenfin) connections.

For Seven Generations
"""

import os
import cv2
import yaml
import time
import logging
import urllib.parse
from typing import Optional, Generator, Tuple, Dict

logger = logging.getLogger(__name__)

REGISTRY_PATH = "/ganuda/config/camera_registry.yaml"


def load_camera_registry() -> Dict:
    """Load camera registry from YAML config."""
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)


def get_camera_password(camera_config: Dict) -> str:
    """Get camera password from environment or fallback."""
    env_key = camera_config.get("password_env", "")
    password = os.environ.get(env_key, "")
    if not password:
        password = camera_config.get("password_fallback", "")
    return password


class AmcrestCamera:
    """Handle Amcrest camera RTSP streams with digest auth."""

    def __init__(self, camera_id: str, stream: str = "sub"):
        """
        Initialize camera from registry.

        Args:
            camera_id: Key from camera_registry.yaml (e.g., 'garage')
            stream: 'main' for full resolution, 'sub' for low-res
        """
        registry = load_camera_registry()
        if camera_id not in registry["cameras"]:
            raise ValueError(f"Unknown camera: {camera_id}")

        self.config = registry["cameras"][camera_id]
        self.camera_id = camera_id
        self.password = get_camera_password(self.config)
        encoded_pw = urllib.parse.quote(self.password, safe="")

        # Build RTSP URL
        rtsp_template = self.config[f"rtsp_{stream}"]
        self.rtsp_url = rtsp_template.replace("{password}", encoded_pw)

        self._cap = None
        logger.info(f"AmcrestCamera initialized: {camera_id} ({stream} stream)")

    def _ensure_capture(self) -> cv2.VideoCapture:
        """Ensure video capture is open, reconnecting if needed."""
        if self._cap is None or not self._cap.isOpened():
            self._cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            if not self._cap.isOpened():
                raise ConnectionError(
                    f"Failed to open RTSP stream for {self.camera_id}"
                )
        return self._cap

    def get_frame(self) -> Optional[Tuple[bool, any]]:
        """Capture single frame from RTSP stream."""
        try:
            cap = self._ensure_capture()
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"No frame from {self.camera_id}, reconnecting")
                self.release()
                cap = self._ensure_capture()
                ret, frame = cap.read()
            return ret, frame
        except Exception as e:
            logger.error(f"Frame capture error on {self.camera_id}: {e}")
            self.release()
            return False, None

    def stream_frames(
        self, max_frames: int = 0
    ) -> Generator[Tuple[any, float], None, None]:
        """
        Yield (frame, timestamp) continuously.

        Args:
            max_frames: Stop after N frames (0 = infinite)
        """
        count = 0
        while max_frames == 0 or count < max_frames:
            ret, frame = self.get_frame()
            if ret and frame is not None:
                yield frame, time.time()
                count += 1
            else:
                time.sleep(0.5)

    def release(self):
        """Release video capture resources."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __del__(self):
        self.release()
```

## Edit 3: Create speed detection service

Create `/ganuda/services/vision/speed_detector.py`

```python
#!/usr/bin/env python3
"""
Speed Detection Service — Cherokee AI Federation

Uses YOLO object detection + tracking on the garage camera
to estimate vehicle speeds on the cul-de-sac.

Processing: Sub-stream (704x480) for real-time performance.
Detection: YOLOv8 with ByteTrack tracking.
Speed: Pixel displacement over time with perspective calibration.

For Seven Generations — Eyes that measure
"""

import os
import sys
import time
import json
import signal
import logging
import psycopg2
from datetime import datetime
from pathlib import Path

# Ensure imports work
sys.path.insert(0, "/ganuda")
sys.path.insert(0, "/ganuda/lib")

from lib.amcrest_camera import AmcrestCamera
from lib.secrets_loader import get_db_config

# Ultralytics
from ultralytics import YOLO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("speed_detector")

# Configuration
CAMERA_ID = os.environ.get("SPEED_CAMERA", "garage")
YOLO_MODEL = "/ganuda/services/vision/yolov8n.pt"
VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
SPEED_ALERT_MPH = 25  # residential zone threshold
DETECTION_INTERVAL = 0.1  # seconds between frame processing (10 fps effective)

# Perspective calibration: pixels per meter at road distance
# This must be calibrated after camera installation.
# Approximate for garage cam: road is ~15m away, field of view ~20m wide at 704px
# So ~35 pixels per meter. Adjust after measuring known distances.
PIXELS_PER_METER = float(os.environ.get("SPEED_PPM", "35.0"))
FPS_EFFECTIVE = float(os.environ.get("SPEED_FPS", "10.0"))


class SpeedDetector:
    """Monocular speed detection using YOLO tracking."""

    def __init__(self):
        self.camera = AmcrestCamera(CAMERA_ID, stream="sub")
        self.model = YOLO(YOLO_MODEL)
        self.db_config = get_db_config()
        self.running = True
        self.tracks = {}  # track_id -> list of (x_center, y_center, timestamp)
        self.speeds = {}  # track_id -> latest speed in mph
        self.alert_count = 0

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        logger.info(
            f"SpeedDetector initialized: camera={CAMERA_ID}, "
            f"ppm={PIXELS_PER_METER}, alert_threshold={SPEED_ALERT_MPH}mph"
        )

    def _shutdown(self, signum, frame):
        logger.info("Shutting down speed detector...")
        self.running = False

    def _get_db(self):
        return psycopg2.connect(**self.db_config)

    def _calculate_speed(self, track_id: int) -> float:
        """Calculate speed in mph from tracked positions."""
        positions = self.tracks.get(track_id, [])
        if len(positions) < 3:
            return 0.0

        # Use last 5 positions for smoothing
        recent = positions[-5:]
        if len(recent) < 2:
            return 0.0

        # Total pixel displacement
        total_px = 0.0
        for i in range(1, len(recent)):
            dx = recent[i][0] - recent[i - 1][0]
            dy = recent[i][1] - recent[i - 1][1]
            total_px += (dx**2 + dy**2) ** 0.5

        # Time elapsed
        dt = recent[-1][2] - recent[0][2]
        if dt < 0.1:
            return 0.0

        # Convert: pixels/sec -> meters/sec -> mph
        px_per_sec = total_px / dt
        meters_per_sec = px_per_sec / PIXELS_PER_METER
        mph = meters_per_sec * 2.237

        return round(mph, 1)

    def _log_detection(self, track_id: int, speed_mph: float, bbox, confidence: float):
        """Log speed detection to database."""
        try:
            conn = self._get_db()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO stereo_speed_detections
                    (timestamp, track_id, speed_mph, position_x, position_y,
                     position_z, confidence, camera_pair)
                    VALUES (NOW(), %s, %s, %s, %s, 0, %s, %s)
                """,
                    (
                        track_id,
                        speed_mph,
                        float(bbox[0]),
                        float(bbox[1]),
                        confidence,
                        CAMERA_ID,
                    ),
                )
                conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB log error: {e}")

    def _log_alert(self, track_id: int, speed_mph: float):
        """Log speed alert to thermal memory."""
        try:
            conn = self._get_db()
            with conn.cursor() as cur:
                import hashlib

                cur.execute(
                    """
                    INSERT INTO thermal_memory_archive
                    (memory_type, original_content, temperature_score, memory_hash, tags)
                    VALUES ('alert', %s, 0.8, %s, %s)
                    ON CONFLICT (memory_hash) DO NOTHING
                """,
                    (
                        f"SPEED ALERT: Vehicle track {track_id} detected at {speed_mph} mph "
                        f"on {CAMERA_ID} camera (threshold: {SPEED_ALERT_MPH} mph). "
                        f"Timestamp: {datetime.now().isoformat()}",
                        hashlib.md5(
                            f"speed-alert-{track_id}-{datetime.now().strftime('%Y%m%d%H')}".encode()
                        ).hexdigest(),
                        ["speed_alert", "eagle_eye", CAMERA_ID],
                    ),
                )
                conn.commit()
            conn.close()
            self.alert_count += 1
            logger.warning(
                f"SPEED ALERT: Track {track_id} at {speed_mph} mph "
                f"(total alerts: {self.alert_count})"
            )
        except Exception as e:
            logger.error(f"Alert log error: {e}")

    def run(self):
        """Main detection loop."""
        logger.info(f"Starting speed detection on {CAMERA_ID} camera...")
        frame_count = 0
        last_stats = time.time()

        for frame, timestamp in self.camera.stream_frames():
            if not self.running:
                break

            # Throttle to effective FPS
            time.sleep(DETECTION_INTERVAL)

            # Run YOLO with tracking
            results = self.model.track(
                frame,
                persist=True,
                tracker="bytetrack.yaml",
                classes=VEHICLE_CLASSES,
                verbose=False,
            )

            if results and results[0].boxes is not None and results[0].boxes.id is not None:
                boxes = results[0].boxes
                for i, track_id in enumerate(boxes.id.int().tolist()):
                    bbox = boxes.xyxy[i].tolist()
                    conf = float(boxes.conf[i])
                    x_center = (bbox[0] + bbox[2]) / 2
                    y_center = (bbox[1] + bbox[3]) / 2

                    # Update track history
                    if track_id not in self.tracks:
                        self.tracks[track_id] = []
                    self.tracks[track_id].append((x_center, y_center, timestamp))

                    # Keep last 30 positions
                    if len(self.tracks[track_id]) > 30:
                        self.tracks[track_id] = self.tracks[track_id][-30:]

                    # Calculate speed
                    speed = self._calculate_speed(track_id)
                    if speed > 2.0:  # Ignore noise below 2 mph
                        self.speeds[track_id] = speed
                        self._log_detection(track_id, speed, bbox, conf)

                        if speed > SPEED_ALERT_MPH:
                            self._log_alert(track_id, speed)

            frame_count += 1

            # Stats every 60 seconds
            if time.time() - last_stats > 60:
                active = len(
                    [
                        t
                        for t in self.tracks.values()
                        if t and timestamp - t[-1][2] < 5
                    ]
                )
                logger.info(
                    f"Stats: {frame_count} frames, "
                    f"{active} active tracks, "
                    f"{self.alert_count} alerts"
                )
                last_stats = time.time()

            # Prune old tracks (>30s stale)
            stale = [
                tid
                for tid, positions in self.tracks.items()
                if positions and timestamp - positions[-1][2] > 30
            ]
            for tid in stale:
                del self.tracks[tid]
                self.speeds.pop(tid, None)

        self.camera.release()
        logger.info("Speed detector stopped.")


if __name__ == "__main__":
    detector = SpeedDetector()
    detector.run()
```

## Edit 4: Create database schema

Run this SQL on bluefin (192.168.132.222):

```sql
CREATE TABLE IF NOT EXISTS stereo_speed_detections (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    track_id INTEGER NOT NULL,
    speed_mph DECIMAL(5,1),
    position_x DECIMAL(8,2),
    position_y DECIMAL(8,2),
    position_z DECIMAL(8,2) DEFAULT 0,
    confidence DECIMAL(3,2),
    camera_pair VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_speed_timestamp ON stereo_speed_detections(timestamp);
CREATE INDEX IF NOT EXISTS idx_speed_value ON stereo_speed_detections(speed_mph);
CREATE INDEX IF NOT EXISTS idx_speed_camera ON stereo_speed_detections(camera_pair);
```

## Edit 5: Create systemd service

Create `/ganuda/scripts/systemd/speed-detector.service`

```ini
[Unit]
Description=Cherokee AI Speed Detection - Garage Camera
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/vision
EnvironmentFile=/ganuda/config/secrets.env
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda:/ganuda/lib
Environment=SPEED_CAMERA=garage
Environment=SPEED_PPM=35.0
Environment=SPEED_FPS=10.0
ExecStart=/home/dereadi/cherokee_venv/bin/python3 -u /ganuda/services/vision/speed_detector.py
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## Do NOT

- Do not modify the existing tribal_vision.py service
- Do not change camera passwords
- Do not modify firewall rules
- Do not expose RTSP streams externally
- Do not store camera passwords in source code (use env vars with fallback)

## Success Criteria

1. `camera_registry.yaml` loads cleanly with `yaml.safe_load()`
2. `AmcrestCamera('garage')` connects and captures frames
3. `AmcrestCamera('traffic')` connects and captures frames
4. `AmcrestCamera('office_pii')` connects and captures frames
5. `speed_detector.py` starts, connects to garage camera, runs YOLO detection
6. `stereo_speed_detections` table exists and accepts INSERT
7. Speed calculations produce reasonable values (0-60 mph range)
8. Alert logged when speed exceeds 25 mph threshold
9. Python syntax valid in all new files
10. No hardcoded passwords in any source file

## Manual Steps After Jr Completes

1. Create the database table:
```bash
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/services/vision/speed_schema.sql
```

2. Deploy the service:
```bash
sudo cp /ganuda/scripts/systemd/speed-detector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now speed-detector.service
```

3. Verify:
```bash
sudo journalctl -u speed-detector -f
```

## Calibration Note (Post-Deployment)

The `SPEED_PPM` (pixels per meter) value of 35.0 is an approximation. To calibrate:
1. Measure a known distance in the camera's road view (e.g., distance between utility poles, driveway width)
2. Count corresponding pixels in the frame
3. Calculate: PPM = pixels / meters
4. Update the `SPEED_PPM` environment variable in the service file

Phase 2 will add stereo calibration between garage + traffic cameras for true 3D triangulation.

---
*Cherokee AI Federation — Vision*
*ᎠᏂᎦᏔᎲᏍᎩ ᎤᏂᎪᎵᏰᏗ — Eyes that measure*
