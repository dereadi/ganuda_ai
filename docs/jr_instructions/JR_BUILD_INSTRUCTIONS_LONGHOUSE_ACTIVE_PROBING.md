# JR BUILD INSTRUCTIONS: Longhouse Active Probing

**Target**: greenfin (192.168.132.224)
**Service**: Longhouse Monitor
**Date**: December 13, 2025
**Priority**: P2 - Enhancement

## Overview

Add active network probing to the Longhouse Monitor using `arp-scan` and `nmap`.
Currently we only use ARP cache (passive). Active probing will:
1. Discover devices not in ARP cache
2. Identify device types via service fingerprinting
3. Detect OS for unknown devices

## Prerequisites (COMPLETED)

```bash
# Already installed:
which arp-scan  # /usr/sbin/arp-scan
which nmap      # /usr/bin/nmap
```

## Implementation

### 1. Add arp-scan Function

Add to `/ganuda/services/longhouse/longhouse_monitor.py`:

```python
def arp_scan_network(interface: str = "eth0") -> list:
    """Active ARP scan - finds all live hosts on subnet

    Requires: sudo or setcap cap_net_raw+ep /usr/sbin/arp-scan
    """
    devices = []
    try:
        # Cherokee subnet
        result = subprocess.run(
            ["sudo", "arp-scan", "--interface", interface, "192.168.132.0/24", "-q"],
            capture_output=True, text=True, timeout=60
        )

        # Parse: IP\tMAC\tVendor
        for line in result.stdout.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2 and re.match(r'\d+\.\d+\.\d+\.\d+', parts[0]):
                devices.append({
                    "ip": parts[0],
                    "mac": parts[1].lower(),
                    "arp_vendor": parts[2] if len(parts) > 2 else None,
                })

        # Also scan WiFi/IoT subnet if reachable
        result2 = subprocess.run(
            ["sudo", "arp-scan", "--interface", interface, "10.0.0.0/24", "-q"],
            capture_output=True, text=True, timeout=60
        )
        for line in result2.stdout.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2 and re.match(r'\d+\.\d+\.\d+\.\d+', parts[0]):
                devices.append({
                    "ip": parts[0],
                    "mac": parts[1].lower(),
                    "arp_vendor": parts[2] if len(parts) > 2 else None,
                })

    except subprocess.TimeoutExpired:
        print("[WARN] arp-scan timed out")
    except Exception as e:
        print(f"[ERROR] arp-scan failed: {e}")

    return devices
```

### 2. Add nmap Fingerprinting Function

```python
def nmap_fingerprint(ip: str) -> dict:
    """Quick nmap fingerprint - OS and top services

    Power conscious: only runs on unknown devices
    """
    result = {
        "os_guess": None,
        "services": [],
        "device_type": None,
    }

    try:
        # Quick scan: OS detection + top 20 ports
        # -T3 = normal speed, -F = fast (top 100 ports)
        proc = subprocess.run(
            ["sudo", "nmap", "-O", "-F", "-T3", "--max-retries", "1", ip],
            capture_output=True, text=True, timeout=30
        )

        output = proc.stdout

        # Parse OS guess
        os_match = re.search(r'OS details: (.+)', output)
        if os_match:
            result["os_guess"] = os_match.group(1)

        # Parse device type
        type_match = re.search(r'Device type: (.+)', output)
        if type_match:
            result["device_type"] = type_match.group(1)

        # Parse open ports
        for line in output.split("\n"):
            port_match = re.match(r'(\d+)/tcp\s+open\s+(\S+)', line)
            if port_match:
                result["services"].append({
                    "port": int(port_match.group(1)),
                    "service": port_match.group(2),
                })

    except subprocess.TimeoutExpired:
        print(f"[WARN] nmap timeout for {ip}")
    except Exception as e:
        print(f"[ERROR] nmap failed for {ip}: {e}")

    return result
```

### 3. Add --active Flag

Update the main function:

```python
def run_discovery(online_lookup: bool = False, active_scan: bool = False):
    """Single discovery run - exits when done (power conscious)"""
    start = time.time()
    print(f"[{datetime.now()}] Longhouse Monitor starting...")
    print(f"[{datetime.now()}] MAC vendor database: {len(MAC_VENDORS)} prefixes")
    if online_lookup:
        print(f"[{datetime.now()}] Online MAC lookup: ENABLED")
    if active_scan:
        print(f"[{datetime.now()}] Active scanning: ENABLED")

    # ... existing code ...

    # Get devices - use active scan OR ARP cache
    if active_scan:
        devices = arp_scan_network()
        print(f"[{datetime.now()}] Devices found via arp-scan: {len(devices)}")
    else:
        devices = get_arp_cache()
        print(f"[{datetime.now()}] Devices in ARP cache: {len(devices)}")

    # ... classification loop ...

    for device in devices:
        mac = device.get("mac", "").lower()
        is_new = mac and mac not in known_macs

        # Classify - only do online lookup for new devices
        classified = classify_device(device, do_online_lookup=(online_lookup and is_new))

        # Deep fingerprint unknown devices with nmap (active mode only)
        if active_scan and classified.get("device_class") == "unknown":
            fingerprint = nmap_fingerprint(device["ip"])
            if fingerprint.get("os_guess"):
                classified["os_fingerprint"] = fingerprint["os_guess"]
            if fingerprint.get("device_type"):
                classified["device_type"] = fingerprint["device_type"]
            if fingerprint.get("services"):
                classified["open_services"] = json.dumps(fingerprint["services"])
            # Bump confidence if we got useful info
            if fingerprint.get("os_guess") or fingerprint.get("services"):
                classified["confidence"] = 0.7

        # ... save and alert ...
```

