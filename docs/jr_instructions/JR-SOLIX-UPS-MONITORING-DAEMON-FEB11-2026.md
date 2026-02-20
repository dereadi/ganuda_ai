# Jr Instruction: Solix 3800 Plus UPS Monitoring Daemon

**Task ID**: SOLIX-MONITOR-001
**Priority**: P1 (Infrastructure Resilience)
**Kanban**: #1763
**Assigned Specialist**: Eagle Eye (Monitoring)
**Estimated Hours**: 8-12h
**Related KB**: KB-POWER-FAILURE-RECOVERY-FEB07-2026, ULTRATHINK-OURO-LOOPED-LLM-SOLIX-MONITORING-FEB11-2026

---

## Context

The Cherokee AI Federation has suffered two power outages (Feb 7, Feb 11, 2026) with zero automated alerting. The cluster is powered by an Anker Solix 3800 Plus solar battery. A smart plug with energy monitoring (TP-Link Kasa KP115 or Shelly Plug S) will be deployed on the Solix AC output to monitor wattage. This Jr task builds the monitoring daemon and graceful shutdown orchestrator.

**NOTE**: The smart plug hardware must be deployed and configured on the local WiFi before this code can be tested end-to-end. The daemon should support a `--dry-run` mode for testing without hardware.

---

## Step 1: Create Power Monitor Service

Create `/ganuda/services/power_monitor/power_monitor.py`

