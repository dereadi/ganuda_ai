# JR Instruction: Tribal Vision Stereo Hub Architecture

**Task ID:** TRIBAL-STEREO-HUB-001
**Priority:** P1
**Date:** January 23, 2026
**Ultrathink Reference:** `/ganuda/docs/ultrathink/ULTRATHINK-TRIBAL-VISION-STEREO-ARCHITECTURE-JAN23-2026.md`

## Objective

Implement the hybrid hub architecture for tribal vision with stereo depth perception:
- **Greenfin:** Bridge cloud cameras (Ring, Nest) to RTSP
- **Bluefin:** Central vision hub with frame sync + VLM + stereo depth
- **Redfin:** Pattern learning and correlation

## Physical Camera Data (From User)

| Camera | Height | Estimated Position |
|--------|--------|-------------------|
| Office (Amcrest 181) | 5' - 5'6" (1.5-1.7m) | Indoor, elevated |
| Ring Doorbell | 3' - 3'6" (0.9-1.1m) | Front door, low |
| Traffic (Amcrest 182) | ~10' (3m) estimated | Outdoor, elevated |

## Phase 1: Greenfin Stream Bridge

### Step 1.1: Deploy ring-mqtt

**On Greenfin (192.168.132.224):**

```bash
# Create service directory
mkdir -p /ganuda/services/ring-mqtt
cd /ganuda/services/ring-mqtt

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: "3"
services:
  ring-mqtt:
    image: tsightler/ring-mqtt
    container_name: ring-mqtt
    restart: unless-stopped
    ports:
      - "8554:8554"
      - "3000:3000"
    volumes:
      - ./data:/data
    environment:
      - RINGTOKEN=${RING_REFRESH_TOKEN}
      - ENABLECAMERAS=true
      - LIVESTREAMUSER=tribal
      - LIVESTREAMPASSWORD=vision2026
      - SNAPSHOTMODE=interval
      - SNAPSHOTINTERVAL=30
EOF

# Generate Ring token (interactive)
docker run -it --rm tsightler/ring-mqtt \
  node /app/ring-mqtt/node_modules/ring-client-api/lib/ring-auth-cli.js

# Save token to .env
echo "RING_REFRESH_TOKEN=<paste_token_here>" > .env

# Start service
docker-compose up -d
```

### Step 1.2: Deploy Scrypted (for Nest cameras)

```bash
mkdir -p /ganuda/services/scrypted
cd /ganuda/services/scrypted

cat > docker-compose.yml << 'EOF'
version: "3"
services:
  scrypted:
    image: koush/scrypted
    container_name: scrypted
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./data:/server/volume
    environment:
      - SCRYPTED_WEBHOOK_UPDATE_AUTHORIZATION=Bearer tribal_scrypted_2026
EOF

docker-compose up -d

# Access web UI at http://greenfin:10443
# Add Google/Nest account via UI
# Note RTSP URLs for each camera
```

### Step 1.3: Verify Streams

```bash
# Test Ring stream
ffprobe rtsp://tribal:vision2026@localhost:8554/DOORBELL_ID_live

# Test Nest streams (after Scrypted setup)
ffprobe rtsp://localhost:PORT/nest_porch
```

## Phase 2: Bluefin Vision Hub

### Step 2.1: Create Unified Camera Registry

**File:** `/ganuda/lib/tribal_vision/camera_registry.py`

