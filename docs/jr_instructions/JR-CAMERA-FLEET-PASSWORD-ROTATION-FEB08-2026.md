# Jr Instruction: Camera Fleet Password Rotation

**Task ID:** CAM-ROTATE-001
**Priority:** P1 (security hygiene)
**Date:** February 8, 2026
**Node:** greenfin (192.168.132.224) — camera gateway
**Assigned:** Security Jr.

## Overview

All three Amcrest cameras currently use the same password (`jawaseatlasers2`) which is the OLD default we set originally. This password is also the old database password that was rotated on Feb 6. Rotate all camera passwords to unique, strong credentials and update all consuming services.

## Camera Inventory

| Camera | IP | Current User | Current Pass | Access Via |
|--------|-----|-------------|-------------|------------|
| office_pii | 192.168.132.182 | admin | jawaseatlasers2 | Direct LAN |
| traffic | 192.168.132.183 | admin | jawaseatlasers2 | Direct LAN |
| garage | 10.0.0.123 | admin | jawaseatlasers2 | Via greenfin tunnel (18080/10554) |

## Phase 1: Generate New Passwords

### Step 1.1: Generate 3 unique passwords

```bash
# On any node with openssl:
openssl rand -base64 24  # → camera_office_pii password
openssl rand -base64 24  # → camera_traffic password
openssl rand -base64 24  # → camera_garage password
```

Record these securely. They will be stored in secrets.env and eventually in the SAG secrets vault.

## Phase 2: Rotate Camera Passwords

### Step 2.1: Rotate office_pii camera (192.168.132.182)

```bash
# Test current credentials
curl --digest -u admin:jawaseatlasers2 "http://192.168.132.182/cgi-bin/magicBox.cgi?action=getSerialNo"

# Change password via Amcrest API
curl --digest -u admin:jawaseatlasers2 \
    "http://192.168.132.182/cgi-bin/userManager.cgi?action=modifyPassword&name=admin&pwd=NEW_OFFICE_PII_PASSWORD&pwdOld=jawaseatlasers2"

# Verify new credentials
curl --digest -u admin:NEW_OFFICE_PII_PASSWORD "http://192.168.132.182/cgi-bin/magicBox.cgi?action=getSerialNo"
```

### Step 2.2: Rotate traffic camera (192.168.132.183)

```bash
curl --digest -u admin:jawaseatlasers2 \
    "http://192.168.132.183/cgi-bin/userManager.cgi?action=modifyPassword&name=admin&pwd=NEW_TRAFFIC_PASSWORD&pwdOld=jawaseatlasers2"

# Verify
curl --digest -u admin:NEW_TRAFFIC_PASSWORD "http://192.168.132.183/cgi-bin/magicBox.cgi?action=getSerialNo"
```

### Step 2.3: Rotate garage camera (via greenfin tunnel)

```bash
curl --digest -u admin:jawaseatlasers2 \
    "http://192.168.132.224:18080/cgi-bin/userManager.cgi?action=modifyPassword&name=admin&pwd=NEW_GARAGE_PASSWORD&pwdOld=jawaseatlasers2"

# Verify
curl --digest -u admin:NEW_GARAGE_PASSWORD "http://192.168.132.224:18080/cgi-bin/magicBox.cgi?action=getSerialNo"
```

## Phase 3: Update Consuming Services

### Step 3.1: Update secrets.env on all nodes

**File:** `/ganuda/config/secrets.env`

Add:
```bash
CAMERA_OFFICE_PII_PASSWORD=NEW_OFFICE_PII_PASSWORD
CAMERA_TRAFFIC_PASSWORD=NEW_TRAFFIC_PASSWORD
CAMERA_GARAGE_PASSWORD=NEW_GARAGE_PASSWORD
```

### Step 3.2: Update SAG Unified Interface camera config

Update `CAMERA_CONFIG` in the SAG app to read passwords from environment instead of hardcoded:

```python
import os
CAMERA_CONFIG = {
    'office_pii': {
        'ip': '192.168.132.182',
        'port': 80,
        'user': 'admin',
        'password': os.environ.get('CAMERA_OFFICE_PII_PASSWORD', ''),
    },
    'traffic': {
        'ip': '192.168.132.183',
        'port': 80,
        'user': 'admin',
        'password': os.environ.get('CAMERA_TRAFFIC_PASSWORD', ''),
    },
    'garage': {
        'ip': '192.168.132.224',
        'port': 18080,
        'user': 'admin',
        'password': os.environ.get('CAMERA_GARAGE_PASSWORD', ''),
    },
}
```

### Step 3.3: Update optic-nerve

If `/ganuda/lib/vlm_optic_nerve.py` has hardcoded camera credentials, update to read from secrets_loader or environment.

### Step 3.4: Update FreeIPA vault

Fix the mismatch (vault says `tribal_vision_2026`, cameras actually use `jawaseatlasers2`):
```bash
ipa vault-archive amcrest_camera_office_pii --data "NEW_OFFICE_PII_PASSWORD"
ipa vault-archive amcrest_camera_traffic --data "NEW_TRAFFIC_PASSWORD"
ipa vault-archive amcrest_camera_garage --data "NEW_GARAGE_PASSWORD"
```

### Step 3.5: Restart affected services

```bash
# On redfin:
sudo systemctl restart sag-unified
# On bluefin:
sudo systemctl restart optic-nerve
```

## Phase 4: Verification

```bash
# Test each camera snapshot — all should return 200
curl --digest -u admin:NEW_OFFICE_PII_PASSWORD "http://192.168.132.182/cgi-bin/snapshot.cgi" -o /dev/null -w "%{http_code}"
curl --digest -u admin:NEW_TRAFFIC_PASSWORD "http://192.168.132.183/cgi-bin/snapshot.cgi" -o /dev/null -w "%{http_code}"
curl --digest -u admin:NEW_GARAGE_PASSWORD "http://192.168.132.224:18080/cgi-bin/snapshot.cgi" -o /dev/null -w "%{http_code}"
```

Verify SAG camera feeds at http://192.168.132.223:4000/

## Rollback

If a camera becomes unreachable after password change:
1. Factory reset via physical reset button (hold 10 sec)
2. Reconfigure network settings (static IP, NTP)
3. Set new password via web UI at default admin/admin

## Security Notes

- Each camera gets a UNIQUE password — compromise of one doesn't expose others
- Store passwords ONLY in secrets.env and FreeIPA vault — never hardcode in source
- Schedule next rotation: 90 days (May 2026)

---
**FOR SEVEN GENERATIONS** — Rotate the locks, not just the keys.
