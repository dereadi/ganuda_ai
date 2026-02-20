# Jr Instruction: Solix Monitor — Fix SOC% Display

**Kanban**: #1774
**Story Points**: 3
**Priority**: 8 (RC-2026-02B)
**Risk**: LOW — single line fix

## Objective

Fix the battery SOC% display in the Solix monitor REST API polling path.
`battery_capacity` (Wh total) is incorrectly used as fallback for SOC% (percentage).
MQTT path (line 211) is correct — only the REST path (line 302) is broken.

## Step 1: Fix REST API SOC% mapping

File: `/ganuda/services/power_monitor/solix_monitor_daemon.py`

```
<<<<<<< SEARCH
soc = dev.get("battery_soc") or dev.get("batt_soc") or dev.get("battery_capacity")
=======
# Calculate SOC% from energy/capacity if direct SOC field unavailable
soc = dev.get("battery_soc") or dev.get("batt_soc") or dev.get("soc_pct")
if not soc:
    battery_energy = dev.get("battery_energy")
    battery_capacity = dev.get("battery_capacity")
    if battery_energy and battery_capacity:
        try:
            soc = round((float(battery_energy) / float(battery_capacity)) * 100, 1)
        except (ValueError, TypeError, ZeroDivisionError):
            soc = None
>>>>>>> REPLACE
```

## Manual Steps

None — daemon will pick up changes on next restart cycle.
