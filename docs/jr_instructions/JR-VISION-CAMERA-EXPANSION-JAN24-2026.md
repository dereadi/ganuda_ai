# Jr Instruction: Camera Fleet Expansion & Credentials Vault Migration

**Task ID:** VISION-CAMS-001
**Priority:** P1
**Date:** January 24, 2026
**Target Date:** Thursday January 30, 2026 (hardware install)

## Overview

1. Migrate camera credentials to Silverfin vault
2. Prepare for camera fleet expansion (3 new cameras)
3. Replace Ring doorbell with Amcrest doorbell

## Current Camera Fleet

| Camera | IP | Type | Location |
|--------|-----|------|----------|
| office_pii | 192.168.132.181 | Amcrest 5MP | Office |
| traffic | 192.168.132.182 | Amcrest 5MP | Front (road view) |
| ring_doorbell | 192.168.132.222 (via bluefin) | Ring | Front door |

## Planned Camera Fleet (Post-Thursday)

| Camera | IP | Type | Location |
|--------|-----|------|----------|
| office_pii | 192.168.132.181 | Amcrest 5MP | Office |
| traffic | 192.168.132.182 | Amcrest 5MP | Front (road view) |
| doorbell | TBD | Amcrest Doorbell | Front door (replaces Ring) |
| garage | TBD | Amcrest | Over garage |
| backyard | TBD | Amcrest | Backyard |

---

## Part 1: Vault Credentials Setup

### 1.1 Add Camera Credentials to Silverfin Vault

SSH to silverfin and add secrets:

```bash
kinit admin

# Camera credentials (Amcrest fleet)
echo "tribal_vision_2026" | ipa vault-archive cherokee-ai-secrets --name=amcrest_camera_password --in=-

# Ring credentials (temporary - removing Thursday)
echo "tribal_vision_2026" | ipa vault-archive cherokee-ai-secrets --name=ring_mqtt_password --in=-

# Verify
ipa vault-show cherokee-ai-secrets
```

### 1.2 Create Camera Credential Retrieval Module

**File:** `/ganuda/lib/tribal_vision/camera_config.py`

```python
"""
Centralized camera configuration for Tribal Vision.

Credentials from Silverfin vault, camera registry from database.
"""
import os
import subprocess
import logging
from functools import lru_cache
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def _get_vault_secret(secret_name: str) -> Optional[str]:
    """Retrieve secret from Silverfin FreeIPA vault."""
    try:
        result = subprocess.run(
            ["/ganuda/scripts/get-vault-secret.sh", secret_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        logger.warning(f"Vault retrieval failed for {secret_name}: {e}")
    return None


@lru_cache()
def get_amcrest_password() -> str:
    """Get Amcrest camera password from vault."""
    password = _get_vault_secret("amcrest_camera_password")
    if not password:
        password = os.environ.get("AMCREST_CAM_PASSWORD")
    if not password:
        raise ValueError("Amcrest camera password not available from vault or env")
    return password


@lru_cache()
def get_ring_password() -> str:
    """Get Ring MQTT password from vault (temporary - until Thursday)."""
    password = _get_vault_secret("ring_mqtt_password")
    if not password:
        password = os.environ.get("RING_MQTT_PASSWORD")
    if not password:
        raise ValueError("Ring MQTT password not available from vault or env")
    return password


# Camera registry - IPs assigned via DHCP reservation on greenfin
CAMERA_REGISTRY = {
    'office_pii': {
        'id': 'office_pii',
        'name': 'Office PII Monitor',
        'ip': '192.168.132.181',
        'type': 'amcrest',
        'purpose': 'Face Detection / Security',
        'specialist': 'Crawdad',
        'features': ['face_detection', 'person_alert', 'ai_detection', '5mp'],
        'stream_path': '/cam/realmonitor?channel=1&subtype=0',
    },
    'traffic': {
        'id': 'traffic',
        'name': 'Traffic Monitor',
        'ip': '192.168.132.182',
        'type': 'amcrest',
        'purpose': 'Vehicle Identification / Snow Gauge',
        'specialist': 'Eagle Eye',
        'features': ['vehicle_tracking', 'license_plate', 'snow_gauge', '5mp'],
        'stream_path': '/cam/realmonitor?channel=1&subtype=1',
        'stereo_partner': 'doorbell',
    },
    'doorbell': {
        'id': 'doorbell',
        'name': 'Front Door',
        'ip': None,  # TBD - will be assigned Thursday
        'type': 'amcrest_doorbell',
        'purpose': 'Entry Detection / Stereo Vision',
        'specialist': 'Eagle Eye',
        'features': ['doorbell', 'person_detection', 'stereo_vision', 'two_way_audio'],
        'stream_path': '/cam/realmonitor?channel=1&subtype=0',
        'stereo_partner': 'traffic',
    },
    'garage': {
        'id': 'garage',
        'name': 'Garage Overhead',
        'ip': None,  # TBD - will be assigned Thursday
        'type': 'amcrest',
        'purpose': 'Driveway / Package Detection',
        'specialist': 'Eagle Eye',
        'features': ['vehicle_tracking', 'package_detection', '5mp'],
        'stream_path': '/cam/realmonitor?channel=1&subtype=0',
    },
    'backyard': {
        'id': 'backyard',
        'name': 'Backyard',
        'ip': None,  # TBD - will be assigned Thursday
        'type': 'amcrest',
        'purpose': 'Wildlife / Security',
        'specialist': 'Eagle Eye',
        'features': ['wildlife_detection', 'person_alert', '5mp'],
        'stream_path': '/cam/realmonitor?channel=1&subtype=0',
    },
}


def get_rtsp_url(camera_id: str) -> str:
    """Build RTSP URL for camera with credentials from vault."""
    cam = CAMERA_REGISTRY.get(camera_id)
    if not cam:
        raise ValueError(f"Unknown camera: {camera_id}")

    if not cam['ip']:
        raise ValueError(f"Camera {camera_id} IP not yet assigned")

    if cam['type'] == 'ring':
        # Ring uses different auth via ring-mqtt
        password = get_ring_password()
        return f"rtsp://ring:{password}@192.168.132.222:8554/{cam.get('ring_device_id', 'unknown')}_live"
    else:
        # All Amcrest cameras use same credentials
        password = get_amcrest_password()
        return f"rtsp://admin:{password}@{cam['ip']}:554{cam['stream_path']}"


def get_active_cameras() -> Dict[str, Any]:
    """Get all cameras with assigned IPs."""
    return {k: v for k, v in CAMERA_REGISTRY.items() if v['ip'] is not None}
```

