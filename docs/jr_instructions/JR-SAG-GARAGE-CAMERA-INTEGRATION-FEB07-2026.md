# Jr Instruction: Add Garage Camera to SAG Unified Interface

**Task ID:** SAG-GARAGE-CAM-001
**Priority:** P1
**Date:** February 7, 2026
**Node:** redfin (192.168.132.223)
**Assigned:** Software Engineer Jr.
**Depends On:** CAMERA-TUNNEL-001 (greenfin iptables tunnel - COMPLETED)

## Overview

Add the new garage Amcrest camera to the SAG Unified Interface camera grid. The camera is physically on the IoT network (10.0.0.123) but tunneled through greenfin (192.168.132.224) on non-standard ports. The frontend dynamically renders cameras from CAMERA_CONFIG, so this is primarily a backend change with one code fix for non-standard HTTP ports.

## Camera Details

| Field | Value |
|-------|-------|
| Model | Amcrest IP5M-T1179EW-AI-V3 |
| Serial | AMC1086CA4E221E066 |
| Physical IP | 10.0.0.123 (IoT network) |
| Tunneled via | greenfin (192.168.132.224) |
| HTTP port | 18080 (tunneled from camera:80) |
| RTSP port | 10554 (tunneled from camera:554) |
| Credentials | admin / jawaseatlasers2 |
| Resolution | 5MP |
| Location | Garage overhead |

## Network Path

```
SAG (redfin:4000) → HTTP → greenfin:18080 → DNAT → 10.0.0.123:80
                  → RTSP → greenfin:10554 → DNAT → 10.0.0.123:554
```

## Step 1: Add Garage Camera to CAMERA_CONFIG

**File:** `/ganuda/home/dereadi/sag_unified_interface/app.py`
**Location:** `CAMERA_CONFIG` dict (approximately line 2640)

Add the following entry after the `ring_doorbell` entry (before the closing `}`):

```python
    'garage': {
        'id': 'garage',
        'name': 'Garage Overhead',
        'ip': '192.168.132.224',       # Via greenfin tunnel
        'port': 18080,                  # Tunneled HTTP port (not standard 80)
        'rtsp_port': 10554,             # Tunneled RTSP port
        'purpose': 'Driveway / Package Detection',
        'specialist': 'Eagle Eye',
        'features': ['vehicle_tracking', 'package_detection', 'ai_detection', '5mp'],
        'type': 'amcrest',
        'stream_path': '/cam/realmonitor?channel=1&subtype=0',
    },
```

## Step 2: Update get_amcrest_camera() for Non-Standard Ports

**File:** `/ganuda/home/dereadi/sag_unified_interface/app.py`
**Function:** `get_amcrest_camera()` (approximately line 2672)

The current code hardcodes port 80:
```python
def get_amcrest_camera(camera_id):
    """Get Amcrest camera instance."""
    from amcrest import AmcrestCamera
    if camera_id not in CAMERA_CONFIG:
        return None
    cam_cfg = CAMERA_CONFIG[camera_id]
    password = os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
    return AmcrestCamera(cam_cfg['ip'], 80, 'admin', password).camera
```

Change the hardcoded `80` to read from the config, defaulting to 80:
```python
def get_amcrest_camera(camera_id):
    """Get Amcrest camera instance."""
    from amcrest import AmcrestCamera
    if camera_id not in CAMERA_CONFIG:
        return None
    cam_cfg = CAMERA_CONFIG[camera_id]
    password = os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
    port = cam_cfg.get('port', 80)
    return AmcrestCamera(cam_cfg['ip'], port, 'admin', password).camera
```

This is the **only code change** needed. The existing `/api/cameras/<id>/snapshot` endpoint, camera grid JS in `control-room.js`, and all other camera API endpoints will automatically pick up the new camera from CAMERA_CONFIG.

## Step 3: Skip Ring Doorbell in Amcrest Calls

Check that existing camera API endpoints handle the `ring_doorbell` camera type gracefully. The Ring camera has `'type': 'ring'` and should not be passed to `get_amcrest_camera()`. Verify the `/api/cameras/<camera_id>/snapshot` endpoint handles this. If it tries to create an AmcrestCamera for the Ring and fails, add a guard:

```python
if cam_cfg.get('type') == 'ring':
    # Ring cameras use different snapshot mechanism
    return jsonify({'error': 'Ring camera snapshots not supported via Amcrest API'}), 400
```

Only add this guard if it doesn't already exist.

## Step 4: Restart SAG Service

```bash
# On redfin:
sudo systemctl restart sag-unified
# Or however the SAG service is managed. Check:
sudo systemctl list-units | grep sag
```

## Step 5: Verify

### 5.1: API Check
```bash
# Camera list should include garage
curl -s http://localhost:4000/api/cameras | python3 -m json.tool

# Garage camera info
curl -s http://localhost:4000/api/cameras/garage/info | python3 -m json.tool

# Live snapshot (should return JPEG)
curl -s -o /tmp/garage_test.jpg http://localhost:4000/api/cameras/garage/snapshot
file /tmp/garage_test.jpg
# Expected: JPEG image data
```

### 5.2: Browser Check
Open http://192.168.132.223:4000/ in browser, navigate to Tribal Vision / Cameras view. The garage camera should appear as a fourth card in the grid with a live thumbnail.

### 5.3: Verify All Cameras Still Work
```bash
# Existing cameras should still respond
curl -s -o /dev/null -w '%{http_code}' http://localhost:4000/api/cameras/office_pii/snapshot
curl -s -o /dev/null -w '%{http_code}' http://localhost:4000/api/cameras/traffic/snapshot
# Expected: 200 for both
```

## Rollback

If the garage camera causes issues, simply remove the `'garage'` entry from CAMERA_CONFIG and revert the `get_amcrest_camera()` port change. Restart SAG.

## CMDB Update

After verification, insert into thermal_memory_archive:
```
Type: cmdb_entry
Summary: Garage camera (Amcrest IP5M-T1179EW-AI-V3, serial AMC1086CA4E221E066) added to SAG camera grid. Tunneled via greenfin:18080 (HTTP) and greenfin:10554 (RTSP). Camera IP 10.0.0.123 on IoT network.
```

## Security Notes

- Camera credentials use the fleet standard password via CHEROKEE_DB_PASS env var
- All traffic routes through greenfin NAT tunnel - no direct IoT network exposure
- Crawdad review: No new external network exposure, SAG is internal-only

---
**FOR SEVEN GENERATIONS** - Four eyes watching, one cluster seeing.
