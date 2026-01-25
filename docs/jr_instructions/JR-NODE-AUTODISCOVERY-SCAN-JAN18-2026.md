# Jr Instructions: Automated Node Discovery & CMDB Scanning

**Priority**: P1 (Critical Infrastructure Gap)
**Assigned To**: Infrastructure Jr / IT Triad
**Created**: 2026-01-18
**Council Vote**: Required before deployment

## Problem Statement

The CMDB is manually maintained and frequently out of date. Hardware changes (GPU swaps, memory upgrades) are not automatically detected. We had incorrect data for both redfin (RTX 6000 not recorded) and bluefin (listed as AMD when it's Intel).

**This is unacceptable for a production AI federation.**

## Requirements

1. **Scheduled node scanning** - All nodes scanned daily for hardware/software changes
2. **Performance metrics** - CPU, memory, GPU utilization collected hourly
3. **Security scanning** - Open ports, failed logins, package vulnerabilities
4. **Event collection** - System events, service restarts, errors
5. **Automatic CMDB updates** - No manual intervention required

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Scheduled Cron Jobs                       │
│                    (on each node)                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              /ganuda/scripts/node_scanner.py                 │
│  - Hardware discovery (CPU, RAM, GPU, disk)                  │
│  - Software inventory (dpkg/brew/pip packages)               │
│  - Security audit (open ports, failed SSH, CVEs)             │
│  - Performance snapshot (load, memory, GPU util)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  PostgreSQL (bluefin)                        │
│  - hardware_inventory (updated automatically)                │
│  - software_cmdb (package versions)                          │
│  - security_audit_log (new table)                            │
│  - node_performance_metrics (new table)                      │
└─────────────────────────────────────────────────────────────┘
```

## Task 1: Create Node Scanner Script

**File**: `/ganuda/scripts/node_scanner.py`

```python
#!/usr/bin/env python3
"""
Cherokee AI Federation - Automated Node Scanner
Scans local node and updates CMDB automatically.
"""

import subprocess
import json
import socket
import psycopg2
import platform
import os
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def get_hostname():
    return socket.gethostname().split('.')[0]

def get_cpu_info():
    """Get CPU model and core count."""
    if platform.system() == 'Darwin':
        cmd = "sysctl -n machdep.cpu.brand_string"
    else:
        cmd = "grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_memory_total():
    """Get total memory in bytes."""
    if platform.system() == 'Darwin':
        cmd = "sysctl -n hw.memsize"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return int(result.stdout.strip())
    else:
        with open('/proc/meminfo') as f:
            for line in f:
                if 'MemTotal' in line:
                    return int(line.split()[1]) * 1024  # Convert KB to bytes
    return 0

def get_gpu_info():
    """Get GPU details using nvidia-smi or system_profiler."""
    gpus = []
    if platform.system() == 'Darwin':
        cmd = "system_profiler SPDisplaysDataType -json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        try:
            data = json.loads(result.stdout)
            for display in data.get('SPDisplaysDataType', []):
                gpus.append({
                    'name': display.get('sppci_model', 'Unknown'),
                    'memory': display.get('spdisplays_vram', 'Unknown'),
                    'vendor': display.get('sppci_vendor', 'Apple')
                })
        except json.JSONDecodeError:
            pass
    else:
        cmd = "nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(', ')
                    gpus.append({
                        'name': parts[0] if len(parts) > 0 else 'Unknown',
                        'memory': parts[1] if len(parts) > 1 else 'Unknown',
                        'driver': parts[2] if len(parts) > 2 else 'Unknown'
                    })
    return gpus

def get_disk_info():
    """Get disk usage information."""
    disks = []
    cmd = "df -B1 / /ganuda 2>/dev/null | tail -n +2"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split()
            if len(parts) >= 6:
                disks.append({
                    'mount': parts[5],
                    'total': int(parts[1]),
                    'used': int(parts[2]),
                    'available': int(parts[3])
                })
    return disks

def get_os_info():
    """Get OS version."""
    if platform.system() == 'Darwin':
        cmd = "sw_vers -productName && sw_vers -productVersion"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.replace('\n', ' ').strip()
    else:
        cmd = "cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()

def get_kernel_version():
    """Get kernel/Darwin version."""
    return platform.release()

def get_network_interfaces():
    """Get network interface info."""
    interfaces = []
    if platform.system() == 'Darwin':
        cmd = "ifconfig | grep -E '^[a-z]|inet ' | grep -A1 en0"
    else:
        cmd = "ip -j addr show 2>/dev/null || ip addr show"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    # Simplified - just capture the output
    return {'raw': result.stdout[:500]}

def get_open_ports():
    """Get listening ports for security audit."""
    if platform.system() == 'Darwin':
        cmd = "lsof -iTCP -sTCP:LISTEN -n -P | awk 'NR>1 {print $9}' | sort -u"
    else:
        cmd = "ss -tlnp 2>/dev/null | awk 'NR>1 {print $4}' | sort -u"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip().split('\n')

def get_failed_logins():
    """Get recent failed login attempts."""
    if platform.system() == 'Linux':
        cmd = "journalctl -u sshd --since '24 hours ago' 2>/dev/null | grep -c 'Failed password' || echo 0"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return int(result.stdout.strip() or 0)
    return 0

def get_installed_packages():
    """Get installed packages with versions."""
    packages = []
    hostname = get_hostname()

    if platform.system() == 'Darwin':
        # Homebrew packages
        cmd = "brew list --versions 2>/dev/null"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split()
                packages.append({
                    'hostname': hostname,
                    'name': parts[0],
                    'version': parts[1] if len(parts) > 1 else 'unknown',
                    'type': 'brew'
                })
    else:
        # Key apt packages only
        key_packages = ['python3', 'postgresql', 'nginx', 'docker', 'nvidia-driver', 'cuda']
        cmd = f"dpkg-query -W -f='${{Package}} ${{Version}}\n' {' '.join(key_packages)} 2>/dev/null"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        for line in result.stdout.strip().split('\n'):
            if line and not line.startswith('dpkg-query'):
                parts = line.split()
                if len(parts) >= 2:
                    packages.append({
                        'hostname': hostname,
                        'name': parts[0],
                        'version': parts[1],
                        'type': 'apt'
                    })

    # Python packages in ganuda venv
    venv_pip = '/home/dereadi/cherokee_venv/bin/pip' if platform.system() == 'Linux' else None
    if venv_pip and os.path.exists(venv_pip):
        cmd = f"{venv_pip} list --format=json 2>/dev/null"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        try:
            pip_packages = json.loads(result.stdout)
            for pkg in pip_packages[:20]:  # Limit to 20 key packages
                packages.append({
                    'hostname': hostname,
                    'name': pkg['name'],
                    'version': pkg['version'],
                    'type': 'pip'
                })
        except json.JSONDecodeError:
            pass

    return packages

def update_hardware_inventory(conn):
    """Update hardware_inventory table."""
    hostname = get_hostname()
    cpu = get_cpu_info()
    memory = get_memory_total()
    gpus = get_gpu_info()
    disks = get_disk_info()
    os_info = get_os_info()
    kernel = get_kernel_version()
    network = get_network_interfaces()

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO hardware_inventory (
            hostname, scan_timestamp, cpu_info, memory_total,
            gpu_count, gpu_details, disk_info, os_info,
            kernel_version, network_interfaces, online_status, last_seen
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true, NOW())
        ON CONFLICT (hostname) DO UPDATE SET
            scan_timestamp = EXCLUDED.scan_timestamp,
            cpu_info = EXCLUDED.cpu_info,
            memory_total = EXCLUDED.memory_total,
            gpu_count = EXCLUDED.gpu_count,
            gpu_details = EXCLUDED.gpu_details,
            disk_info = EXCLUDED.disk_info,
            os_info = EXCLUDED.os_info,
            kernel_version = EXCLUDED.kernel_version,
            network_interfaces = EXCLUDED.network_interfaces,
            online_status = true,
            last_seen = NOW()
    """, (
        hostname, datetime.now(), cpu, memory,
        len(gpus), json.dumps(gpus), json.dumps(disks), os_info,
        kernel, json.dumps(network)
    ))
    conn.commit()
    print(f"[{hostname}] Hardware inventory updated")

def update_software_cmdb(conn):
    """Update software_cmdb table."""
    packages = get_installed_packages()
    cur = conn.cursor()

    for pkg in packages:
        cur.execute("""
            INSERT INTO software_cmdb (
                hostname, package_name, version, package_type,
                install_date, last_updated
            ) VALUES (%s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (hostname, package_name, package_type) DO UPDATE SET
                version = EXCLUDED.version,
                last_updated = NOW()
        """, (pkg['hostname'], pkg['name'], pkg['version'], pkg['type']))

    conn.commit()
    print(f"[{pkg['hostname']}] Software CMDB updated: {len(packages)} packages")

def log_security_audit(conn):
    """Log security audit results."""
    hostname = get_hostname()
    open_ports = get_open_ports()
    failed_logins = get_failed_logins()

    cur = conn.cursor()
    # Ensure table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS security_audit_log (
            id SERIAL PRIMARY KEY,
            hostname VARCHAR(100),
            scan_time TIMESTAMP DEFAULT NOW(),
            open_ports JSONB,
            failed_login_count INTEGER,
            findings JSONB
        )
    """)

    cur.execute("""
        INSERT INTO security_audit_log (hostname, open_ports, failed_login_count, findings)
        VALUES (%s, %s, %s, %s)
    """, (hostname, json.dumps(open_ports), failed_logins, json.dumps({})))

    conn.commit()
    print(f"[{hostname}] Security audit logged: {len(open_ports)} open ports, {failed_logins} failed logins")

def main():
    print(f"=== Cherokee Node Scanner - {datetime.now().isoformat()} ===")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        update_hardware_inventory(conn)
        update_software_cmdb(conn)
        log_security_audit(conn)
        conn.close()
        print("=== Scan complete ===")
    except Exception as e:
        print(f"ERROR: {e}")
        raise

if __name__ == '__main__':
    main()
```

## Task 2: Create Systemd Service (Linux)

**File**: `/etc/systemd/system/ganuda-node-scanner.service`

```ini
[Unit]
Description=Cherokee AI Federation Node Scanner
After=network-online.target postgresql.service

[Service]
Type=oneshot
User=dereadi
ExecStart=/home/dereadi/cherokee_venv/bin/python3 /ganuda/scripts/node_scanner.py
StandardOutput=journal
StandardError=journal
```

**File**: `/etc/systemd/system/ganuda-node-scanner.timer`

```ini
[Unit]
Description=Run Cherokee Node Scanner every 6 hours

[Timer]
OnBootSec=5min
OnUnitActiveSec=6h
Persistent=true

[Install]
WantedBy=timers.target
```

## Task 3: Create LaunchAgent (macOS)

**File**: `/Users/Shared/ganuda/LaunchAgents/com.cherokee.node-scanner.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cherokee.node-scanner</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/Shared/ganuda/scripts/node_scanner.py</string>
    </array>
    <key>StartInterval</key>
    <integer>21600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/Shared/ganuda/logs/node_scanner.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/Shared/ganuda/logs/node_scanner.log</string>
</dict>
</plist>
```

## Task 4: Ansible Playbook for Deployment

**File**: `/ganuda/ansible/playbooks/deploy_node_scanner.yml`

```yaml
---
- name: Deploy Cherokee Node Scanner
  hosts: all
  become: yes
  vars:
    scanner_script: /ganuda/scripts/node_scanner.py

  tasks:
    - name: Copy node scanner script
      copy:
        src: ../scripts/node_scanner.py
        dest: "{{ scanner_script }}"
        mode: '0755'

    - name: Install psycopg2 dependency
      pip:
        name: psycopg2-binary
        executable: "{{ '/home/dereadi/cherokee_venv/bin/pip' if ansible_system == 'Linux' else '/usr/local/bin/pip3' }}"

    - name: Deploy systemd timer (Linux)
      when: ansible_system == 'Linux'
      block:
        - copy:
            src: ../systemd/ganuda-node-scanner.service
            dest: /etc/systemd/system/
        - copy:
            src: ../systemd/ganuda-node-scanner.timer
            dest: /etc/systemd/system/
        - systemd:
            name: ganuda-node-scanner.timer
            enabled: yes
            state: started
            daemon_reload: yes

    - name: Deploy LaunchAgent (macOS)
      when: ansible_system == 'Darwin'
      block:
        - copy:
            src: ../LaunchAgents/com.cherokee.node-scanner.plist
            dest: /Library/LaunchAgents/
        - command: launchctl load /Library/LaunchAgents/com.cherokee.node-scanner.plist
          ignore_errors: yes

    - name: Run initial scan
      command: "{{ '/home/dereadi/cherokee_venv/bin/python3' if ansible_system == 'Linux' else '/usr/bin/python3' }} {{ scanner_script }}"
```

## Task 5: Create Performance Metrics Table

```sql
CREATE TABLE IF NOT EXISTS node_performance_metrics (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(100) NOT NULL,
    collected_at TIMESTAMP DEFAULT NOW(),
    cpu_percent REAL,
    memory_percent REAL,
    memory_used_bytes BIGINT,
    gpu_utilization REAL,
    gpu_memory_used BIGINT,
    disk_io_read_bytes BIGINT,
    disk_io_write_bytes BIGINT,
    network_bytes_sent BIGINT,
    network_bytes_recv BIGINT,
    load_average JSONB
);

CREATE INDEX idx_perf_hostname_time ON node_performance_metrics(hostname, collected_at DESC);
```

## Deployment Steps

1. **Council Vote**: Submit for Infrastructure/Security review
2. **Create tables**: Run SQL migrations on bluefin
3. **Deploy scanner**: Push to all nodes via Ansible
4. **Enable timers**: Activate scheduled scanning
5. **Verify**: Check CMDB updates after first scan
6. **Alert setup**: Notify on scan failures

## Success Criteria

- [ ] All 6 nodes scanned automatically every 6 hours
- [ ] Hardware changes detected within 24 hours
- [ ] Security audit log populated
- [ ] No manual CMDB updates required
- [ ] Performance metrics visible in Grafana

## Federation Nodes

| Node | Type | Scanner Schedule |
|------|------|------------------|
| redfin | Linux (AMD/RTX 6000) | systemd timer |
| bluefin | Linux (Intel/RTX 5070) | systemd timer |
| greenfin | Linux (AMD/integrated) | systemd timer |
| sasass | macOS (M1 Max) | LaunchAgent |
| sasass2 | macOS (M1 Max) | LaunchAgent |
| tpm-macbook | macOS (M4) | LaunchAgent |

---
*For Seven Generations - Cherokee AI Federation*
*Automated infrastructure monitoring ensures continuity across generations.*
