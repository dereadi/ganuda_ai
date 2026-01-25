# ULTRATHINK: Tribal Vision Stereo Architecture

**Date:** January 23, 2026
**Author:** TPM (Claude Opus 4.5)
**Council Decision:** CONTESTED → Lean Option C with hybrid elements
**Status:** Architecture Design

---

## Executive Summary

This document analyzes the optimal architecture for integrating multiple camera streams into the Cherokee AI Federation's vision system, with particular focus on enabling **stereo vision / depth perception** through triangulation of overlapping camera views.

**Recommendation:** Hybrid architecture with Bluefin as VLM Hub + synchronized frame capture, Redfin for pattern learning and correlation, Greenfin as stream bridge for cloud-dependent cameras.

---

## 1. Current State Analysis

### 1.1 Camera Inventory

| Camera | Type | Stream | Location | Resolution | Latency |
|--------|------|--------|----------|------------|---------|
| Amcrest 181 | IPC | Native RTSP | Office (indoor) | 2960×1668 | ~50ms |
| Amcrest 182 | IPC | Native RTSP | Traffic (street) | 704×480 | ~50ms |
| Ring Doorbell | Cloud | ring-mqtt bridge | Front door | 1080p | ~500-2000ms |
| Nest Porch | Cloud | Scrypted bridge | Front porch | 1080p | ~500-2000ms |
| Nest Backyard | Cloud | Scrypted bridge | Backyard | 1080p | ~500-2000ms |

### 1.2 Compute Resources

| Node | Role | GPU | RAM | Network |
|------|------|-----|-----|---------|
| **Bluefin** (.222) | VLM Processing | RTX 5070 (CUDA) | 128GB | 1Gbps |
| **Greenfin** (.224) | Gateway/Router | None | 32GB | Multi-VLAN |
| **Redfin** (.223) | Trading/Compute | Available | 64GB | 1Gbps |

### 1.3 Existing Infrastructure

- **NFS Mount:** `/ganuda/data/vision` shared across nodes
- **VLM Service:** Qwen2-VL-7B-Instruct on Bluefin:8090
- **Current Services:**
  - `delivery-watch.service` (wildlife mode, Bluefin)
  - `snow-timelapse.service` (periodic capture, Bluefin)

---

## 2. Stereo Vision Requirements

### 2.1 What Stereo Vision Enables

```
Camera A (position Pa)              Camera B (position Pb)
        \                                  /
         \   Object O visible            /
          \  in both frames             /
           \                           /
            \    TRIANGULATION        /
             \        ↓              /
              \   3D Position       /
               \  of Object O      /
                \                 /
                 ────────────────
```

**Key Capabilities:**
1. **Depth Estimation:** Distance from cameras to objects
2. **3D Position:** X, Y, Z coordinates in world space
3. **Velocity Vectors:** True speed and direction (not just pixel movement)
4. **Occlusion Handling:** See around obstacles via second viewpoint

### 2.2 Technical Requirements for Stereo

Based on research from GitHub stereo vision projects:

| Requirement | Why | Implementation |
|-------------|-----|----------------|
| **Frame Synchronization** | Triangulation requires simultaneous capture | < 100ms sync tolerance |
| **Camera Calibration** | Intrinsic/extrinsic parameters needed | OpenCV calibration routine |
| **Overlapping FOV** | Cameras must see same objects | Ring + Traffic have overlap |
| **Known Baseline** | Distance between cameras | Physical measurement |
| **Rectification** | Align image planes mathematically | cv2.stereoRectify() |

### 2.3 Relevant GitHub Projects

