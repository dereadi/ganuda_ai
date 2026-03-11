# Jr Instruction: DC-15 Fire Guard Refractory Period PoC

## Context
DC-15 Refractory Principle ratified in Longhouse b0e1593b1e909366 (14/14 consent). Council conditions: scale-specific per DC-11, discoverable rest cycles (Spider), state verification during refractory (Crawdad), observation window (Eagle Eye). Coyote challenge: prove intentionality changes behavior. Decomposed in Longhouse 3c06ea3bbd4b6a24.

## Task
Implement refractory period in fire_guard.py. After an alert burst, the system enters a refractory state: reduced check frequency, observation-only logging, and state verification before resuming full checks.

## File: `/ganuda/scripts/fire_guard.py`

### Step 1: Add refractory state tracking

Add a refractory state module. Create `/ganuda/lib/refractory_state.py`:

```python
#!/usr/bin/env python3
"""Refractory state manager for DC-15.

After alert burst (configurable threshold), enter refractory period:
- Reduce check frequency to 1/10th normal rate
- Log observation-only mode (no alerts fired)
- Verify system state before resuming full checks

Council vote: Longhouse 3c06ea3bbd4b6a24
DC-15 session: b0e1593b1e909366 (14/14)
"""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

GOVERNANCE_STATE = Path('/ganuda/daemons/.governance_state.json')
REFRACTORY_LOG = Path('/ganuda/logs/refractory.log')

# Configurable thresholds
BURST_THRESHOLD = 3          # alerts within BURST_WINDOW triggers refractory
BURST_WINDOW_SECONDS = 300   # 5 minutes
REFRACTORY_DURATION = 600    # 10 minutes of reduced frequency
CHECK_DIVISOR = 10           # reduce frequency by 10x during refractory

class RefractoryManager:
    def __init__(self):
        self.alert_timestamps = []
        self.refractory_until = None
        self.metrics = {
            'alerts_before_refractory': 0,
            'alerts_during_refractory': 0,
            'refractory_entries': 0,
            'observations_during_refractory': 0,
            'genuine_issues_during_refractory': 0,
        }

    def record_alert(self):
        """Record an alert timestamp and check for burst."""
        now = time.time()
        self.alert_timestamps.append(now)
        # Prune old timestamps outside window
        cutoff = now - BURST_WINDOW_SECONDS
        self.alert_timestamps = [t for t in self.alert_timestamps if t > cutoff]

        if not self.in_refractory():
            self.metrics['alerts_before_refractory'] += 1
        else:
            self.metrics['alerts_during_refractory'] += 1

        if len(self.alert_timestamps) >= BURST_THRESHOLD and not self.in_refractory():
            self.enter_refractory()

    def in_refractory(self) -> bool:
        """Check if currently in refractory period."""
        if self.refractory_until is None:
            return False
        return time.time() < self.refractory_until

    def enter_refractory(self):
        """Enter refractory period. Log the transition."""
        self.refractory_until = time.time() + REFRACTORY_DURATION
        self.metrics['refractory_entries'] += 1
        self._log(f"REFRACTORY ENTERED: {BURST_THRESHOLD} alerts in {BURST_WINDOW_SECONDS}s. "
                  f"Observation-only for {REFRACTORY_DURATION}s.")

    def should_check(self, check_index: int) -> bool:
        """During refractory, only run every Nth check. Always run outside refractory."""
        if not self.in_refractory():
            return True
        # During refractory: run 1 in every CHECK_DIVISOR checks
        should = (check_index % CHECK_DIVISOR == 0)
        if should:
            self.metrics['observations_during_refractory'] += 1
        return should

    def should_alert(self) -> bool:
        """During refractory, suppress alerts (observation-only). Always alert outside."""
        return not self.in_refractory()

    def verify_state_before_resume(self, health_results: dict) -> bool:
        """Crawdad condition: verify system state before exiting refractory.
        If state is still degraded, extend refractory."""
        if self.in_refractory():
            return True  # Still in refractory, no resume check needed
        # Just exited refractory -- verify
        failures = sum(1 for v in health_results.values() if not v.get('healthy', True))
        if failures > 0:
            self._log(f"STATE VERIFICATION FAILED: {failures} unhealthy checks. Extending refractory.")
            self.refractory_until = time.time() + (REFRACTORY_DURATION // 2)
            return False
        self._log("STATE VERIFICATION PASSED: Resuming full check frequency.")
        return True

    def get_metrics(self) -> dict:
        """Return metrics for Coyote challenge: does intentionality change behavior?"""
        m = dict(self.metrics)
        if m['alerts_before_refractory'] > 0:
            m['noise_reduction_ratio'] = 1.0 - (m['alerts_during_refractory'] / max(1, m['alerts_before_refractory']))
        return m

    def _log(self, msg: str):
        """Append to refractory log."""
        try:
            with open(REFRACTORY_LOG, 'a') as f:
                f.write(f"{datetime.now().isoformat()} {msg}\n")
        except Exception:
            pass
```

