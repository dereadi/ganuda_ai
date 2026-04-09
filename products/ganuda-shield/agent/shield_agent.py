#!/usr/bin/env python3
"""
Ganuda Shield Agent — Main runner.
Ties together consent, monitor, transport, and tray.

Usage:
    python3 shield_agent.py                    # Start with interactive consent
    python3 shield_agent.py --employee jsmith  # Set employee ID
    python3 shield_agent.py --config /path/to/config.yaml
    python3 shield_agent.py --status           # Check agent status

PRIVATE — Commercial License. Council vote #7cfe224b87cb349f.
"""

import argparse
import signal
import sys
import time
import logging
import json
import os
from datetime import datetime

from config import load_config, save_default_config, ShieldConfig
from consent import check_consent_exists, load_consent, request_consent_cli, withdraw_consent
from monitor import capture_activity_snapshot, ActivityBuffer
from transport import ShieldTransport

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [Shield] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('shield.agent')


class ShieldAgent:
    """Main Shield agent — consent → monitor → transport loop."""

    def __init__(self, config: ShieldConfig):
        self.config = config
        self.running = False
        self.transport = ShieldTransport(config.server_url, config.machine_id)
        self.buffer = ActivityBuffer(config.buffer_max_hours)
        self.snapshot_count = 0
        self.batch = []
        self.last_heartbeat = 0
        self.last_batch_send = 0
        self.escalated = False

    def check_consent(self) -> bool:
        """Verify consent exists. Agent WILL NOT START without it."""
        if check_consent_exists():
            consent = load_consent()
            if consent.get('withdrawn'):
                logger.error("Consent has been withdrawn. Agent cannot run.")
                logger.error("To re-consent, delete ~/.ganuda-shield/consent.json and restart.")
                return False
            logger.info(f"Consent verified: {consent.get('employee_id')} @ {consent.get('consent_timestamp', '?')[:19]}")
            self.config.employee_id = consent.get('employee_id', self.config.employee_id)
            return True
        else:
            logger.info("No consent recorded. Starting consent flow...")
            if not self.config.employee_id:
                self.config.employee_id = input("Enter your employee ID: ").strip()
            return request_consent_cli(
                self.config.employee_id,
                self.config.machine_id,
                self.config.jurisdiction
            )

    def register_with_server(self) -> bool:
        """Register agent with collection server."""
        consent = load_consent()
        api_key = self.transport.register(self.config.employee_id, consent)
        if api_key:
            # Save API key locally
            key_path = os.path.expanduser("~/.ganuda-shield/api_key")
            with open(key_path, 'w') as f:
                f.write(api_key)
            os.chmod(key_path, 0o600)
            logger.info("Registered with collection server.")
            return True
        else:
            logger.warning("Server registration failed. Running in buffered mode.")
            return False

    def send_heartbeat(self):
        """Send periodic heartbeat to server."""
        now = time.time()
        if now - self.last_heartbeat >= 60:
            self.transport.send_heartbeat()
            self.last_heartbeat = now

    def send_batch(self):
        """Send accumulated snapshots to server."""
        now = time.time()
        if now - self.last_batch_send >= self.config.batch_interval and self.batch:
            success = self.transport.send_batch(self.batch)
            if success:
                self.batch = []
                # Also send any buffered data from previous offline periods
                buffered = self.buffer.get_batch()
                if buffered:
                    self.transport.send_batch(buffered)
            else:
                # Server unreachable — buffer locally
                for snapshot in self.batch:
                    self.buffer.add(snapshot)
                self.batch = []
                logger.warning("Server unreachable. Buffering locally.")
            self.last_batch_send = now

    def check_escalation(self):
        """Check if server has escalated monitoring for this agent."""
        config_update = self.transport.check_config_update()
        if config_update:
            was_escalated = self.escalated
            self.escalated = config_update.get('escalated', False)
            if self.escalated and not was_escalated:
                logger.warning("⚠️ ENHANCED MONITORING ACTIVATED by admin")
                logger.warning(f"Reason: {config_update.get('escalation_reason', 'not specified')}")
                # Employee notification — in production this would update the tray icon
                print("\n" + "="*60)
                print("⚠️ ENHANCED MONITORING IS NOW ACTIVE")
                print(f"Reason: {config_update.get('escalation_reason', 'security investigation')}")
                print("Your tray icon is now RED. View your dashboard for details.")
                print("="*60 + "\n")
            elif not self.escalated and was_escalated:
                logger.info("Enhanced monitoring deactivated. Returning to normal.")

    def run(self):
        """Main agent loop."""
        # Step 1: Consent check (NON-NEGOTIABLE)
        if not self.check_consent():
            logger.error("Cannot start without consent. Exiting.")
            sys.exit(1)

        # Step 2: Load buffered data from any previous session
        self.buffer.load_from_disk()
        buffered_count = len(self.buffer.buffer)
        if buffered_count:
            logger.info(f"Loaded {buffered_count} buffered snapshots from previous session")

        # Step 3: Try to register with server
        # Load saved API key if exists
        key_path = os.path.expanduser("~/.ganuda-shield/api_key")
        if os.path.exists(key_path):
            with open(key_path) as f:
                self.transport.api_key = f.read().strip()
            logger.info("Loaded saved API key.")
        else:
            self.register_with_server()

        # Step 4: Start monitoring
        self.running = True
        self.last_batch_send = time.time()
        self.last_heartbeat = time.time()
        escalation_check_counter = 0

        logger.info(f"Shield Agent running — {self.config.machine_id}")
        logger.info(f"Employee: {self.config.employee_id}")
        logger.info(f"Capture interval: {self.config.capture_interval}s")
        logger.info(f"Batch interval: {self.config.batch_interval}s")
        logger.info(f"Server: {self.config.server_url}")
        logger.info("Press Ctrl+C to stop\n")

        def shutdown(sig, frame):
            logger.info("Shutting down...")
            self.running = False
            # Save any remaining data
            for snapshot in self.batch:
                self.buffer.add(snapshot)
            self.buffer.save_to_disk()
            logger.info(f"Buffered {len(self.buffer.buffer)} snapshots to disk.")
            logger.info(f"Total snapshots captured this session: {self.snapshot_count}")
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        while self.running:
            try:
                # Capture activity snapshot
                snapshot = capture_activity_snapshot(self.config)
                self.batch.append(snapshot)
                self.snapshot_count += 1

                if self.snapshot_count % 10 == 0:
                    logger.info(f"Captured {self.snapshot_count} snapshots | Batch: {len(self.batch)} pending")

                # Heartbeat
                self.send_heartbeat()

                # Send batch if interval elapsed
                self.send_batch()

                # Check for escalation updates (every 5 captures)
                escalation_check_counter += 1
                if escalation_check_counter >= 5:
                    self.check_escalation()
                    escalation_check_counter = 0

                time.sleep(self.config.capture_interval)

            except Exception as e:
                logger.error(f"Capture error: {e}")
                time.sleep(self.config.capture_interval)


def main():
    parser = argparse.ArgumentParser(description="Ganuda Shield Agent — Transparent Endpoint Monitoring")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--employee", default=None, help="Employee ID")
    parser.add_argument("--status", action="store_true", help="Check agent status")
    parser.add_argument("--withdraw-consent", action="store_true", help="Withdraw consent and stop")
    args = parser.parse_args()

    if args.withdraw_consent:
        if withdraw_consent():
            print("Consent withdrawn. Agent will not run until re-consented.")
        else:
            print("No consent record found.")
        return

    if args.status:
        if check_consent_exists():
            consent = load_consent()
            print(f"Consent: {'WITHDRAWN' if consent.get('withdrawn') else 'ACTIVE'}")
            print(f"Employee: {consent.get('employee_id')}")
            print(f"Since: {consent.get('consent_timestamp', '?')[:19]}")
            print(f"Jurisdiction: {consent.get('jurisdiction')}")
        else:
            print("No consent recorded. Agent has not been initialized.")
        return

    config = load_config(args.config) if args.config else load_config()
    if args.employee:
        config.employee_id = args.employee

    agent = ShieldAgent(config)
    agent.run()


if __name__ == '__main__':
    main()
