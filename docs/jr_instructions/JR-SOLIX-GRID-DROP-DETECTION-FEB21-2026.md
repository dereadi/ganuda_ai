# JR Instruction: Solix Grid Power Drop Detection

**Task**: SOLIX-GRID-DROP-001
**Priority**: P1
**File**: `/ganuda/services/power_monitor/solix_monitor_daemon.py`
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.

## Context

The Solix monitor daemon polls battery telemetry via REST API and MQTT but does NOT detect grid power transitions. During power outages, we get no Telegram alert until SOC drops below thresholds. We need immediate detection when grid power drops to 0 (outage) or comes back online (restoration).

The existing `send_telegram()` function and `_last_alerts` debounce pattern are already in the file. We add a parallel debounce dict for grid transitions and a new `check_grid_transition()` method on the `SolixDaemon` class, then wire it into both the REST and MQTT polling paths.

## Changes

### Change 1: Add grid state tracking to `__init__`

File: `/ganuda/services/power_monitor/solix_monitor_daemon.py`

```python
<<<<<<< SEARCH
    def __init__(self):
        self.api = None
        self.devices = {}
        self.last_soc = {}          # device_sn -> last SOC reading
        self.stable_count = {}      # device_sn -> consecutive stable readings
        self.fast_mode = False
        self.running = True
=======
    def __init__(self):
        self.api = None
        self.devices = {}
        self.last_soc = {}          # device_sn -> last SOC reading
        self.last_grid_power = {}   # device_sn -> last grid power reading (W)
        self._grid_alert_times = {} # device_sn -> datetime of last grid alert
        self.stable_count = {}      # device_sn -> consecutive stable readings
        self.fast_mode = False
        self.running = True
>>>>>>> REPLACE
```

### Change 2: Add `check_grid_transition()` method after `update_polling_mode()`

File: `/ganuda/services/power_monitor/solix_monitor_daemon.py`

```python
<<<<<<< SEARCH
    def process_device_data(self, device_sn, device_name, mqtt_data):
=======
    def check_grid_transition(self, device_sn, device_name, current_grid_power):
        """Detect grid power transitions and send Telegram alerts.

        Fires alert when grid goes from >0W to 0W (outage) or 0W to >0W (restored).
        Uses a 5-minute debounce per device to avoid alert spam.
        """
        GRID_DEBOUNCE_SEC = 300  # 5 minutes

        prev = self.last_grid_power.get(device_sn)
        self.last_grid_power[device_sn] = current_grid_power

        if prev is None:
            # First reading — no transition to detect
            return

        # Check debounce
        now = datetime.now()
        last_alert = self._grid_alert_times.get(device_sn)
        if last_alert and (now - last_alert).total_seconds() < GRID_DEBOUNCE_SEC:
            return

        current = current_grid_power if current_grid_power is not None else 0

        if prev > 0 and current == 0:
            msg = (
                "\u26a1 *GRID POWER DOWN*\n"
                f"Device: {device_name}\n"
                f"Solix running on battery.\n"
                f"Previous grid: {prev}W"
            )
            send_telegram(msg)
            self._grid_alert_times[device_sn] = now
            log.warning("GRID DOWN detected for %s (was %sW)", device_name, prev)

        elif prev == 0 and current > 0:
            msg = (
                "\u2705 *GRID POWER RESTORED*\n"
                f"Device: {device_name}\n"
                f"Grid power: {current}W"
            )
            send_telegram(msg)
            self._grid_alert_times[device_sn] = now
            log.info("GRID RESTORED for %s (%sW)", device_name, current)

    def process_device_data(self, device_sn, device_name, mqtt_data):
>>>>>>> REPLACE
```

### Change 3: Wire grid transition check into REST API polling path

File: `/ganuda/services/power_monitor/solix_monitor_daemon.py`

```python
<<<<<<< SEARCH
                if grid_power is not None:
                    try:
                        write_timeline("solix_grid_power", source, float(grid_power), meta)
                    except (ValueError, TypeError):
                        pass
=======
                if grid_power is not None:
                    try:
                        gp = float(grid_power)
                        write_timeline("solix_grid_power", source, gp, meta)
                        self.check_grid_transition(sn, name, gp)
                    except (ValueError, TypeError):
                        pass
>>>>>>> REPLACE
```

### Change 4: Wire grid transition check into MQTT path

File: `/ganuda/services/power_monitor/solix_monitor_daemon.py`

```python
<<<<<<< SEARCH
        grid = mqtt_data.get("grid_connected") or mqtt_data.get("ac_in_type")

        # Build source name
=======
        grid = mqtt_data.get("grid_connected") or mqtt_data.get("ac_in_type")
        grid_power_mqtt = mqtt_data.get("grid_power") or mqtt_data.get("grid_watts")

        if grid_power_mqtt is not None:
            try:
                self.check_grid_transition(device_sn, device_name, float(grid_power_mqtt))
            except (ValueError, TypeError):
                pass

        # Build source name
>>>>>>> REPLACE
```

## Verification

After the Jr executor applies these changes, verify:

```text
# 1. Syntax check
python3 -c "import ast; ast.parse(open('/ganuda/services/power_monitor/solix_monitor_daemon.py').read()); print('SYNTAX OK')"

# 2. Confirm new attributes in __init__
grep -n 'last_grid_power\|_grid_alert_times' /ganuda/services/power_monitor/solix_monitor_daemon.py

# 3. Confirm new method exists
grep -n 'def check_grid_transition' /ganuda/services/power_monitor/solix_monitor_daemon.py

# 4. Confirm REST path wiring
grep -n 'check_grid_transition' /ganuda/services/power_monitor/solix_monitor_daemon.py

# Expected: 4 matches — method def, REST call, MQTT call, plus class attributes
```

## Rollback

If anything breaks, the only file modified is `/ganuda/services/power_monitor/solix_monitor_daemon.py`. Restore from git:

```text
git checkout -- /ganuda/services/power_monitor/solix_monitor_daemon.py
```

## Notes

- The `datetime` import is already present in the file (used by existing `_last_alerts` logic).
- The `send_telegram()` function is a module-level function already defined above the class.
- MQTT path may not have `grid_power` in its payload (F3800P MQTT is sparse). The `grid_power_mqtt` extraction tries two field names and no-ops if neither exists.
- The 5-minute debounce prevents alert storms from noisy readings. Each device has independent debounce.