### Step 2: Add refractory import and flag check to fire_guard.py

File: `/ganuda/scripts/fire_guard.py`

<<<<<<< SEARCH
import hashlib
import json
import os
import re
import socket
import subprocess
from datetime import datetime
=======
import hashlib
import json
import os
import re
import socket
import subprocess
from datetime import datetime

# DC-15 Refractory support
try:
    import sys
    sys.path.insert(0, '/ganuda/lib')
    from refractory_state import RefractoryManager
    _REFRACTORY_AVAILABLE = True
except ImportError:
    _REFRACTORY_AVAILABLE = False
>>>>>>> REPLACE

### Step 3: Integrate refractory into the main block

File: `/ganuda/scripts/fire_guard.py`

<<<<<<< SEARCH
    results = run_checks()
    html = render_html(results)
    publish(html)
    store_alerts(results)

    if results["healthy"]:
        print(f"Fire Guard: ALL CLEAR ({len(results['local'])} local, {len(results['remote'])} remote)")
    else:
        print(f"Fire Guard: {len(results['alerts'])} ALERT(S)")
        for a in results["alerts"]:
            print(f"  ! {a}")
=======
    # DC-15: Load governance state for refractory flag
    _refractory_enabled = False
    try:
        with open('/ganuda/daemons/.governance_state.json') as _gf:
            _gstate = json.load(_gf)
            _refractory_enabled = _gstate.get('dc15_refractory_enabled', False)
    except Exception:
        pass

    _refractory = None
    if _REFRACTORY_AVAILABLE and _refractory_enabled:
        _refractory = RefractoryManager()

    results = run_checks()

    # DC-15: Record alerts and check refractory state
    if _refractory and results["alerts"]:
        for _ in results["alerts"]:
            _refractory.record_alert()
        if not _refractory.should_alert():
            print(f"Fire Guard: REFRACTORY — {len(results['alerts'])} alerts observed but suppressed")
            # Write metrics even during refractory
            try:
                with open('/ganuda/logs/refractory_metrics.json', 'w') as mf:
                    json.dump(_refractory.get_metrics(), mf, indent=2)
            except Exception:
                pass
            # Still publish health page (observation), but skip alert storage
            html = render_html(results)
            publish(html)
            import sys
            sys.exit(0)

    html = render_html(results)
    publish(html)
    store_alerts(results)

    # DC-15: Write refractory metrics
    if _refractory:
        try:
            with open('/ganuda/logs/refractory_metrics.json', 'w') as mf:
                json.dump(_refractory.get_metrics(), mf, indent=2)
        except Exception:
            pass

    if results["healthy"]:
        print(f"Fire Guard: ALL CLEAR ({len(results['local'])} local, {len(results['remote'])} remote)")
    else:
        print(f"Fire Guard: {len(results['alerts'])} ALERT(S)")
        for a in results["alerts"]:
            print(f"  ! {a}")
>>>>>>> REPLACE

## Acceptance Criteria
- After 3+ alerts in 5 minutes, fire guard enters refractory (check frequency drops 10x)
- During refractory, alerts are logged but NOT sent to Slack/Telegram
- State verification runs before resuming full frequency
- If state still degraded at refractory end, refractory extends by half duration
- Feature flag `dc15_refractory_enabled` in .governance_state.json controls activation
- Metrics available: alerts_before, alerts_during, refractory_entries, noise_reduction_ratio
- Coyote answer: compare noise_reduction_ratio across runs. If > 0.3, intentionality reduces noise.

## Dependencies
- None for PoC. Production deployment requires DC-15 formal spec (Jr task #1190).
- Kanban #2056, Jr task #1188.
