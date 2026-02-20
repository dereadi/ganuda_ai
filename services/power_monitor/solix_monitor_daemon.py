#!/usr/bin/env python3
"""Solix F3800 Plus Battery Monitoring Daemon.

Council Vote #8525 design:
- Adaptive polling: 120s normal, 30s when SOC dropping
- Telegram alerts at 50%, 30%, 15% with debounce
- Data to unified_timeline on bluefin PostgreSQL
- Monitors both F3800 Plus and Prime Power Bank
- Runs on greenfin (monitoring node)

Long Man Methodology: BUILD phase
Ultrathink: ULTRATHINK-SOLIX-F3800-MONITORING-DESIGN-FEB11-2026.md
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import psycopg2
import psycopg2.extras
import requests
from dotenv import load_dotenv

# Load Anker credentials
SOLIX_API_DIR = Path(__file__).parent / "anker-solix-api"
load_dotenv(SOLIX_API_DIR / ".env")

# Add anker-solix-api to path for imports
sys.path.insert(0, str(SOLIX_API_DIR))

from aiohttp import ClientSession
from api.api import AnkerSolixApi
from api.mqtt import AnkerSolixMqttSession

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ANKER_USER = os.getenv("ANKERUSER")
ANKER_PASS = os.getenv("ANKERPASSWORD")
ANKER_COUNTRY = os.getenv("ANKERCOUNTRY", "US")

DB_HOST = os.getenv("CHEROKEE_DB_HOST", "192.168.132.222")
DB_USER = os.getenv("CHEROKEE_DB_USER", "claude")
DB_PASS = os.getenv("CHEROKEE_DB_PASS", os.getenv("PGPASSWORD", ""))
DB_NAME = os.getenv("CHEROKEE_DB_NAME", "zammad_production")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Adaptive polling (Council Vote #8525)
NORMAL_INTERVAL = 120       # seconds
ALERT_INTERVAL = 30         # seconds
SOC_DROP_THRESHOLD = -2.0   # percent per reading triggers fast mode
STABLE_COUNT_RESET = 3      # consecutive stable readings to return to normal

# Alert thresholds (Council consensus: 50/30/15)
ALERT_THRESHOLDS = [
    {"soc": 50, "level": "WARNING",   "emoji": "⚠️"},
    {"soc": 30, "level": "CRITICAL",  "emoji": "🔴"},
    {"soc": 15, "level": "EMERGENCY", "emoji": "🚨"},
]
ALERT_DEBOUNCE_MINUTES = 30

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("solix-monitor")


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def get_db():
    """Get PostgreSQL connection to bluefin."""
    return psycopg2.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME
    )


def write_timeline(event_type, source, value, metadata):
    """Write a reading to unified_timeline."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO unified_timeline (timestamp, event_type, source, value, metadata)
               VALUES (NOW(), %s, %s, %s, %s)
               ON CONFLICT (timestamp, event_type, source) DO UPDATE
               SET value = EXCLUDED.value, metadata = EXCLUDED.metadata""",
            (event_type, source, value, json.dumps(metadata)),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        log.error("DB write failed: %s", e)


# ---------------------------------------------------------------------------
# Telegram Alerts
# ---------------------------------------------------------------------------
_last_alerts = {}  # threshold_soc -> datetime of last alert


def send_telegram(message):
    """Send Telegram notification."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram not configured, skipping alert")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
        }, timeout=10)
    except Exception as e:
        log.error("Telegram send failed: %s", e)


def check_alerts(soc, device_name, watts_out):
    """Check SOC against alert thresholds with debounce."""
    now = datetime.now()
    for threshold in ALERT_THRESHOLDS:
        if soc <= threshold["soc"]:
            last = _last_alerts.get(threshold["soc"])
            if last and (now - last) < timedelta(minutes=ALERT_DEBOUNCE_MINUTES):
                continue  # debounced

            _last_alerts[threshold["soc"]] = now
            msg = (
                f"{threshold['emoji']} *SOLIX {threshold['level']}*\n"
                f"Battery: *{soc}%*\n"
                f"Device: {device_name}\n"
                f"Load: {watts_out}W\n"
            )
            if threshold["soc"] == 50:
                msg += f"Status: Monitoring. Battery declining."
            elif threshold["soc"] == 30:
                msg += f"Action: Consider stopping non-essential services."
            elif threshold["soc"] == 15:
                msg += f"Action: EMERGENCY — preserving databases."

            send_telegram(msg)
            log.warning("ALERT %s: SOC=%s%% on %s", threshold["level"], soc, device_name)

            # Log to thermal memory for critical/emergency
            if threshold["soc"] <= 30:
                write_timeline(
                    "solix_alert",
                    device_name,
                    soc,
                    {"level": threshold["level"], "watts_out": watts_out},
                )
            break  # only fire the most severe matching threshold


