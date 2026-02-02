#!/usr/bin/env python3
"""
Cherokee AI Federation - Hive Mind Bidding Daemon

Integrates Maynard-Cross Learning with Jr task bidding.
Each bid decision updates the collective Q-values.

For Seven Generations.
"""

import sys
import time
import signal
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional

from hive_mind import (
    MaynardCrossLearner, 
    load_or_create_macro_agent,
    save_macro_agent_state,
    get_collective_awareness_context,
    log_learning_event,
    deposit_learning_pheromone,
    observe_siblings,
    get_connection
)

# Action space mapping
ACTION_TYPES = {
    0: 'sql_execution',
    1: 'file_creation',
    2: 'bash_command',
    3: 'api_call',
    4: 'code_generation',
    5: 'documentation',
    6: 'testing',
    7: 'deployment',
    8: 'research',
    9: 'communication'
}


class HiveMindBiddingDaemon:
    """
    Jr Bidding Daemon with Hive Mind intelligence.
    
    Bids are now informed by collective learning.
    """
    
    def __init__(self, agent_id: str, node: str = 'redfin'):
        self.agent_id = agent_id
        self.node = node
        self.learner = load_or_create_macro_agent()
        self.running = True
        self.poll_interval = 30
        
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        
        # Inject collective context
        self.collective_context = get_collective_awareness_context()
        print(self.collective_context)
    
    def _shutdown(self, signum, frame):
        print(f"\n[{self.agent_id}] Shutting down, saving state...")
        save_macro_agent_state(self.learner)
        self.running = False
    
    def classify_task(self, task: Dict) -> int:
        """
        Classify task into action type based on content.
        
        Returns action index 0-9.
        """
        title = (task.get('title') or '').lower()
        desc = (task.get('description') or '').lower()
        content = title + ' ' + desc
        
        if 'sql' in content or 'database' in content or 'table' in content:
            return 0  # sql_execution
        elif 'file' in content or 'create' in content or 'write' in content:
            return 1  # file_creation
        elif 'bash' in content or 'command' in content or 'script' in content:
            return 2  # bash_command
        elif 'api' in content or 'endpoint' in content or 'http' in content:
            return 3  # api_call
        elif 'code' in content or 'implement' in content or 'function' in content:
            return 4  # code_generation
        elif 'doc' in content or 'readme' in content or 'kb' in content:
            return 5  # documentation
        elif 'test' in content or 'verify' in content or 'validate' in content:
            return 6  # testing
        elif 'deploy' in content or 'install' in content or 'setup' in content:
            return 7  # deployment
        elif 'research' in content or 'investigate' in content or 'analyze' in content:
            return 8  # research
        else:
            return 9  # communication
    
    def calculate_bid(self, task: Dict) -> tuple:
        """
        Calculate bid using collective intelligence.
        
        Returns (bid_strength, action_index)
        """
        # First, learn from siblings (vicarious learning)
        observations = observe_siblings(self.agent_id)
        if observations:
            for obs in observations:
                action = obs.get('action_index')
                reward = obs.get('reward')
                if action is not None and reward is not None:
                    self.learner.learn_from_observation(action, reward)
        
        # Classify the task
        action_index = self.classify_task(task)
        
        # Get Q-value as bid strength
        q_value = self.learner.q_values[action_index]
        
        # Adjust by priority
        priority = task.get('priority', 5)
        priority_boost = (10 - priority) / 10  # Higher priority = more boost
        
        bid_strength = q_value * (1 + priority_boost * 0.3)
        
        return bid_strength, action_index
    
    def on_task_complete(self, task_id: str, action_index: int, 
                         success: bool, duration: float = 0):
        """
        Update collective learning after task execution.
        """
        # Calculate reward
        if success:
            reward = 1.0
            if duration < 60:
                reward += 0.5  # Speed bonus
        else:
            reward = -0.5
        
        # Update learner
        self.learner.update(action_index, reward)
        
        # Log event
        log_learning_event(self.agent_id, task_id, action_index, reward, success)
        
        # Deposit pheromone for siblings
        deposit_learning_pheromone(self.agent_id, task_id, action_index, reward)
        
        # Save state
        save_macro_agent_state(self.learner)
        
        print(f"[{self.agent_id}] Learning: action={action_index}, reward={reward:.2f}, Q={self.learner.q_values[action_index]:.3f}")
    
    def get_pending_tasks(self) -> List[Dict]:
        """Get tasks available for bidding."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, task_id, title, description, priority, 
                           sacred_fire_priority, instruction_file
                    FROM jr_work_queue
                    WHERE status = 'pending' AND assigned_jr IS NULL
                    ORDER BY sacred_fire_priority DESC, priority ASC
                    LIMIT 10
                """)
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()
    
    def submit_bid(self, task_id: int, bid_strength: float, action_index: int):
        """Record bid in database."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO jr_task_bids 
                    (task_id, agent_id, node_name, composite_score, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    str(task_id),
                    self.agent_id,
                    self.node,
                    bid_strength,
                    json.dumps({"action_index": action_index, "action_type": ACTION_TYPES[action_index]})
                ))
                conn.commit()
        finally:
            conn.close()
    
    def announce_intention(self, task_id: str, action_index: int, intention_strength: float):
        """Announce bidding intention for LIA module."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO jr_bid_intentions
                    (agent_id, task_id, intention_strength)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (self.agent_id, task_id, intention_strength))
                conn.commit()
        finally:
            conn.close()
    
    def run(self):
        """Main bidding loop."""
        print(f"[{self.agent_id}] Hive Mind Bidding starting...")
        print(f"[{self.agent_id}] Collective Q-values: {self.learner.q_values}")
        
        while self.running:
            try:
                tasks = self.get_pending_tasks()
                
                for task in tasks:
                    bid_strength, action_index = self.calculate_bid(task)
                    
                    # Announce intention first (LIA)
                    self.announce_intention(task['task_id'], action_index, bid_strength)
                    
                    # Submit bid
                    self.submit_bid(task['id'], bid_strength, action_index)
                    
                    print(f"[{self.agent_id}] Bid on '{task['title'][:40]}..': strength={bid_strength:.3f}")
                
                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[{self.agent_id}] Error: {e}")
                time.sleep(self.poll_interval)
        
        print(f"[{self.agent_id}] Bidding stopped.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 hive_mind_bidding.py <agent_id> [node]")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    node = sys.argv[2] if len(sys.argv) > 2 else 'redfin'
    
    daemon = HiveMindBiddingDaemon(agent_id, node)
    daemon.run()