```python
#!/usr/bin/env python3
"""
Solix 3800 Plus Power Monitor Daemon

Polls a smart plug (TP-Link Kasa or Shelly) for wattage readings.
Triggers alerts and graceful shutdown when battery is depleting.

Configuration via environment variables:
  POWER_PLUG_TYPE: "kasa" or "shelly"
  POWER_PLUG_IP: IP address of the smart plug
  POWER_POLL_INTERVAL: Seconds between polls (default: 60)
  POWER_WARNING_WATTS: Wattage threshold for WARNING (default: 150)
  POWER_ALERT_WATTS: Wattage threshold for ALERT (default: 80)
  POWER_CRITICAL_WATTS: Wattage threshold for CRITICAL (default: 30)
  POWER_ZERO_WATTS: Wattage considered "dead" (default: 5)
  TELEGRAM_BOT_TOKEN: For alert delivery
  TELEGRAM_CHAT_ID: TPM chat ID for alerts
  SHUTDOWN_ENABLED: "true" to enable graceful shutdown (default: "false")
  DRY_RUN: "true" to log without executing shutdown (default: "true")
"""

import os
import sys
import time
import json
import logging
import signal
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from pathlib import Path

# --- Configuration ---

PLUG_TYPE = os.environ.get("POWER_PLUG_TYPE", "kasa")
PLUG_IP = os.environ.get("POWER_PLUG_IP", "")
POLL_INTERVAL = int(os.environ.get("POWER_POLL_INTERVAL", "60"))
WARNING_WATTS = float(os.environ.get("POWER_WARNING_WATTS", "150"))
ALERT_WATTS = float(os.environ.get("POWER_ALERT_WATTS", "80"))
CRITICAL_WATTS = float(os.environ.get("POWER_CRITICAL_WATTS", "30"))
ZERO_WATTS = float(os.environ.get("POWER_ZERO_WATTS", "5"))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SHUTDOWN_ENABLED = os.environ.get("SHUTDOWN_ENABLED", "false").lower() == "true"
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"

# Federation nodes for graceful shutdown (reverse dependency order)
FEDERATION_NODES = [
    {"name": "greenfin", "ip": "192.168.132.224", "services": ["promtail"]},
    {"name": "bluefin", "ip": "192.168.132.222", "services": ["vlm-adapter", "vlm-bluefin", "grafana-server"]},
    {"name": "redfin", "ip": "localhost", "services": [
        "jr-executor", "jr-orchestrator", "jr-bidding", "it-jr-executor",
        "research-worker", "sag-unified", "llm-gateway", "vllm",
        "tribal-vision", "speed-detector", "telegram-chief"
    ]},
]

STATE_FILE = Path("/ganuda/services/power_monitor/state.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/var/log/ganuda/power_monitor.log"),
    ]
)
logger = logging.getLogger("PowerMonitor")


# --- Smart Plug Readers ---

def read_kasa_wattage(ip: str) -> Optional[float]:
    """Read wattage from TP-Link Kasa KP115 via python-kasa."""
    try:
        import asyncio
        from kasa import SmartPlug

        async def _read():
            plug = SmartPlug(ip)
            await plug.update()
            emeter = plug.emeter_realtime
            return emeter.get("power", emeter.get("power_mw", 0) / 1000.0)

        return asyncio.run(_read())
    except Exception as e:
        logger.error(f"Kasa read failed: {e}")
        return None


def read_shelly_wattage(ip: str) -> Optional[float]:
    """Read wattage from Shelly Plug S via HTTP API."""
    try:
        import urllib.request
        url = f"http://{ip}/meter/0"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("power", 0.0)
    except Exception as e:
        logger.error(f"Shelly read failed: {e}")
        return None


def read_wattage() -> Optional[float]:
    """Read wattage from configured smart plug."""
    if not PLUG_IP:
        logger.error("POWER_PLUG_IP not configured")
        return None
    if PLUG_TYPE == "kasa":
        return read_kasa_wattage(PLUG_IP)
    elif PLUG_TYPE == "shelly":
        return read_shelly_wattage(PLUG_IP)
    else:
        logger.error(f"Unknown plug type: {PLUG_TYPE}")
        return None


# --- Alert System ---

def send_telegram(message: str):
    """Send alert via Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning(f"Telegram not configured. Alert: {message}")
        return
    try:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }).encode()
        urllib.request.urlopen(url, data, timeout=10)
        logger.info("Telegram alert sent")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


def classify_power_state(watts: float) -> str:
    """Classify power state based on wattage."""
    if watts <= ZERO_WATTS:
        return "DEAD"
    elif watts <= CRITICAL_WATTS:
        return "CRITICAL"
    elif watts <= ALERT_WATTS:
        return "ALERT"
    elif watts <= WARNING_WATTS:
        return "WARNING"
    else:
        return "HEALTHY"


# --- Graceful Shutdown ---

def graceful_shutdown():
    """Execute graceful shutdown across federation nodes."""
    if DRY_RUN:
        logger.info("[DRY RUN] Would execute graceful shutdown")
        send_telegram("🔴 *[DRY RUN] POWER CRITICAL* — Graceful shutdown would execute. DRY_RUN=true prevents actual shutdown.")
        return

    if not SHUTDOWN_ENABLED:
        logger.info("Shutdown not enabled (SHUTDOWN_ENABLED=false)")
        send_telegram("🔴 *POWER CRITICAL* — Shutdown NOT enabled. Manual intervention required!")
        return

    send_telegram("🔴 *POWER CRITICAL — INITIATING GRACEFUL SHUTDOWN*\nFederation shutting down to protect data. Battery depleted.")

    for node in FEDERATION_NODES:
        name = node["name"]
        ip = node["ip"]
        services = node["services"]

        logger.info(f"Shutting down {name} ({ip})...")

        for svc in services:
            try:
                if ip == "localhost":
                    cmd = ["sudo", "systemctl", "stop", svc]
                else:
                    cmd = ["ssh", ip, "sudo", "systemctl", "stop", svc]
                subprocess.run(cmd, timeout=30, capture_output=True)
                logger.info(f"  Stopped {svc} on {name}")
            except Exception as e:
                logger.error(f"  Failed to stop {svc} on {name}: {e}")

    # Final shutdown with delay
    send_telegram("⚫ *All services stopped.* Nodes shutting down in 2 minutes.")
    for node in FEDERATION_NODES:
        ip = node["ip"]
        name = node["name"]
        try:
            if ip == "localhost":
                subprocess.run(["sudo", "shutdown", "-h", "+2"], timeout=10)
            else:
                subprocess.run(["ssh", ip, "sudo", "shutdown", "-h", "+2"], timeout=10)
            logger.info(f"Shutdown scheduled for {name}")
        except Exception as e:
            logger.error(f"Failed to schedule shutdown for {name}: {e}")


# --- State Management ---

def load_state() -> Dict:
    """Load persistent state."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_state": "HEALTHY", "state_since": datetime.now().isoformat(), "shutdown_initiated": False}


def save_state(state: Dict):
    """Save persistent state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# --- Main Loop ---

def main():
    logger.info(f"Power Monitor starting — plug={PLUG_TYPE}@{PLUG_IP}, poll={POLL_INTERVAL}s")
    logger.info(f"Thresholds: WARNING<{WARNING_WATTS}W, ALERT<{ALERT_WATTS}W, CRITICAL<{CRITICAL_WATTS}W, DEAD<{ZERO_WATTS}W")
    logger.info(f"DRY_RUN={DRY_RUN}, SHUTDOWN_ENABLED={SHUTDOWN_ENABLED}")

    state = load_state()
    consecutive_failures = 0

    def handle_signal(sig, frame):
        logger.info("Shutting down power monitor")
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    while True:
        watts = read_wattage()

        if watts is None:
            consecutive_failures += 1
            if consecutive_failures >= 5:
                send_telegram(f"⚠️ *Power Monitor* — Cannot read smart plug ({consecutive_failures} consecutive failures). Check plug at {PLUG_IP}.")
                consecutive_failures = 0
            time.sleep(POLL_INTERVAL)
            continue

        consecutive_failures = 0
        power_state = classify_power_state(watts)

        # State transition alerts
        if power_state != state["last_state"]:
            old_state = state["last_state"]
            state["last_state"] = power_state
            state["state_since"] = datetime.now().isoformat()
            save_state(state)

            if power_state == "WARNING":
                send_telegram(f"⚠️ *POWER WARNING* — Solix output: {watts:.1f}W (declining)\nGrid power may be down. Battery discharging.\nMonitoring continues.")
            elif power_state == "ALERT":
                send_telegram(f"🟠 *POWER ALERT* — Solix output: {watts:.1f}W\nBattery below 50%. Prepare for potential shutdown.\nEstimate ~2-3 hours remaining.")
            elif power_state == "CRITICAL":
                send_telegram(f"🔴 *POWER CRITICAL* — Solix output: {watts:.1f}W\nBattery nearly depleted. Graceful shutdown imminent.")
                if not state.get("shutdown_initiated"):
                    state["shutdown_initiated"] = True
                    save_state(state)
                    graceful_shutdown()
            elif power_state == "DEAD":
                logger.critical(f"Power DEAD at {watts:.1f}W — should already be shut down")
            elif power_state == "HEALTHY" and old_state != "HEALTHY":
                send_telegram(f"✅ *POWER RESTORED* — Solix output: {watts:.1f}W\nGrid power recovered. Federation operational.")
                state["shutdown_initiated"] = False
                save_state(state)

        logger.info(f"Wattage: {watts:.1f}W | State: {power_state}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
```

