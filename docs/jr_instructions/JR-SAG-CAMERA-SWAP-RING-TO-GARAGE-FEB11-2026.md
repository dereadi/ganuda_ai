# Jr Instruction: SAG Camera Swap — Ring Doorbell to Garage Cam

**Task**: Replace Ring Doorbell camera with Garage Cam in SAG Unified Interface
**Priority**: P2
**Assigned Jr**: Software Engineer Jr
**Date**: February 11, 2026

## Context

The SAG Unified Interface at port 4000 has a hardcoded `ring_doorbell` camera entry in `CAMERA_CONFIG` that is no longer in use. The Ring doorbell was removed from the fleet. The garage camera (Amcrest, tunneled through greenfin at 192.168.132.224) needs to replace it.

Additionally, the Ring entry has a hardcoded RTSP password in the URL which is a security concern.

## Target File

`/ganuda/home/dereadi/sag_unified_interface/app.py`

## Step 1: Replace ring_doorbell with garage in CAMERA_CONFIG

File: `/ganuda/home/dereadi/sag_unified_interface/app.py`

```
<<<<<<< SEARCH
    'ring_doorbell': {
        'id': 'ring_doorbell',
        'name': 'Ring Front Door',
        'ip': '192.168.132.222',
        'rtsp_url': 'rtsp://ring:tribal_vision_2026@192.168.132.222:8554/d436398fc2b8_live',
        'purpose': 'Entry Detection / Stereo Vision',
        'specialist': 'Eagle Eye',
        'features': ['doorbell', 'person_detection', 'stereo_vision', 'on_demand'],
        'type': 'ring',
        'stereo_partner': 'traffic',
        'on_demand': True,
    },
=======
    'garage': {
        'id': 'garage',
        'name': 'Garage Monitor',
        'ip': '10.0.0.123',
        'tunnel_host': '192.168.132.224',
        'tunnel_http_port': 18080,
        'tunnel_rtsp_port': 10554,
        'purpose': 'Speed Detection / Garage Security',
        'specialist': 'Eagle Eye',
        'features': ['vehicle_tracking', 'speed_detection', 'ai_detection', '5mp'],
        'stereo_partner': 'traffic',
    },
>>>>>>> REPLACE
```

## Step 2: Update traffic camera stereo_partner reference

File: `/ganuda/home/dereadi/sag_unified_interface/app.py`

```
<<<<<<< SEARCH
        'stereo_partner': 'ring_doorbell',
=======
        'stereo_partner': 'garage',
>>>>>>> REPLACE
```

## Step 3: Add garage to gallery camera filter dropdown

File: `/ganuda/home/dereadi/sag_unified_interface/templates/index.html`

```
<<<<<<< SEARCH
                            <option value="office_pii">Office PII</option>
                            <option value="traffic">Traffic</option>
=======
                            <option value="office_pii">Office PII</option>
                            <option value="traffic">Traffic</option>
                            <option value="garage">Garage</option>
>>>>>>> REPLACE
```

## Step 4: Remove Ring API endpoints (cleanup)

File: `/ganuda/home/dereadi/sag_unified_interface/app.py`

```
<<<<<<< SEARCH
# ==================== RING DOORBELL ENDPOINTS ====================

@app.route('/api/home-hub/ring/doorbells')
def api_ring_doorbells():
    """Get Ring doorbells."""
    import sys
    sys.path.insert(0, '/ganuda/services/device_control/venv/lib/python3.12/site-packages')
    sys.path.insert(0, '/ganuda/services/device_control')

    try:
        from ring_api import get_doorbells
        doorbells = get_doorbells()
        return jsonify({'doorbells': doorbells, 'count': len(doorbells)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/home-hub/ring/cameras')
def api_ring_cameras():
    """Get Ring cameras."""
    import sys
    sys.path.insert(0, '/ganuda/services/device_control/venv/lib/python3.12/site-packages')
    sys.path.insert(0, '/ganuda/services/device_control')

    try:
        from ring_api import get_cameras
        cameras = get_cameras()
        return jsonify({'cameras': cameras, 'count': len(cameras)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
=======
# Ring doorbell endpoints REMOVED Feb 11, 2026 — Ring no longer in fleet
>>>>>>> REPLACE
```

## Manual Step (TPM/sudo)

After Jr applies changes:
```text
sudo systemctl restart sag
```

## Verification

1. Navigate to http://192.168.132.223:4000/
2. Click "Cameras" tab
3. Verify garage camera appears instead of Ring doorbell
4. Click "Gallery" tab — verify garage option in dropdown
5. Verify no hardcoded passwords in CAMERA_CONFIG
