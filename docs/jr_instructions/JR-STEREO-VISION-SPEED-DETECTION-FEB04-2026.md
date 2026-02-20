# JR-STEREO-VISION-SPEED-DETECTION-FEB04-2026

## Priority: P2
## Assignee: Vision Jr.
## Estimated Effort: 8-12 hours (multi-phase)

## Context

Chief is installing 2-3 Amcrest cameras:
- One outside the office
- One over the garage
- (Possibly a third)

Goal: **Stereo vision speed detection** — use two cameras with known baseline to triangulate 3D position of moving objects and calculate speed.

Existing infrastructure in `/ganuda/lib/`:
- `vehicle_tracker.py` — centroid-based tracking
- `camera_vision_processor.py` — frame processing pipeline
- `enhanced_vision_processor.py` — extended processing
- `bytetrack_tracker.py` — advanced multi-object tracking

## Deliverables

### Phase 1: Amcrest Integration

**1.1 RTSP Stream Handler**

Amcrest cameras expose RTSP streams. Create `/ganuda/lib/amcrest_camera.py`:

```python
class AmcrestCamera:
    """Handle Amcrest camera RTSP streams."""
    
    def __init__(self, ip: str, username: str, password: str, channel: int = 1):
        self.rtsp_url = f"rtsp://{username}:{password}@{ip}:554/cam/realmonitor?channel={channel}&subtype=0"
        
    def get_frame(self) -> np.ndarray:
        """Capture single frame from RTSP stream."""
        
    def stream_frames(self) -> Generator[np.ndarray, None, None]:
        """Yield frames continuously."""
```

**1.2 Camera Registry**

Add Amcrest cameras to `/ganuda/config/camera_registry.yaml`:

```yaml
cameras:
  office_exterior:
    type: amcrest
    ip: 192.168.X.X  # TBD after installation
    location: "outside office"
    role: stereo_left  # or stereo_right
    
  garage_overhead:
    type: amcrest
    ip: 192.168.X.X
    location: "over garage"
    role: stereo_right
```

### Phase 2: Stereo Calibration

**2.1 Calibration Module**

Create `/ganuda/lib/stereo_calibration.py`:

- Capture checkerboard pattern from both cameras
- Calculate intrinsic matrices (focal length, principal point, distortion)
- Calculate extrinsic matrices (rotation, translation between cameras)
- Store calibration in `/ganuda/config/stereo_calibration.json`

**2.2 Baseline Measurement**

Chief must measure:
- Physical distance between camera centers (baseline)
- Camera mounting angles
- Height above ground

Store in calibration config for 3D reconstruction.

### Phase 3: Synchronized Capture

**3.1 Frame Synchronization**

Create `/ganuda/lib/stereo_capture.py`:

```python
class StereoCapture:
    """Synchronized capture from stereo camera pair."""
    
    def __init__(self, left_cam: AmcrestCamera, right_cam: AmcrestCamera):
        self.left = left_cam
        self.right = right_cam
        
    def capture_pair(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """Capture synchronized frame pair with timestamp."""
        # Use threading to minimize time delta
        # Return (left_frame, right_frame, timestamp)
```

Amcrest cameras may have 50-100ms latency variance. Options:
- Accept small desync for slow-moving objects
- Use NTP sync on cameras if supported
- Timestamp-based frame matching from buffer

### Phase 4: 3D Position Estimation

**4.1 Stereo Matching**

Create `/ganuda/lib/stereo_matcher.py`:

- Detect objects in both frames (YOLO or similar)
- Match corresponding objects between views
- Calculate disparity for each matched object

**4.2 Triangulation**

```python
def triangulate_position(
    left_point: Tuple[int, int],
    right_point: Tuple[int, int],
    calibration: StereoCalibration
) -> Tuple[float, float, float]:
    """
    Calculate 3D world position from stereo correspondence.
    Returns (x, y, z) in meters from camera baseline center.
    """
    disparity = left_point[0] - right_point[0]
    depth = (calibration.baseline * calibration.focal_length) / disparity
    # ... full triangulation math
```

### Phase 5: Speed Calculation

**5.1 Velocity Tracker**

Create `/ganuda/lib/stereo_speed_tracker.py`:

```python
class StereoSpeedTracker:
    """Track objects in 3D space and calculate velocity."""
    
    def __init__(self, calibration: StereoCalibration):
        self.calibration = calibration
        self.tracks: Dict[int, List[Position3D]] = {}
        
    def update(self, left_frame, right_frame, timestamp) -> Dict[int, Speed]:
        """
        Process stereo pair, update tracks, return speeds.
        Speed in mph/kph based on config.
        """
        
    def get_speed(self, track_id: int) -> float:
        """Calculate speed from position history."""
        # Use last N positions
        # Linear regression or average velocity
        # Convert m/s to mph
```

**5.2 Speed Accuracy**

Factors affecting accuracy:
- Calibration quality
- Frame sync precision
- Object detection consistency
- Distance from cameras (accuracy degrades with range)

Target: ±2 mph accuracy at 50ft range.

### Phase 6: Integration

**6.1 Daemon Service**

Create `/ganuda/scripts/systemd/stereo-speed.service`:

- Run continuously
- Log all speed detections to database
- Alert on threshold exceedance (e.g., >25 mph in residential zone)

**6.2 Database Schema**

```sql
CREATE TABLE stereo_speed_detections (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    track_id INTEGER NOT NULL,
    speed_mph DECIMAL(5,1),
    position_x DECIMAL(8,2),
    position_y DECIMAL(8,2),
    position_z DECIMAL(8,2),
    confidence DECIMAL(3,2),
    camera_pair VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_speed_timestamp ON stereo_speed_detections(timestamp);
CREATE INDEX idx_speed_value ON stereo_speed_detections(speed_mph);
```

**6.3 SAG UI Integration**

Add to SAG dashboard:
- Real-time speed display
- Historical speed chart
- Speed heatmap by time of day
- Alert log

## Hardware Requirements

- 2x Amcrest cameras (IP, PoE recommended)
- Known baseline distance (measure after installation)
- Network connectivity to processing node
- GPU recommended for real-time object detection

## Processing Node

Recommend running on:
- **redfin** if GPU needed for YOLO inference
- **sasass2** M4 Max for MLX-based detection

## Dependencies

- OpenCV with stereo support
- NumPy, SciPy
- YOLO or similar object detector
- Existing `/ganuda/lib/` modules

## Verification

1. Single camera RTSP stream works
2. Stereo calibration produces valid parameters
3. Frame sync achieves <100ms delta
4. Static object at known distance triangulates correctly
5. Moving object speed matches radar gun (if available) or GPS speedometer

## References

### Existing Infrastructure
- `/ganuda/lib/vehicle_tracker.py` — centroid tracking
- `/ganuda/lib/camera_vision_processor.py` — frame pipeline
- `/ganuda/lib/bytetrack_tracker.py` — multi-object tracking
- Thermal memory: Vision Jr camera work from Dec 2025

### Study Material: AlexJinlei/Stereo_Vision_Camera

**Repository:** https://github.com/AlexJinlei/Stereo_Vision_Camera

**Status:** Reference only — DO NOT clone and run. Study algorithms, adapt for our stack.

**Why it's useful:**
- OpenCV-based stereo calibration workflow (Phase 2)
- Depth map generation via stereo matching (Phase 4)
- 3D reconstruction from disparity calculation (Phase 4)
- Cross-laser hardware alignment method (calibration technique)
- Working example: 120mm baseline, 1-10m effective range

**Key differences from our setup:**
| Their Setup | Our Setup |
|-------------|-----------|
| ELP USB cameras | Amcrest IP cameras (RTSP) |
| Direct V4L2 capture | Network stream capture |
| 120mm baseline | TBD after installation |
| Drone application | Fixed installation speed detection |

**Files to study:**
- `stereo_cam_opencv/` — Python calibration and depth algorithms
- Calibration workflow documentation
- Disparity-to-depth calculation

**What to extract:**
1. Checkerboard calibration procedure
2. Stereo rectification math
3. Disparity calculation approach
4. Depth-from-disparity formula

**What NOT to use:**
- V4L2 USB capture code (we use RTSP)
- Their camera-specific parameters
- Any hardcoded values

This is algorithm reference, not a library to install.

---
*Cherokee AI Federation — Vision*
*ᎠᏂᎦᏔᎲᏍᎩ ᎤᏂᎪᎵᏰᏗ — Eyes that measure*