```python
"""
Tribal Vision Camera Registry
Centralized configuration for all camera streams
"""

from dataclasses import dataclass
from typing import Optional, Dict
import os

@dataclass
class CameraConfig:
    """Configuration for a single camera."""
    camera_id: str
    name: str
    url: str
    location: str
    height_meters: float
    is_local: bool  # True for direct RTSP, False for cloud-bridged
    stereo_pair: Optional[str] = None  # ID of paired camera for stereo
    fov_horizontal: float = 90.0
    fov_vertical: float = 60.0

# Camera registry - update URLs after bridge setup
CAMERAS: Dict[str, CameraConfig] = {
    "office": CameraConfig(
        camera_id="office",
        name="Office Camera",
        url="rtsp://admin:jawaseatlasers2@192.168.132.181:554/cam/realmonitor?channel=1&subtype=0",
        location="indoor_office",
        height_meters=1.6,  # 5'3" average
        is_local=True,
        fov_horizontal=90,
        fov_vertical=60
    ),

    "traffic": CameraConfig(
        camera_id="traffic",
        name="Traffic Camera",
        url="rtsp://admin:jawaseatlasers2@192.168.132.182:554/cam/realmonitor?channel=1&subtype=1",
        location="street_view",
        height_meters=3.0,  # Estimated
        is_local=True,
        stereo_pair="doorbell",
        fov_horizontal=90,
        fov_vertical=60
    ),

    "doorbell": CameraConfig(
        camera_id="doorbell",
        name="Ring Doorbell",
        url="rtsp://tribal:vision2026@greenfin:8554/DOORBELL_ID_live",  # Update ID
        location="front_door",
        height_meters=1.0,  # 3'3" average
        is_local=False,
        stereo_pair="traffic",
        fov_horizontal=160,  # Wide angle doorbell
        fov_vertical=90
    ),

    "porch": CameraConfig(
        camera_id="porch",
        name="Nest Porch",
        url="rtsp://greenfin:PORT/nest_porch",  # Update after Scrypted
        location="front_porch",
        height_meters=2.5,  # Estimated
        is_local=False,
        stereo_pair="doorbell",
        fov_horizontal=130,
        fov_vertical=80
    ),

    "backyard": CameraConfig(
        camera_id="backyard",
        name="Nest Backyard",
        url="rtsp://greenfin:PORT/nest_backyard",  # Update after Scrypted
        location="backyard",
        height_meters=2.5,  # Estimated
        is_local=False,
        fov_horizontal=130,
        fov_vertical=80
    )
}

def get_camera(camera_id: str) -> Optional[CameraConfig]:
    """Get camera configuration by ID."""
    return CAMERAS.get(camera_id)

def get_stereo_pairs() -> list:
    """Get list of stereo camera pairs."""
    pairs = []
    seen = set()
    for cam_id, config in CAMERAS.items():
        if config.stereo_pair and cam_id not in seen:
            pairs.append((cam_id, config.stereo_pair))
            seen.add(cam_id)
            seen.add(config.stereo_pair)
    return pairs

def get_local_cameras() -> list:
    """Get cameras with direct RTSP (no cloud bridge)."""
    return [c for c in CAMERAS.values() if c.is_local]

def get_bridged_cameras() -> list:
    """Get cameras requiring cloud bridge."""
    return [c for c in CAMERAS.values() if not c.is_local]
```

### Step 2.2: Frame Synchronizer

**File:** `/ganuda/lib/tribal_vision/frame_sync.py`

