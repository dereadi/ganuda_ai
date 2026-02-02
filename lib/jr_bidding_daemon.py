#!/usr/bin/env python3
"""
Jr Bidding Daemon - Contract Net Protocol Bidding for Task Assignment

Monitors jr_task_announcements for open tasks and submits bids.
Bids are scored by capability match, agent experience, current load,
and now SwarmSys pheromone signals.

Run as: python3 jr_bidding_daemon.py <agent_id> <node_name> [specialization]
Example: python3 jr_bidding_daemon.py jr-redfin-gecko redfin general

Enhanced Dec 24, 2025: Added SwarmSys pheromone integration for stigmergic coordination.

For Seven Generations - Cherokee AI Federation
"""

import os
import sys
import time
import signal
import json
import platform
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Optional

# Determine ganuda path based on OS
GANUDA_PATH = "/Users/Shared/ganuda" if platform.system() == "Darwin" else "/ganuda"

# Add lib to path for pheromone imports
sys.path.insert(0, os.path.join(GANUDA_PATH, 'lib'))

# Import pheromone functions for SwarmSys integration
try:
    from smadrl_pheromones import calculate_pheromone_boost, get_agent_pheromone_affinity
    PHEROMONES_ENABLED = True
except ImportError:
    PHEROMONES_ENABLED = False
    print("[WARN] smadrl_pheromones not available, pheromone boosting disabled")

# Configuration
POLL_INTERVAL = 15  # seconds between bid cycles
BID_WINDOW = 60  # seconds to wait for other bids before assignment

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
}

# Capability definitions by specialization
SPECIALIZATION_CAPABILITIES = {
    'general': ['python', 'sql', 'documentation', 'research'],
    'strategy': ['planning', 'architecture', 'analysis', 'research'],
    'mobile_council': ['voting', 'consensus', 'deliberation'],
    'tpm_assistant': ['coordination', 'planning', 'review'],
    'code': ['python', 'sql', 'javascript', 'testing', 'debugging'],
    'research': ['research', 'analysis', 'documentation'],
    'security': ['security', 'audit', 'compliance'],
}