---

## Step 2: Create Requirements File

Create `/ganuda/services/power_monitor/requirements.txt`

```text
python-kasa>=0.7.0
```

---

## Step 3: Create Environment Template

Create `/ganuda/services/power_monitor/.env.template`

```env
# Solix Power Monitor Configuration
# Copy to .env and fill in values

# Smart plug type: "kasa" or "shelly"
POWER_PLUG_TYPE=kasa

# Smart plug IP address on local network
POWER_PLUG_IP=

# Poll interval in seconds
POWER_POLL_INTERVAL=60

# Wattage thresholds (adjust based on observed Solix output)
POWER_WARNING_WATTS=150
POWER_ALERT_WATTS=80
POWER_CRITICAL_WATTS=30
POWER_ZERO_WATTS=5

# Telegram alerts
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Safety controls
SHUTDOWN_ENABLED=false
DRY_RUN=true
```

---

## Step 4: Create Systemd Service File (Staged)

**NOTE**: This file must be deployed by the TPM via sudo. Jr creates the file; TPM deploys it.

Create `/ganuda/services/power_monitor/power-monitor.service`

```ini
[Unit]
Description=Solix 3800 Plus Power Monitor
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/power_monitor
EnvironmentFile=/ganuda/services/power_monitor/.env
ExecStart=/usr/bin/python3 /ganuda/services/power_monitor/power_monitor.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

## Validation Checklist

- [ ] `power_monitor.py` created at `/ganuda/services/power_monitor/`
- [ ] `requirements.txt` created
- [ ] `.env.template` created
- [ ] `power-monitor.service` staged (NOT deployed — TPM handles systemd)
- [ ] Daemon runs in `--dry-run` mode without hardware
- [ ] State file persists across restarts
- [ ] Telegram alerts format correctly
- [ ] Graceful shutdown respects `DRY_RUN` and `SHUTDOWN_ENABLED` flags

---

## Out of Scope (Future)

- Solix BLE API reverse engineering (separate research task)
- Anker Cloud API integration
- Auto-recovery on power restore (separate task)
- Integration with Grafana dashboards
- Multi-UPS support

---

*For Seven Generations — the rabbit who only looks for the hawk above misses the snake below.*