```python
"""
Frame Synchronizer for Stereo Vision
Aligns frames from multiple cameras by timestamp
"""

import cv2
import time
import threading
from collections import deque
from dataclasses import dataclass
from typing import Optional, Tuple, Dict
import numpy as np

from .camera_registry import CAMERAS, CameraConfig

@dataclass
class TimestampedFrame:
    """Frame with capture timestamp."""
    frame: np.ndarray
    timestamp: float
    camera_id: str

class FrameSynchronizer:
    """
    Captures frames from multiple cameras and synchronizes for stereo.

    Handles latency differences between local RTSP and cloud-bridged streams.
    """

    def __init__(self, sync_tolerance_ms: float = 500):
        self.sync_tolerance = sync_tolerance_ms / 1000.0  # Convert to seconds
        self.buffers: Dict[str, deque] = {}
        self.captures: Dict[str, cv2.VideoCapture] = {}
        self.running = False
        self.threads: Dict[str, threading.Thread] = {}

        # Initialize buffers for each camera
        for cam_id in CAMERAS:
            self.buffers[cam_id] = deque(maxlen=60)  # ~2 min at 0.5 fps

    def _capture_loop(self, camera_id: str, config: CameraConfig):
        """Continuous capture loop for a single camera."""
        cap = cv2.VideoCapture(config.url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        while self.running:
            ret, frame = cap.read()
            if ret:
                ts_frame = TimestampedFrame(
                    frame=frame,
                    timestamp=time.time(),
                    camera_id=camera_id
                )
                self.buffers[camera_id].append(ts_frame)
            time.sleep(0.5)  # 2 FPS capture rate

        cap.release()

    def start(self):
        """Start capture threads for all cameras."""
        self.running = True
        for cam_id, config in CAMERAS.items():
            thread = threading.Thread(
                target=self._capture_loop,
                args=(cam_id, config),
                daemon=True
            )
            thread.start()
            self.threads[cam_id] = thread
            print(f"Started capture thread for {config.name}")

    def stop(self):
        """Stop all capture threads."""
        self.running = False
        for thread in self.threads.values():
            thread.join(timeout=2.0)

    def get_latest_frame(self, camera_id: str) -> Optional[TimestampedFrame]:
        """Get most recent frame from a camera."""
        buffer = self.buffers.get(camera_id)
        if buffer and len(buffer) > 0:
            return buffer[-1]
        return None

    def get_stereo_pair(
        self,
        cam_a_id: str,
        cam_b_id: str
    ) -> Optional[Tuple[TimestampedFrame, TimestampedFrame, float]]:
        """
        Find best matching frame pair for stereo processing.

        Returns (frame_a, frame_b, time_delta_seconds) or None.
        """
        buffer_a = self.buffers.get(cam_a_id)
        buffer_b = self.buffers.get(cam_b_id)

        if not buffer_a or not buffer_b:
            return None

        best_pair = None
        best_delta = float('inf')

        # Find closest timestamp match
        for frame_a in buffer_a:
            for frame_b in buffer_b:
                delta = abs(frame_a.timestamp - frame_b.timestamp)
                if delta < best_delta:
                    best_delta = delta
                    best_pair = (frame_a, frame_b, delta)

        # Only return if within tolerance
        if best_pair and best_pair[2] <= self.sync_tolerance:
            return best_pair

        return None

    def get_all_synced_frames(
        self,
        reference_time: Optional[float] = None
    ) -> Dict[str, TimestampedFrame]:
        """
        Get frames from all cameras closest to reference time.

        Args:
            reference_time: Target timestamp (default: now)

        Returns:
            Dict mapping camera_id to closest frame
        """
        if reference_time is None:
            reference_time = time.time()

        synced = {}
        for cam_id, buffer in self.buffers.items():
            if not buffer:
                continue

            # Find frame closest to reference time
            closest = min(buffer, key=lambda f: abs(f.timestamp - reference_time))
            if abs(closest.timestamp - reference_time) <= self.sync_tolerance:
                synced[cam_id] = closest

        return synced
```

### Step 2.3: Stereo Depth Estimator

**File:** `/ganuda/lib/tribal_vision/stereo_depth.py`

