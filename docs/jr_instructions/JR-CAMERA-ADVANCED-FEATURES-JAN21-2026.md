# JR Instruction: Advanced Camera Features - PTZ & Live Streaming

**Task ID**: CAMERA-ADVANCED-001
**Priority**: P2 - Medium
**Created**: January 21, 2026
**TPM**: Claude Opus 4.5

## Objective

Implement advanced camera features for the SAG Camera Intelligence tab:
1. PTZ (Pan-Tilt-Zoom) controls if cameras support ONVIF
2. Live RTSP streaming to browser
3. Camera presets and tours

## Research Sources

Based on research from GitHub IP camera projects:
- [onvif-ptz-webui](https://github.com/vpuhoff/onvif-ptz-webui) - Flask-based ONVIF PTZ control
- [PTZController](https://github.com/zSeriesGuy/PTZController) - Python ONVIF webserver
- [Moonfire NVR](https://github.com/scottlamb/moonfire-nvr) - Rust-based NVR with web interface

## Current Camera Configuration

Our Dahua cameras (192.168.132.181, 192.168.132.182) support:
- RTSP streaming (main stream and sub-stream)
- ONVIF protocol (typically on port 80 or 8080)
- Potentially PTZ if equipped with motors

## Phase 1: ONVIF Discovery

### Task 1.1: Check ONVIF Support

Create `/ganuda/lib/onvif_client.py`:

```python
"""
ONVIF Client for Dahua Cameras
Cherokee AI Federation - Tribal Vision System
"""

from onvif import ONVIFCamera
import logging

logger = logging.getLogger(__name__)

class CameraONVIFClient:
    """ONVIF client for camera control."""

    def __init__(self, ip: str, port: int = 80, user: str = 'admin', password: str = ''):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.cam = None
        self.ptz = None
        self.media = None

    def connect(self) -> bool:
        """Connect to camera via ONVIF."""
        try:
            self.cam = ONVIFCamera(self.ip, self.port, self.user, self.password)
            self.media = self.cam.create_media_service()

            # Check for PTZ capability
            try:
                self.ptz = self.cam.create_ptz_service()
                logger.info(f"PTZ service available on {self.ip}")
            except:
                logger.info(f"No PTZ service on {self.ip}")
                self.ptz = None

            return True
        except Exception as e:
            logger.error(f"ONVIF connection failed: {e}")
            return False

    def get_capabilities(self) -> dict:
        """Get camera capabilities."""
        if not self.cam:
            return {}

        caps = {
            'ptz': self.ptz is not None,
            'profiles': [],
            'presets': []
        }

        if self.media:
            profiles = self.media.GetProfiles()
            caps['profiles'] = [p.Name for p in profiles]

        if self.ptz:
            try:
                profile = self.media.GetProfiles()[0]
                presets = self.ptz.GetPresets({'ProfileToken': profile.token})
                caps['presets'] = [{'token': p.token, 'name': p.Name} for p in presets]
            except:
                pass

        return caps

    def move(self, direction: str, speed: float = 0.5):
        """Move camera in specified direction."""
        if not self.ptz:
            return False

        # Implementation depends on camera PTZ capabilities
        pass

    def goto_preset(self, preset_token: str):
        """Go to a saved preset position."""
        if not self.ptz:
            return False

        profile = self.media.GetProfiles()[0]
        self.ptz.GotoPreset({
            'ProfileToken': profile.token,
            'PresetToken': preset_token
        })
        return True
```

### Dependencies

```bash
pip install onvif-zeep
```

## Phase 2: Live RTSP Streaming

### Option A: Server-Side Transcoding (Recommended)

Use FFmpeg to transcode RTSP to HLS for browser playback.

Create `/ganuda/services/vision/stream_server.py`:

```python
"""
RTSP to HLS Streaming Server
Cherokee AI Federation
"""

import subprocess
import os
from pathlib import Path

HLS_DIR = Path('/ganuda/data/vision/hls')

def start_stream(camera_id: str, rtsp_url: str):
    """Start HLS stream for a camera."""
    HLS_DIR.mkdir(parents=True, exist_ok=True)
    output_dir = HLS_DIR / camera_id
    output_dir.mkdir(exist_ok=True)

    cmd = [
        'ffmpeg', '-i', rtsp_url,
        '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
        '-c:a', 'aac',
        '-f', 'hls',
        '-hls_time', '2',
        '-hls_list_size', '3',
        '-hls_flags', 'delete_segments',
        str(output_dir / 'stream.m3u8')
    ]

    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
```

### Option B: WebRTC (Lower Latency)

Use go2rtc or mediamtx for WebRTC streaming.

## Phase 3: API Endpoints

Add to `/ganuda/home/dereadi/sag_unified_interface/app.py`:

```python
@app.route('/api/cameras/<camera_id>/ptz/<action>', methods=['POST'])
def api_camera_ptz(camera_id, action):
    """Control camera PTZ."""
    # action: up, down, left, right, zoom_in, zoom_out, stop
    pass

@app.route('/api/cameras/<camera_id>/presets')
def api_camera_presets(camera_id):
    """Get camera presets."""
    pass

@app.route('/api/cameras/<camera_id>/preset/<preset_id>', methods=['POST'])
def api_camera_goto_preset(camera_id, preset_id):
    """Go to preset position."""
    pass

@app.route('/api/cameras/<camera_id>/stream')
def api_camera_stream_url(camera_id):
    """Get HLS stream URL for camera."""
    pass
```

## Phase 4: Frontend Controls

Add PTZ control overlay to camera cards:

```html
<div class="ptz-controls">
    <button class="ptz-btn" data-dir="up">▲</button>
    <div class="ptz-row">
        <button class="ptz-btn" data-dir="left">◀</button>
        <button class="ptz-btn" data-dir="home">●</button>
        <button class="ptz-btn" data-dir="right">▶</button>
    </div>
    <button class="ptz-btn" data-dir="down">▼</button>
    <div class="ptz-zoom">
        <button class="ptz-btn" data-zoom="in">+</button>
        <button class="ptz-btn" data-zoom="out">-</button>
    </div>
</div>
```

## Testing Checklist

1. [ ] Check if cameras support ONVIF (try port 80 and 8080)
2. [ ] Verify PTZ motors exist on cameras
3. [ ] Test RTSP to HLS transcoding latency
4. [ ] Measure bandwidth requirements for live streaming
5. [ ] Test PTZ controls response time

## Notes

- Dahua cameras typically use port 80 for ONVIF
- RTSP main stream: `subtype=0` (1080p), sub-stream: `subtype=1` (lower res)
- Consider sub-stream for live view to reduce bandwidth
- HLS adds 4-10 second latency; WebRTC is better for real-time control

---
*Cherokee AI Federation - For Seven Generations*
