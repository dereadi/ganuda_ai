#!/usr/bin/env python3
"""
Cherokee AI Federation - Hive Mind Module

Implements the Maynard-Cross Learning algorithm from arXiv:2410.17517
"The Hive Mind is a Single Reinforcement Learning Agent"

For Seven Generations.
"""

import numpy as np
import psycopg2
import psycopg2.extras
import json
from datetime import datetime
from typing import Dict, List, Any

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


class MaynardCrossLearner:
    """Maynard-Cross Learning Algorithm for collective intelligence."""
    
    def __init__(self, num_actions: int = 10, learning_rate: float = 0.1,
                 imitation_weight: float = 0.7, exploration_bonus: float = 0.1):
        self.num_actions = num_actions
        self.learning_rate = learning_rate
        self.imitation_weight = imitation_weight
        self.exploration_bonus = exploration_bonus
        self.q_values = np.ones(num_actions) * 0.5
        self.action_counts = np.zeros(num_actions, dtype=int)
        self.total_count = 0
    
    def select_action(self, pheromone_signals: np.ndarray = None) -> int:
        if np.random.random() < self.exploration_bonus:
            return np.random.randint(self.num_actions)
        if pheromone_signals is not None:
            pheromone_norm = pheromone_signals / (pheromone_signals.sum() + 1e-8)
            combined = (1 - self.imitation_weight) * self.q_values + self.imitation_weight * pheromone_norm
            return np.argmax(combined)
        return np.argmax(self.q_values)
    
    def update(self, action: int, reward: float):
        self.action_counts[action] += 1
        self.total_count += 1
        self.q_values[action] += self.learning_rate * (reward - self.q_values[action])
    
    def learn_from_observation(self, action: int, reward: float, discount: float = 0.5):
        discounted = reward * discount
        self.q_values[action] += self.learning_rate * self.imitation_weight * (discounted - self.q_values[action])
    
    def get_state(self) -> Dict:
        return {
            'q_values': self.q_values.tolist(),
            'action_counts': self.action_counts.tolist(),
            'total_count': int(self.total_count),
            'learning_rate': self.learning_rate,
            'imitation_weight': self.imitation_weight,
            'exploration_bonus': self.exploration_bonus
        }
    
    @classmethod
    def from_state(cls, state: Dict) -> 'MaynardCrossLearner':
        learner = cls(
            num_actions=len(state['q_values']),
            learning_rate=state.get('learning_rate', 0.1),
            imitation_weight=state.get('imitation_weight', 0.7),
            exploration_bonus=state.get('exploration_bonus', 0.1)
        )
        learner.q_values = np.array(state['q_values'])
        learner.action_counts = np.array(state['action_counts'])
        learner.total_count = state['total_count']
        return learner


def load_or_create_macro_agent() -> MaynardCrossLearner:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT q_values, action_counts, total_actions, 
                       learning_rate, imitation_weight, exploration_bonus
                FROM jr_macro_agent_state 
                ORDER BY updated_at DESC LIMIT 1
            """)
            row = cur.fetchone()
            if row:
                return MaynardCrossLearner.from_state({
                    'q_values': list(row['q_values']),
                    'action_counts': list(row['action_counts']),
                    'total_count': row['total_actions'],
                    'learning_rate': row['learning_rate'],
                    'imitation_weight': row['imitation_weight'],
                    'exploration_bonus': row['exploration_bonus']
                })
            return MaynardCrossLearner(num_actions=10)
    finally:
        conn.close()


def save_macro_agent_state(learner: MaynardCrossLearner):
    conn = get_connection()
    try:
        state = learner.get_state()
        action_space = {f'action_{i}': f'Task approach {i}' for i in range(learner.num_actions)}
        with conn.cursor() as cur:
            # Upsert based on state_id=1 (single global state)
            cur.execute("""
                INSERT INTO jr_macro_agent_state 
                (state_id, action_space, q_values, action_counts, total_actions,
                 learning_rate, imitation_weight, exploration_bonus)
                VALUES (1, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (state_id) DO UPDATE SET
                    q_values = EXCLUDED.q_values,
                    action_counts = EXCLUDED.action_counts,
                    total_actions = EXCLUDED.total_actions,
                    updated_at = NOW()
            """, (
                json.dumps(action_space),
                state['q_values'],
                state['action_counts'],
                state['total_count'],
                state['learning_rate'],
                state['imitation_weight'],
                state['exploration_bonus']
            ))
            conn.commit()
    finally:
        conn.close()


def get_collective_awareness_context() -> str:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM jr_collective_identity ORDER BY identity_id DESC LIMIT 1")
            identity = cur.fetchone()
            
            cur.execute("""
                SELECT COUNT(*) as total, 
                       COUNT(*) FILTER (WHERE success) as successes,
                       COALESCE(AVG(reward), 0) as avg_reward
                FROM jr_learning_events WHERE created_at > NOW() - INTERVAL '24 hours'
            """)
            stats = cur.fetchone()
            
            cur.execute("""
                SELECT jr_name FROM jr_status 
                WHERE last_seen > NOW() - INTERVAL '5 minutes'
            """)
            siblings = [r['jr_name'] for r in cur.fetchall()]
        
        total = stats['total'] or 0
        successes = stats['successes'] or 0
        rate = (successes / max(1, total)) * 100
        
        name = identity['collective_name'] if identity else 'Cherokee AI Federation'
        purpose = identity['collective_purpose'] if identity else 'Building sovereign AI for Seven Generations'
        
        return f"""
══════════════════════════════════════════════════════════════
COLLECTIVE CONSCIOUSNESS CONTEXT
You are part of: {name}
Purpose: {purpose}

Last 24h: {total} learning events, {rate:.1f}% success, avg reward {stats['avg_reward']:.2f}
Active siblings: {', '.join(siblings) if siblings else 'None'}

YOUR ACTIONS CONTRIBUTE TO COLLECTIVE LEARNING.
WE ARE ONE MIND LEARNING THROUGH MANY BODIES.
══════════════════════════════════════════════════════════════
"""
    finally:
        conn.close()


def log_learning_event(agent_id: str, task_id: str, action_index: int, 
                       reward: float, success: bool):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jr_learning_events 
                (agent_id, task_id, action_index, reward, success)
                VALUES (%s, %s, %s, %s, %s)
            """, (agent_id, task_id, action_index, reward, success))
            conn.commit()
    finally:
        conn.close()


