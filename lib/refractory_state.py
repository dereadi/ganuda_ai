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