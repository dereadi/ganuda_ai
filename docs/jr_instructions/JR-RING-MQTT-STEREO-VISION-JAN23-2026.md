# JR Instruction: Ring Doorbell Integration for Stereo Vision

**Task ID:** RING-STEREO-001
**Priority:** P2
**Assigned Node:** greenfin (gateway/bridge node)
**Date:** January 23, 2026

## Objective

Integrate Ring doorbell via ring-mqtt to provide RTSP stream for tribal vision system. Combined with existing Amcrest traffic camera, this enables **stereo vision / depth perception** through overlapping fields of view.

## Architecture

```
Ring Doorbell ──► Ring Cloud ──► ring-mqtt (greenfin) ──► RTSP :8554
                                        │
                                        ▼
                              Tribal Vision (bluefin)
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
              Ring Doorbell      Amcrest Traffic      Depth Fusion
              (front angle)      (street angle)       (triangulation)
```

## Prerequisites

- Ring account credentials (email/password or refresh token)
- Docker on greenfin
- Network access from greenfin to bluefin

## Implementation Steps

### Step 1: Deploy ring-mqtt on Greenfin

```bash
# On greenfin
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
      - "8554:8554"   # RTSP streaming
      - "3000:3000"   # Web UI (optional)
    volumes:
      - ./data:/data
    environment:
      - RINGTOKEN=${RING_REFRESH_TOKEN}
      - ENABLECAMERAS=true
      - LIVESTREAMUSER=ring
      - LIVESTREAMPASSWORD=tribal_vision_2026
      - SNAPSHOTMODE=interval
      - SNAPSHOTINTERVAL=30
    logging:
      options:
        max-size: "10m"
        max-file: "3"
EOF
```

### Step 2: Generate Ring Refresh Token

```bash
# Install ring-client-api to generate token
docker run -it --rm tsightler/ring-mqtt node /app/ring-mqtt/node_modules/ring-client-api/lib/ring-auth-cli.js

# Follow prompts:
# 1. Enter Ring email
# 2. Enter Ring password
# 3. Enter 2FA code (sent to phone)
# 4. Copy the refresh token output

# Save token
echo "RING_REFRESH_TOKEN=your_token_here" > .env
```

### Step 3: Start ring-mqtt

```bash
docker-compose up -d

# Verify running
docker logs ring-mqtt --tail 50

# Check RTSP is available
curl http://localhost:3000/api/devices
```

### Step 4: Get RTSP URL

The RTSP stream URL format:
```
rtsp://ring:tribal_vision_2026@greenfin:8554/{device_id}_live
```

To find device_id:
```bash
curl -s http://localhost:3000/api/devices | jq '.[] | {name, id}'
```

### Step 5: Test Stream

```bash
# From bluefin, test Ring stream
ffprobe rtsp://ring:tribal_vision_2026@greenfin:8554/DEVICE_ID_live

# Or capture a test frame
ffmpeg -i rtsp://ring:tribal_vision_2026@greenfin:8554/DEVICE_ID_live \
  -frames:v 1 /tmp/ring_test.jpg
```

### Step 6: Add to Tribal Vision Config

Update `/ganuda/lib/tribal_vision/quick_delivery_watch.py` to include Ring:

```python
CAMERAS = {
    "traffic": {
        "url": "rtsp://admin:jawaseatlasers2@192.168.132.182:554/cam/realmonitor?channel=1&subtype=1",
        "type": "outdoor",
        "location": "street_view"
    },
    "office": {
        "url": "rtsp://admin:jawaseatlasers2@192.168.132.181:554/cam/realmonitor?channel=1&subtype=0",
        "type": "indoor",
        "location": "office"
    },
    "doorbell": {
        "url": "rtsp://ring:tribal_vision_2026@greenfin:8554/DEVICE_ID_live",
        "type": "outdoor",
        "location": "front_door",
        "stereo_pair": "traffic"  # For depth perception
    }
}
```

### Step 7: Stereo Vision / Depth Module (Future)

Create depth estimation module using overlapping camera views:

**File:** `/ganuda/lib/tribal_vision/depth_estimator.py`

