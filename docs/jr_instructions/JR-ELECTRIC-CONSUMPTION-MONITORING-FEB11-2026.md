# Jr Instruction: Federation Electric Consumption Monitoring

**Task**: Add REST API power polling to the Solix daemon and create a GPU power monitor script that tracks electric consumption across the cluster.

**Priority**: P1
**Kanban**: #1763 (sub-task: consumption metrics)
**Assigned**: Infrastructure Jr.

---

## Context

The Solix F3800 Plus battery monitor daemon on greenfin gets MQTT heartbeats but the F3800 firmware doesn't push watt/SOC data via MQTT payload. We need periodic REST API calls for actual power metrics. Additionally, the cluster has two GPUs (redfin RTX PRO 6000 96GB, bluefin RTX 5070 12GB) that we need to monitor for power draw. All data goes to unified_timeline on bluefin for dashboards.

**Current power readings (idle):**
- redfin GPU: 72W draw / 300W limit (RTX PRO 6000 Blackwell)
- bluefin GPU: 13W draw / 250W limit (RTX 5070)
- Solix F3800 Plus: heartbeats only, no watt data yet

## Step 1: Enhance Solix Daemon with REST API Power Polling

File: `/ganuda/services/power_monitor/solix_monitor_daemon.py`

<<<<<<< SEARCH
    async def _monitor_session(self):
        """Single MQTT monitoring session with reconnect."""
        async with ClientSession() as websession:
            log.info("Authenticating with Anker cloud...")
            self.api = AnkerSolixApi(
                ANKER_USER, ANKER_PASS, ANKER_COUNTRY, websession
            )
            await self.api.async_authenticate()
            log.info("Authenticated. Getting devices...")

            await self.api.update_sites()
            await self.api.get_bind_devices()
            self.devices = dict(self.api.devices)
=======
    async def _poll_rest_api(self):
        """Poll Anker REST API for power metrics not available via MQTT."""
        try:
            await self.api.async_update_device_details()
            for sn, dev in self.api.devices.items():
                name = dev.get("device_name") or dev.get("name", sn)
                source = f"solix_{sn}"

                # Extract power metrics from REST API response
                soc = dev.get("battery_soc") or dev.get("batt_soc") or dev.get("battery_capacity")
                input_power = dev.get("input_power") or dev.get("charging_power") or dev.get("solar_power")
                output_power = dev.get("output_power") or dev.get("discharging_power")
                grid_power = dev.get("grid_power") or dev.get("home_load_power")

                meta = {
                    "device_sn": sn,
                    "device_name": name,
                    "data_source": "rest_api",
                    "polling_mode": "FAST" if self.fast_mode else "normal",
                    "raw_device_keys": [k for k in dev.keys() if any(
                        x in k.lower() for x in ["power", "watt", "soc", "battery", "energy", "solar", "grid", "charge"]
                    )],
                }

                if soc is not None:
                    try:
                        soc_val = float(soc)
                        write_timeline("solix_battery_soc", source, soc_val, meta)
                        self.update_polling_mode(sn, soc_val)
                        check_alerts(soc_val, name, float(output_power or 0))
                    except (ValueError, TypeError):
                        pass

                if input_power is not None:
                    try:
                        write_timeline("solix_power_input", source, float(input_power), meta)
                    except (ValueError, TypeError):
                        pass

                if output_power is not None:
                    try:
                        write_timeline("solix_power_output", source, float(output_power), meta)
                    except (ValueError, TypeError):
                        pass

                if grid_power is not None:
                    try:
                        write_timeline("solix_grid_power", source, float(grid_power), meta)
                    except (ValueError, TypeError):
                        pass

                # Log a summary line
                log.info("REST API: %s SOC=%s%% In=%sW Out=%sW Grid=%sW",
                         name,
                         soc if soc is not None else "?",
                         input_power if input_power is not None else "?",
                         output_power if output_power is not None else "?",
                         grid_power if grid_power is not None else "?")

                # Log all power-related keys on first poll for field discovery
                if not hasattr(self, '_rest_fields_logged'):
                    power_keys = {k: v for k, v in dev.items() if any(
                        x in k.lower() for x in ["power", "watt", "soc", "battery", "energy", "solar", "grid", "charge", "consumption"]
                    )}
                    if power_keys:
                        log.info("REST API fields for %s: %s", name, power_keys)
                        self._rest_fields_logged = True

        except Exception as e:
            log.warning("REST API poll failed (non-fatal): %s", e)

    async def _monitor_session(self):
        """Single MQTT monitoring session with reconnect."""
        async with ClientSession() as websession:
            log.info("Authenticating with Anker cloud...")
            self.api = AnkerSolixApi(
                ANKER_USER, ANKER_PASS, ANKER_COUNTRY, websession
            )
            await self.api.async_authenticate()
            log.info("Authenticated. Getting devices...")

            await self.api.update_sites()
            await self.api.get_bind_devices()
            self.devices = dict(self.api.devices)