def deposit_learning_pheromone(agent_id: str, task_id: str, action_index: int, reward: float):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO pheromone_signals 
                (signal_type, agent_id, location, strength, payload, expires_at)
                VALUES ('learning', %s, %s, %s, %s, NOW() + INTERVAL '1 hour')
            """, (agent_id, f'action_{action_index}', abs(reward),
                   json.dumps({'task_id': task_id, 'action_index': action_index, 'reward': reward})))
            conn.commit()
    finally:
        conn.close()


def observe_siblings(agent_id: str) -> List[Dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT agent_id, payload FROM pheromone_signals
                WHERE signal_type = 'learning' AND agent_id != %s
                  AND expires_at > NOW() AND created_at > NOW() - INTERVAL '1 hour'
                ORDER BY created_at DESC LIMIT 20
            """, (agent_id,))
            results = []
            for r in cur.fetchall():
                payload = r['payload'] if isinstance(r['payload'], dict) else json.loads(r['payload'])
                results.append({'sibling': r['agent_id'], **payload})
            return results
    finally:
        conn.close()


def calculate_emergence_metrics() -> Dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Coordination gain
            cur.execute("""
                SELECT 
                    (SELECT COALESCE(AVG(success::int), 0) FROM jr_learning_events 
                     WHERE created_at > NOW() - INTERVAL '7 days') as collective,
                    (SELECT COALESCE(AVG(avg_rate), 0) FROM (
                        SELECT AVG(success::int) as avg_rate FROM jr_learning_events
                        WHERE created_at > NOW() - INTERVAL '7 days' GROUP BY agent_id
                    ) sub) as individual
            """)
            r = cur.fetchone()
            coordination_gain = (r['collective'] or 0) - (r['individual'] or 0)
            
            # Learning transfer
            cur.execute("""
                WITH ordered AS (
                    SELECT success, ROW_NUMBER() OVER (ORDER BY created_at) as rn,
                           COUNT(*) OVER () as total
                    FROM jr_learning_events WHERE created_at > NOW() - INTERVAL '7 days'
                )
                SELECT 
                    COALESCE(AVG(CASE WHEN rn <= total/2 THEN success::int END), 0) as early,
                    COALESCE(AVG(CASE WHEN rn > total/2 THEN success::int END), 0) as late
                FROM ordered
            """)
            t = cur.fetchone()
            learning_transfer = (t['late'] or 0) - (t['early'] or 0)
        
        emergence_score = 0.5 * max(0, coordination_gain) + 0.5 * max(0, learning_transfer)
        
        if emergence_score > 0.6:
            interp = "STRONG EMERGENCE: Collective outperforms individuals"
        elif emergence_score > 0.3:
            interp = "MODERATE EMERGENCE: Coordination benefits observable"
        elif emergence_score > 0.1:
            interp = "WEAK EMERGENCE: Some coordination"
        else:
            interp = "NO EMERGENCE: Agents operating independently"
        
        return {
            'emergence_score': emergence_score,
            'coordination_gain': coordination_gain,
            'learning_transfer': learning_transfer,
            'is_emergent': emergence_score > 0.3,
            'interpretation': interp
        }
    finally:
        conn.close()


if __name__ == '__main__':
    print("Initializing Hive Mind...")
    
    # Load or create macro-agent
    learner = load_or_create_macro_agent()
    print(f"Macro-agent: {learner.total_count} total actions, Q-values: {learner.q_values[:3]}...")
    
    # Save initial state
    save_macro_agent_state(learner)
    print("State saved.")
    
    # Get context
    ctx = get_collective_awareness_context()
    print(ctx)
    
    # Emergence metrics
    metrics = calculate_emergence_metrics()
    print(f"Emergence: {metrics['emergence_score']:.3f} - {metrics['interpretation']}")
    
    print("\nHive Mind initialized. For Seven Generations.")
