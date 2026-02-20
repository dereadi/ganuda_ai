# KB: Tribal Vision Camera Authentication Fix

**Date**: February 10, 2026
**Thermal**: Pending
**Kanban**: Related to camera fleet password rotation (#645)
**Severity**: P1 — 3 days of lost detection data

## Problem

`tribal-vision.service` stopped logging detections on February 7, 2026. After a system reboot on February 9, the service started but immediately failed with `401 Unauthorized` on both RTSP camera streams.

## Root Cause

Camera fleet passwords were rotated on February 9, 2026 (Jr #645). Per-camera passwords were stored in:
- `/ganuda/config/secrets.env` as `CAMERA_OFFICE_PII_PASSWORD`, `CAMERA_TRAFFIC_PASSWORD`, `CAMERA_GARAGE_PASSWORD`
- FreeIPA KRA vault on silverfin as `cherokee-camera-credentials`
- `/ganuda/config/camera_registry.yaml` documenting the `password_env` field per camera

However, `tribal_vision.py` still used a single `get_cam_password()` function that read `CHEROKEE_DB_PASS` (the database password) for RTSP authentication. After the DB password rotation on Feb 6 and camera password rotation on Feb 9, these diverged.

## Fix Applied

Updated `get_cam_password()` in `/ganuda/services/vision/tribal_vision.py` to accept a `cam_key` parameter and look up per-camera env vars:

```
get_cam_password("office_pii") → CAMERA_OFFICE_PII_PASSWORD
get_cam_password("traffic")    → CAMERA_TRAFFIC_PASSWORD
get_cam_password("garage")     → CAMERA_GARAGE_PASSWORD
get_cam_password()             → CHEROKEE_DB_PASS (fallback)
```

CAMERAS dict updated to pass the camera key to each RTSP URL construction.

## Lesson Learned

**When rotating credentials for any service, audit ALL consumers of those credentials.** The camera_registry.yaml correctly documented the new env var pattern, but tribal_vision.py was not updated to read from it. The speed_detector.py was unaffected because it doesn't use RTSP directly.

**Credential rotation checklist for cameras:**
1. Rotate passwords on physical cameras
2. Update `/ganuda/config/secrets.env`
3. Update FreeIPA vault
4. Update `/ganuda/config/camera_registry.yaml`
5. Update ALL scripts/services that connect to cameras:
   - `tribal_vision.py` (tribal-vision.service)
   - `speed_detector.py` (if it ever uses RTSP)
   - Any ad-hoc scripts in `/ganuda/scripts/`
6. Restart affected services
7. Verify detections flowing to thermal_memory_archive

## Impact

- ~40,952 total vision detections before outage
- 3 days of lost detection data (Feb 7-10)
- Darrell + Eddie walked past cameras undetected on Feb 10

## Related

- KB-PASSWORD-ROTATION-CASCADE-FEB08-2026.md
- KB-FREEIPA-KRA-VAULT-DEPLOYMENT-FEB10-2026.md
- camera_registry.yaml — canonical camera credential mapping
