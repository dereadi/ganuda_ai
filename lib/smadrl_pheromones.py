#!/usr/bin/env python3
"""
S-MADRL Pheromone Library - Stigmergic Multi-Agent Coordination

Based on SwarmSys (arXiv:2510.10047) pheromone-based coordination.
Validates our existing stigmergy implementation with academic research.

Pheromone Types:
- task_completed: Success trail (intensity=1.0)
- task_failed: Failure warning (intensity=0.2)
- task_claimed: Agent working here
- exploration_success: New capability discovered

For Seven Generations - Cherokee AI Federation
"""

import os
import psycopg2
from typing import List, Dict, Optional
from datetime import datetime

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

# Pheromone configuration
DEFAULT_DECAY_RATE = 0.1  # 10% decay per hour
MIN_INTENSITY_THRESHOLD = 0.01  # Remove pheromones below this


def get_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)


def deposit_pheromone(
    location_type: str,
    location_id: str,
    pheromone_type: str,
    intensity: float,
    agent_id: str,
    decay_rate: float = DEFAULT_DECAY_RATE
) -> bool:
    """
    Deposit a pheromone at a location.

    Args:
        location_type: 'task_type', 'task', 'file', 'endpoint', etc.
        location_id: Specific identifier (e.g., 'implementation', 'task-123')
        pheromone_type: 'task_completed', 'task_failed', 'task_claimed', etc.
        intensity: Strength of signal (0.0-1.0, can accumulate higher)
        agent_id: Which agent deposited this
        decay_rate: How fast this decays (0.0-1.0 per hour)

    Returns:
        True if successful, False otherwise
    """
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # Upsert: add to existing intensity or insert new
            cur.execute("""
                INSERT INTO stigmergy_pheromones
                (location_type, location_id, pheromone_type, intensity, deposited_by, decay_rate)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (location_type, location_id, pheromone_type, deposited_by)
                DO UPDATE SET
                    intensity = stigmergy_pheromones.intensity + EXCLUDED.intensity,
                    deposited_at = NOW(),
                    decay_rate = EXCLUDED.decay_rate
            """, (location_type, location_id, pheromone_type, intensity, agent_id, decay_rate))
            conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[PHEROMONE] Error depositing: {e}")
        return False


def read_pheromones(
    location_type: str,
    location_id: str,
    pheromone_type: Optional[str] = None
) -> List[Dict]:
    """
    Read all pheromones at a location.

    Args:
        location_type: Type of location to query
        location_id: Specific location identifier
        pheromone_type: Optional filter by type

    Returns:
        List of pheromone dicts with intensity, type, depositor, etc.
    """
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            if pheromone_type:
                cur.execute("""
                    SELECT pheromone_id, pheromone_type, intensity,
                           deposited_by, deposited_at, decay_rate
                    FROM stigmergy_pheromones
                    WHERE location_type = %s AND location_id = %s
                      AND pheromone_type = %s
                      AND intensity > %s
                    ORDER BY intensity DESC
                """, (location_type, location_id, pheromone_type, MIN_INTENSITY_THRESHOLD))
            else:
                cur.execute("""
                    SELECT pheromone_id, pheromone_type, intensity,
                           deposited_by, deposited_at, decay_rate
                    FROM stigmergy_pheromones
                    WHERE location_type = %s AND location_id = %s
                      AND intensity > %s
                    ORDER BY intensity DESC
                """, (location_type, location_id, MIN_INTENSITY_THRESHOLD))

            rows = cur.fetchall()
        conn.close()

        return [
            {
                'pheromone_id': row[0],
                'pheromone_type': row[1],
                'intensity': float(row[2]),
                'deposited_by': row[3],
                'deposited_at': row[4],
                'decay_rate': float(row[5])
            }
            for row in rows
        ]
    except Exception as e:
        print(f"[PHEROMONE] Error reading: {e}")
        return []


def get_total_intensity(location_type: str, location_id: str, pheromone_type: str = None) -> float:
    """Get sum of all pheromone intensities at a location."""
    pheromones = read_pheromones(location_type, location_id, pheromone_type)
    return sum(p['intensity'] for p in pheromones)