class JrBiddingDaemon:
    """
    Daemon that monitors for open tasks and submits bids.
    Enhanced with SwarmSys pheromone-based bid scoring.
    """

    def __init__(self, agent_id: str, node_name: str, specialization: str = 'general'):
        self.agent_id = agent_id
        self.node_name = node_name
        self.specialization = specialization
        self.capabilities = SPECIALIZATION_CAPABILITIES.get(specialization, ['general'])
        self.running = True
        self._conn = None
        self.tasks_in_progress = 0

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
        return self._conn

    def _shutdown(self, signum, frame):
        print(f"\n[{self.agent_id}] Shutting down bidding daemon...")
        self.running = False

    def update_agent_state(self):
        """Update agent heartbeat in jr_agent_state."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO jr_agent_state (agent_id, node_name, specialization, last_active)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (agent_id)
                    DO UPDATE SET last_active = NOW(), node_name = EXCLUDED.node_name
                """, (self.agent_id, self.node_name, self.specialization))
                conn.commit()
        except Exception as e:
            print(f"[{self.agent_id}] Error updating state: {e}")

    def get_open_tasks(self) -> List[dict]:
        """Get tasks that are open for bidding."""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT task_id, task_type, task_content, priority,
                           required_capabilities, preferred_node, announced_at
                    FROM jr_task_announcements
                    WHERE status = 'open'
                    ORDER BY priority ASC, announced_at ASC
                    LIMIT 10
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"[{self.agent_id}] Error getting tasks: {e}")
            return []

    def calculate_capability_score(self, task: dict) -> float:
        """Calculate how well agent capabilities match task requirements."""
        required = task.get('required_capabilities') or []
        if not required:
            return 0.7  # Default match for unspecified requirements

        matches = sum(1 for cap in required if cap in self.capabilities)
        return min(matches / max(len(required), 1), 1.0)

    def calculate_experience_score(self, task_type: str) -> float:
        """Calculate experience score based on past task completions."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Count successful completions of this task type
                cur.execute("""
                    SELECT COUNT(*) FROM jr_task_announcements
                    WHERE assigned_to = %s
                      AND task_type = %s
                      AND status = 'completed'
                """, (self.agent_id, task_type))
                completed = cur.fetchone()[0]

                # Diminishing returns: 1 completion = 0.5, 5 = 0.8, 10+ = 0.95
                if completed == 0:
                    return 0.3
                elif completed < 5:
                    return 0.5 + (completed * 0.06)
                else:
                    return min(0.8 + (completed * 0.015), 0.95)
        except Exception as e:
            print(f"[{self.agent_id}] Error calculating experience: {e}")
            return 0.3

    def calculate_load_score(self) -> float:
        """Calculate load score (lower load = higher score)."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM jr_task_announcements
                    WHERE assigned_to = %s
                      AND status IN ('assigned', 'in_progress')
                """, (self.agent_id,))
                active_tasks = cur.fetchone()[0]

                # Fewer active tasks = higher score
                if active_tasks == 0:
                    return 1.0
                elif active_tasks == 1:
                    return 0.7
                elif active_tasks == 2:
                    return 0.4
                else:
                    return 0.1
        except Exception as e:
            print(f"[{self.agent_id}] Error calculating load: {e}")
            return 0.5

    def calculate_node_preference_boost(self, task: dict) -> float:
        """Boost score if this node is preferred for the task."""
        preferred = task.get('preferred_node')
        if preferred and preferred == self.node_name:
            return 0.1
        return 0.0

    def calculate_bid_score(self, task: dict) -> tuple:
        """
        Calculate composite bid score for a task.
        Now includes SwarmSys pheromone boost.

        Returns:
            (composite_score, capability_score, experience_score, load_score, pheromone_boost)
        """
        task_type = task.get('task_type', 'unknown')

        # Base scores
        capability = self.calculate_capability_score(task)
        experience = self.calculate_experience_score(task_type)
        load = self.calculate_load_score()
        node_boost = self.calculate_node_preference_boost(task)

        # SwarmSys pheromone boost
        pheromone_boost = 0.0
        if PHEROMONES_ENABLED:
            try:
                pheromone_boost = calculate_pheromone_boost(task_type, self.agent_id)
            except Exception as e:
                print(f"[{self.agent_id}] Pheromone boost error: {e}")

        # Weighted composite (capability 35%, experience 25%, load 30%, pheromone 10%)
        composite = (
            capability * 0.35 +
            experience * 0.25 +
            load * 0.30 +
            pheromone_boost * 0.10 +
            node_boost
        )

        return composite, capability, experience, load, pheromone_boost

    def submit_bid(self, task: dict):
        """Submit a bid for a task."""
        task_id = task['task_id']

        # Calculate scores
        composite, capability, experience, load, pheromone = self.calculate_bid_score(task)

        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Check if we already bid
                cur.execute("""
                    SELECT id FROM jr_task_bids
                    WHERE task_id = %s AND agent_id = %s
                """, (task_id, self.agent_id))

                if cur.fetchone():
                    return  # Already bid on this task

                # Submit bid
                metadata = {
                    'pheromone_boost': pheromone,
                    'pheromones_enabled': PHEROMONES_ENABLED,
                    'capabilities': self.capabilities
                }

                cur.execute("""
                    INSERT INTO jr_task_bids
                    (task_id, agent_id, node_name, capability_score, experience_score,
                     load_score, confidence, composite_score, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    task_id, self.agent_id, self.node_name,
                    capability, experience, load,
                    0.8,  # Confidence placeholder
                    composite,
                    json.dumps(metadata)
                ))
                conn.commit()

                print(f"[{self.agent_id}] Bid on {task_id}: score={composite:.3f} "
                      f"(cap={capability:.2f}, exp={experience:.2f}, load={load:.2f}, pheromone={pheromone:.2f})")

        except Exception as e:
            print(f"[{self.agent_id}] Error submitting bid: {e}")

    def select_winning_bids(self):
        """
        Select winning bids for tasks past the bid window.
        Only runs on the 'primary' bidding daemon (first one to check).
        """
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Find tasks ready for assignment (past bid window, have bids)
                cur.execute("""
                    SELECT DISTINCT t.task_id, t.task_type
                    FROM jr_task_announcements t
                    JOIN jr_task_bids b ON t.task_id = b.task_id
                    WHERE t.status = 'open'
                      AND t.announced_at < NOW() - INTERVAL '%s seconds'
                """, (BID_WINDOW,))

                tasks_ready = cur.fetchall()

                for task in tasks_ready:
                    task_id = task['task_id']

                    # Get highest bidder
                    cur.execute("""
                        SELECT agent_id, composite_score
                        FROM jr_task_bids
                        WHERE task_id = %s
                        ORDER BY composite_score DESC
                        LIMIT 1
                    """, (task_id,))

                    winner = cur.fetchone()
                    if winner:
                        # Assign task to winner
                        cur.execute("""
                            UPDATE jr_task_announcements
                            SET status = 'assigned', assigned_to = %s
                            WHERE task_id = %s AND status = 'open'
                        """, (winner['agent_id'], task_id))

                        if cur.rowcount > 0:
                            print(f"[ASSIGN] {task_id} -> {winner['agent_id']} "
                                  f"(score: {winner['composite_score']:.3f})")

                conn.commit()

        except Exception as e:
            print(f"[{self.agent_id}] Error selecting winners: {e}")

    def run(self):
        """Main daemon loop."""
        print(f"[{self.agent_id}] Bidding Daemon starting on {self.node_name}")
        print(f"[{self.agent_id}] Specialization: {self.specialization}")
        print(f"[{self.agent_id}] Capabilities: {self.capabilities}")
        print(f"[{self.agent_id}] Pheromones: {'ENABLED' if PHEROMONES_ENABLED else 'DISABLED'}")
        print(f"[{self.agent_id}] Poll interval: {POLL_INTERVAL}s, Bid window: {BID_WINDOW}s")

        while self.running:
            try:
                # Update heartbeat
                self.update_agent_state()

                # Get open tasks
                tasks = self.get_open_tasks()

                # Submit bids
                for task in tasks:
                    self.submit_bid(task)

                # Select winners for tasks past bid window
                self.select_winning_bids()

                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[{self.agent_id}] Error in main loop: {e}")
                time.sleep(POLL_INTERVAL)

        print(f"[{self.agent_id}] Bidding Daemon stopped")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 jr_bidding_daemon.py <agent_id> <node_name> [specialization]")
        print("Example: python3 jr_bidding_daemon.py jr-redfin-gecko redfin general")
        sys.exit(1)

    agent_id = sys.argv[1]
    node_name = sys.argv[2]
    specialization = sys.argv[3] if len(sys.argv) > 3 else 'general'

    daemon = JrBiddingDaemon(agent_id, node_name, specialization)
    daemon.run()
