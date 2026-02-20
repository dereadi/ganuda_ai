# Jr Instruction: Tunnel Garage Camera Through Greenfin

**Task ID:** CAMERA-TUNNEL-001
**Priority:** P1
**Date:** February 7, 2026
**Node:** greenfin (192.168.132.224)

## Overview

The garage Amcrest camera is physically on the IoT network at **10.0.0.123**. The vision pipeline on redfin needs RTSP access. Greenfin bridges both networks (192.168.132.224 on federation, 10.0.0.118 on IoT). Set up iptables DNAT to tunnel the camera's ports through greenfin.

## Network Diagram

```
redfin (192.168.132.223)          greenfin (192.168.132.224 / 10.0.0.118)          camera (10.0.0.123)
         │                                    │                                         │
    vision pipeline ──RTSP──▶ greenfin:10554 ──DNAT──▶ 10.0.0.123:554
    browser        ──HTTP──▶ greenfin:10080 ──DNAT──▶ 10.0.0.123:80
```

## Prerequisites

- Camera at 10.0.0.123 is UP (verified: HTTP 200, RTSP 554 open)
- Camera has default password (admin/admin)
- IP forwarding already enabled on greenfin (`/proc/sys/net/ipv4/ip_forward` = 1)

## Step 1: Set Up iptables Port Forwarding (requires sudo)

```bash
# On greenfin as root/sudo:

# RTSP tunnel: greenfin:10554 → camera:554
sudo iptables -t nat -A PREROUTING -p tcp -d 192.168.132.224 --dport 10554 -j DNAT --to-destination 10.0.0.123:554
sudo iptables -t nat -A POSTROUTING -p tcp -d 10.0.0.123 --dport 554 -j MASQUERADE

# HTTP tunnel: greenfin:10080 → camera:80
sudo iptables -t nat -A PREROUTING -p tcp -d 192.168.132.224 --dport 10080 -j DNAT --to-destination 10.0.0.123:80
sudo iptables -t nat -A POSTROUTING -p tcp -d 10.0.0.123 --dport 80 -j MASQUERADE

# Allow forwarding for these specific flows
sudo iptables -A FORWARD -p tcp -d 10.0.0.123 --dport 554 -j ACCEPT
sudo iptables -A FORWARD -p tcp -d 10.0.0.123 --dport 80 -j ACCEPT
sudo iptables -A FORWARD -p tcp -s 10.0.0.123 -j ACCEPT
```

## Step 2: Persist iptables Rules

```bash
# Save rules so they survive reboot
sudo iptables-save | sudo tee /etc/iptables/rules.v4 > /dev/null
# Or on Fedora/RHEL:
sudo iptables-save | sudo tee /etc/sysconfig/iptables > /dev/null
```

## Step 3: Verify Tunnel Works

From redfin (or any federation node):
```bash
# Test HTTP management
curl -s --connect-timeout 5 -o /dev/null -w '%{http_code}' http://192.168.132.224:10080
# Expected: 200 or 401 (auth required)

# Test RTSP
ffprobe -v quiet -print_format json -show_streams rtsp://admin:admin@192.168.132.224:10554/cam/realmonitor?channel=1\&subtype=0
```

## Step 4: Change Camera Default Password

Access camera web UI through the tunnel:
```
http://192.168.132.224:10080
```

Login with admin/admin, then change password to match fleet standard.
Retrieve fleet password: `/ganuda/scripts/get-vault-secret.sh amcrest_camera_password`

## Step 5: Update Camera Registry

Update `/ganuda/lib/tribal_vision/camera_config.py` CAMERA_REGISTRY:

```python
'garage': {
    'id': 'garage',
    'name': 'Garage Overhead',
    'ip': '192.168.132.224',  # Via greenfin tunnel
    'port': 10554,            # Tunneled RTSP port
    'type': 'amcrest',
    'purpose': 'Driveway / Package Detection',
    'specialist': 'Eagle Eye',
    'features': ['vehicle_tracking', 'package_detection', '5mp'],
    'stream_path': '/cam/realmonitor?channel=1&subtype=0',
},
```

## Step 6: Update CMDB

Insert camera into iot_devices and hardware_inventory tables:
```sql
INSERT INTO iot_devices (device_name, device_type, ip_address, location, is_authorized, network_segment)
VALUES ('garage_camera', 'amcrest_5mp', '10.0.0.123', 'Garage overhead', true, 'iot_10.0.0.x');

INSERT INTO hardware_inventory (hostname, device_type, ip_address, location, status)
VALUES ('garage-cam', 'Amcrest 5MP IP Camera', '10.0.0.123 (tunneled via greenfin:10554)', 'Garage', 'active');
```

## Verification Checklist

- [ ] iptables DNAT rules active on greenfin
- [ ] RTSP stream accessible from redfin at 192.168.132.224:10554
- [ ] HTTP management accessible at 192.168.132.224:10080
- [ ] Default password changed to fleet standard
- [ ] Camera registry updated
- [ ] CMDB updated
- [ ] Rules persisted for reboot survival

## Security Notes

- Per KB-SEC-001, only greenfin is authorized to bridge IoT ↔ federation
- Tunneled ports use non-standard numbers (10554, 10080) to avoid conflicts
- Camera traffic is NAT'd through greenfin - no direct IoT routing exposed
- Crawdad review recommended for production deployment

---
**FOR SEVEN GENERATIONS** - Three eyes watching, one cluster seeing.