```python
"""
Stereo Depth Estimation from Ring + Traffic Camera

Uses triangulation when same object detected in both views
to estimate real-world distance and 3D position.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class CameraPosition:
    """Camera location and orientation"""
    x: float  # meters from reference point
    y: float
    z: float  # height
    yaw: float  # horizontal angle in degrees
    fov_h: float  # horizontal field of view
    fov_v: float  # vertical field of view

# Camera positions (calibrate with measurements)
CAMERAS = {
    "traffic": CameraPosition(
        x=0, y=0, z=3.0,  # Reference point, 3m high
        yaw=180,  # Facing street
        fov_h=90, fov_v=60
    ),
    "doorbell": CameraPosition(
        x=15, y=8, z=1.2,  # 15m east, 8m north, 1.2m high
        yaw=270,  # Facing driveway/street
        fov_h=160, fov_v=90  # Wide angle doorbell
    )
}

def pixel_to_angle(pixel_x: int, pixel_y: int,
                   frame_width: int, frame_height: int,
                   camera: CameraPosition) -> Tuple[float, float]:
    """Convert pixel position to viewing angle"""
    # Normalize to -0.5 to 0.5
    norm_x = (pixel_x / frame_width) - 0.5
    norm_y = (pixel_y / frame_height) - 0.5

    # Convert to angles
    angle_h = camera.yaw + (norm_x * camera.fov_h)
    angle_v = norm_y * camera.fov_v

    return angle_h, angle_v

def triangulate_position(
    cam1_id: str, cam1_pixel: Tuple[int, int], cam1_frame_size: Tuple[int, int],
    cam2_id: str, cam2_pixel: Tuple[int, int], cam2_frame_size: Tuple[int, int]
) -> Optional[Tuple[float, float, float]]:
    """
    Estimate 3D position of object seen in both cameras.

    Returns (x, y, z) in meters from reference point, or None if no intersection.
    """
    cam1 = CAMERAS[cam1_id]
    cam2 = CAMERAS[cam2_id]

    # Get viewing angles
    angle1_h, angle1_v = pixel_to_angle(*cam1_pixel, *cam1_frame_size, cam1)
    angle2_h, angle2_v = pixel_to_angle(*cam2_pixel, *cam2_frame_size, cam2)

    # Convert to radians and compute ray directions
    # ... (full triangulation math)

    # Find intersection point of two rays
    # ...

    return (x, y, z)

def estimate_distance(
    object_bbox: Tuple[int, int, int, int],  # x, y, w, h
    camera_id: str,
    known_height: float = 1.7  # Assume human height in meters
) -> float:
    """
    Estimate distance using single camera and known object size.
    Fallback when stereo not available.
    """
    # Use pinhole camera model
    # distance = (known_height * focal_length) / pixel_height
    pass
```

## Verification

```bash
# Check ring-mqtt is running
docker ps | grep ring-mqtt

# Verify RTSP stream accessible from bluefin
ssh bluefin "ffprobe rtsp://ring:tribal_vision_2026@greenfin:8554/DEVICE_ID_live 2>&1 | head -10"

# Test VLM can process Ring frame
ssh bluefin "ffmpeg -i rtsp://ring:tribal_vision_2026@greenfin:8554/DEVICE_ID_live -frames:v 1 /tmp/ring.jpg && \
  curl -X POST http://localhost:8090/v1/vlm/describe \
    -H 'Content-Type: application/json' \
    -d '{\"image_path\": \"/tmp/ring.jpg\", \"prompt\": \"Describe what you see\"}'"
```

## Success Criteria

- [ ] ring-mqtt running on greenfin
- [ ] RTSP stream accessible from bluefin
- [ ] Ring frames processable by VLM
- [ ] Tribal vision config updated with doorbell camera
- [ ] Stereo depth estimation functional (phase 2)

## Security Notes

- Ring refresh token stored in `.env` file (add to .gitignore)
- RTSP password should be strong
- ring-mqtt web UI (port 3000) should be firewalled from WAN

## References

- https://github.com/tsightler/ring-mqtt
- https://github.com/tsightler/ring-mqtt/wiki/Video-Streaming
- https://docs.scrypted.app/add-camera.html