```python
"""
Stereo Depth Estimation using triangulation from camera pairs.

Based on: https://github.com/erget/StereoVision
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
import json
from pathlib import Path

from .camera_registry import CAMERAS, get_stereo_pairs

@dataclass
class CameraCalibration:
    """Intrinsic and extrinsic camera parameters."""
    camera_matrix: np.ndarray  # 3x3 intrinsic matrix
    dist_coeffs: np.ndarray    # Distortion coefficients
    rotation: np.ndarray       # 3x3 rotation matrix (for stereo)
    translation: np.ndarray    # 3x1 translation vector (for stereo)

class StereoDepthEstimator:
    """
    Estimates depth/distance using stereo camera pairs.
    """

    CALIBRATION_DIR = Path("/ganuda/data/vision/calibration")

    def __init__(self):
        self.calibrations: dict = {}
        self.stereo_maps: dict = {}
        self._load_calibrations()

    def _load_calibrations(self):
        """Load camera calibrations from files."""
        for cam_id in CAMERAS:
            cal_file = self.CALIBRATION_DIR / f"{cam_id}_calibration.json"
            if cal_file.exists():
                with open(cal_file) as f:
                    data = json.load(f)
                    self.calibrations[cam_id] = CameraCalibration(
                        camera_matrix=np.array(data['camera_matrix']),
                        dist_coeffs=np.array(data['dist_coeffs']),
                        rotation=np.array(data.get('rotation', np.eye(3))),
                        translation=np.array(data.get('translation', [0, 0, 0]))
                    )

    def compute_disparity(
        self,
        frame_left: np.ndarray,
        frame_right: np.ndarray,
        cam_left_id: str,
        cam_right_id: str
    ) -> Optional[np.ndarray]:
        """
        Compute disparity map from stereo pair.

        Returns disparity map (higher values = closer objects).
        """
        # Convert to grayscale
        gray_left = cv2.cvtColor(frame_left, cv2.COLOR_BGR2GRAY)
        gray_right = cv2.cvtColor(frame_right, cv2.COLOR_BGR2GRAY)

        # Resize to match if needed
        if gray_left.shape != gray_right.shape:
            h = min(gray_left.shape[0], gray_right.shape[0])
            w = min(gray_left.shape[1], gray_right.shape[1])
            gray_left = cv2.resize(gray_left, (w, h))
            gray_right = cv2.resize(gray_right, (w, h))

        # Create stereo matcher
        stereo = cv2.StereoBM_create(numDisparities=64, blockSize=15)

        # Compute disparity
        disparity = stereo.compute(gray_left, gray_right)

        return disparity

    def disparity_to_depth(
        self,
        disparity: np.ndarray,
        baseline_meters: float,
        focal_length_pixels: float
    ) -> np.ndarray:
        """
        Convert disparity map to depth map.

        depth = (baseline * focal_length) / disparity
        """
        # Avoid division by zero
        disparity_safe = np.where(disparity > 0, disparity, 0.1)

        depth = (baseline_meters * focal_length_pixels) / disparity_safe

        # Clamp to reasonable range (0.5m to 50m)
        depth = np.clip(depth, 0.5, 50.0)

        return depth

    def estimate_object_distance(
        self,
        bbox: Tuple[int, int, int, int],  # x, y, w, h
        depth_map: np.ndarray
    ) -> float:
        """
        Estimate distance to object given bounding box and depth map.

        Returns median depth within bounding box.
        """
        x, y, w, h = bbox

        # Extract depth values within bbox
        roi = depth_map[y:y+h, x:x+w]

        # Use median to be robust to outliers
        distance = np.median(roi)

        return float(distance)

    def triangulate_point(
        self,
        pixel_left: Tuple[int, int],
        pixel_right: Tuple[int, int],
        cam_left_id: str,
        cam_right_id: str
    ) -> Optional[Tuple[float, float, float]]:
        """
        Triangulate 3D position from corresponding points in stereo pair.

        Returns (x, y, z) in meters or None if calibration missing.
        """
        cal_left = self.calibrations.get(cam_left_id)
        cal_right = self.calibrations.get(cam_right_id)

        if not cal_left or not cal_right:
            return None

        # Build projection matrices
        P1 = cal_left.camera_matrix @ np.hstack([np.eye(3), np.zeros((3, 1))])
        P2 = cal_right.camera_matrix @ np.hstack([
            cal_right.rotation,
            cal_right.translation.reshape(3, 1)
        ])

        # Triangulate
        points_4d = cv2.triangulatePoints(
            P1, P2,
            np.array(pixel_left, dtype=np.float32).reshape(2, 1),
            np.array(pixel_right, dtype=np.float32).reshape(2, 1)
        )

        # Convert from homogeneous coordinates
        point_3d = points_4d[:3] / points_4d[3]

        return tuple(point_3d.flatten())
```

### Step 2.4: Vision Hub Service

**File:** `/ganuda/lib/tribal_vision/vision_hub.py`

