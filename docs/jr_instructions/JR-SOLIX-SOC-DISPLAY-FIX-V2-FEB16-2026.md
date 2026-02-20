# Jr Instruction: Solix SOC% Display Fix (v2)

**Kanban**: #1774 (3 SP)
**Council Vote**: #4d0745c25d7868c3 (PROCEED WITH CAUTION, 0.739)
**Sprint**: RC-2026-02B
**Assigned Jr**: Software Engineer Jr.
**Previous Attempt**: Jr #748 (failed — SR match issue during executor extraction bug period)

## Context

The Solix F3800P UPS monitor has a SOC% display bug. The REST API returns `battery_capacity=3840` (Wh total capacity), which the fallback chain treats as SOC percentage, resulting in "3840%" being logged. The Anker REST API does NOT expose true SOC% for the F3800P model — `battery_soc` and `batt_soc` are both absent from the response.

## Step 1: Fix SOC fallback chain to remove battery_capacity

File: `/ganuda/services/power_monitor/solix_monitor_daemon.py`

<<<<<<< SEARCH
                # Extract power metrics from REST API response
                soc = dev.get("battery_soc") or dev.get("batt_soc") or dev.get("battery_capacity")
=======
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
>>>>>>> REPLACE

## Verification

After deployment on **greenfin**, check logs:

```text
journalctl -u solix-monitor --since "5 min ago" | grep -i soc
```

Expected: SOC should show as `None` or a calculated percentage (0-100), NOT 3840.

## Manual Steps (TPM only)

On **greenfin**:
1. `sudo systemctl restart solix-monitor` (or whatever the service name is — check with `systemctl list-units | grep solix`)
2. Verify with log check above

## Rollback

Revert the SEARCH/REPLACE block — restore original single-line fallback chain.
