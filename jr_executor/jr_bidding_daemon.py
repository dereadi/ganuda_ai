#!/usr/bin/env python3
"""
Jr Bidding Daemon - Polls for announced tasks and submits bids.

Based on Contract Net Protocol from JR_TASK_BIDDING_SYSTEM.md.
Implements arXiv research-based task assignment.

Run as: python3 jr_bidding_daemon.py <agent_id> <node_name>
Example: python3 jr_bidding_daemon.py jr-redfin-gecko redfin

For Seven Generations - Cherokee AI Federation
"""

import os
import sys
import time
import signal
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Configuration
POLL_INTERVAL = 10  # seconds between task polls
HEARTBEAT_INTERVAL = 60  # seconds between heartbeats

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}


class JrBiddingDaemon:
    """
    Daemon that polls for announced tasks and submits bids.
    One daemon runs per Jr agent, watching for tasks it can do.
    """

    def __init__(self, agent_id: str, node_name: str):
        self.agent_id = agent_id
        self.node_name = node_name
        self.running = True
        self.last_heartbeat = 0
        self._conn = None

        # Load agent capabilities
        self.capabilities = self._load_capabilities()

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
        return self._conn

    def _shutdown(self, signum, frame):
        print(f"\n[{self.agent_id}] Shutting down bidding daemon...")
        self.running = False

    def _load_capabilities(self):
        """Load agent capabilities from jr_agent_state"""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT specialization, specialization_scores, success_rate
                    FROM jr_agent_state
                    WHERE agent_id = %s
                """, (self.agent_id,))
                result = cur.fetchone()

                if result:
                    return {
                        'specialization': result['specialization'],
                        'scores': result.get('specialization_scores') or {},
                        'success_rate': result.get('success_rate') or 0.5
                    }
        except Exception as e:
            print(f"[{self.agent_id}] Error loading capabilities: {e}")

        return {'specialization': 'general', 'scores': {}, 'success_rate': 0.5}

    def _heartbeat(self):
        """Update agent's last_active timestamp"""
        now = time.time()
        if now - self.last_heartbeat >= HEARTBEAT_INTERVAL:
            try:
                conn = self._get_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE jr_agent_state
                        SET last_active = NOW()
                        WHERE agent_id = %s
                    """, (self.agent_id,))

                    if cur.rowcount == 0:
                        # Agent doesn't exist, create it
                        cur.execute("""
                            INSERT INTO jr_agent_state (agent_id, node_name, specialization)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (agent_id) DO UPDATE SET last_active = NOW()
                        """, (self.agent_id, self.node_name, 'general'))

                    conn.commit()
                self.last_heartbeat = now
                print(f"[{self.agent_id}] Heartbeat sent")

            except Exception as e:
                print(f"[{self.agent_id}] Heartbeat failed: {e}")

    def get_open_tasks(self):
        """Get tasks open for bidding"""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT task_id, task_type, task_content,
                           required_capabilities, preferred_node, priority, deadline
                    FROM jr_task_announcements
                    WHERE status = 'open'
                    ORDER BY priority ASC, announced_at ASC
                    LIMIT 10
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"[{self.agent_id}] Error fetching tasks: {e}")
            return []

    def already_bid_on(self, task_id: str) -> bool:
        """Check if we already bid on this task"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM jr_task_bids
                    WHERE task_id = %s AND agent_id = %s
                """, (task_id, self.agent_id))
                return cur.fetchone() is not None
        except:
            return False

    def calculate_bid(self, task: dict) -> dict:
        """Calculate bid score for a task"""

        # Capability score: How well do we match required capabilities?
        required_caps = task.get('required_capabilities') or []
        if not required_caps:
            capability_score = 0.7  # No requirements = assume capable
        else:
            matches = sum(1 for cap in required_caps
                         if cap in str(self.capabilities.get('scores', {})))
            capability_score = matches / len(required_caps) if required_caps else 0.7

        # Experience score: Based on success rate
        experience_score = self.capabilities.get('success_rate', 0.5)

        # Load score: Check current assignments (1.0 = fully available)
        load_score = self._calculate_load()

        # Confidence: Based on task complexity (content length as proxy)
        content_len = len(task.get('task_content', ''))
        if content_len < 500:
            confidence = 0.9
        elif content_len < 2000:
            confidence = 0.7
        else:
            confidence = 0.5

        # Composite score calculation
        # Weights: capability 40%, experience 30%, load 20%, confidence 10%
        composite = (
            0.40 * capability_score +
            0.30 * experience_score +
            0.20 * load_score +
            0.10 * confidence
        )

        # Bonus for preferred node
        if task.get('preferred_node') == self.node_name:
            composite *= 1.1

        return {
            'task_id': task['task_id'],
            'agent_id': self.agent_id,
            'node_name': self.node_name,
            'capability_score': capability_score,
            'experience_score': experience_score,
            'load_score': load_score,
            'confidence': confidence,
            'composite_score': min(1.0, composite)
        }

    def _calculate_load(self) -> float:
        """Calculate load score (higher = more available)"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM jr_task_announcements
                    WHERE assigned_to = %s AND status = 'assigned'
                """, (self.agent_id,))
                current_tasks = cur.fetchone()[0]

                # Assume max 3 concurrent tasks
                return max(0.1, 1.0 - (current_tasks / 3.0))
        except:
            return 0.5

    def submit_bid(self, bid: dict):
        """Submit bid to database"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO jr_task_bids
                    (task_id, agent_id, node_name, capability_score,
                     experience_score, load_score, confidence, composite_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    bid['task_id'], bid['agent_id'], bid['node_name'],
                    bid['capability_score'], bid['experience_score'],
                    bid['load_score'], bid['confidence'], bid['composite_score']
                ))
                conn.commit()
                print(f"[{self.agent_id}] Bid submitted: {bid['task_id']} (score: {bid['composite_score']:.2f})")
        except Exception as e:
            print(f"[{self.agent_id}] Bid submission failed: {e}")

    def run(self):
        """Main daemon loop"""
        print(f"[{self.agent_id}] Bidding daemon starting on {self.node_name}")
        print(f"[{self.agent_id}] Capabilities: {self.capabilities}")
        print(f"[{self.agent_id}] Poll interval: {POLL_INTERVAL}s")

        self._heartbeat()

        while self.running:
            try:
                self._heartbeat()

                # Get open tasks
                tasks = self.get_open_tasks()

                if tasks:
                    print(f"[{self.agent_id}] Found {len(tasks)} open task(s)")

                for task in tasks:
                    task_id = task['task_id']

                    # Skip if already bid
                    if self.already_bid_on(task_id):
                        continue

                    # Calculate and submit bid
                    bid = self.calculate_bid(task)
                    self.submit_bid(bid)

                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[{self.agent_id}] Error in main loop: {e}")
                time.sleep(POLL_INTERVAL)

        print(f"[{self.agent_id}] Bidding daemon stopped")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 jr_bidding_daemon.py <agent_id> <node_name>")
        print("Example: python3 jr_bidding_daemon.py jr-redfin-gecko redfin")
        sys.exit(1)

    agent_id = sys.argv[1]
    node_name = sys.argv[2]

    daemon = JrBiddingDaemon(agent_id, node_name)
    daemon.run()