| Project | Use Case | Integration Path |
|---------|----------|------------------|
| [erget/StereoVision](https://github.com/erget/StereoVision) | Full 3D reconstruction | Primary library candidate |
| [sourishg/stereo-calibration](https://github.com/sourishg/stereo-calibration) | Camera calibration | Calibration tooling |
| [aliyasineser/stereoDepth](https://github.com/aliyasineser/stereoDepth) | Disparity/depth maps | Depth calculation |
| [TemugeB/python_stereo_camera_calibrate](https://github.com/TemugeB/python_stereo_camera_calibrate) | OpenCV calibration | Python integration |

---

## 3. Architecture Options Analysis

### 3.1 Option A: Distributed Processing

```
Amcrest ──► RTSP ──────────────────────────────┐
                                               ▼
Ring ──► Greenfin ──► NFS ──► Redfin ──► VLM API (Bluefin)
                                               │
Nest ──► Greenfin ──► NFS ─────────────────────┘
```

**Pros:**
- Load distribution across nodes
- Fault tolerance (Redfin can queue if Bluefin down)
- Greenfin handles cloud latency independently

**Cons:**
- Network hop for every VLM call
- Frame sync difficult across NFS
- Higher total latency

**Stereo Viability:** ⚠️ Poor - sync issues across NFS + network

### 3.2 Option B: Tiered Pipeline

```
All Cameras ──► NFS ──► Bluefin (VLM) ──► Results ──► Redfin (Learning)
```

**Pros:**
- GPU-local VLM processing
- Clear separation: Bluefin=perception, Redfin=cognition
- NFS provides buffer

**Cons:**
- Bluefin becomes potential bottleneck
- Still using NFS for frame delivery

**Stereo Viability:** ✅ Moderate - Bluefin can sync frames locally

### 3.3 Option C: Bluefin Hub (Council Preference)

```
Amcrest ──► RTSP ──────────────┐
                               │
Ring ──► Greenfin:8554 ────────┼──► Bluefin ──► VLM ──► Results
                               │        │
Nest ──► Greenfin:8555 ────────┘        ▼
                                   NFS (archival)
                                        │
                                        ▼
                                    Redfin (learning)
```

**Pros:**
- Lowest latency for VLM
- All frames arrive at same node for sync
- GPU always local to processing
- Best for stereo triangulation

**Cons:**
- Single point of failure
- Bluefin load concentration

**Stereo Viability:** ✅ Excellent - frames synchronized at capture point

---

## 4. Recommended Architecture: Hybrid Hub

### 4.1 Design Principles

1. **Frames converge on Bluefin** for stereo synchronization
2. **Greenfin bridges cloud streams** but doesn't process
3. **Redfin handles learning/correlation** post-VLM
4. **NFS for archival and cross-node sharing** of results

### 4.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TRIBAL VISION MESH                          │
└─────────────────────────────────────────────────────────────────────┘

   LOCAL CAMERAS                    CLOUD-BRIDGED CAMERAS
   ══════════════                   ═════════════════════

   Amcrest 181 ───┐                 Ring ──► Ring Cloud ──┐
   (Office)       │                                       │
                  │                 Nest ──► Google ──────┤
   Amcrest 182 ───┼─── RTSP ──────────────────────────────┤
   (Traffic)      │                                       │
                  │                                       ▼
                  │                              ┌─────────────────┐
                  │                              │    GREENFIN     │
                  │                              │   (Bridge)      │
                  │                              │                 │
                  │                              │ ring-mqtt:8554  │
                  │                              │ scrypted:8555   │
                  │                              └────────┬────────┘
                  │                                       │
                  │            RTSP Rebroadcast           │
                  │                                       │
                  └───────────────────┬───────────────────┘
                                      │
                                      ▼
                  ┌───────────────────────────────────────┐
                  │              BLUEFIN                   │
                  │         (Vision Hub + VLM)             │
                  │                                        │
                  │  ┌──────────────────────────────────┐  │
                  │  │      Frame Synchronizer          │  │
                  │  │  - Captures from all streams     │  │
                  │  │  - Aligns timestamps             │  │
                  │  │  - Buffers for stereo pairs      │  │
                  │  └──────────────┬───────────────────┘  │
                  │                 │                      │
                  │                 ▼                      │
                  │  ┌──────────────────────────────────┐  │
                  │  │    Stereo Depth Estimator        │  │
                  │  │  - Triangulation (Ring+Traffic)  │  │
                  │  │  - Disparity maps                │  │
                  │  │  - 3D position estimation        │  │
                  │  └──────────────┬───────────────────┘  │
                  │                 │                      │
                  │                 ▼                      │
                  │  ┌──────────────────────────────────┐  │
                  │  │      VLM Analysis (GPU)          │  │
                  │  │  - Qwen2-VL-7B-Instruct          │  │
                  │  │  - Object detection              │  │
                  │  │  - Scene understanding           │  │
                  │  │  - Delivery/wildlife classify    │  │
                  │  └──────────────┬───────────────────┘  │
                  │                 │                      │
                  │  RTX 5070       │                      │
                  └─────────────────┼──────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
             ┌───────────┐  ┌─────────────┐  ┌───────────┐
             │    NFS    │  │   REDFIN    │  │  Telegram │
             │  Archive  │  │  Learning   │  │   Alerts  │
             │           │  │             │  │           │
             │ /ganuda/  │  │ - Patterns  │  │ - Delivery│
             │ data/     │  │ - Anomalies │  │ - Wildlife│
             │ vision/   │  │ - Thermal   │  │ - Speeding│
             │           │  │   Memory    │  │           │
             └───────────┘  └─────────────┘  └───────────┘
```

### 4.3 Component Specifications

#### 4.3.1 Greenfin: Stream Bridge

```yaml
services:
  ring-mqtt:
    port: 8554
    function: Bridge Ring doorbell to RTSP

  scrypted:
    ports:
      - 8555  # Nest Porch
      - 8556  # Nest Backyard
    function: Bridge Nest cameras to RTSP
```

#### 4.3.2 Bluefin: Vision Hub

```yaml
services:
  tribal-vision-hub:
    port: 8095
    function: Unified camera ingestion and sync

  vlm-api:
    port: 8090
    function: Qwen2-VL inference

  stereo-depth:
    port: 8096
    function: Depth estimation from camera pairs

camera_streams:
  - name: office
    url: rtsp://admin:***@192.168.132.181:554/...
    local: true

  - name: traffic
    url: rtsp://admin:***@192.168.132.182:554/...
    local: true
    stereo_pair: doorbell

  - name: doorbell
    url: rtsp://ring:***@greenfin:8554/DEVICE_ID_live
    local: false
    stereo_pair: traffic

  - name: porch
    url: rtsp://scrypted:***@greenfin:8555/nest_porch
    local: false

  - name: backyard
    url: rtsp://scrypted:***@greenfin:8556/nest_backyard
    local: false
```

#### 4.3.3 Redfin: Learning Engine

```yaml
services:
  pattern-learner:
    function: Analyze VLM results for patterns
    inputs:
      - VLM descriptions
      - Stereo depth data
      - Timestamps
    outputs:
      - Delivery time predictions
      - Wildlife behavior patterns
      - Anomaly alerts

  thermal-memory-writer:
    function: Store significant events
    destination: PostgreSQL thermal memory
```

### 4.4 Stereo Pairs Configuration

| Pair Name | Camera A | Camera B | Baseline | Overlap FOV |
|-----------|----------|----------|----------|-------------|
| **front-stereo** | Traffic (Amcrest 182) | Ring Doorbell | ~15m | Street/driveway |
| **porch-stereo** | Ring Doorbell | Nest Porch | ~3m | Front porch area |

### 4.5 Frame Synchronization Strategy

```python
class FrameSynchronizer:
    """
    Synchronizes frames from multiple cameras for stereo processing.

    Challenge: Cloud-bridged cameras have 500-2000ms latency
    Solution: Timestamp-based buffering with tolerance window
    """

    def __init__(self, cameras: list, sync_tolerance_ms: int = 500):
        self.cameras = cameras
        self.sync_tolerance = sync_tolerance_ms
        self.frame_buffer = {cam: deque(maxlen=30) for cam in cameras}

    def add_frame(self, camera_id: str, frame: np.ndarray, timestamp: float):
        """Add frame to buffer with timestamp."""
        self.frame_buffer[camera_id].append((timestamp, frame))

    def get_stereo_pair(self, cam_a: str, cam_b: str) -> Optional[Tuple]:
        """
        Find closest timestamp match between two cameras.
        Returns (frame_a, frame_b, time_delta_ms) or None.
        """
        buffer_a = self.frame_buffer[cam_a]
        buffer_b = self.frame_buffer[cam_b]

        best_match = None
        best_delta = float('inf')

        for ts_a, frame_a in buffer_a:
            for ts_b, frame_b in buffer_b:
                delta = abs(ts_a - ts_b) * 1000  # ms
                if delta < best_delta and delta < self.sync_tolerance:
                    best_delta = delta
                    best_match = (frame_a, frame_b, delta)

        return best_match
```

---

## 5. Calibration Requirements

### 5.1 Intrinsic Calibration (per camera)

Each camera needs:
- Focal length (fx, fy)
- Principal point (cx, cy)
- Distortion coefficients (k1, k2, p1, p2, k3)

**Method:** Checkerboard calibration using OpenCV

```bash
# Generate calibration images
python3 -m tribal_vision.calibrate capture --camera traffic --output /ganuda/data/vision/calibration/

# Run calibration
python3 -m tribal_vision.calibrate intrinsic --images /ganuda/data/vision/calibration/traffic/
```

### 5.2 Extrinsic Calibration (camera pairs)

For each stereo pair:
- Rotation matrix (R)
- Translation vector (T)
- Essential matrix (E)
- Fundamental matrix (F)

**Method:** Stereo calibration with simultaneous checkerboard views

### 5.3 Physical Measurements Needed

| Measurement | Description | Method |
|-------------|-------------|--------|
| Camera positions | X, Y, Z from reference point | Tape measure + level |
| Camera orientations | Yaw, pitch, roll | Compass + inclinometer |
| Baseline distance | Distance between stereo pairs | Direct measurement |
| Reference objects | Known sizes for validation | Measure car width, door height |

---

## 6. Fault Tolerance

### 6.1 Failure Scenarios

| Failure | Impact | Mitigation |
|---------|--------|------------|
| Bluefin VLM down | No vision processing | Queue frames to NFS, alert, manual review |
| Greenfin bridge down | No cloud cameras | Local cameras continue, degraded stereo |
| Ring/Nest cloud outage | No cloud camera feeds | Local cameras only |
| Network partition | Nodes isolated | Each node operates independently |

### 6.2 Health Monitoring

```yaml
health_checks:
  - service: vlm-api
    endpoint: http://bluefin:8090/v1/vlm/health
    interval: 30s

  - service: ring-mqtt
    endpoint: http://greenfin:3000/api/devices
    interval: 60s

  - service: frame-sync
    metric: frames_synced_per_minute
    threshold: "> 0"
```

---

## 7. Implementation Phases

### Phase 1: Ring Integration (Week 1)
- Deploy ring-mqtt on Greenfin
- Test RTSP stream accessibility from Bluefin
- Add Ring to tribal vision config

### Phase 2: Stereo Calibration (Week 2)
- Physical measurements of camera positions
- Intrinsic calibration of all cameras
- Extrinsic calibration of stereo pairs

### Phase 3: Depth Estimation (Week 3)
- Implement frame synchronizer
- Integrate StereoVision library
- Test triangulation accuracy

### Phase 4: Nest Integration (Week 4)
- Deploy Scrypted on Greenfin
- Add Nest cameras to pipeline
- Expand stereo pairs (porch-stereo)

### Phase 5: Learning Integration (Week 5)
- Connect Redfin pattern learner
- Thermal memory integration
- Anomaly detection tuning

---

## 8. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Frame sync accuracy | < 200ms delta | Timestamp comparison |
| Depth estimation error | < 15% at 10m | Validate against known distances |
| VLM latency | < 5s per frame | End-to-end timing |
| Stereo pair availability | > 95% uptime | Health check logs |
| Detection accuracy | > 90% for vehicles | Manual validation |

---

## 9. Conclusion

The hybrid hub architecture with Bluefin as the central vision processor best serves the tribe's need for:

1. **Stereo vision** - Frames must converge for triangulation
2. **Low latency** - GPU-local processing
3. **Scalability** - Additional cameras add to existing streams
4. **Learning** - Redfin correlation enables pattern discovery

The Council's wisdom guided us toward centralized perception with distributed cognition - the tribe gains eyes that see in depth.

---

## References

- [erget/StereoVision](https://github.com/erget/StereoVision) - 3D reconstruction library
- [sourishg/stereo-calibration](https://github.com/sourishg/stereo-calibration) - Calibration tools
- [aliyasineser/stereoDepth](https://github.com/aliyasineser/stereoDepth) - Depth estimation
- [tsightler/ring-mqtt](https://github.com/tsightler/ring-mqtt) - Ring bridge
- [Scrypted](https://www.scrypted.app/) - Camera bridge platform
- OpenCV Stereo Documentation

---

*Generated by Ultrathink Protocol - Cherokee AI Federation TPM*