def get_agent_pheromone_affinity(agent_id: str, task_type: str) -> float:
    """
    Get agent's affinity for a task type based on their pheromone history.

    Returns:
        0.0 = all failures
        0.5 = neutral (no history or equal success/failure)
        1.0 = all successes
    """
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN pheromone_type = 'task_completed' THEN intensity END), 0) as success,
                    COALESCE(SUM(CASE WHEN pheromone_type = 'task_failed' THEN intensity END), 0) as failure
                FROM stigmergy_pheromones
                WHERE deposited_by = %s
                  AND location_type = 'task_type'
                  AND location_id = %s
            """, (agent_id, task_type))
            row = cur.fetchone()
        conn.close()

        if not row or (row[0] == 0 and row[1] == 0):
            return 0.5  # Neutral - no history

        success = float(row[0])
        failure = float(row[1])
        total = success + failure

        return success / total if total > 0 else 0.5

    except Exception as e:
        print(f"[PHEROMONE] Error getting affinity: {e}")
        return 0.5


def should_explore(agent_id: str, task_type: str) -> bool:
    """
    Decide if agent should explore (try new) or exploit (stick to known).

    Based on SwarmSys exploration/exploitation balance.

    Returns:
        True = explore (try new task types)
        False = exploit (stick to proven paths)
    """
    import random

    affinity = get_agent_pheromone_affinity(agent_id, task_type)
    total_intensity = get_total_intensity('task_type', task_type)

    # Low pheromone intensity = unexplored territory = explore
    if total_intensity < 0.3:
        return True
    # High intensity with good affinity = exploit proven path
    elif total_intensity > 0.7 and affinity > 0.6:
        return False
    # Middle ground = probabilistic based on affinity
    else:
        return random.random() < (1 - affinity)


def calculate_pheromone_boost(task_type: str, agent_id: str) -> float:
    """
    Calculate bid score boost based on pheromone data.

    Returns:
        Boost value to add to base bid score (can be negative for penalties)
    """
    # Read pheromones at this task type
    pheromones = read_pheromones('task_type', task_type)

    # Sum intensities by type
    success_intensity = sum(
        p['intensity'] for p in pheromones
        if p['pheromone_type'] == 'task_completed'
    )
    failure_intensity = sum(
        p['intensity'] for p in pheromones
        if p['pheromone_type'] == 'task_failed'
    )

    # Boost for proven task types (max +0.3)
    pheromone_boost = min(success_intensity * 0.1, 0.3)

    # Penalty for failure-prone tasks (max -0.15)
    failure_penalty = min(failure_intensity * 0.05, 0.15)

    # Agent's personal affinity bonus (max +0.2)
    affinity = get_agent_pheromone_affinity(agent_id, task_type)
    affinity_boost = (affinity - 0.5) * 0.4  # -0.2 to +0.2

    return pheromone_boost - failure_penalty + affinity_boost


def decay_all_pheromones() -> tuple:
    """
    Apply decay to all pheromones. Called hourly by decay daemon.

    Returns:
        (decayed_count, deleted_count)
    """
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # Apply decay: intensity = intensity * (1 - decay_rate)
            cur.execute("""
                UPDATE stigmergy_pheromones
                SET intensity = intensity * (1 - decay_rate)
                WHERE intensity > %s
            """, (MIN_INTENSITY_THRESHOLD,))
            decayed = cur.rowcount

            # Remove pheromones that have decayed below threshold
            cur.execute("""
                DELETE FROM stigmergy_pheromones
                WHERE intensity < %s
            """, (MIN_INTENSITY_THRESHOLD,))
            deleted = cur.rowcount

            conn.commit()
        conn.close()

        return decayed, deleted

    except Exception as e:
        print(f"[PHEROMONE] Error decaying: {e}")
        return 0, 0


def get_pheromone_stats() -> Dict:
    """Get summary statistics of pheromone system."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total_pheromones,
                    COUNT(DISTINCT deposited_by) as unique_agents,
                    COUNT(DISTINCT location_id) as unique_locations,
                    SUM(intensity) as total_intensity,
                    AVG(intensity) as avg_intensity,
                    SUM(CASE WHEN pheromone_type = 'task_completed' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN pheromone_type = 'task_failed' THEN 1 ELSE 0 END) as failure_count
                FROM stigmergy_pheromones
                WHERE intensity > %s
            """, (MIN_INTENSITY_THRESHOLD,))
            row = cur.fetchone()
        conn.close()

        return {
            'total_pheromones': row[0] or 0,
            'unique_agents': row[1] or 0,
            'unique_locations': row[2] or 0,
            'total_intensity': float(row[3]) if row[3] else 0,
            'avg_intensity': float(row[4]) if row[4] else 0,
            'success_count': row[5] or 0,
            'failure_count': row[6] or 0
        }
    except Exception as e:
        print(f"[PHEROMONE] Error getting stats: {e}")
        return {}


# Convenience function for task execution integration
def on_task_complete(task_id: str, task_type: str, success: bool, agent_id: str):
    """
    Deposit pheromones after task completion.
    Call this from jr_task_executor after each task.

    Args:
        task_id: The task identifier
        task_type: Type of task (implementation, research, etc.)
        success: Whether task succeeded
        agent_id: Which agent completed the task
    """
    pheromone_type = 'task_completed' if success else 'task_failed'
    intensity = 1.0 if success else 0.2

    # Deposit at task_type location (for future similar tasks)
    deposit_pheromone(
        location_type='task_type',
        location_id=task_type,
        pheromone_type=pheromone_type,
        intensity=intensity,
        agent_id=agent_id
    )

    # Also deposit at specific task (for debugging/tracking)
    deposit_pheromone(
        location_type='task',
        location_id=task_id,
        pheromone_type=pheromone_type,
        intensity=intensity,
        agent_id=agent_id
    )

    print(f"[PHEROMONE] {agent_id} deposited {pheromone_type} ({intensity}) at {task_type}")


if __name__ == '__main__':
    # Test the library
    print("Testing smadrl_pheromones.py...")

    # Test deposit
    success = deposit_pheromone(
        location_type='task_type',
        location_id='test_implementation',
        pheromone_type='task_completed',
        intensity=1.0,
        agent_id='test-agent'
    )
    print(f"Deposit test: {'PASS' if success else 'FAIL'}")

    # Test read
    pheromones = read_pheromones('task_type', 'test_implementation')
    print(f"Read test: Found {len(pheromones)} pheromones")

    # Test affinity
    affinity = get_agent_pheromone_affinity('test-agent', 'test_implementation')
    print(f"Affinity test: {affinity}")

    # Test stats
    stats = get_pheromone_stats()
    print(f"Stats: {stats}")

    print("Tests complete!")
