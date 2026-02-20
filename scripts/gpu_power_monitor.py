#!/usr/bin/env python3
"""
GPU Power Monitor — Adaptive polling for federation GPU nodes.

Council Vote #ba677ef5213772b7 — Adaptive architecture:
  IDLE mode (300s): Light poll — power + temp only
  ACTIVE mode (15s): Full telemetry — power, temp, util, memory, fan
  Transition: GPU util >40% OR power delta >20% from baseline
  Return to idle: 3 consecutive below-threshold readings

Cherokee AI Federation — For Seven Generations
"""

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime

import psutil
import psycopg2

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

# Adaptive polling thresholds (Council consensus)
IDLE_INTERVAL = 300       # 5 minutes
ACTIVE_INTERVAL = 15      # 15 seconds
UTIL_THRESHOLD = 40.0     # GPU util % to trigger active mode
POWER_DELTA_PCT = 20.0    # Power jump % from baseline to trigger active
COOLDOWN_READINGS = 3     # Consecutive below-threshold to return to idle

GPU_NODES = {
    "redfin": {
        "ip": "192.168.132.223",
        "gpu": "RTX PRO 6000 Blackwell",
        "power_limit": 300,
        "local": True,
    },
    "bluefin": {
        "ip": "192.168.132.222",
        "gpu": "RTX 5070",
        "power_limit": 250,
        "local": False,
    },
}

# State
mode = "idle"  # "idle" or "active"
baseline_power = {}  # node_name -> baseline watts
cooldown_counter = 0
db_conn = None
running = True


def signal_handler(sig, frame):
    global running
    print(f"[{datetime.now().isoformat()}] Signal {sig} received, shutting down...")
    running = False


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def get_db_connection():
    """Get or create persistent DB connection (Spider: avoid connection churn)."""
    global db_conn
    try:
        if db_conn is None or db_conn.closed:
            db_conn = psycopg2.connect(
                host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
            )
            db_conn.autocommit = True
            print(f"[{datetime.now().isoformat()}] DB connection established")
        # Test connection is alive
        db_conn.cursor().execute("SELECT 1")
        return db_conn
    except Exception:
        db_conn = None
        try:
            db_conn = psycopg2.connect(
                host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
            )
            db_conn.autocommit = True
            return db_conn
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] DB connection failed: {e}")
            return None


def query_nvidia_smi(node_name, node_config):
    """Query nvidia-smi for power and utilization data."""
    cmd = [
        "nvidia-smi",
        "--query-gpu=power.draw,power.limit,temperature.gpu,memory.used,memory.total,utilization.gpu,fan.speed",
        "--format=csv,noheader,nounits"
    ]

    try:
        if node_config["local"]:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        else:
            ssh_cmd = ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", node_name] + cmd
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)

        if result.returncode != 0:
            return None

        line = result.stdout.strip()
        if not line:
            return None

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            return None

        return {
            "power_draw_w": float(parts[0]),
            "power_limit_w": float(parts[1]),
            "temperature_c": float(parts[2]),
            "memory_used_mb": float(parts[3]),
            "memory_total_mb": float(parts[4]),
            "gpu_utilization_pct": float(parts[5]),
            "fan_speed_pct": float(parts[6]) if len(parts) > 6 and parts[6] != "[N/A]" else None,
        }
    except (subprocess.TimeoutExpired, Exception):
        return None


def get_cpu_stats():
    """Get CPU utilization and load average (Council: add CPU monitoring at idle interval)."""
    try:
        cpu_pct = psutil.cpu_percent(interval=1)
        load_1, load_5, load_15 = psutil.getloadavg()
        mem = psutil.virtual_memory()
        return {
            "cpu_utilization_pct": cpu_pct,
            "load_avg_1m": load_1,
            "load_avg_5m": load_5,
            "load_avg_15m": load_15,
            "memory_used_pct": mem.percent,
            "memory_used_gb": round(mem.used / (1024**3), 1),
            "memory_total_gb": round(mem.total / (1024**3), 1),
        }
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] CPU stats error: {e}")
        return None


def write_records(records):
    """Write power readings to unified_timeline using persistent connection."""
    if not records:
        return
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        for rec in records:
            cur.execute("""
                INSERT INTO unified_timeline (timestamp, event_type, source, value, metadata, created_at)
                VALUES (NOW(), %s, %s, %s, %s, NOW())
            """, (rec["event_type"], rec["source"], rec["value"],
                  json.dumps(rec["metadata"])))
        cur.close()
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] DB write error: {e}")
        # Reset connection on error
        global db_conn
        db_conn = None


