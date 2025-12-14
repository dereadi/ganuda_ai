# Jr Build Instructions: IoT Discovery, Network Monitoring & Honeypot
## Cherokee AI Federation - December 13, 2025

**Purpose**: Implement comprehensive IoT device discovery, network monitoring, command logging, and honeypot detection for the Cherokee AI cluster

**Owner**: Crawdad Jr (Security) + Eagle Eye Jr (Monitoring)

**Priority**: HIGH - Network visibility is foundational to security

---

## MAINTAINABILITY REVIEW GATE

> **"80,000 cameras deployed with no public audit. We will not become this."**

**Status**: [ ] NOT REVIEWED / [ ] APPROVED / [ ] BLOCKED

**Council Vote Required Before Implementation**

| Specialist | Concern Area | Sign-off | Date |
|------------|--------------|----------|------|
| Crawdad | No hardcoded creds, debug disabled, deps current | [ ] | |
| Turtle | Maintainer named, succession plan, sunset plan | [ ] | |
| Eagle Eye | Health checks, purge verification, alerting | [ ] | |
| Gecko | Code reviewed, tests exist, rollback possible | [ ] | |
| Spider | Fits architecture, CMDB entry, thermal memory | [ ] | |
| Raven | Aligns with roadmap, ROI justified | [ ] | |
| Peace Chief | All voices heard, concerns addressed | [ ] | |

**Concerns Raised**:
- (To be filled during review)

**Mitigations Applied**:
- (To be filled during review)

**Maintainability Commitments**:

| Component | Maintainer | Review Frequency | Sunset Trigger |
|-----------|------------|------------------|----------------|
| IoT Discovery | ________ | Monthly | If accuracy < 80% or unpatched > 30 days |
| CMD Audit Log | ________ | Weekly | If log backlog > 7 days |
| Network Monitor | ________ | Weekly | If false positives > 20% |
| Honeypot | ________ | Daily | If compromised or unmonitored > 24h |

**Next Review Date**: __________ (max 90 days from deployment)

---

## Part 1: IoT Device Discovery & Fingerprinting

### 1.1 Overview

Cherokee AI needs to identify and track all IoT devices on the 192.168.132.0/24 network using multiple techniques:

| Technique | Accuracy | Latency | Use Case |
|-----------|----------|---------|----------|
| Traffic Features (TCP window, DNS) | 95%+ | ~1 min | Real-time classification |
| DHCP Fingerprinting | 90%+ | Variable | New device detection |
| Protocol Discovery (uPnP, mDNS) | 98%+ | Seconds | Service enumeration |
| Behavioral Analysis | 85%+ | Hours | Anomaly detection |

### 1.2 Database Schema

Deploy to bluefin (192.168.132.222):

```sql
-- IoT Device Registry
CREATE TABLE IF NOT EXISTS iot_devices (
    device_id SERIAL PRIMARY KEY,
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    ip_address INET,
    hostname VARCHAR(255),
    device_class VARCHAR(50),  -- 'iot', 'not', 'unknown'
    device_type VARCHAR(100),  -- 'camera', 'sensor', 'hub', 'workstation', etc.
    manufacturer VARCHAR(255),
    model VARCHAR(255),
    firmware_version VARCHAR(100),
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    discovery_method VARCHAR(50),  -- 'traffic', 'dhcp', 'upnp', 'mdns', 'manual'
    fingerprint_hash VARCHAR(64),
    confidence_score FLOAT DEFAULT 0.5,
    is_authorized BOOLEAN DEFAULT FALSE,
    is_cherokee_node BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_iot_mac ON iot_devices(mac_address);
CREATE INDEX idx_iot_ip ON iot_devices(ip_address);
CREATE INDEX idx_iot_class ON iot_devices(device_class);
CREATE INDEX idx_iot_authorized ON iot_devices(is_authorized);

-- Device Traffic Patterns
CREATE TABLE IF NOT EXISTS iot_traffic_patterns (
    pattern_id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES iot_devices(device_id),
    captured_at TIMESTAMP DEFAULT NOW(),
    tcp_window_size INTEGER,
    unique_dns_queries INTEGER,
    avg_packet_size INTEGER,
    protocols_used TEXT[],
    ports_contacted INTEGER[],
    external_ips_contacted INTEGER,
    bytes_sent BIGINT,
    bytes_received BIGINT,
    pattern_hash VARCHAR(64)
);

CREATE INDEX idx_traffic_device ON iot_traffic_patterns(device_id);
CREATE INDEX idx_traffic_time ON iot_traffic_patterns(captured_at DESC);

-- DHCP Fingerprints
CREATE TABLE IF NOT EXISTS dhcp_fingerprints (
    fingerprint_id SERIAL PRIMARY KEY,
    mac_address VARCHAR(17),
    dhcp_options TEXT[],
    vendor_class VARCHAR(255),
    hostname VARCHAR(255),
    fingerprint_hash VARCHAR(64),
    captured_at TIMESTAMP DEFAULT NOW()
);

-- Known Device Signatures (Golden Images)
CREATE TABLE IF NOT EXISTS device_signatures (
    signature_id SERIAL PRIMARY KEY,
    device_type VARCHAR(100),
    manufacturer VARCHAR(255),
    model VARCHAR(255),
    signature_hash VARCHAR(64),
    traffic_profile JSONB,
    dhcp_profile JSONB,
    expected_ports INTEGER[],
    expected_protocols TEXT[],
    is_trusted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Seed Cherokee nodes as authorized
INSERT INTO iot_devices (mac_address, ip_address, hostname, device_class, device_type, is_authorized, is_cherokee_node, discovery_method)
VALUES
    ('REDFIN_MAC', '192.168.132.223', 'redfin', 'not', 'gpu_server', TRUE, TRUE, 'manual'),
    ('BLUEFIN_MAC', '192.168.132.222', 'bluefin', 'not', 'database_server', TRUE, TRUE, 'manual'),
    ('GREENFIN_MAC', '192.168.132.224', 'greenfin', 'not', 'daemon_server', TRUE, TRUE, 'manual'),
    ('SASASS_MAC', '192.168.132.241', 'sasass', 'not', 'mac_studio', TRUE, TRUE, 'manual'),
    ('SASASS2_MAC', '192.168.132.242', 'sasass2', 'not', 'mac_studio', TRUE, TRUE, 'manual')
ON CONFLICT (mac_address) DO NOTHING;

GRANT ALL ON iot_devices, iot_traffic_patterns, dhcp_fingerprints, device_signatures TO claude;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO claude;
```

