# Jr Instruction: Speed Detector EOF Cleanup

**Task ID:** VISION-CLEANUP-001
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Date:** February 10, 2026

## Context

A previous Jr run partially applied lens calibration edits to `speed_detector.py`, leaving duplicate import lines appended after `if __name__`. These garbage lines must be removed before the calibration instruction can be re-applied cleanly.

## Edit 1: Remove garbage duplicate imports at end of file

File: `/ganuda/services/vision/speed_detector.py`

```
<<<<<<< SEARCH
if __name__ == "__main__":
    detector = SpeedDetector()
    detector.run()
from lib.amcrest_camera import AmcrestCamera
from lib.secrets_loader import get_db_config


from lib.amcrest_camera import AmcrestCamera
from lib.secrets_loader import get_db_config
from lib.camera_calibration import CameraCalibrator

=======
if __name__ == "__main__":
    detector = SpeedDetector()
    detector.run()
>>>>>>> REPLACE
```

## Do NOT

- Do not modify any other part of speed_detector.py
- Do not modify camera_calibration.py
- This is strictly a cleanup of corrupted trailing lines