def evaluate_mode(gpu_readings):
    """Evaluate whether to switch polling mode based on GPU data.

    Transition logic (Council consensus):
    - IDLE -> ACTIVE: Any GPU util >40% OR power delta >20% from baseline
    - ACTIVE -> IDLE: 3 consecutive readings ALL below threshold
    """
    global mode, baseline_power, cooldown_counter

    any_active = False
    for node_name, data in gpu_readings.items():
        if data is None:
            continue

        util = data["gpu_utilization_pct"]
        power = data["power_draw_w"]

        # Check utilization threshold
        if util > UTIL_THRESHOLD:
            any_active = True

        # Check power delta from baseline
        if node_name in baseline_power and baseline_power[node_name] > 0:
            delta_pct = abs(power - baseline_power[node_name]) / baseline_power[node_name] * 100
            if delta_pct > POWER_DELTA_PCT:
                any_active = True
        else:
            # Set baseline on first reading
            baseline_power[node_name] = power

    old_mode = mode

    if any_active:
        cooldown_counter = 0
        if mode == "idle":
            mode = "active"
    else:
        cooldown_counter += 1
        if mode == "active" and cooldown_counter >= COOLDOWN_READINGS:
            mode = "idle"
            cooldown_counter = 0
            # Update baselines when returning to idle
            for node_name, data in gpu_readings.items():
                if data:
                    baseline_power[node_name] = data["power_draw_w"]

    # Log transitions (Crawdad: log all mode changes)
    if old_mode != mode:
        now = datetime.now().isoformat()
        print(f"[{now}] MODE TRANSITION: {old_mode} -> {mode}")
        transition_record = [{
            "event_type": "power_monitor_mode_change",
            "source": "gpu_power_monitor",
            "value": 1.0 if mode == "active" else 0.0,
            "metadata": {
                "old_mode": old_mode,
                "new_mode": mode,
                "trigger": "utilization" if any_active else "cooldown",
                "gpu_readings": {n: d["gpu_utilization_pct"] for n, d in gpu_readings.items() if d},
                "timestamp": now,
            },
        }]
        write_records(transition_record)


def poll_cycle(include_cpu=False):
    """Run one polling cycle. Returns GPU readings for mode evaluation."""
    records = []
    total_watts = 0.0
    gpu_readings = {}

    for node_name, config in GPU_NODES.items():
        data = query_nvidia_smi(node_name, config)
        gpu_readings[node_name] = data
        if data is None:
            continue

        source = f"gpu_{node_name}"
        meta = {
            "node": node_name,
            "gpu_model": config["gpu"],
            "power_draw_w": data["power_draw_w"],
            "power_limit_w": data["power_limit_w"],
            "temperature_c": data["temperature_c"],
            "gpu_utilization_pct": data["gpu_utilization_pct"],
            "monitoring_mode": mode,
        }

        # Always record power draw
        records.append({
            "event_type": "gpu_power_draw",
            "source": source,
            "value": data["power_draw_w"],
            "metadata": meta,
        })

        # Full telemetry only in active mode
        if mode == "active":
            full_meta = {**meta,
                "memory_used_mb": data["memory_used_mb"],
                "memory_total_mb": data["memory_total_mb"],
                "fan_speed_pct": data["fan_speed_pct"],
                "power_efficiency_pct": round(data["power_draw_w"] / data["power_limit_w"] * 100, 1),
            }
            records.append({
                "event_type": "gpu_temperature",
                "source": source,
                "value": data["temperature_c"],
                "metadata": full_meta,
            })
            records.append({
                "event_type": "gpu_utilization",
                "source": source,
                "value": data["gpu_utilization_pct"],
                "metadata": full_meta,
            })

        total_watts += data["power_draw_w"]

    # Cluster total
    if records:
        records.append({
            "event_type": "cluster_gpu_power_total",
            "source": "gpu_cluster",
            "value": total_watts,
            "metadata": {
                "nodes_reporting": len([n for n, d in gpu_readings.items() if d]),
                "total_watts": total_watts,
                "monitoring_mode": mode,
                "timestamp": datetime.now().isoformat(),
            },
        })

    # CPU monitoring at idle interval (Council: add CPU, don't over-poll)
    if include_cpu:
        cpu = get_cpu_stats()
        if cpu:
            records.append({
                "event_type": "host_cpu_utilization",
                "source": "cpu_redfin",
                "value": cpu["cpu_utilization_pct"],
                "metadata": {**cpu, "node": "redfin", "timestamp": datetime.now().isoformat()},
            })

    write_records(records)

    now = datetime.now().strftime("%H:%M:%S")
    node_summary = ", ".join(
        f"{n}: {gpu_readings[n]['power_draw_w']:.0f}W/{gpu_readings[n]['gpu_utilization_pct']:.0f}%"
        for n in gpu_readings if gpu_readings[n]
    )
    print(f"[{now}] [{mode.upper():6s}] {total_watts:.0f}W total | {node_summary}")

    return gpu_readings


def main():
    global mode
    print(f"[{datetime.now().isoformat()}] GPU Power Monitor starting (adaptive mode)")
    print(f"  Idle: {IDLE_INTERVAL}s | Active: {ACTIVE_INTERVAL}s")
    print(f"  Util threshold: {UTIL_THRESHOLD}% | Power delta: {POWER_DELTA_PCT}%")
    print(f"  Cooldown: {COOLDOWN_READINGS} readings")

    cycle_count = 0

    while running:
        cycle_count += 1
        include_cpu = (mode == "idle")  # CPU only during idle polls

        gpu_readings = poll_cycle(include_cpu=include_cpu)
        evaluate_mode(gpu_readings)

        sleep_time = ACTIVE_INTERVAL if mode == "active" else IDLE_INTERVAL

        # Sleep in small increments so we can respond to signals
        elapsed = 0
        while elapsed < sleep_time and running:
            time.sleep(min(5, sleep_time - elapsed))
            elapsed += 5

    # Cleanup
    if db_conn and not db_conn.closed:
        db_conn.close()
    print(f"[{datetime.now().isoformat()}] GPU Power Monitor stopped")


if __name__ == "__main__":
    main()
