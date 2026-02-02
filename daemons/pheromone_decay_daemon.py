#!/usr/bin/env python3
"""
Pheromone Decay Daemon - Hourly decay of stigmergic signals

Based on SwarmSys (arXiv:2510.10047) pheromone dynamics.
Pheromones decay over time, preventing stale trails from dominating.

Run hourly via cron or systemd timer:
  0 * * * * /path/to/python3 /ganuda/daemons/pheromone_decay_daemon.py

Or as standalone with --daemon flag for continuous operation:
  python3 pheromone_decay_daemon.py --daemon

For Seven Generations - Cherokee AI Federation
"""

import os
import sys
import time
import platform
from datetime import datetime

# Determine ganuda path based on OS
GANUDA_PATH = "/Users/Shared/ganuda" if platform.system() == "Darwin" else "/ganuda"

# Add lib to path
sys.path.insert(0, os.path.join(GANUDA_PATH, 'lib'))

try:
    from smadrl_pheromones import decay_all_pheromones, get_pheromone_stats
except ImportError as e:
    print(f"[ERROR] Cannot import smadrl_pheromones: {e}")
    sys.exit(1)

# Configuration
DAEMON_INTERVAL = 3600  # 1 hour in seconds
LOG_FILE = os.path.join(GANUDA_PATH, 'logs', 'pheromone_decay.log')


def log_message(msg: str):
    """Log to file and stdout."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)

    # Ensure log directory exists
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    try:
        with open(LOG_FILE, 'a') as f:
            f.write(full_msg + '\n')
    except Exception as e:
        print(f"[WARN] Could not write to log: {e}")


def run_decay():
    """Execute one decay cycle."""
    log_message("Starting pheromone decay cycle...")

    # Get stats before
    before = get_pheromone_stats()
    log_message(f"Before: {before.get('total_pheromones', 0)} pheromones, "
                f"total intensity: {before.get('total_intensity', 0):.2f}")

    # Run decay
    decayed, deleted = decay_all_pheromones()

    # Get stats after
    after = get_pheromone_stats()
    log_message(f"Decay applied to {decayed} pheromones, {deleted} removed")
    log_message(f"After: {after.get('total_pheromones', 0)} pheromones, "
                f"total intensity: {after.get('total_intensity', 0):.2f}")

    # Log agent activity
    log_message(f"Active agents: {after.get('unique_agents', 0)}, "
                f"Unique locations: {after.get('unique_locations', 0)}")
    log_message(f"Success/Failure ratio: {after.get('success_count', 0)}/{after.get('failure_count', 0)}")

    log_message("Decay cycle complete.")
    return decayed, deleted


def run_daemon():
    """Run in continuous daemon mode."""
    log_message("Pheromone Decay Daemon starting in continuous mode...")
    log_message(f"Decay interval: {DAEMON_INTERVAL}s ({DAEMON_INTERVAL//3600}h)")

    while True:
        try:
            run_decay()
        except Exception as e:
            log_message(f"[ERROR] Decay failed: {e}")

        log_message(f"Sleeping for {DAEMON_INTERVAL}s until next decay...")
        time.sleep(DAEMON_INTERVAL)


def main():
    """Main entry point."""
    if '--daemon' in sys.argv:
        run_daemon()
    elif '--stats' in sys.argv:
        stats = get_pheromone_stats()
        print("Pheromone System Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        # Single run (for cron)
        run_decay()


if __name__ == '__main__':
    main()