### 1.3 IoT Discovery Service

Deploy to greenfin (192.168.132.224) - the monitoring node:

```python
#!/usr/bin/env python3
"""
Cherokee AI IoT Discovery Service
Deploy to: /ganuda/services/iot_discovery/iot_discovery.py
Schedule: Every 5 minutes via systemd timer
"""

import subprocess
import psycopg2
import json
import hashlib
import re
from datetime import datetime
from typing import Optional, Dict, List

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

NETWORK = "192.168.132.0/24"

# Cherokee nodes - always authorized
CHEROKEE_IPS = {
    "192.168.132.223": "redfin",
    "192.168.132.222": "bluefin",
    "192.168.132.224": "greenfin",
    "192.168.132.241": "sasass",
    "192.168.132.242": "sasass2",
    "192.168.132.21": "bmasass"
}


def scan_network_arp() -> List[Dict]:
    """Scan network using ARP to find active devices"""
    devices = []
    try:
        # Use arp-scan if available, fallback to nmap
        result = subprocess.run(
            ["arp-scan", "--localnet", "-q"],
            capture_output=True, text=True, timeout=60
        )

        for line in result.stdout.split('\n'):
            match = re.match(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:]+)\s+(.*)', line)
            if match:
                devices.append({
                    "ip": match.group(1),
                    "mac": match.group(2).upper(),
                    "vendor": match.group(3).strip()
                })
    except FileNotFoundError:
        # Fallback to nmap
        result = subprocess.run(
            ["nmap", "-sn", NETWORK],
            capture_output=True, text=True, timeout=120
        )
        # Parse nmap output...
    except Exception as e:
        print(f"ARP scan error: {e}")

    return devices


def discover_upnp() -> List[Dict]:
    """Discover devices via UPnP/SSDP"""
    devices = []
    try:
        import socket

        SSDP_ADDR = "239.255.255.250"
        SSDP_PORT = 1900
        SSDP_MX = 2

        ssdp_request = (
            'M-SEARCH * HTTP/1.1\r\n'
            f'HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n'
            'MAN: "ssdp:discover"\r\n'
            f'MX: {SSDP_MX}\r\n'
            'ST: ssdp:all\r\n'
            '\r\n'
        )

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(SSDP_MX + 1)
        sock.sendto(ssdp_request.encode(), (SSDP_ADDR, SSDP_PORT))

        while True:
            try:
                data, addr = sock.recvfrom(1024)
                response = data.decode()
                device = parse_ssdp_response(response, addr[0])
                if device:
                    devices.append(device)
            except socket.timeout:
                break

        sock.close()
    except Exception as e:
        print(f"UPnP discovery error: {e}")

    return devices


def parse_ssdp_response(response: str, ip: str) -> Optional[Dict]:
    """Parse SSDP response to extract device info"""
    device = {"ip": ip, "discovery_method": "upnp"}

    for line in response.split('\r\n'):
        if line.startswith('SERVER:'):
            device["server"] = line.split(':', 1)[1].strip()
        elif line.startswith('ST:'):
            device["service_type"] = line.split(':', 1)[1].strip()
        elif line.startswith('USN:'):
            device["usn"] = line.split(':', 1)[1].strip()
        elif line.startswith('LOCATION:'):
            device["location"] = line.split(':', 1)[1].strip()

    return device if "service_type" in device else None


def discover_mdns() -> List[Dict]:
    """Discover devices via mDNS/Bonjour"""
    devices = []
    try:
        result = subprocess.run(
            ["avahi-browse", "-a", "-t", "-r", "-p"],
            capture_output=True, text=True, timeout=30
        )

        for line in result.stdout.split('\n'):
            if line.startswith('='):
                parts = line.split(';')
                if len(parts) >= 8:
                    devices.append({
                        "hostname": parts[3],
                        "service": parts[4],
                        "ip": parts[7],
                        "discovery_method": "mdns"
                    })
    except Exception as e:
        print(f"mDNS discovery error: {e}")

    return devices


def classify_device(mac: str, traffic_features: Dict = None) -> Dict:
    """Classify device as IoT or NoT using traffic features"""

    # Known IoT MAC prefixes (OUI)
    IOT_OUIS = [
        "00:1A:22",  # Cisco IoT
        "B8:27:EB",  # Raspberry Pi
        "DC:A6:32",  # Raspberry Pi
        "00:04:4B",  # Nvidia
        "AC:BC:32",  # Apple
        "F0:B4:29",  # Amazon Echo
        "68:54:FD",  # Amazon
        "50:DC:E7",  # Amazon
        "A0:02:DC",  # Google Home
        "48:D6:D5",  # Google
    ]

    mac_prefix = mac[:8].upper()

    result = {
        "device_class": "unknown",
        "confidence": 0.5,
        "method": "heuristic"
    }

    # Check if it's a known Cherokee node
    # (would need to look up by MAC)

    # Check OUI
    if mac_prefix in IOT_OUIS:
        result["device_class"] = "iot"
        result["confidence"] = 0.7

    # If we have traffic features, use ML classification
    if traffic_features:
        # Simplified heuristic - real implementation would use trained model
        tcp_window = traffic_features.get("tcp_window_size", 0)
        dns_queries = traffic_features.get("unique_dns_queries", 0)

        # IoT devices typically have smaller TCP windows and fewer DNS queries
        if tcp_window < 16384 and dns_queries < 10:
            result["device_class"] = "iot"
            result["confidence"] = 0.85
        elif tcp_window >= 65535 and dns_queries > 50:
            result["device_class"] = "not"
            result["confidence"] = 0.9

    return result


def generate_fingerprint(device: Dict) -> str:
    """Generate unique fingerprint hash for device"""
    fp_data = f"{device.get('mac', '')}{device.get('vendor', '')}{device.get('hostname', '')}"
    return hashlib.sha256(fp_data.encode()).hexdigest()[:16]


def save_device(device: Dict):
    """Save or update device in database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        mac = device.get("mac", "").upper()
        ip = device.get("ip")
        hostname = device.get("hostname", "")
        vendor = device.get("vendor", "")
        discovery_method = device.get("discovery_method", "arp")

        classification = classify_device(mac)
        fingerprint = generate_fingerprint(device)

        is_cherokee = ip in CHEROKEE_IPS
        is_authorized = is_cherokee  # Cherokee nodes auto-authorized

        cur.execute("""
            INSERT INTO iot_devices
            (mac_address, ip_address, hostname, manufacturer, device_class,
             confidence_score, discovery_method, fingerprint_hash,
             is_authorized, is_cherokee_node, last_seen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (mac_address) DO UPDATE SET
                ip_address = EXCLUDED.ip_address,
                hostname = COALESCE(EXCLUDED.hostname, iot_devices.hostname),
                manufacturer = COALESCE(EXCLUDED.manufacturer, iot_devices.manufacturer),
                device_class = CASE
                    WHEN EXCLUDED.confidence_score > iot_devices.confidence_score
                    THEN EXCLUDED.device_class
                    ELSE iot_devices.device_class
                END,
                confidence_score = GREATEST(EXCLUDED.confidence_score, iot_devices.confidence_score),
                last_seen = NOW()
        """, (mac, ip, hostname, vendor, classification["device_class"],
              classification["confidence"], discovery_method, fingerprint,
              is_authorized, is_cherokee))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Save device error: {e}")


def alert_new_device(device: Dict):
    """Alert on new unauthorized device"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO tpm_notifications
            (priority, category, title, message, source_system, related_hash)
            VALUES ('P2', 'security', %s, %s, 'iot_discovery', %s)
        """, (
            f"New device detected: {device.get('ip', 'unknown')}",
            f"""New device discovered on network:

MAC: {device.get('mac', 'unknown')}
IP: {device.get('ip', 'unknown')}
Hostname: {device.get('hostname', 'unknown')}
Vendor: {device.get('vendor', 'unknown')}
Classification: {device.get('device_class', 'unknown')}
Discovery Method: {device.get('discovery_method', 'unknown')}

This device is NOT authorized. Review and authorize if legitimate.""",
            device.get('mac', 'unknown')
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Alert error: {e}")


def run_discovery():
    """Run full discovery cycle"""
    print(f"[{datetime.now()}] Starting IoT discovery...")

    # Get known devices
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT mac_address FROM iot_devices")
    known_macs = set(row[0] for row in cur.fetchall())
    conn.close()

    # ARP scan
    print("  Running ARP scan...")
    arp_devices = scan_network_arp()
    print(f"    Found {len(arp_devices)} devices")

    # UPnP discovery
    print("  Running UPnP discovery...")
    upnp_devices = discover_upnp()
    print(f"    Found {len(upnp_devices)} services")

    # mDNS discovery
    print("  Running mDNS discovery...")
    mdns_devices = discover_mdns()
    print(f"    Found {len(mdns_devices)} services")

    # Process and save devices
    new_devices = 0
    for device in arp_devices:
        mac = device.get("mac", "").upper()
        if mac and mac not in known_macs:
            new_devices += 1
            ip = device.get("ip")
            if ip not in CHEROKEE_IPS:
                alert_new_device(device)
        save_device(device)

    print(f"[{datetime.now()}] Discovery complete. New devices: {new_devices}")


if __name__ == "__main__":
    run_discovery()
```

