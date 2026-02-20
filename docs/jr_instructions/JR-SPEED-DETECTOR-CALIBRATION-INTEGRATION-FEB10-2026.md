# Jr Instruction: Integrate Calibration into Speed Detector

**Task ID:** VISION-CAL-002
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Date:** February 10, 2026
**Depends On:** camera_calibration.py (already created)

## Context

`/ganuda/lib/camera_calibration.py` was created by Jr #680. This instruction integrates it into the speed detector via 4 SEARCH/REPLACE edits.

## Edit 1: Add calibration import

File: `/ganuda/services/vision/speed_detector.py`

```
<<<<<<< SEARCH
from lib.amcrest_camera import AmcrestCamera
from lib.secrets_loader import get_db_config
=======
from lib.amcrest_camera import AmcrestCamera
from lib.secrets_loader import get_db_config
from lib.camera_calibration import CameraCalibrator
>>>>>>> REPLACE
```

## Edit 2: Add calibrator to init

File: `/ganuda/services/vision/speed_detector.py`

```
<<<<<<< SEARCH
        self.camera = AmcrestCamera(CAMERA_ID, stream="sub")
        self.model = YOLO(YOLO_MODEL)
        self.db_config = get_db_config()
=======
        self.camera = AmcrestCamera(CAMERA_ID, stream="sub")
        self.model = YOLO(YOLO_MODEL)
        self.db_config = get_db_config()
        self.calibrator = CameraCalibrator(CAMERA_ID)
>>>>>>> REPLACE
```

## Edit 3: Replace speed calculation with calibrated version

File: `/ganuda/services/vision/speed_detector.py`

```
<<<<<<< SEARCH
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
=======
    def _calculate_speed(self, track_id: int) -> float:
        """Calculate speed in mph from tracked positions using calibrated ground distance."""
        positions = self.tracks.get(track_id, [])
        if len(positions) < 3:
            return 0.0

        recent = positions[-5:]
        if len(recent) < 2:
            return 0.0

        dt = recent[-1][2] - recent[0][2]
        if dt < 0.1:
            return 0.0

        # Try calibrated ground distance first
        if self.calibrator.K is not None:
            total_m = 0.0
            for i in range(1, len(recent)):
                d = self.calibrator.ground_distance(
                    (recent[i-1][0], recent[i-1][1]),
                    (recent[i][0], recent[i][1])
                )
                if d is not None:
                    total_m += d
                else:
                    # Fallback to flat PPM for this segment
                    dx = recent[i][0] - recent[i-1][0]
                    dy = recent[i][1] - recent[i-1][1]
                    total_m += (dx**2 + dy**2)**0.5 / PIXELS_PER_METER

            meters_per_sec = total_m / dt
        else:
            # No calibration — use flat PPM (original behavior)
            total_px = 0.0
            for i in range(1, len(recent)):
                dx = recent[i][0] - recent[i-1][0]
                dy = recent[i][1] - recent[i-1][1]
                total_px += (dx**2 + dy**2)**0.5
            meters_per_sec = (total_px / dt) / PIXELS_PER_METER

        mph = meters_per_sec * 2.237
        return round(mph, 1)
>>>>>>> REPLACE
```

## Edit 4: Add frame undistortion before detection

File: `/ganuda/services/vision/speed_detector.py`

```
<<<<<<< SEARCH
            # Run YOLO with tracking
            results = self.model.track(
=======
            # Undistort frame before detection (corrects barrel distortion)
            frame = self.calibrator.undistort(frame)

            # Run YOLO with tracking
            results = self.model.track(
>>>>>>> REPLACE
```

## Do NOT

- Do not modify camera_calibration.py (already created and verified)
- Do not run any manual calibration commands
- Do not create any new files — only edit speed_detector.py
