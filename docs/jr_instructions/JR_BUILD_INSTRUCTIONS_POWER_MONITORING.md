# JR BUILD INSTRUCTIONS: Tribe Power Monitoring

**Target**: greenfin (192.168.132.224) - runs collector
**Scope**: All 6 Cherokee nodes
**Date**: December 13, 2025
**Priority**: P2 - Infrastructure

## Overview

Power monitoring for the Cherokee AI Federation. Collects CPU, GPU, and system power metrics from all nodes every 5 minutes.

## Data Sources by Node

| Node | IP | CPU Power | GPU Power | Temp |
|------|-----|-----------|-----------|------|
| bluefin | .222 | Intel RAPL | N/A | lm-sensors |
| redfin | .223 | Intel RAPL | nvidia-smi | nvidia-smi |
| greenfin | .224 | Intel RAPL | AMD hwmon | hwmon |
| sasass | .241 | powermetrics | Apple M-series | powermetrics |
| sasass2 | .242 | powermetrics | Apple M-series | powermetrics |

## Database Schema (CREATED)

```sql
-- Raw metrics (every 5 min)
tribe_power_metrics (
    node_name, node_ip, timestamp,
    cpu_power_watts, cpu_temp_celsius, cpu_utilization,
    gpu_power_watts, gpu_temp_celsius, gpu_utilization,
    memory_used_gb, memory_total_gb,
    total_power_watts, raw_data
)

-- Daily aggregates
tribe_power_daily (
    node_name, date,
    avg_cpu_power, max_cpu_power,
    avg_gpu_power, max_gpu_power,
    avg_total_power, max_total_power,
    energy_kwh, sample_count
)
```

## Implementation

### 1. Power Collector Script

Create `/ganuda/services/longhouse/power_collector.py`:

```python
#!/usr/bin/env python3
"""
Cherokee AI Tribe Power Collector
Runs on greenfin, collects from all nodes
"""

import subprocess
import json
import re
import time
from datetime import datetime
import psycopg2

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

NODES = {
    "bluefin": {"ip": "192.168.132.222", "type": "linux_intel"},
    "redfin": {"ip": "192.168.132.223", "type": "linux_nvidia"},
    "greenfin": {"ip": "192.168.132.224", "type": "linux_amd"},
    "sasass": {"ip": "192.168.132.241", "type": "macos"},
    "sasass2": {"ip": "192.168.132.242", "type": "macos"},
}


def get_linux_intel_power(ip: str) -> dict:
    """Get power from Intel RAPL and lm-sensors"""
    result = {"cpu_power": None, "cpu_temp": None, "cpu_util": None}

    try:
        # CPU power from RAPL (two readings 1 sec apart)
        cmd = f"ssh dereadi@{ip} 'cat /sys/class/powercap/intel-rapl:0/energy_uj'"
        e1 = int(subprocess.check_output(cmd, shell=True, timeout=10).strip())
        time.sleep(1)
        e2 = int(subprocess.check_output(cmd, shell=True, timeout=10).strip())
        result["cpu_power"] = (e2 - e1) / 1_000_000  # Convert µJ to W

        # CPU temp from sensors
        cmd = f"ssh dereadi@{ip} 'sensors -u coretemp-isa-0000 2>/dev/null | grep temp1_input | head -1'"
        out = subprocess.check_output(cmd, shell=True, timeout=10).decode()
        match = re.search(r'(\d+\.?\d*)', out)
        if match:
            result["cpu_temp"] = float(match.group(1))

        # CPU utilization
        cmd = f"ssh dereadi@{ip} \"top -bn1 | grep 'Cpu(s)' | awk '{{print 100 - \\$8}}'\""
        out = subprocess.check_output(cmd, shell=True, timeout=10).decode().strip()
        result["cpu_util"] = float(out) if out else None

    except Exception as e:
        print(f"[WARN] Intel power read failed for {ip}: {e}")

    return result


def get_nvidia_power(ip: str) -> dict:
    """Get NVIDIA GPU power and temp"""
    result = {"gpu_power": None, "gpu_temp": None, "gpu_util": None}

    try:
        cmd = f"ssh dereadi@{ip} 'nvidia-smi --query-gpu=power.draw,temperature.gpu,utilization.gpu --format=csv,noheader,nounits'"
        out = subprocess.check_output(cmd, shell=True, timeout=10).decode().strip()
        parts = [p.strip() for p in out.split(',')]
        if len(parts) >= 3:
            result["gpu_power"] = float(parts[0])
            result["gpu_temp"] = float(parts[1])
            result["gpu_util"] = float(parts[2])
    except Exception as e:
        print(f"[WARN] NVIDIA power read failed for {ip}: {e}")

    return result


def get_amd_gpu_power(ip: str) -> dict:
    """Get AMD GPU power from hwmon"""
    result = {"gpu_power": None, "gpu_temp": None}

    try:
        # Find amdgpu hwmon
        cmd = f"ssh dereadi@{ip} 'cat /sys/class/hwmon/hwmon*/power1_average 2>/dev/null | head -1'"
        out = subprocess.check_output(cmd, shell=True, timeout=10).decode().strip()
        if out:
            result["gpu_power"] = int(out) / 1_000_000  # µW to W

        cmd = f"ssh dereadi@{ip} 'cat /sys/class/hwmon/hwmon*/temp1_input 2>/dev/null | head -1'"
        out = subprocess.check_output(cmd, shell=True, timeout=10).decode().strip()
        if out:
            result["gpu_temp"] = int(out) / 1000  # mC to C
    except Exception as e:
        print(f"[WARN] AMD GPU power read failed for {ip}: {e}")

    return result


def get_macos_power(ip: str) -> dict:
    """Get power from macOS powermetrics (needs sudo)"""
    result = {"cpu_power": None, "gpu_power": None, "cpu_temp": None}

    try:
        # powermetrics requires root, use cached values if available
        cmd = f"ssh dereadi@{ip} 'cat /tmp/powermetrics.json 2>/dev/null'"
        out = subprocess.check_output(cmd, shell=True, timeout=10).decode().strip()
        if out:
            data = json.loads(out)
            result["cpu_power"] = data.get("cpu_power")
            result["gpu_power"] = data.get("gpu_power")
    except Exception as e:
        print(f"[WARN] macOS power read failed for {ip}: {e}")

    return result


def get_memory_usage(ip: str, node_type: str) -> dict:
    """Get memory usage"""
    result = {"mem_used": None, "mem_total": None}

    try:
        if "linux" in node_type:
            cmd = f"ssh dereadi@{ip} 'free -g | grep Mem'"
            out = subprocess.check_output(cmd, shell=True, timeout=10).decode()
            parts = out.split()
            if len(parts) >= 3:
                result["mem_total"] = float(parts[1])
                result["mem_used"] = float(parts[2])
        else:  # macOS
            cmd = f"ssh dereadi@{ip} 'vm_stat | head -5'"
            # Parse macOS vm_stat (more complex)
            pass
    except Exception as e:
        print(f"[WARN] Memory read failed for {ip}: {e}")

    return result


def collect_node(name: str, info: dict) -> dict:
    """Collect all metrics for a node"""
    ip = info["ip"]
    node_type = info["type"]

    metrics = {
        "node_name": name,
        "node_ip": ip,
        "timestamp": datetime.now(),
        "cpu_power": None,
        "cpu_temp": None,
        "cpu_util": None,
        "gpu_power": None,
        "gpu_temp": None,
        "gpu_util": None,
        "mem_used": None,
        "mem_total": None,
        "total_power": None,
    }

    # Get CPU power (Intel RAPL for Linux)
    if "linux" in node_type:
        cpu = get_linux_intel_power(ip)
        metrics.update({
            "cpu_power": cpu.get("cpu_power"),
            "cpu_temp": cpu.get("cpu_temp"),
            "cpu_util": cpu.get("cpu_util"),
        })
    elif node_type == "macos":
        mac = get_macos_power(ip)
        metrics.update({
            "cpu_power": mac.get("cpu_power"),
            "gpu_power": mac.get("gpu_power"),
        })

    # Get GPU power
    if node_type == "linux_nvidia":
        gpu = get_nvidia_power(ip)
        metrics.update({
            "gpu_power": gpu.get("gpu_power"),
            "gpu_temp": gpu.get("gpu_temp"),
            "gpu_util": gpu.get("gpu_util"),
        })
    elif node_type == "linux_amd":
        gpu = get_amd_gpu_power(ip)
        metrics.update({
            "gpu_power": gpu.get("gpu_power"),
            "gpu_temp": gpu.get("gpu_temp"),
        })

    # Get memory
    mem = get_memory_usage(ip, node_type)
    metrics.update({
        "mem_used": mem.get("mem_used"),
        "mem_total": mem.get("mem_total"),
    })

    # Calculate total power
    cpu_p = metrics.get("cpu_power") or 0
    gpu_p = metrics.get("gpu_power") or 0
    metrics["total_power"] = cpu_p + gpu_p if (cpu_p or gpu_p) else None

    return metrics


def save_metrics(metrics: dict):
    """Save metrics to database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO tribe_power_metrics
            (node_name, node_ip, timestamp,
             cpu_power_watts, cpu_temp_celsius, cpu_utilization,
             gpu_power_watts, gpu_temp_celsius, gpu_utilization,
             memory_used_gb, memory_total_gb, total_power_watts, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            metrics["node_name"],
            metrics["node_ip"],
            metrics["timestamp"],
            metrics.get("cpu_power"),
            metrics.get("cpu_temp"),
            metrics.get("cpu_util"),
            metrics.get("gpu_power"),
            metrics.get("gpu_temp"),
            metrics.get("gpu_util"),
            metrics.get("mem_used"),
            metrics.get("mem_total"),
            metrics.get("total_power"),
            json.dumps(metrics, default=str),
        ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return False


def run_collection():
    """Single collection run"""
    print(f"[{datetime.now()}] Power collection starting...")

    for name, info in NODES.items():
        try:
            metrics = collect_node(name, info)
            if save_metrics(metrics):
                power_str = f"{metrics.get('total_power', 'N/A'):.1f}W" if metrics.get('total_power') else "N/A"
                print(f"  {name}: {power_str}")
        except Exception as e:
            print(f"  {name}: ERROR - {e}")

    print(f"[{datetime.now()}] Power collection done")


if __name__ == "__main__":
    run_collection()
```