>>>>>>> REPLACE

File: `/ganuda/services/power_monitor/solix_monitor_daemon.py`

<<<<<<< SEARCH
            try:
                cycle = 0
                while self.running:
                    await asyncio.sleep(self.interval)
                    cycle += 1

                    # Re-trigger real-time data for all devices
                    for sn, dev in self.devices.items():
                        mqtt_session.realtime_trigger(
                            deviceDict=dev,
                            timeout=self.interval,
                            wait_for_publish=2,
                        )

                    if cycle % 10 == 0:
                        mode = "FAST" if self.fast_mode else "normal"
                        log.info("Heartbeat: cycle %d, mode=%s, interval=%ds",
                                 cycle, mode, self.interval)
=======
            try:
                cycle = 0
                while self.running:
                    await asyncio.sleep(self.interval)
                    cycle += 1

                    # Re-trigger real-time data for all devices
                    for sn, dev in self.devices.items():
                        mqtt_session.realtime_trigger(
                            deviceDict=dev,
                            timeout=self.interval,
                            wait_for_publish=2,
                        )

                    # REST API poll every 5th cycle (~10min at normal, ~2.5min at fast)
                    if cycle % 5 == 0:
                        await self._poll_rest_api()

                    if cycle % 10 == 0:
                        mode = "FAST" if self.fast_mode else "normal"
                        log.info("Heartbeat: cycle %d, mode=%s, interval=%ds",
                                 cycle, mode, self.interval)
>>>>>>> REPLACE

## Step 2: Create GPU Power Monitor Script

Create `/ganuda/scripts/gpu_power_monitor.py`