---

## Part 2: Command Logging (CMD Audit Trail)

### 2.1 Overview

Log all significant commands executed across the cluster for audit and forensics.

### 2.2 Database Schema

```sql
-- Command Audit Log
CREATE TABLE IF NOT EXISTS cmd_audit_log (
    log_id SERIAL PRIMARY KEY,
    node_name VARCHAR(50) NOT NULL,
    username VARCHAR(100) NOT NULL,
    command TEXT NOT NULL,
    working_directory TEXT,
    exit_code INTEGER,
    executed_at TIMESTAMP DEFAULT NOW(),
    duration_ms INTEGER,
    is_sudo BOOLEAN DEFAULT FALSE,
    is_sensitive BOOLEAN DEFAULT FALSE,
    source_ip INET,
    session_id VARCHAR(100),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_cmd_node ON cmd_audit_log(node_name);
CREATE INDEX idx_cmd_user ON cmd_audit_log(username);
CREATE INDEX idx_cmd_time ON cmd_audit_log(executed_at DESC);
CREATE INDEX idx_cmd_sensitive ON cmd_audit_log(is_sensitive);

GRANT ALL ON cmd_audit_log TO claude;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO claude;
```

### 2.3 Bash Command Logger

Add to `/etc/profile.d/cherokee_audit.sh` on each Linux node:

```bash
#!/bin/bash
# Cherokee AI Command Audit Logger
# Deploy to: /etc/profile.d/cherokee_audit.sh

CHEROKEE_AUDIT_ENABLED=true
CHEROKEE_AUDIT_DB_HOST="192.168.132.222"
CHEROKEE_NODE=$(hostname)

# Sensitive command patterns
SENSITIVE_PATTERNS="password|secret|key|token|credential|sudo|rm -rf|chmod 777|curl.*\|.*sh"

log_command() {
    local cmd="$1"
    local exit_code="$2"

    # Skip logging the logger itself
    [[ "$cmd" == *"cherokee_log_cmd"* ]] && return

    # Check if sensitive
    local is_sensitive="false"
    if echo "$cmd" | grep -qiE "$SENSITIVE_PATTERNS"; then
        is_sensitive="true"
    fi

    # Check if sudo
    local is_sudo="false"
    [[ "$cmd" == sudo* ]] && is_sudo="true"

    # Log to database asynchronously
    (
        PGPASSWORD="jawaseatlasers2" psql -h "$CHEROKEE_AUDIT_DB_HOST" \
            -U claude -d zammad_production -q -c \
            "INSERT INTO cmd_audit_log (node_name, username, command, working_directory, exit_code, is_sudo, is_sensitive, source_ip)
             VALUES ('$CHEROKEE_NODE', '$USER', \$\$${cmd}\$\$, '$PWD', $exit_code, $is_sudo, $is_sensitive, '${SSH_CLIENT%% *}')" \
            2>/dev/null
    ) &
}

# Trap command execution
cherokee_prompt_command() {
    local exit_code=$?
    local cmd=$(history 1 | sed 's/^[ ]*[0-9]*[ ]*//')
    [ -n "$cmd" ] && log_command "$cmd" "$exit_code"
}

if [ "$CHEROKEE_AUDIT_ENABLED" = "true" ]; then
    PROMPT_COMMAND="cherokee_prompt_command${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
fi
```