# ---------------------------------------------------------------------------
# MQTT Monitor
# ---------------------------------------------------------------------------
class SolixDaemon:
    """Solix battery monitoring daemon with adaptive polling."""

    def __init__(self):
        self.api = None
        self.devices = {}
        self.last_soc = {}          # device_sn -> last SOC reading
        self.stable_count = {}      # device_sn -> consecutive stable readings
        self.fast_mode = False
        self.running = True

    @property
    def interval(self):
        return ALERT_INTERVAL if self.fast_mode else NORMAL_INTERVAL

    def update_polling_mode(self, device_sn, current_soc):
        """Adaptive polling: speed up when SOC dropping, slow down when stable."""
        prev = self.last_soc.get(device_sn)
        self.last_soc[device_sn] = current_soc

        if prev is None:
            return

        delta = current_soc - prev

        if delta < SOC_DROP_THRESHOLD:
            self.fast_mode = True
            self.stable_count[device_sn] = 0
            log.info("FAST MODE: SOC dropped %.1f%% (%.1f->%.1f)", delta, prev, current_soc)
        elif delta >= 0:
            count = self.stable_count.get(device_sn, 0) + 1
            self.stable_count[device_sn] = count
            if self.fast_mode and count >= STABLE_COUNT_RESET:
                self.fast_mode = False
                log.info("NORMAL MODE: %d consecutive stable readings", count)

    def process_device_data(self, device_sn, device_name, mqtt_data):
        """Extract and store telemetry from MQTT device data."""
        # The mqtt_data dict contains decoded fields from the hex payload
        # Field names vary by device model — extract what we can
        soc = mqtt_data.get("battery_soc") or mqtt_data.get("soc_pct") or mqtt_data.get("batt_soc")
        watts_out = mqtt_data.get("output_power") or mqtt_data.get("watts_out") or mqtt_data.get("output_watts")
        watts_in = mqtt_data.get("input_power") or mqtt_data.get("watts_in") or mqtt_data.get("input_watts") or mqtt_data.get("charge_power")
        grid = mqtt_data.get("grid_connected") or mqtt_data.get("ac_in_type")

        # Build source name
        source = f"solix_{device_sn}"

        # Store all raw fields
        meta = {
            "device_sn": device_sn,
            "device_name": device_name,
            "raw_fields": {k: v for k, v in mqtt_data.items() if k != "topics"},
            "polling_mode": "fast" if self.fast_mode else "normal",
            "interval_sec": self.interval,
        }

        if soc is not None:
            try:
                soc = float(soc)
                write_timeline("solix_battery_soc", source, soc, meta)
                self.update_polling_mode(device_sn, soc)
                check_alerts(soc, device_name, watts_out or 0)
                log.info("SOC: %.1f%% | Out: %sW | In: %sW | Grid: %s | Mode: %s",
                         soc, watts_out or "?", watts_in or "?", grid or "?",
                         "FAST" if self.fast_mode else "normal")
            except (ValueError, TypeError):
                pass

        if watts_out is not None:
            try:
                write_timeline("solix_power_output", source, float(watts_out), meta)
            except (ValueError, TypeError):
                pass

        if watts_in is not None:
            try:
                write_timeline("solix_power_input", source, float(watts_in), meta)
            except (ValueError, TypeError):
                pass

        # Always write a heartbeat with whatever we have
        write_timeline("solix_heartbeat", source, soc or 0, meta)

    def mqtt_callback(self, session, topic, message, data, model, *args, **kwargs):
        """Handle incoming MQTT messages."""
        if not data:
            return

        device_sn = topic.split("/")[3] if "/" in topic else "unknown"
        device_name = "unknown"
        for dev in self.devices.values():
            if dev.get("device_sn") == device_sn:
                device_name = dev.get("device_name") or dev.get("name") or device_sn
                break

        # Get decoded data from the mqtt session
        mqtt_data = {}
        if hasattr(session, "mqtt_data") and device_sn in session.mqtt_data:
            mqtt_data = dict(session.mqtt_data[device_sn])

        if mqtt_data:
            self.process_device_data(device_sn, device_name, mqtt_data)
        else:
            log.debug("Message on %s but no decoded data yet", topic)

    async def run(self):
        """Main daemon loop."""
        log.info("=" * 60)
        log.info("Solix F3800 Plus Monitor Starting")
        log.info("Council Vote #8525 | Long Man BUILD Phase")
        log.info("Adaptive polling: %ds normal / %ds fast", NORMAL_INTERVAL, ALERT_INTERVAL)
        log.info("Alert thresholds: %s", [t["soc"] for t in ALERT_THRESHOLDS])
        log.info("=" * 60)

        while self.running:
            try:
                await self._monitor_session()
            except Exception as e:
                log.error("Session error: %s — reconnecting in 30s", e)
                await asyncio.sleep(30)

    async def _poll_rest_api(self):
        """Poll Anker REST API for power metrics not available via MQTT."""
        try:
            await self.api.async_update_device_details()
            for sn, dev in self.api.devices.items():
                name = dev.get("device_name") or dev.get("name", sn)
                source = f"solix_{sn}"

                # Extract power metrics from REST API response
                # SOC fallback: battery_soc → batt_soc → soc_pct → calculated (Council #4d0745c25d7868c3)
                # NOTE: battery_capacity is Wh (e.g. 3840), NOT a percentage — never use as SOC
                soc = dev.get("battery_soc") or dev.get("batt_soc") or dev.get("soc_pct")
                if soc is None:
                    # Try to calculate SOC from energy/capacity
                    energy = dev.get("battery_energy") or dev.get("batt_energy")
                    capacity = dev.get("battery_capacity")
                    if energy is not None and capacity is not None:
                        try:
                            cap_f = float(capacity)
                            if cap_f > 0:
                                soc = round(float(energy) / cap_f * 100, 1)
                        except (ValueError, TypeError, ZeroDivisionError):
                            pass
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

            for sn, dev in self.devices.items():
                name = dev.get("device_name") or dev.get("name", sn)
                model = dev.get("device_pn") or dev.get("product_code", "?")
                log.info("Device: %s (%s) SN: %s", name, model, sn)

            if not self.devices:
                log.error("No devices found!")
                return

            # Start MQTT session
            log.info("Connecting to MQTT broker...")
            mqtt_session = await self.api.startMqttSession()
            if not mqtt_session or not mqtt_session.is_connected():
                log.error("MQTT connection failed!")
                return

            log.info("MQTT connected to %s:%s", mqtt_session.host, mqtt_session.port)

            # Subscribe to all devices
            topics = set()
            trigger_devices = set()
            for sn, dev in self.devices.items():
                if prefix := mqtt_session.get_topic_prefix(deviceDict=dev):
                    topics.add(f"{prefix}#")
                if cmd_prefix := mqtt_session.get_topic_prefix(deviceDict=dev, publish=True):
                    topics.add(f"{cmd_prefix}#")
                trigger_devices.add(sn)

            log.info("Subscribed to %d topics for %d devices", len(topics), len(self.devices))

            # Set our callback
            mqtt_session.message_callback(func=self.mqtt_callback)

            # Start the message poller
            poller_task = asyncio.get_running_loop().create_task(
                mqtt_session.message_poller(
                    topics=topics,
                    trigger_devices=trigger_devices,
                    msg_callback=self.mqtt_callback,
                    timeout=self.interval,
                )
            )

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
            finally:
                poller_task.cancel()
                try:
                    await poller_task
                except asyncio.CancelledError:
                    pass
                if self.api.mqttsession:
                    self.api.mqttsession.cleanup()
                log.info("MQTT session closed")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    if not ANKER_USER or not ANKER_PASS:
        log.error("ANKERUSER/ANKERPASSWORD not set. Check .env file.")
        sys.exit(1)

    if not DB_PASS:
        log.error("CHEROKEE_DB_PASS not set. Check environment.")
        sys.exit(1)

    daemon = SolixDaemon()
    try:
        asyncio.run(daemon.run())
    except KeyboardInterrupt:
        log.info("Shutting down...")
        daemon.running = False


if __name__ == "__main__":
    main()