---

## Part 2: Update Existing Files

### 2.1 Update tribal_vision.py

**File:** `/ganuda/services/vision/tribal_vision.py`

Replace hardcoded CAMERAS dict with:

```python
from lib.tribal_vision.camera_config import get_rtsp_url, get_active_cameras, CAMERA_REGISTRY

# Remove old CAMERAS dict and get_cam_password()
# Use get_active_cameras() and get_rtsp_url() instead
```

### 2.2 Update SAG app.py

**File:** `/ganuda/home/dereadi/sag_unified_interface/app.py`

Replace CAMERA_CONFIG around line 2635 with import from camera_config module:

```python
from lib.tribal_vision.camera_config import CAMERA_REGISTRY, get_rtsp_url

# Update CAMERA_CONFIG to use CAMERA_REGISTRY
# Replace hardcoded rtsp_url with get_rtsp_url() calls
```

### 2.3 Update snow_timelapse.py

Ensure it uses the new camera_config module.

---

## Part 3: DHCP Reservations

When new cameras arrive Thursday, add DHCP reservations on greenfin:

```bash
# On greenfin router
# Edit /etc/dhcp/dhcpd.conf or dnsmasq.conf

# Suggested IPs (VLAN 132 - IoT):
# doorbell:  192.168.132.183
# garage:    192.168.132.184
# backyard:  192.168.132.185
```

Then update `CAMERA_REGISTRY` IPs.

---

## Part 4: Ring Removal

After Amcrest doorbell is installed Thursday:

1. Remove `ring_doorbell` from CAMERA_REGISTRY
2. Remove ring-mqtt service from bluefin (if no longer needed)
3. Remove `ring_mqtt_password` from vault
4. Update stereo_partner references to point to new `doorbell`

---

## Testing Checklist

- [ ] Vault secrets created on Silverfin
- [ ] `get_amcrest_password()` retrieves from vault
- [ ] All active cameras have working RTSP URLs
- [ ] SAG cameras page shows all cameras
- [ ] No hardcoded passwords in grep search
- [ ] Snow timelapse continues working

## Post-Thursday Checklist

- [ ] New camera IPs assigned and added to registry
- [ ] All 5 cameras visible in SAG
- [ ] Stereo vision working with new doorbell
- [ ] Ring-mqtt removed
- [ ] Motion detection on all cameras

---

**FOR SEVEN GENERATIONS** - Five eyes watching, one cluster seeing.
