# JR INSTRUCTION: Fire Guard — Port Check Debounce + DC-15 Refractory Wiring

**Task**: Add retry logic to Fire Guard port checks and wire in the DC-15 RefractoryManager to suppress alert storms
**Priority**: P1 — alert noise is drowning real signals
**Date**: 2026-03-11
**TPM**: Claude Opus
**Story Points**: 3

## Problem Statement

During a power outage on Mar 11 2026, Fire Guard generated 20+ "bluefin/PostgreSQL DOWN" alerts in 6 hours. PostgreSQL was UP the entire time — the alerts were caused by brief network blips during the outage. Fire Guard's `check_port()` does a single TCP connect with a 3s timeout. One failed connect = DOWN = thermal memory entry.

This is the exact problem DC-15 (Refractory Principle) was designed to solve. The `RefractoryManager` class exists at `/ganuda/lib/refractory_state.py` but is not wired into Fire Guard.

**Impact**: 20 false thermals at temp 85-95, polluting thermal memory. Real alerts get lost in the noise. This is the boy who cried wolf.

## What You're Building

### Change 1: Retry before declaring DOWN

In `fire_guard.py`, modify `check_port()` to retry before returning False:

```python
def check_port(ip, port, timeout=3, retries=3, retry_delay=1):
    """Check if a TCP port is reachable, with retries."""
    for attempt in range(retries):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((ip, port))
            s.close()
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            if attempt < retries - 1:
                time.sleep(retry_delay)
    return False
```

This means a port must fail 3 consecutive checks (with 1s gaps) before being declared DOWN. Total time: ~12s worst case. Acceptable for a 2-minute check cycle.

### Change 2: Wire RefractoryManager into Fire Guard

Import and instantiate the RefractoryManager:

```python
import sys
sys.path.insert(0, '/ganuda/lib')
from refractory_state import RefractoryManager

refractory = RefractoryManager()
```

Before thermalizing a DOWN alert, check with the refractory manager:

```python
# In the alert/thermal writing section:
refractory.record_alert()
if refractory.should_alert():
    # Write thermal, send Slack/Telegram
    store_thermal_alert(...)
else:
    # Log locally only — observation mode
    logging.info(f"REFRACTORY: Suppressed alert for {node}/{service}. Observation only.")
```

### Change 3: Add state tracking for DOWN→UP transitions

Currently Fire Guard doesn't track whether a service was already known DOWN. Add a simple dict:

```python
known_down = {}  # key: "node/service", value: timestamp first detected

# When a port check fails:
key = f"{node}/{service}"
if key not in known_down:
    known_down[key] = datetime.now()
    # This is a NEW failure — alert (if refractory allows)
else:
    # Already known down — don't re-alert
    pass

# When a port check succeeds:
if key in known_down:
    duration = datetime.now() - known_down.pop(key)
    # Log recovery
    store_thermal(f"RECOVERED: {node}/{service} back UP after {duration}")
```

This eliminates the core problem: repeated alerts for the same known-down service.

## Target Files

- `/ganuda/scripts/fire_guard.py` — main Fire Guard script (MODIFY)
- `/ganuda/lib/refractory_state.py` — RefractoryManager (READ ONLY — already built)

## Constraints

- Do NOT change the check interval (every 2 minutes via systemd timer)
- Do NOT remove any existing checks — only add retry + debounce + refractory
- Do NOT modify refractory_state.py — it's already built and tested
- Keep `check_port()` total time under 15 seconds worst case (3 retries * (3s timeout + 1s delay))
- Refractory suppresses alerts, NOT checks — Fire Guard still observes during refractory

## Acceptance Criteria

- `check_port()` retries 3 times before returning False
- RefractoryManager is imported and active in the main check loop
- 3+ alerts in 5 minutes triggers refractory (observation-only mode)
- A service already known DOWN does not generate repeat alerts
- A service transitioning DOWN→UP generates a RECOVERED thermal
- `python3 -c "import py_compile; py_compile.compile('scripts/fire_guard.py', doraise=True)"` passes
- Existing checks (local services, remote ports, timers) still run as before

## DO NOT

- Change systemd timer intervals
- Remove any existing health checks
- Modify refractory_state.py
- Suppress the FIRST alert for a genuinely down service — only suppress repeats
