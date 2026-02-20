#!/usr/bin/env python3
"""
Cherokee AI Power Reporter - Local Node Reporter
Each node runs this to report its own power metrics to bluefin

Deploy to each node and run via cron/systemd timer
"""

import subprocess
import json
import re
import time
import os
import socket
from datetime import datetime
import psycopg2

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": os.environ.get('CHEROKEE_DB_PASS', ''),
    "database": "zammad_production"
}

# Auto-detect node name from hostname
HOSTNAME = socket.gethostname().split('.')[0]

# Node configs (TDP estimates for power calculation)
NODE_CONFIGS = {
    "bluefin": {"type": "linux_intel", "cpu_tdp": 150},
    "redfin": {"type": "linux_nvidia", "cpu_tdp": 125, "gpu_tdp": 350},
    "greenfin": {"type": "linux_amd", "cpu_tdp": 65, "gpu_tdp": 15},
    "sasass": {"type": "macos", "cpu_tdp": 60},
    "sasass2": {"type": "macos", "cpu_tdp": 60},
}


def get_local_cmd(cmd: str, timeout: int = 10) -> str:
    """Execute local command and return output"""
    try:
        result = subprocess.check_output(cmd, shell=True, timeout=timeout, stderr=subprocess.DEVNULL)
        return result.decode().strip()
    except Exception:
        return ""


def get_cpu_util_linux() -> float:
    """Get CPU utilization from /proc/stat"""
    try:
        out1 = get_local_cmd("grep 'cpu ' /proc/stat")
        time.sleep(0.5)
        out2 = get_local_cmd("grep 'cpu ' /proc/stat")

        if out1 and out2:
            p1 = [int(x) for x in out1.split()[1:8]]
            p2 = [int(x) for x in out2.split()[1:8]]

            idle1, idle2 = p1[3], p2[3]
            total1, total2 = sum(p1), sum(p2)

            idle_delta = idle2 - idle1
            total_delta = total2 - total1

            if total_delta > 0:
                return 100 * (1 - idle_delta / total_delta)
    except Exception:
        pass
    return None


def get_cpu_temp_linux() -> float:
    """Get CPU temp from hwmon"""
    # Try coretemp first, then k10temp for AMD
    for pattern in ["coretemp", "k10temp", "acpitz"]:
        cmd = f"for h in /sys/class/hwmon/hwmon*; do if grep -q '{pattern}' $h/name 2>/dev/null; then cat $h/temp1_input 2>/dev/null; break; fi; done"
        out = get_local_cmd(cmd)
        if out:
            try:
                return int(out) / 1000
            except Exception:
                pass

    # Fallback: any temp1_input
    out = get_local_cmd("cat /sys/class/hwmon/hwmon*/temp1_input 2>/dev/null | head -1")
    if out:
        try:
            return int(out) / 1000
        except Exception:
            pass
    return None


def get_intel_rapl_power() -> float:
    """Get CPU power from Intel RAPL (requires root or readable sysfs)"""
    try:
        e1 = get_local_cmd("cat /sys/class/powercap/intel-rapl:0/energy_uj 2>/dev/null")
        if not e1:
            return None
        e1 = int(e1)
        time.sleep(1)
        e2 = int(get_local_cmd("cat /sys/class/powercap/intel-rapl:0/energy_uj"))
        return (e2 - e1) / 1_000_000
    except Exception:
        return None


def estimate_cpu_power(cpu_util: float, tdp: float) -> float:
    """Estimate CPU power from utilization"""
    if cpu_util is None or tdp is None:
        return None
    idle_power = tdp * 0.10
    return idle_power + (tdp - idle_power) * (cpu_util / 100)


def get_nvidia_power() -> dict:
    """Get NVIDIA GPU metrics"""
    result = {"power": None, "temp": None, "util": None}
    try:
        out = get_local_cmd("nvidia-smi --query-gpu=power.draw,temperature.gpu,utilization.gpu --format=csv,noheader,nounits")
        if out:
            parts = [p.strip() for p in out.split(',')]
            if len(parts) >= 3:
                result["power"] = float(parts[0])
                result["temp"] = float(parts[1])
                result["util"] = float(parts[2])
    except Exception:
        pass
    return result