---

## Part 3: Network Monitoring

### 3.1 Overview

Continuous network traffic monitoring for anomaly detection.

### 3.2 Database Schema

```sql
-- Network Flow Records
CREATE TABLE IF NOT EXISTS network_flows (
    flow_id SERIAL PRIMARY KEY,
    captured_at TIMESTAMP DEFAULT NOW(),
    src_ip INET,
    dst_ip INET,
    src_port INTEGER,
    dst_port INTEGER,
    protocol VARCHAR(10),
    bytes_sent BIGINT,
    bytes_received BIGINT,
    packets INTEGER,
    duration_ms INTEGER,
    flags TEXT,
    is_external BOOLEAN DEFAULT FALSE,
    is_anomalous BOOLEAN DEFAULT FALSE,
    anomaly_score FLOAT DEFAULT 0.0
);

CREATE INDEX idx_flow_time ON network_flows(captured_at DESC);
CREATE INDEX idx_flow_src ON network_flows(src_ip);
CREATE INDEX idx_flow_dst ON network_flows(dst_ip);
CREATE INDEX idx_flow_anomaly ON network_flows(is_anomalous);

-- Network Baselines (for anomaly detection)
CREATE TABLE IF NOT EXISTS network_baselines (
    baseline_id SERIAL PRIMARY KEY,
    device_ip INET,
    hour_of_day INTEGER,
    day_of_week INTEGER,
    avg_bytes_out BIGINT,
    avg_bytes_in BIGINT,
    avg_connections INTEGER,
    common_ports INTEGER[],
    common_destinations INET[],
    calculated_at TIMESTAMP DEFAULT NOW()
);

GRANT ALL ON network_flows, network_baselines TO claude;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO claude;
```

### 3.3 Network Monitor Service

Deploy to greenfin:

```python
#!/usr/bin/env python3
"""
Cherokee AI Network Monitor
Deploy to: /ganuda/services/network_monitor/network_monitor.py
Requires: tcpdump (run as root or with capabilities)
"""

import subprocess
import psycopg2
import re
import threading
from datetime import datetime
from collections import defaultdict

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

# Internal network
INTERNAL_NETWORK = "192.168.132."

# Flow aggregation buffer
flows = defaultdict(lambda: {
    "bytes_sent": 0,
    "bytes_received": 0,
    "packets": 0,
    "first_seen": None,
    "last_seen": None
})

# Anomaly thresholds
ANOMALY_THRESHOLDS = {
    "bytes_per_minute": 100_000_000,  # 100MB/min
    "connections_per_minute": 1000,
    "new_external_ips": 50
}


def is_external(ip: str) -> bool:
    """Check if IP is external to our network"""
    return not ip.startswith(INTERNAL_NETWORK) and not ip.startswith("127.")


def parse_tcpdump_line(line: str) -> dict:
    """Parse tcpdump output line"""
    # Example: 12:34:56.789 IP 192.168.132.223.443 > 8.8.8.8.53: UDP, length 64
    match = re.match(
        r'[\d:.]+\s+IP\s+(\d+\.\d+\.\d+\.\d+)\.(\d+)\s+>\s+(\d+\.\d+\.\d+\.\d+)\.(\d+):\s+(\w+).*length\s+(\d+)',
        line
    )
    if match:
        return {
            "src_ip": match.group(1),
            "src_port": int(match.group(2)),
            "dst_ip": match.group(3),
            "dst_port": int(match.group(4)),
            "protocol": match.group(5),
            "length": int(match.group(6))
        }
    return None


def calculate_anomaly_score(flow: dict) -> float:
    """Calculate anomaly score for a flow"""
    score = 0.0

    # Large data transfer
    total_bytes = flow["bytes_sent"] + flow["bytes_received"]
    if total_bytes > 10_000_000:  # 10MB
        score += 0.3
    if total_bytes > 100_000_000:  # 100MB
        score += 0.3

    # Unusual ports
    unusual_ports = [4444, 5555, 6666, 31337, 12345]  # Common backdoor ports
    if flow.get("dst_port") in unusual_ports or flow.get("src_port") in unusual_ports:
        score += 0.5

    # External destination
    if is_external(flow.get("dst_ip", "")):
        score += 0.1

    return min(1.0, score)


def flush_flows():
    """Flush aggregated flows to database"""
    global flows

    if not flows:
        return

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        for key, flow in flows.items():
            src_ip, dst_ip, src_port, dst_port, protocol = key

            anomaly_score = calculate_anomaly_score(flow)
            is_anomalous = anomaly_score > 0.5

            if flow["first_seen"] and flow["last_seen"]:
                duration_ms = int((flow["last_seen"] - flow["first_seen"]).total_seconds() * 1000)
            else:
                duration_ms = 0

            cur.execute("""
                INSERT INTO network_flows
                (src_ip, dst_ip, src_port, dst_port, protocol, bytes_sent, bytes_received,
                 packets, duration_ms, is_external, is_anomalous, anomaly_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (src_ip, dst_ip, src_port, dst_port, protocol,
                  flow["bytes_sent"], flow["bytes_received"], flow["packets"],
                  duration_ms, is_external(dst_ip), is_anomalous, anomaly_score))

            # Alert on high anomaly scores
            if is_anomalous:
                alert_anomaly(src_ip, dst_ip, anomaly_score, flow)

        conn.commit()
        conn.close()

        flows = defaultdict(lambda: {
            "bytes_sent": 0, "bytes_received": 0, "packets": 0,
            "first_seen": None, "last_seen": None
        })

    except Exception as e:
        print(f"Flush error: {e}")


def alert_anomaly(src_ip: str, dst_ip: str, score: float, flow: dict):
    """Alert on anomalous network activity"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO tpm_notifications
            (priority, category, title, message, source_system)
            VALUES ('P1', 'security', %s, %s, 'network_monitor')
        """, (
            f"Anomalous network activity: {src_ip} -> {dst_ip}",
            f"""Suspicious network flow detected:

Source: {src_ip}
Destination: {dst_ip}
Anomaly Score: {score:.2f}
Bytes Transferred: {flow['bytes_sent'] + flow['bytes_received']:,}
Packets: {flow['packets']}

Review immediately."""
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Alert error: {e}")


def monitor_network():
    """Main network monitoring loop"""
    print(f"[{datetime.now()}] Starting network monitor...")

    # Start tcpdump
    proc = subprocess.Popen(
        ["tcpdump", "-i", "any", "-n", "-l", "-q", "ip"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )

    # Flush timer
    def flush_timer():
        while True:
            threading.Event().wait(60)  # Flush every minute
            flush_flows()

    flush_thread = threading.Thread(target=flush_timer, daemon=True)
    flush_thread.start()

    try:
        for line in proc.stdout:
            parsed = parse_tcpdump_line(line)
            if parsed:
                key = (
                    parsed["src_ip"],
                    parsed["dst_ip"],
                    parsed["src_port"],
                    parsed["dst_port"],
                    parsed["protocol"]
                )

                now = datetime.now()
                flows[key]["packets"] += 1
                flows[key]["bytes_sent"] += parsed["length"]

                if flows[key]["first_seen"] is None:
                    flows[key]["first_seen"] = now
                flows[key]["last_seen"] = now

    except KeyboardInterrupt:
        proc.terminate()
        flush_flows()


if __name__ == "__main__":
    monitor_network()
```

---

## Part 4: Honeypot Deployment

### 4.1 Overview

Deploy honeypot services to detect attackers and gather threat intelligence.

### 4.2 Database Schema

```sql
-- Honeypot Events
CREATE TABLE IF NOT EXISTS honeypot_events (
    event_id SERIAL PRIMARY KEY,
    honeypot_type VARCHAR(50) NOT NULL,  -- 'ssh', 'http', 'telnet', 'ftp', 'smb'
    src_ip INET NOT NULL,
    src_port INTEGER,
    dst_port INTEGER,
    event_type VARCHAR(50),  -- 'connection', 'login_attempt', 'command', 'exploit'
    username VARCHAR(255),
    password VARCHAR(255),
    command TEXT,
    payload TEXT,
    user_agent TEXT,
    captured_at TIMESTAMP DEFAULT NOW(),
    geo_location VARCHAR(100),
    threat_score FLOAT DEFAULT 0.5,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_honeypot_time ON honeypot_events(captured_at DESC);
CREATE INDEX idx_honeypot_src ON honeypot_events(src_ip);
CREATE INDEX idx_honeypot_type ON honeypot_events(honeypot_type);
CREATE INDEX idx_honeypot_threat ON honeypot_events(threat_score);

-- Threat Intelligence (aggregated from honeypot)
CREATE TABLE IF NOT EXISTS threat_intel (
    intel_id SERIAL PRIMARY KEY,
    ip_address INET UNIQUE NOT NULL,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    total_attempts INTEGER DEFAULT 0,
    attack_types TEXT[],
    usernames_tried TEXT[],
    threat_level VARCHAR(20),  -- 'low', 'medium', 'high', 'critical'
    is_blocked BOOLEAN DEFAULT FALSE,
    notes TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_threat_ip ON threat_intel(ip_address);
CREATE INDEX idx_threat_level ON threat_intel(threat_level);

GRANT ALL ON honeypot_events, threat_intel TO claude;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO claude;
```