### 4. Update argparse

```python
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cherokee AI Longhouse Monitor")
    parser.add_argument("--online", action="store_true", help="Enable online MAC lookups")
    parser.add_argument("--active", action="store_true", help="Enable active scanning (arp-scan + nmap)")
    args = parser.parse_args()

    run_discovery(online_lookup=args.online, active_scan=args.active)
```

### 5. Database Schema Update

Add columns for fingerprint data:

```sql
-- Run on bluefin
ALTER TABLE iot_devices
ADD COLUMN IF NOT EXISTS os_fingerprint TEXT,
ADD COLUMN IF NOT EXISTS open_services JSONB,
ADD COLUMN IF NOT EXISTS last_active_scan TIMESTAMP;
```

### 6. Sudoers Configuration (Optional - Better Security)

Instead of running as root, grant specific capabilities:

```bash
# Option A: Sudoers entry (safe)
echo "dereadi ALL=(ALL) NOPASSWD: /usr/sbin/arp-scan, /usr/bin/nmap" | sudo tee /etc/sudoers.d/longhouse

# Option B: Capabilities (more secure)
sudo setcap cap_net_raw,cap_net_admin+eip /usr/sbin/arp-scan
sudo setcap cap_net_raw,cap_net_admin+eip /usr/bin/nmap
```

### 7. Systemd Service Update

Create `/ganuda/services/longhouse/longhouse-active.service`:

```ini
[Unit]
Description=Cherokee AI Longhouse Active Scan
Documentation=file:///ganuda/docs/jr_instructions/JR_BUILD_INSTRUCTIONS_LONGHOUSE_ACTIVE_PROBING.md
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/ganuda/services/longhouse
ExecStart=/usr/bin/python3 /ganuda/services/longhouse/longhouse_monitor.py --active --online
# Power conscious
Nice=15
CPUQuota=25%

[Install]
WantedBy=multi-user.target
```

Create `/ganuda/services/longhouse/longhouse-active.timer`:

```ini
[Unit]
Description=Cherokee AI Longhouse Active Scan Timer
Documentation=file:///ganuda/docs/jr_instructions/JR_BUILD_INSTRUCTIONS_LONGHOUSE_ACTIVE_PROBING.md

[Timer]
# Run once per hour (active scanning is heavier)
OnCalendar=hourly
RandomizedDelaySec=120
Persistent=false

[Install]
WantedBy=timers.target
```

## Testing

```bash
# Test arp-scan manually
sudo arp-scan --interface eth0 192.168.132.0/24

# Test nmap on one device
sudo nmap -O -F -T3 192.168.132.222

# Test full active discovery
cd /ganuda/services/longhouse
sudo python3 longhouse_monitor.py --active --online
```

## Expected Output

```
[2025-12-13 ...] Longhouse Monitor starting...
[2025-12-13 ...] MAC vendor database: 57 prefixes
[2025-12-13 ...] Online MAC lookup: ENABLED
[2025-12-13 ...] Active scanning: ENABLED
[2025-12-13 ...] Known devices in DB: 45
[2025-12-13 ...] Devices found via arp-scan: 52
  NEW: 10.0.0.155 - Unknown (OS: Linux 5.x, Services: 22/ssh, 80/http)
[2025-12-13 ...] Done in 45.2s. New: 7, Updated: 45, Identified: 38/52
```

## Power Budget

| Mode | CPU | Network | Frequency |
|------|-----|---------|-----------|
| Passive (default) | <5% | None | Every 30 min |
| Active | <25% | Moderate | Hourly |

## Safety Notes

1. **Never run active scans more than hourly** - too much network noise
2. **nmap is only used on unknown devices** - Cherokee nodes and IoT are skipped
3. **Timeout all scans** - prevent hangs from unresponsive hosts
4. **Log all activity** - for audit trail

## Verification Checklist

- [ ] arp-scan finds devices not in ARP cache
- [ ] nmap identifies OS on unknown devices
- [ ] Database stores fingerprint data
- [ ] Timer runs hourly (not more frequent)
- [ ] CPU stays under 25% quota

---

FOR SEVEN GENERATIONS