```python
"""
Tribal Vision Hub - Central service coordinating all vision processing.
"""

import cv2
import httpx
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from .camera_registry import CAMERAS, get_stereo_pairs
from .frame_sync import FrameSynchronizer, TimestampedFrame
from .stereo_depth import StereoDepthEstimator

class TribalVisionHub:
    """
    Central vision processing hub.

    Coordinates:
    - Frame capture from all cameras
    - Stereo depth estimation
    - VLM analysis
    - Result distribution
    """

    VLM_URL = "http://localhost:8090"
    OUTPUT_DIR = Path("/ganuda/data/vision")
    REDFIN_API = "http://redfin:8097"  # Pattern learner

    def __init__(self):
        self.synchronizer = FrameSynchronizer(sync_tolerance_ms=500)
        self.depth_estimator = StereoDepthEstimator()
        self.stereo_pairs = get_stereo_pairs()

    def start(self):
        """Start the vision hub."""
        print("Tribal Vision Hub starting...")
        print(f"Cameras: {len(CAMERAS)}")
        print(f"Stereo pairs: {self.stereo_pairs}")

        self.synchronizer.start()
        print("Frame synchronizer running")

    def stop(self):
        """Stop the vision hub."""
        self.synchronizer.stop()

    def analyze_frame(
        self,
        frame: np.ndarray,
        camera_id: str,
        prompt: Optional[str] = None
    ) -> dict:
        """Send frame to VLM for analysis."""
        # Save frame temporarily
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        frame_path = self.OUTPUT_DIR / "frames" / f"{camera_id}_{ts}.jpg"
        frame_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(frame_path), frame)

        # Default prompt
        if prompt is None:
            prompt = """Analyze this security camera image:
1. List any VEHICLES (type, color, company if delivery)
2. List any ANIMALS (species, color, behavior)
3. List any PEOPLE (activity, direction)
4. Note any UNUSUAL activity

Be concise."""

        # Call VLM
        try:
            resp = httpx.post(
                f"{self.VLM_URL}/v1/vlm/describe",
                json={"image_path": str(frame_path), "prompt": prompt},
                timeout=120.0
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def process_stereo_pair(
        self,
        cam_a_id: str,
        cam_b_id: str
    ) -> Optional[dict]:
        """
        Process a stereo camera pair for depth estimation.
        """
        pair = self.synchronizer.get_stereo_pair(cam_a_id, cam_b_id)
        if not pair:
            return None

        frame_a, frame_b, time_delta = pair

        # Compute disparity
        disparity = self.depth_estimator.compute_disparity(
            frame_a.frame, frame_b.frame,
            cam_a_id, cam_b_id
        )

        if disparity is None:
            return None

        # Get baseline from camera positions (placeholder)
        baseline = 15.0  # meters - update with actual measurement

        # Convert to depth
        depth_map = self.depth_estimator.disparity_to_depth(
            disparity,
            baseline_meters=baseline,
            focal_length_pixels=500  # Update with calibration
        )

        return {
            "pair": (cam_a_id, cam_b_id),
            "sync_delta_ms": time_delta * 1000,
            "depth_map": depth_map,
            "timestamp": frame_a.timestamp
        }

    def send_to_learner(self, event: dict):
        """Send event to Redfin pattern learner."""
        try:
            httpx.post(
                f"{self.REDFIN_API}/v1/learn/event",
                json=event,
                timeout=10.0
            )
        except:
            pass  # Non-critical

    def run_detection_cycle(self):
        """Run one detection cycle across all cameras."""
        results = {}

        # Get synced frames from all cameras
        frames = self.synchronizer.get_all_synced_frames()

        for cam_id, ts_frame in frames.items():
            # VLM analysis
            vlm_result = self.analyze_frame(ts_frame.frame, cam_id)
            results[cam_id] = {
                "vlm": vlm_result,
                "timestamp": ts_frame.timestamp
            }

        # Process stereo pairs
        for cam_a, cam_b in self.stereo_pairs:
            stereo_result = self.process_stereo_pair(cam_a, cam_b)
            if stereo_result:
                results[f"stereo_{cam_a}_{cam_b}"] = stereo_result

        # Send to learner
        self.send_to_learner({
            "type": "detection_cycle",
            "timestamp": time.time(),
            "results": results
        })

        return results


def main():
    """Run vision hub as daemon."""
    hub = TribalVisionHub()
    hub.start()

    try:
        while True:
            hub.run_detection_cycle()
            time.sleep(30)  # Detection every 30 seconds
    except KeyboardInterrupt:
        hub.stop()


if __name__ == "__main__":
    main()
```

### Step 2.5: Systemd Service

**File:** `/ganuda/scripts/systemd/tribal-vision-hub.service`

```ini
[Unit]
Description=Tribal Vision Hub - Stereo Vision Processing
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python3 -m tribal_vision.vision_hub
Restart=always
RestartSec=10
Environment=PYTHONPATH=/ganuda/lib

[Install]
WantedBy=multi-user.target
```

## Phase 3: Calibration Procedure

### Step 3.1: Print Calibration Target

```bash
# Generate checkerboard pattern
python3 -c "
import cv2
import numpy as np

# 9x6 checkerboard, 25mm squares
board = np.zeros((6*25, 9*25), dtype=np.uint8)
board[::50, :] = 255
board[:, ::50] = 255
cv2.imwrite('/tmp/checkerboard.png', board)
print('Saved /tmp/checkerboard.png - print at 100% scale')
"
```

### Step 3.2: Capture Calibration Images

