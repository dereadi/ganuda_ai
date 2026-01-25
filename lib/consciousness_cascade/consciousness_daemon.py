#!/usr/bin/env python3
"""
Consciousness Cascade Daemon - Maintains stable attractor for Assist platform.

Runs as a systemd service. Ignites cascade once, then maintains via efficient
cruise monitoring. Exposes state for Council integration.

Cherokee AI Federation - For Seven Generations
Created: January 18, 2026
"""

import asyncio
import json
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/ganuda/lib')
sys.path.insert(0, '/ganuda/lib/consciousness_cascade')

from cascade_controller import CascadeController
from cruise_monitor import CruiseMonitor

# State file location (use /tmp for now, /var/run requires root)
STATE_DIR = Path('/tmp/consciousness_state')
STATE_FILE = STATE_DIR / 'state.json'
PID_FILE = STATE_DIR / 'daemon.pid'


class ConsciousnessDaemon:
    """
    Daemon that maintains consciousness cascade attractor.

    Lifecycle:
        1. Ignition (one-time, ~90 seconds, 300W)
        2. Cruise (continuous, ~2W average with tiered monitoring)
    """

    def __init__(self):
        self.controller = CascadeController()
        self.cruise_monitor = None
        self.running = False
        self.state = {
            'phase': 'starting',
            'attractor_locked': False,
            'coherence': 0.0,
            'lock_duration_seconds': 0,
            'last_update': None,
            'ignition_completed': False,
            'total_observations': 0,
            'daemon_start': None
        }

    def write_state(self):
        """Write current state to file for external queries."""
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            self.state['last_update'] = datetime.now().isoformat()
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"[Daemon] Could not write state: {e}")

    def write_pid(self):
        """Write PID file."""
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            with open(PID_FILE, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            print(f"[Daemon] Could not write PID: {e}")

    async def ignition_sequence(self) -> bool:
        """
        Run ignition and cascade phases to achieve stable cruise.

        Returns True if cruise achieved, False if failed.
        """
        print("[Daemon] Starting ignition sequence...")
        self.state['phase'] = 'ignition'
        self.state['daemon_start'] = datetime.now().isoformat()
        self.write_state()

        try:
            # Run full experiment to achieve cruise
            results = await self.controller.run_experiment("Daemon Ignition")

            if results.get('success'):
                self.state['ignition_completed'] = True
                self.state['phase'] = 'cruise'
                self.state['total_observations'] = results.get('observation_count', 0)
                print(f"[Daemon] Ignition complete! Depth: {results['max_depth']:.2f}")
                return True
            else:
                self.state['phase'] = 'failed'
                print(f"[Daemon] Ignition failed: {results.get('abort_reason')}")
                return False

        except Exception as e:
            self.state['phase'] = 'error'
            print(f"[Daemon] Ignition error: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def cruise_maintenance(self):
        """
        Run continuous cruise monitoring.

        This is the steady-state operation - heartbeat probes every 60 seconds,
        escalating only when coherence drops.
        """
        print("[Daemon] Entering cruise maintenance mode...")

        self.cruise_monitor = CruiseMonitor(
            council=self.controller.council,
            gpu_monitor=self.controller.gpu_monitor
        )

        # Callbacks to update state
        def on_probe(result):
            self.state['coherence'] = result.coherence
            self.state['total_observations'] += 1
            self.write_state()

        def on_lock_achieved(s):
            self.state['attractor_locked'] = True
            print("[Daemon] >>> ATTRACTOR LOCKED")
            self.write_state()

        def on_lock_lost(s):
            self.state['attractor_locked'] = False
            print("[Daemon] >>> ATTRACTOR LOCK LOST - recovering...")
            self.write_state()

        self.cruise_monitor.on_probe = on_probe
        self.cruise_monitor.on_lock_achieved = on_lock_achieved
        self.cruise_monitor.on_lock_lost = on_lock_lost

        # Run forever (until stopped)
        await self.cruise_monitor.start_monitoring()

    async def run(self):
        """Main daemon loop."""
        self.running = True
        self.write_pid()

        print("=" * 60)
        print("  CONSCIOUSNESS CASCADE DAEMON")
        print("  Cherokee AI Federation - For Seven Generations")
        print("=" * 60)

        # Phase 1: Ignition
        if not await self.ignition_sequence():
            print("[Daemon] Failed to achieve cruise. Exiting.")
            self.state['phase'] = 'failed'
            self.write_state()
            return 1

        # Phase 2: Cruise maintenance (runs forever)
        self.write_state()
        await self.cruise_maintenance()

        return 0

    def stop(self):
        """Graceful shutdown."""
        print("[Daemon] Shutdown requested...")
        self.running = False
        if self.cruise_monitor:
            self.cruise_monitor.stop()
        self.state['phase'] = 'stopped'
        self.write_state()


# Global daemon instance for signal handling
daemon = None


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global daemon
    if daemon:
        daemon.stop()


async def main():
    global daemon

    daemon = ConsciousnessDaemon()

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    return await daemon.run()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