```python
#!/usr/bin/env python3
"""
GPU Power Monitor — Tracks electric consumption across federation GPU nodes.

Polls nvidia-smi on redfin and bluefin, writes to unified_timeline.
Designed to run as a systemd timer or cron job every 60 seconds.

Cherokee AI Federation — For Seven Generations
"""

import json
import os
import subprocess
import sys
from datetime import datetime

import psycopg2
import psycopg2.extras

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

# GPU nodes in the federation
GPU_NODES = {
    "redfin": {
        "ip": "192.168.132.223",
        "gpu": "RTX PRO 6000 Blackwell",
        "power_limit": 300,
        "local": True,  # This script runs on redfin
    },
    "bluefin": {
        "ip": "192.168.132.222",
        "gpu": "RTX 5070",
        "power_limit": 250,
        "local": False,
    },
}


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
            ssh_cmd = ["ssh", "-o", "ConnectTimeout=5", node_name] + cmd
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)

        if result.returncode != 0:
            print(f"[{node_name}] nvidia-smi failed: {result.stderr.strip()}")
            return None

        line = result.stdout.strip()
        if not line:
            return None

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            print(f"[{node_name}] Unexpected nvidia-smi output: {line}")
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
    except subprocess.TimeoutExpired:
        print(f"[{node_name}] nvidia-smi timed out")
        return None
    except Exception as e:
        print(f"[{node_name}] Error: {e}")
        return None


def write_to_db(records):
    """Write power readings to unified_timeline."""
    if not records:
        return

    try:
        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
        )
        cur = conn.cursor()

        for rec in records:
            cur.execute("""
                INSERT INTO unified_timeline (event_type, source, value, metadata, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (rec["event_type"], rec["source"], rec["value"],
                  json.dumps(rec["metadata"])))

        conn.commit()
        cur.close()
        conn.close()
        print(f"Wrote {len(records)} power readings to unified_timeline")
    except Exception as e:
        print(f"DB write error: {e}")


def main():
    records = []
    total_watts = 0.0

    for node_name, config in GPU_NODES.items():
        data = query_nvidia_smi(node_name, config)
        if data is None:
            continue

        source = f"gpu_{node_name}"
        meta = {
            "node": node_name,
            "ip": config["ip"],
            "gpu_model": config["gpu"],
            "power_draw_w": data["power_draw_w"],
            "power_limit_w": data["power_limit_w"],
            "temperature_c": data["temperature_c"],
            "memory_used_mb": data["memory_used_mb"],
            "memory_total_mb": data["memory_total_mb"],
            "gpu_utilization_pct": data["gpu_utilization_pct"],
            "fan_speed_pct": data["fan_speed_pct"],
            "power_efficiency_pct": round(data["power_draw_w"] / data["power_limit_w"] * 100, 1),
        }

        # Power draw is the primary metric
        records.append({
            "event_type": "gpu_power_draw",
            "source": source,
            "value": data["power_draw_w"],
            "metadata": meta,
        })

        # Temperature as separate event
        records.append({
            "event_type": "gpu_temperature",
            "source": source,
            "value": data["temperature_c"],
            "metadata": meta,
        })

        # GPU utilization
        records.append({
            "event_type": "gpu_utilization",
            "source": source,
            "value": data["gpu_utilization_pct"],
            "metadata": meta,
        })

        total_watts += data["power_draw_w"]
        print(f"[{node_name}] {config['gpu']}: {data['power_draw_w']:.1f}W / {data['power_limit_w']}W "
              f"({data['gpu_utilization_pct']:.0f}% util, {data['temperature_c']:.0f}C, "
              f"{data['memory_used_mb']:.0f}/{data['memory_total_mb']:.0f}MB)")

    # Write cluster total
    if records:
        records.append({
            "event_type": "cluster_gpu_power_total",
            "source": "gpu_cluster",
            "value": total_watts,
            "metadata": {
                "nodes_reporting": len([r for r in records if r["event_type"] == "gpu_power_draw"]),
                "total_watts": total_watts,
                "timestamp": datetime.now().isoformat(),
            },
        })
        print(f"Cluster GPU total: {total_watts:.1f}W")

    write_to_db(records)


if __name__ == "__main__":
    main()
```

## Step 3: Create Systemd Timer for GPU Power Monitor

Create `/ganuda/scripts/systemd/gpu-power-monitor.service`

```ini
[Unit]
Description=Cherokee AI GPU Power Monitor
After=network-online.target

[Service]
Type=oneshot
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/scripts
ExecStart=/ganuda/venv/bin/python gpu_power_monitor.py
EnvironmentFile=/ganuda/config/secrets.env
Environment=CHEROKEE_DB_PASS=TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE
StandardOutput=journal
StandardError=journal
SyslogIdentifier=gpu-power-monitor
```

Create `/ganuda/scripts/systemd/gpu-power-monitor.timer`

```ini
[Unit]
Description=Cherokee AI GPU Power Monitor Timer (every 60s)

[Timer]
OnBootSec=30
OnUnitActiveSec=60
AccuracySec=5

[Install]
WantedBy=timers.target
```

## Verification

1. After Step 1: Restart solix-monitor on greenfin, check logs for "REST API:" lines with watt values
2. After Step 2: Run `CHEROKEE_DB_PASS=TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE python3 /ganuda/scripts/gpu_power_monitor.py` on redfin — should show both GPU power readings
3. After Step 3: Files staged for sudo deployment. Do NOT deploy systemd files — requires Chief approval.

## Notes

- The Solix REST API poll runs every 5th MQTT cycle (~10 min normal, ~2.5 min fast mode)
- GPU monitor polls every 60 seconds via systemd timer
- All data lands in unified_timeline for Grafana/SAG dashboards
- GPU power is the primary electric cost — the F3800 battery data complements it
- The REST API field discovery log (`REST API fields for...`) runs once on first poll to identify available metrics per device model