### 4.3 SSH Honeypot

Deploy to an unused IP or port on greenfin:

```python
#!/usr/bin/env python3
"""
Cherokee AI SSH Honeypot
Deploy to: /ganuda/services/honeypot/ssh_honeypot.py
Run on: Non-standard port (e.g., 2222) or dedicated honeypot IP

WARNING: Run in isolated environment. Attackers WILL try to exploit.
"""

import socket
import threading
import paramiko
import psycopg2
import json
from datetime import datetime

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

HONEYPOT_PORT = 2222
HONEYPOT_HOST = "0.0.0.0"

# Generate or load host key
HOST_KEY = paramiko.RSAKey.generate(2048)


class SSHHoneypot(paramiko.ServerInterface):
    def __init__(self, client_ip):
        self.client_ip = client_ip
        self.username = None
        self.password = None

    def check_auth_password(self, username, password):
        self.username = username
        self.password = password

        # Log the attempt
        log_honeypot_event(
            honeypot_type="ssh",
            src_ip=self.client_ip,
            dst_port=HONEYPOT_PORT,
            event_type="login_attempt",
            username=username,
            password=password
        )

        # Always reject - this is a honeypot
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        return "password"


def log_honeypot_event(honeypot_type: str, src_ip: str, dst_port: int,
                       event_type: str, username: str = None, password: str = None,
                       command: str = None, payload: str = None):
    """Log honeypot event to database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Calculate threat score
        threat_score = 0.5
        if event_type == "login_attempt":
            threat_score = 0.6
            # Common attack usernames increase score
            if username in ["root", "admin", "administrator", "test", "user"]:
                threat_score = 0.7
        if event_type == "command":
            threat_score = 0.8
        if event_type == "exploit":
            threat_score = 1.0

        cur.execute("""
            INSERT INTO honeypot_events
            (honeypot_type, src_ip, dst_port, event_type, username, password,
             command, payload, threat_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (honeypot_type, src_ip, dst_port, event_type, username, password,
              command, payload, threat_score))

        # Update threat intel
        cur.execute("""
            INSERT INTO threat_intel (ip_address, first_seen, last_seen, total_attempts, attack_types, usernames_tried, threat_level)
            VALUES (%s, NOW(), NOW(), 1, ARRAY[%s], ARRAY[%s],
                    CASE WHEN %s >= 0.8 THEN 'high' WHEN %s >= 0.6 THEN 'medium' ELSE 'low' END)
            ON CONFLICT (ip_address) DO UPDATE SET
                last_seen = NOW(),
                total_attempts = threat_intel.total_attempts + 1,
                attack_types = array_cat(threat_intel.attack_types, ARRAY[%s]),
                usernames_tried = array_cat(threat_intel.usernames_tried, ARRAY[%s]),
                threat_level = CASE
                    WHEN threat_intel.total_attempts > 100 THEN 'critical'
                    WHEN threat_intel.total_attempts > 50 THEN 'high'
                    WHEN threat_intel.total_attempts > 10 THEN 'medium'
                    ELSE 'low'
                END,
                updated_at = NOW()
        """, (src_ip, event_type, username, threat_score, threat_score,
              event_type, username))

        conn.commit()
        conn.close()

        # Alert on high-threat events
        if threat_score >= 0.8:
            alert_threat(src_ip, event_type, username, threat_score)

    except Exception as e:
        print(f"Log error: {e}")


def alert_threat(src_ip: str, event_type: str, username: str, score: float):
    """Alert on high-threat honeypot activity"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO tpm_notifications
            (priority, category, title, message, source_system, related_hash)
            VALUES ('P1', 'security', %s, %s, 'honeypot', %s)
        """, (
            f"Honeypot Alert: Attack from {src_ip}",
            f"""High-threat activity detected on honeypot:

Source IP: {src_ip}
Event Type: {event_type}
Username Attempted: {username}
Threat Score: {score:.2f}

Consider blocking this IP.""",
            src_ip
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Alert error: {e}")


def handle_client(client_socket, client_address):
    """Handle incoming honeypot connection"""
    client_ip = client_address[0]

    # Log connection
    log_honeypot_event(
        honeypot_type="ssh",
        src_ip=client_ip,
        dst_port=HONEYPOT_PORT,
        event_type="connection"
    )

    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(HOST_KEY)

        server = SSHHoneypot(client_ip)
        transport.start_server(server=server)

        # Wait for auth (will always fail)
        channel = transport.accept(timeout=30)
        if channel:
            channel.close()

    except Exception as e:
        pass
    finally:
        try:
            transport.close()
        except:
            pass
        client_socket.close()


def run_honeypot():
    """Run the SSH honeypot"""
    print(f"[{datetime.now()}] Starting SSH honeypot on port {HONEYPOT_PORT}...")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HONEYPOT_HOST, HONEYPOT_PORT))
    server_socket.listen(100)

    print(f"  Listening on {HONEYPOT_HOST}:{HONEYPOT_PORT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nShutting down honeypot...")
        server_socket.close()


if __name__ == "__main__":
    run_honeypot()
```