```bash
# Capture 20+ images per camera showing checkerboard at various angles
python3 << 'EOF'
import cv2
import time
from pathlib import Path

CAMERAS = {
    "traffic": "rtsp://admin:jawaseatlasers2@192.168.132.182:554/cam/realmonitor?channel=1&subtype=1",
    "doorbell": "rtsp://tribal:vision2026@greenfin:8554/DOORBELL_ID_live"
}

for cam_id, url in CAMERAS.items():
    output_dir = Path(f"/ganuda/data/vision/calibration/{cam_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(url)
    count = 0

    print(f"Capturing calibration images for {cam_id}")
    print("Press 's' to save, 'q' to quit")

    while count < 25:
        ret, frame = cap.read()
        if not ret:
            continue

        cv2.imshow(f"Calibration - {cam_id}", frame)
        key = cv2.waitKey(100)

        if key == ord('s'):
            path = output_dir / f"cal_{count:03d}.jpg"
            cv2.imwrite(str(path), frame)
            print(f"Saved {path}")
            count += 1
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
EOF
```

### Step 3.3: Run Calibration

```bash
python3 << 'EOF'
import cv2
import numpy as np
import json
from pathlib import Path
import glob

def calibrate_camera(image_dir: Path, board_size=(9, 6)):
    """Calibrate single camera from checkerboard images."""
    objp = np.zeros((board_size[0] * board_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:board_size[0], 0:board_size[1]].T.reshape(-1, 2)
    objp *= 25  # 25mm squares

    obj_points = []
    img_points = []

    images = list(image_dir.glob("*.jpg"))
    print(f"Found {len(images)} calibration images")

    for img_path in images:
        img = cv2.imread(str(img_path))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        ret, corners = cv2.findChessboardCorners(gray, board_size, None)
        if ret:
            obj_points.append(objp)
            corners2 = cv2.cornerSubPix(
                gray, corners, (11, 11), (-1, -1),
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            )
            img_points.append(corners2)

    print(f"Found checkerboard in {len(obj_points)} images")

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        obj_points, img_points, gray.shape[::-1], None, None
    )

    return {
        "camera_matrix": mtx.tolist(),
        "dist_coeffs": dist.tolist(),
        "calibration_error": ret
    }

# Calibrate each camera
for cam_id in ["traffic", "doorbell", "office"]:
    image_dir = Path(f"/ganuda/data/vision/calibration/{cam_id}")
    if image_dir.exists():
        print(f"\nCalibrating {cam_id}...")
        cal = calibrate_camera(image_dir)
        print(f"Calibration error: {cal['calibration_error']}")

        output_file = image_dir.parent / f"{cam_id}_calibration.json"
        with open(output_file, 'w') as f:
            json.dump(cal, f, indent=2)
        print(f"Saved {output_file}")
EOF
```

## Verification

```bash
# Check Greenfin bridges
curl http://greenfin:3000/api/devices  # ring-mqtt
curl http://greenfin:10443/api/status  # scrypted

# Check Bluefin hub
systemctl --user status tribal-vision-hub

# Test stereo pair
python3 -c "
from tribal_vision.vision_hub import TribalVisionHub
hub = TribalVisionHub()
hub.start()
result = hub.process_stereo_pair('traffic', 'doorbell')
print(f'Stereo result: {result}')
hub.stop()
"
```

## Success Criteria

- [ ] ring-mqtt serving Ring doorbell on Greenfin:8554
- [ ] Scrypted serving Nest cameras on Greenfin
- [ ] Frame synchronizer capturing from all cameras
- [ ] Stereo pairs producing depth maps
- [ ] VLM processing frames from all sources
- [ ] Results flowing to Redfin learner

## Physical Measurements Needed

Before full calibration:
1. Measure exact height of each camera
2. Measure horizontal distance between stereo pairs
3. Measure camera angles (compass heading)
4. Note reference objects with known dimensions

### Reference Object: 2021 Chevy Silverado 2500 (White)

**Owner's truck - use for depth validation:**

| Dimension | Imperial | Metric |
|-----------|----------|--------|
| Height | 79.82" | **2.03m** |
| Width (body) | 81.85" | **2.08m** |
| Length | 249.95" | **6.35m** |
| Wheelbase | 158.94" | **4.04m** |

Source: [Edmunds 2021 Silverado 2500HD Specs](https://www.edmunds.com/chevrolet/silverado-2500hd/2021/features-specs/)

**Validation procedure:**
1. Park truck in stereo overlap zone (driveway)
2. Capture synced frames from Traffic + Ring
3. Run depth estimation
4. Compare estimated truck dimensions to known values
5. Adjust calibration parameters until error < 10%

---

*Council-Approved Architecture - Cherokee AI Federation*
