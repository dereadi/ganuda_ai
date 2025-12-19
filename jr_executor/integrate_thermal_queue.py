#!/usr/bin/env python3
"""
Integration script to add thermal queue polling to jr_cli.py main loop
Run this to patch the Jr executor with thermal queue support
"""

import os

PATCH_CODE = '''
# === THERMAL QUEUE INTEGRATION ===
# Added by JR-THERMAL-QUEUE-001
try:
    from thermal_queue import ThermalQueuePoller, poll_and_process
    THERMAL_QUEUE_ENABLED = True
except ImportError:
    THERMAL_QUEUE_ENABLED = False
    print("[Warning] thermal_queue.py not found - thermal queue disabled")

def check_thermal_queue(jr_name='it_triad_jr'):
    """Check thermal queue for tasks alongside file-based missions"""
    if not THERMAL_QUEUE_ENABLED:
        return []
    return poll_and_process(jr_name)
# === END THERMAL QUEUE INTEGRATION ===
'''

def main():
    print("Thermal queue integration ready.")
    print("Add this to jr_cli.py main polling loop:")
    print("-" * 60)
    print(PATCH_CODE)
    print("-" * 60)
    print("\\nCall check_thermal_queue() in the daemon's poll cycle.")


if __name__ == '__main__':
    main()