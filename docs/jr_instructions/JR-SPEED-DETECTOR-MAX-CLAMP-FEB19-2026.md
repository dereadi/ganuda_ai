# Jr Instruction: Add Max Speed Clamp to Speed Detector

**Task ID**: SPEED-CLAMP-001
**Priority**: 3 (medium)
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 1
**use_rlm**: false

## Context

The garage camera speed detector is producing impossible readings (4126 mph, 8723 mph) in thermal memory. These occur when YOLO tracking produces a large pixel displacement in a short time window (e.g., a vehicle ID reassignment or detection jump between frames). The `_calculate_speed()` method has a minimum dt guard (0.1s) but no maximum speed clamp. Residential cul-de-sac vehicles cannot exceed ~80 mph in any realistic scenario.

## Step 1: Add MAX_SPEED_MPH constant

File: `/ganuda/services/vision/speed_detector.py`

<<<<<<< SEARCH
SPEED_ALERT_MPH = float(os.environ.get("SPEED_ALERT_MPH", "25"))
=======
SPEED_ALERT_MPH = float(os.environ.get("SPEED_ALERT_MPH", "25"))
MAX_SPEED_MPH = float(os.environ.get("MAX_SPEED_MPH", "120"))  # Physical clamp — reject tracking artifacts
>>>>>>> REPLACE

## Step 2: Clamp speed in _calculate_speed

File: `/ganuda/services/vision/speed_detector.py`

<<<<<<< SEARCH
        mph = meters_per_sec * 2.237
        return round(mph, 1)
=======
        mph = meters_per_sec * 2.237
        if mph > MAX_SPEED_MPH:
            logger.debug(f"Speed clamp: {mph:.1f} mph exceeds {MAX_SPEED_MPH} mph — tracking artifact, returning 0")
            return 0.0
        return round(mph, 1)
>>>>>>> REPLACE

## Manual Steps (TPM)

1. On redfin: `sudo systemctl restart speed-detector` (if running)
2. Monitor thermal memory for absurd readings — they should stop
