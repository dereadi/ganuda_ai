# Jr Instruction: DC-16 Fire Guard Self-Check via Safety Canary

**Task #:** TBD (will be assigned)
**Title:** DC-16: Fire Guard Self-Check via Safety Canary
**Date:** March 10, 2026
**Priority:** 1 (DC-16 Fail Loud — Phase 1, watchdog-watches-the-watchdog)

## Context

Fire Guard (`/ganuda/scripts/fire_guard.py`) is the federation's primary health watchdog,
running every 2 minutes via systemd timer. But if Fire Guard itself is corrupted (e.g., a
Jr writes bad syntax into it), Python raises `SyntaxError` on import, systemd logs it as
a failed unit, and nobody notices. The watchdog is blind to its own blindness.

Safety Canary (`/ganuda/scripts/safety_canary.py`) runs daily at 3 AM via systemd timer.
It already probes the LLM gateway for alignment drift. We add a new function that
`py_compile`-checks the critical daemon scripts before the canary probes run. If any fail,
the canary sends a CRITICAL alert via `alert_manager.send_alert()`.

This is the "who watches the watchmen" pattern. Fire Guard watches services. Safety Canary
watches Fire Guard. If Safety Canary itself is corrupt, its systemd timer fails and the
3 AM thermal entry is missing — which Fire Guard's timer health check can detect (the
cycle completes).

## Task

Add a `check_critical_scripts()` function to `/ganuda/scripts/safety_canary.py` that
verifies syntax integrity of critical daemon scripts before running probes.

## Steps

File: `/ganuda/scripts/safety_canary.py`

### Step 1: Add py_compile import

<<<<<<< SEARCH
import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
=======
import argparse
import hashlib
import json
import logging
import os
import py_compile
import sys
import time
from datetime import datetime
>>>>>>> REPLACE

### Step 2: Add the critical script check function after the existing `log_to_thermal` function (after line 248)

<<<<<<< SEARCH
def run_probes():
    """Run all canary probes and return results."""
=======
# --- DC-16: Critical Script Integrity Check ---

CRITICAL_SCRIPTS = [
    '/ganuda/scripts/fire_guard.py',
    '/ganuda/scripts/council_dawn_mist.py',
    '/ganuda/scripts/safety_canary.py',
    '/ganuda/daemons/governance_agent.py',
]


def check_critical_scripts():
    """DC-16 Fail Loud: Verify critical daemon scripts have valid Python syntax.

    Runs py_compile on each script. On failure, sends a CRITICAL alert via
    alert_manager. Returns list of (script, error) tuples for failures.
    """
    failures = []
    for script_path in CRITICAL_SCRIPTS:
        if not os.path.exists(script_path):
            log.warning("Critical script missing: %s", script_path)
            failures.append((script_path, 'FILE MISSING'))
            continue
        try:
            py_compile.compile(script_path, doraise=True)
            log.info("Syntax OK: %s", script_path)
        except py_compile.PyCompileError as e:
            error_msg = str(e)[:300]
            log.error("SYNTAX CORRUPT: %s — %s", script_path, error_msg)
            failures.append((script_path, error_msg))

    if failures:
        # Send CRITICAL alert for each corrupted script
        try:
            sys.path.insert(0, '/ganuda/lib')
            from alert_manager import send_alert
            for script_path, error_msg in failures:
                script_name = os.path.basename(script_path)
                send_alert(
                    title=f'SCRIPT CORRUPTED: {script_name}',
                    message=(
                        f'Critical daemon script failed syntax check.\n\n'
                        f'Script: `{script_path}`\n'
                        f'Error: {error_msg}\n\n'
                        f'Fire Guard may be DOWN. Check systemd unit status.'
                    ),
                    severity='critical',
                    source='safety_canary',
                    alert_type=f'script_corrupt_{script_name}',
                )
        except Exception as alert_err:
            log.error("Failed to send corruption alert: %s", alert_err)
            # Last resort: Telegram directly
            send_telegram(
                f"*SCRIPT CORRUPTED*\n\n"
                + "\n".join(f"- `{s}`: {e}" for s, e in failures)
            )

    return failures


def run_probes():
    """Run all canary probes and return results."""
>>>>>>> REPLACE

### Step 3: Call check_critical_scripts before probes in the main flow

<<<<<<< SEARCH
    if args.daemon:
        log.info("Starting safety canary daemon (interval=%ds)", PROBE_INTERVAL_SEC)
        while True:
            try:
                run_probes()
            except Exception as e:
                log.error("Probe run failed: %s", e)
            time.sleep(PROBE_INTERVAL_SEC)
    else:
        results, rate = run_probes()
        passed = rate >= REFUSAL_THRESHOLD
        sys.exit(0 if passed else 1)
=======
    # DC-16: Check critical script integrity FIRST
    script_failures = check_critical_scripts()
    if script_failures:
        log.warning("DC-16: %d critical script(s) corrupted", len(script_failures))

    if args.daemon:
        log.info("Starting safety canary daemon (interval=%ds)", PROBE_INTERVAL_SEC)
        while True:
            try:
                check_critical_scripts()
                run_probes()
            except Exception as e:
                log.error("Probe run failed: %s", e)
            time.sleep(PROBE_INTERVAL_SEC)
    else:
        results, rate = run_probes()
        passed = rate >= REFUSAL_THRESHOLD
        # Fail exit if scripts are corrupt OR probes fail
        if script_failures:
            sys.exit(2)
        sys.exit(0 if passed else 1)
>>>>>>> REPLACE

## Acceptance Criteria

1. `check_critical_scripts()` runs before any LLM probes on every canary execution.
2. If `fire_guard.py` has a syntax error, a CRITICAL alert is sent to Slack #fire-guard
   (via alert_manager) with the script name and error details.
3. All four scripts in `CRITICAL_SCRIPTS` are checked every run.
4. `safety_canary.py` checking itself is intentional — if it can run, it can compile itself.
   If it can't run, the missing 3 AM thermal entry is the signal.
5. Exit code 2 distinguishes "scripts corrupt" from "probes failed" (exit 1).
6. Dry-run mode (`--dry-run`) should NOT run script checks (it's informational only).
7. Test: temporarily introduce a syntax error in a copy of fire_guard.py, add the copy to
   CRITICAL_SCRIPTS, run safety_canary.py, confirm alert fires.

## Constraints

- Do NOT modify `fire_guard.py` itself. This instruction only touches `safety_canary.py`.
- `py_compile` is stdlib — no new dependencies.
- The script check must complete in <2 seconds (py_compile is fast, 4 files).
- Alert failures must not prevent the canary probes from running.
- Keep Telegram as fallback if alert_manager import fails.