def get_amd_gpu_power() -> dict:
    """Get AMD GPU metrics"""
    result = {"power": None, "temp": None}
    try:
        cmd = "for h in /sys/class/hwmon/hwmon*; do if [ \"$(cat $h/name 2>/dev/null)\" = 'amdgpu' ]; then cat $h/power1_average 2>/dev/null; fi; done"
        out = get_local_cmd(cmd)
        if out:
            result["power"] = int(out) / 1_000_000

        cmd = "for h in /sys/class/hwmon/hwmon*; do if [ \"$(cat $h/name 2>/dev/null)\" = 'amdgpu' ]; then cat $h/temp1_input 2>/dev/null; fi; done"
        out = get_local_cmd(cmd)
        if out:
            result["temp"] = int(out) / 1000
    except Exception:
        pass
    return result


def get_memory_linux() -> dict:
    """Get memory usage"""
    result = {"used": None, "total": None}
    try:
        out = get_local_cmd("free -b | grep Mem")
        if out:
            parts = out.split()
            if len(parts) >= 3:
                result["total"] = int(parts[1]) / (1024**3)
                result["used"] = int(parts[2]) / (1024**3)
    except Exception:
        pass
    return result


def get_macos_cpu_util() -> float:
    """Get macOS CPU utilization"""
    try:
        out = get_local_cmd("ps -A -o %cpu | awk '{s+=$1} END {print s}'")
        if out:
            # Total CPU% across all cores, divide by core count
            cores = int(get_local_cmd("sysctl -n hw.ncpu") or 8)
            return float(out) / cores
    except Exception:
        pass
    return None


def collect_metrics() -> dict:
    """Collect metrics for this node"""
    config = NODE_CONFIGS.get(HOSTNAME, {"type": "linux_intel", "cpu_tdp": 100})
    node_type = config["type"]
    cpu_tdp = config.get("cpu_tdp", 100)

    ip = get_local_cmd("hostname -I | awk '{print $1}'") or "unknown"

    metrics = {
        "node_name": HOSTNAME,
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
        "power_source": "estimated",
    }

    # Linux nodes
    if "linux" in node_type:
        metrics["cpu_util"] = get_cpu_util_linux()
        metrics["cpu_temp"] = get_cpu_temp_linux()

        # Try RAPL
        rapl = get_intel_rapl_power()
        if rapl:
            metrics["cpu_power"] = rapl
            metrics["power_source"] = "rapl"
        elif metrics["cpu_util"] is not None:
            metrics["cpu_power"] = estimate_cpu_power(metrics["cpu_util"], cpu_tdp)

        # Memory
        mem = get_memory_linux()
        metrics["mem_used"] = mem.get("used")
        metrics["mem_total"] = mem.get("total")

        # GPU
        if node_type == "linux_nvidia":
            gpu = get_nvidia_power()
            metrics["gpu_power"] = gpu.get("power")
            metrics["gpu_temp"] = gpu.get("temp")
            metrics["gpu_util"] = gpu.get("util")
            if gpu.get("power"):
                metrics["power_source"] = "nvidia"
        elif node_type == "linux_amd":
            gpu = get_amd_gpu_power()
            metrics["gpu_power"] = gpu.get("power")
            metrics["gpu_temp"] = gpu.get("temp")

    # macOS
    elif node_type == "macos":
        metrics["cpu_util"] = get_macos_cpu_util()
        if metrics["cpu_util"] is not None:
            metrics["cpu_power"] = estimate_cpu_power(metrics["cpu_util"], cpu_tdp)

    # Total power
    cpu_p = metrics.get("cpu_power") or 0
    gpu_p = metrics.get("gpu_power") or 0
    if cpu_p or gpu_p:
        metrics["total_power"] = cpu_p + gpu_p

    return metrics


def save_metrics(metrics: dict) -> bool:
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


def run():
    """Single collection run"""
    metrics = collect_metrics()

    power_str = f"{metrics['total_power']:.1f}W" if metrics.get('total_power') else "N/A"
    extra = ""
    if metrics.get("gpu_power"):
        extra += f" (GPU: {metrics['gpu_power']:.1f}W)"
    if metrics.get("cpu_temp"):
        extra += f" [{metrics['cpu_temp']:.0f}°C]"

    print(f"[{datetime.now()}] {HOSTNAME}: {power_str}{extra} [{metrics.get('power_source')}]")

    if save_metrics(metrics):
        print(f"[{datetime.now()}] Saved to database")
    else:
        print(f"[{datetime.now()}] FAILED to save")


if __name__ == "__main__":
    run()