### 2. Systemd Timer

Create `/ganuda/services/longhouse/power-collector.service`:

```ini
[Unit]
Description=Cherokee AI Power Collector
After=network.target

[Service]
Type=oneshot
User=dereadi
WorkingDirectory=/ganuda/services/longhouse
ExecStart=/usr/bin/python3 /ganuda/services/longhouse/power_collector.py
Nice=15
CPUQuota=10%

[Install]
WantedBy=multi-user.target
```

Create `/ganuda/services/longhouse/power-collector.timer`:

```ini
[Unit]
Description=Cherokee AI Power Collector Timer

[Timer]
# Run every 5 minutes
OnCalendar=*:0/5
RandomizedDelaySec=30
Persistent=false

[Install]
WantedBy=timers.target
```

### 3. Daily Aggregation Script

Add to `/ganuda/scripts/power_daily_aggregate.sql`:

```sql
-- Run daily via cron at 00:05
INSERT INTO tribe_power_daily
(node_name, date, avg_cpu_power, max_cpu_power, avg_gpu_power, max_gpu_power,
 avg_total_power, max_total_power, energy_kwh, sample_count)
SELECT
    node_name,
    DATE(timestamp),
    AVG(cpu_power_watts),
    MAX(cpu_power_watts),
    AVG(gpu_power_watts),
    MAX(gpu_power_watts),
    AVG(total_power_watts),
    MAX(total_power_watts),
    -- Energy = avg power * hours (288 samples/day * 5min = 24h)
    AVG(total_power_watts) * 24 / 1000,
    COUNT(*)
FROM tribe_power_metrics
WHERE DATE(timestamp) = CURRENT_DATE - INTERVAL '1 day'
GROUP BY node_name, DATE(timestamp)
ON CONFLICT (node_name, date) DO UPDATE SET
    avg_cpu_power = EXCLUDED.avg_cpu_power,
    max_cpu_power = EXCLUDED.max_cpu_power,
    avg_gpu_power = EXCLUDED.avg_gpu_power,
    max_gpu_power = EXCLUDED.max_gpu_power,
    avg_total_power = EXCLUDED.avg_total_power,
    max_total_power = EXCLUDED.max_total_power,
    energy_kwh = EXCLUDED.energy_kwh,
    sample_count = EXCLUDED.sample_count;
```

### 4. macOS Power Helper (on sasass/sasass2)

Create `/Users/Shared/ganuda/scripts/powermetrics_cache.sh`:

```bash
#!/bin/bash
# Run via launchd every 5 minutes as root
# Caches powermetrics output for non-root readers

sudo powermetrics -i 1000 -n 1 --samplers cpu_power,gpu_power -o /tmp/powermetrics_raw.txt 2>/dev/null

# Parse to JSON
cpu_power=$(grep "CPU Power" /tmp/powermetrics_raw.txt | awk '{print $3}')
gpu_power=$(grep "GPU Power" /tmp/powermetrics_raw.txt | awk '{print $3}')

cat > /tmp/powermetrics.json << EOF
{"cpu_power": $cpu_power, "gpu_power": $gpu_power, "timestamp": "$(date -Iseconds)"}
EOF

chmod 644 /tmp/powermetrics.json
```

## Testing

```bash
# Test single collection
cd /ganuda/services/longhouse
python3 power_collector.py

# Check data
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c \
  "SELECT node_name, total_power_watts, timestamp FROM tribe_power_metrics ORDER BY timestamp DESC LIMIT 10;"
```

## Expected Output

```
[2025-12-13 ...] Power collection starting...
  bluefin: 45.2W
  redfin: 65.8W (GPU: 10.8W)
  greenfin: 32.1W (GPU: 7.0W)
  sasass: N/A (needs powermetrics setup)
  sasass2: N/A (needs powermetrics setup)
[2025-12-13 ...] Power collection done
```

## Power Budget Estimates

| Node | Idle | Typical | Peak |
|------|------|---------|------|
| bluefin | 30W | 50W | 150W |
| redfin | 40W | 80W | 350W (GPU) |
| greenfin | 20W | 35W | 100W |
| sasass | 15W | 30W | 75W |
| sasass2 | 15W | 30W | 75W |
| **Total** | **120W** | **225W** | **750W** |

## Verification Checklist

- [ ] Tables created in database
- [ ] Collector runs without errors
- [ ] Data appearing in tribe_power_metrics
- [ ] Timer runs every 5 minutes
- [ ] Daily aggregation working

---

FOR SEVEN GENERATIONS
