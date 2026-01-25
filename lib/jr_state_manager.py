#!/usr/bin/env python3
"""
Cherokee AI Federation - Jr Agent State Manager
Implements episodic and semantic memory for Jr agents.

Based on: Emergent Collective Memory research (arXiv:2512.10166)
"Individual memory alone = 68.7% improvement. Traces alone = failure."
"""

import json
import psycopg2
from datetime import datetime
from typing import Optional, List, Dict

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

class JrStateManager:
    """Manages persistent state for Jr agents"""
    
    def __init__(self, agent_id: str, node_name: str):
        self.agent_id = agent_id
        self.node_name = node_name
        self.conn = self._connect()
        self._ensure_state_exists()
    
    def _connect(self):
        return psycopg2.connect(**DB_CONFIG)
    
    def _ensure_state_exists(self):
        """Create agent state if not exists"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jr_agent_state (agent_id, node_name)
                VALUES (%s, %s)
                ON CONFLICT (agent_id) DO NOTHING
            """, (self.agent_id, self.node_name))
            self.conn.commit()
    
    def load_state(self) -> Optional[Dict]:
        """Load agent's persistent state"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT working_memory, episodic_memory, semantic_memory,
                       tasks_completed, specialization_scores
                FROM jr_agent_state WHERE agent_id = %s
            """, (self.agent_id,))
            row = cur.fetchone()
            if row:
                return {
                    "working_memory": row[0],
                    "episodic_memory": row[1],
                    "semantic_memory": row[2],
                    "tasks_completed": row[3],
                    "specialization_scores": row[4]
                }
        return None
    
    def save_task_outcome(self, task_summary: str, success: bool, learnings: str = None):
        """Save task to episodic memory (keeps last 50)"""
        episode = {
            "timestamp": datetime.now().isoformat(),
            "summary": task_summary,
            "success": success,
            "learnings": learnings
        }
        
        with self.conn.cursor() as cur:
            # Get current episodic memory
            cur.execute("""
                SELECT episodic_memory FROM jr_agent_state WHERE agent_id = %s
            """, (self.agent_id,))
            row = cur.fetchone()
            episodes = row[0] if row and row[0] else []
            
            # Add new episode and keep last 50
            episodes.insert(0, episode)
            episodes = episodes[:50]
            
            # Update state
            cur.execute("""
                UPDATE jr_agent_state
                SET episodic_memory = %s,
                    tasks_completed = tasks_completed + 1,
                    success_rate = (success_rate * tasks_completed + %s) / (tasks_completed + 1),
                    last_active = NOW()
                WHERE agent_id = %s
            """, (json.dumps(episodes), 1.0 if success else 0.0, self.agent_id))
            self.conn.commit()
    
    def update_semantic_memory(self, key: str, value):
        """Update long-term learned patterns"""
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE jr_agent_state
                SET semantic_memory = semantic_memory || %s::jsonb
                WHERE agent_id = %s
            """, (json.dumps({key: value}), self.agent_id))
            self.conn.commit()
    
    def get_relevant_episodes(self, keywords: List[str], limit: int = 5) -> List[Dict]:
        """Recall relevant past tasks based on keywords"""
        state = self.load_state()
        if not state:
            return []
        
        relevant = []
        for episode in state.get("episodic_memory", []):
            summary = episode.get("summary", "").lower()
            if any(kw.lower() in summary for kw in keywords):
                relevant.append(episode)
        
        return relevant[:limit]
    
    def update_specialization(self, task_type: str, success: bool):
        """Track specialization scores by task type"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT specialization_scores FROM jr_agent_state WHERE agent_id = %s
            """, (self.agent_id,))
            row = cur.fetchone()
            scores = row[0] if row and row[0] else {}
            
            if task_type not in scores:
                scores[task_type] = {"attempts": 0, "successes": 0}
            
            scores[task_type]["attempts"] += 1
            if success:
                scores[task_type]["successes"] += 1
            
            cur.execute("""
                UPDATE jr_agent_state
                SET specialization_scores = %s
                WHERE agent_id = %s
            """, (json.dumps(scores), self.agent_id))
            self.conn.commit()
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_state_manager():
    """Test the state manager"""
    print("Testing Jr State Manager:")
    print("=" * 50)
    
    # Create test agent
    mgr = JrStateManager("test-jr-001", "redfin")
    
    # Save some tasks
    mgr.save_task_outcome("Fixed bug in gateway", True, "Check logs first")
    mgr.save_task_outcome("Deployed new service", True, "Use systemd")
    mgr.save_task_outcome("Database migration", False, "Backup first")
    
    # Update semantic memory
    mgr.update_semantic_memory("preferred_editor", "vim")
    mgr.update_semantic_memory("common_paths", ["/ganuda/lib", "/ganuda/services"])
    
    # Load state
    state = mgr.load_state()
    print(f"Agent: {mgr.agent_id}")
    print(f"Tasks completed: {state['tasks_completed']}")
    print(f"Episodic memory entries: {len(state['episodic_memory'])}")
    print(f"Semantic memory: {state['semantic_memory']}")
    
    # Find relevant episodes
    episodes = mgr.get_relevant_episodes(["bug", "gateway"])
    print(f"Relevant episodes for 'bug gateway': {len(episodes)}")
    
    mgr.close()
    print("=" * 50)
    print("Jr State Manager: OPERATIONAL")


if __name__ == "__main__":
    test_state_manager()