### 4.4 HTTP Honeypot

```python
#!/usr/bin/env python3
"""
Cherokee AI HTTP Honeypot
Simulates vulnerable web services to attract attackers
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import psycopg2
import urllib.parse
import json
from datetime import datetime

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

HONEYPOT_PORT = 8888

# Fake vulnerable paths
VULNERABLE_PATHS = [
    "/wp-admin", "/wp-login.php", "/administrator",
    "/phpmyadmin", "/.env", "/config.php", "/backup.sql",
    "/api/v1/users", "/.git/config", "/server-status"
]


class HoneypotHandler(BaseHTTPRequestHandler):
    def log_request(self, event_type="request", payload=None):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            client_ip = self.client_address[0]
            user_agent = self.headers.get("User-Agent", "")

            threat_score = 0.3
            if any(vp in self.path for vp in VULNERABLE_PATHS):
                threat_score = 0.7
            if "sql" in self.path.lower() or "union" in self.path.lower():
                threat_score = 0.9
            if "script" in str(payload).lower() or "<" in str(payload):
                threat_score = 0.9

            cur.execute("""
                INSERT INTO honeypot_events
                (honeypot_type, src_ip, dst_port, event_type, command, payload, user_agent, threat_score)
                VALUES ('http', %s, %s, %s, %s, %s, %s, %s)
            """, (client_ip, HONEYPOT_PORT, event_type, self.path, payload, user_agent, threat_score))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Log error: {e}")

    def do_GET(self):
        self.log_request("get_request")

        # Return fake responses for known attack paths
        if "/wp-admin" in self.path:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>WordPress Admin</h1><form>Login:</form></body></html>")
        elif "/.env" in self.path:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"DB_PASSWORD=fake_password_12345\nAPI_KEY=fake_key_67890")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(content_length).decode("utf-8", errors="ignore")

        self.log_request("post_request", payload)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

    def log_message(self, format, *args):
        pass  # Suppress default logging


def run_http_honeypot():
    print(f"[{datetime.now()}] Starting HTTP honeypot on port {HONEYPOT_PORT}...")
    server = HTTPServer(("0.0.0.0", HONEYPOT_PORT), HoneypotHandler)
    server.serve_forever()


if __name__ == "__main__":
    run_http_honeypot()
```

---

## Part 5: Deployment Summary

### 5.1 Systemd Services

Create on greenfin for each service:

```bash
# /etc/systemd/system/iot-discovery.timer
[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
[Install]
WantedBy=timers.target

# /etc/systemd/system/network-monitor.service
[Service]
ExecStart=/usr/bin/python3 /ganuda/services/network_monitor/network_monitor.py
Restart=always
User=root

# /etc/systemd/system/ssh-honeypot.service
[Service]
ExecStart=/usr/bin/python3 /ganuda/services/honeypot/ssh_honeypot.py
Restart=always
User=root
```

### 5.2 Installation Steps

```bash
# On greenfin (192.168.132.224):

# 1. Install dependencies
sudo apt install arp-scan avahi-utils tcpdump

# 2. Create directories
mkdir -p /ganuda/services/{iot_discovery,network_monitor,honeypot}

# 3. Deploy scripts (copy from above)

# 4. Install Python dependencies
pip3 install paramiko psycopg2-binary

# 5. Deploy and run database schema on bluefin

# 6. Enable services
sudo systemctl enable --now iot-discovery.timer
sudo systemctl enable --now network-monitor
sudo systemctl enable --now ssh-honeypot

# On all Linux nodes:
# Deploy /etc/profile.d/cherokee_audit.sh for command logging
```

### 5.3 Telegram Integration

Eagle Eye can now answer:
- "What IoT devices are on the network?"
- "Show me unauthorized devices"
- "Any honeypot activity?"
- "Network anomalies today?"

---

**For Seven Generations.**
*See everything. Trust nothing. Protect the tribe.*
