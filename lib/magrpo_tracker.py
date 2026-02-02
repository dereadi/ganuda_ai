#!/usr/bin/env python3
"""
MAGRPO Group Task Tracker
Multi-Agent Group Relative Policy Optimization for Jr Cooperation

Cherokee AI Federation - For Seven Generations
Based on arXiv 2508.04652

Tracks:
- Which Jrs participate in each task
- Handoff quality between Jrs
- Group reward distribution

Created: January 27, 2026
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

# Database config
DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_DB = True
except ImportError:
    HAS_DB = False
    logger.warning("psycopg2 not available, using in-memory tracking only")


class MAGRPOGroupTracker:
    """
    Track group task outcomes for MAGRPO optimization.

    Responsibilities:
    1. Register Jr participation in tasks
    2. Record handoffs between Jrs
    3. Compute group rewards based on task success
    4. Persist metrics to database
    """

    def __init__(self, persist_to_db: bool = True):
        """
        Initialize group tracker.

        Args:
            persist_to_db: Whether to persist to PostgreSQL
        """
        self.persist_to_db = persist_to_db and HAS_DB
        self.group_tasks: Dict[str, List[Dict]] = defaultdict(list)
        self.handoff_log: List[Dict] = []

        # Reward configuration
        self.base_success_reward = 1.0
        self.base_failure_penalty = -0.3
        self.handoff_bonus_multiplier = 0.2
        self.context_preservation_weight = 0.5

        logger.info(f"[MAGRPO] GroupTracker initialized, persist={self.persist_to_db}")

    def _get_db_connection(self):
        """Get database connection."""
        if not HAS_DB:
            return None
        return psycopg2.connect(**DB_CONFIG)

    def register_participation(self, task_id: str, jr_type: str,
                                handoff_from: Optional[str] = None) -> bool:
        """
        Register Jr participation in a task.

        Args:
            task_id: Unique task identifier
            jr_type: Type of Jr (e.g., 'Software Engineer Jr.')
            handoff_from: Jr type that handed off the task (if any)

        Returns:
            True if registered successfully
        """
        participation = {
            'jr_type': jr_type,
            'joined_at': datetime.now(),
            'handoff_from': handoff_from,
            'contribution_score': None  # Set when task completes
        }

        self.group_tasks[task_id].append(participation)

        logger.info(f"[MAGRPO] Registered {jr_type} for task {task_id[:8]}... "
                   f"(handoff_from={handoff_from})")

        # Persist to database
        if self.persist_to_db:
            self._persist_participation(task_id, participation)

        return True

    def record_handoff(self, from_jr: str, to_jr: str, task_id: str,
                       context_preserved: float = 0.0) -> bool:
        """
        Record task handoff between Jrs.

        Args:
            from_jr: Jr type handing off
            to_jr: Jr type receiving
            task_id: Task being handed off
            context_preserved: Score 0-1 indicating context quality

        Returns:
            True if recorded successfully
        """
        handoff = {
            'from_jr': from_jr,
            'to_jr': to_jr,
            'task_id': task_id,
            'context_preserved': min(max(context_preserved, 0.0), 1.0),
            'timestamp': datetime.now()
        }

        self.handoff_log.append(handoff)

        logger.info(f"[MAGRPO] Handoff: {from_jr} -> {to_jr} for task {task_id[:8]}... "
                   f"(context={context_preserved:.2f})")

        # Persist to database
        if self.persist_to_db:
            self._persist_handoff(handoff)

        return True

    def compute_group_reward(self, task_id: str, task_success: bool) -> Dict[str, float]:
        """
        Compute reward for each Jr based on group outcome.

        MAGRPO Reward Formula:
        - Base reward distributed among participants
        - Bonus for successful handoffs (context preservation)
        - No reward for non-participants

        Args:
            task_id: Task that completed
            task_success: Whether task succeeded

        Returns:
            Dict mapping jr_type -> reward
        """
        participants = self.group_tasks.get(task_id, [])

        if not participants:
            logger.warning(f"[MAGRPO] No participants found for task {task_id[:8]}")
            return {}

        # Base reward (positive for success, negative for failure)
        base_reward = self.base_success_reward if task_success else self.base_failure_penalty

        rewards: Dict[str, float] = {}
        num_participants = len(participants)

        for p in participants:
            jr_type = p['jr_type']

            # Equal share of base reward
            individual_share = base_reward / num_participants

            # Handoff bonus - reward for good context preservation
            handoff_bonus = self._compute_handoff_bonus(jr_type, task_id)

            # Total reward
            total_reward = individual_share + handoff_bonus

            # Accumulate if Jr participated multiple times
            if jr_type in rewards:
                rewards[jr_type] += total_reward
            else:
                rewards[jr_type] = total_reward

        logger.info(f"[MAGRPO] Group rewards for task {task_id[:8]}: "
                   f"success={task_success}, rewards={rewards}")

        # Persist metrics
        if self.persist_to_db:
            self._persist_rewards(task_id, task_success, rewards)

        return rewards

    def _compute_handoff_bonus(self, jr_type: str, task_id: str) -> float:
        """
        Compute handoff bonus for a Jr's participation.

        Rewards:
        - Jrs who sent good context to others
        - Jrs who received and utilized context well
        """
        bonus = 0.0

        # Find handoffs involving this Jr for this task
        relevant_handoffs = [
            h for h in self.handoff_log
            if h['task_id'] == task_id and (h['from_jr'] == jr_type or h['to_jr'] == jr_type)
        ]

        for handoff in relevant_handoffs:
            context_score = handoff['context_preserved']

            if handoff['from_jr'] == jr_type:
                # Jr sent context - reward for good handoff
                bonus += context_score * self.handoff_bonus_multiplier

            if handoff['to_jr'] == jr_type:
                # Jr received context - partial reward for utilizing it
                bonus += context_score * self.handoff_bonus_multiplier * 0.5

        return bonus

    def get_jr_cooperation_stats(self, jr_type: str,
                                  since: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get cooperation statistics for a Jr.

        Args:
            jr_type: Jr type to query
            since: Only include data after this timestamp

        Returns:
            Dict with cooperation metrics
        """
        # Filter by time if specified
        if since:
            handoffs = [h for h in self.handoff_log if h['timestamp'] >= since]
            tasks = {
                tid: [p for p in parts if p['joined_at'] >= since]
                for tid, parts in self.group_tasks.items()
            }
        else:
            handoffs = self.handoff_log
            tasks = self.group_tasks

        # Count metrics
        tasks_participated = sum(
            1 for parts in tasks.values()
            if any(p['jr_type'] == jr_type for p in parts)
        )

        handoffs_sent = sum(1 for h in handoffs if h['from_jr'] == jr_type)
        handoffs_received = sum(1 for h in handoffs if h['to_jr'] == jr_type)

        # Average context preservation
        relevant_handoffs = [h for h in handoffs if h['from_jr'] == jr_type]
        avg_context = (
            sum(h['context_preserved'] for h in relevant_handoffs) / len(relevant_handoffs)
            if relevant_handoffs else 0.0
        )

        return {
            'jr_type': jr_type,
            'tasks_participated': tasks_participated,
            'handoffs_sent': handoffs_sent,
            'handoffs_received': handoffs_received,
            'avg_context_preservation': avg_context,
            'period_start': since,
            'period_end': datetime.now()
        }

    def _persist_participation(self, task_id: str, participation: Dict):
        """Persist participation to database."""
        try:
            conn = self._get_db_connection()
            if not conn:
                return

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO magrpo_task_participation
                    (task_id, jr_type, joined_at, handoff_from)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (task_id, jr_type, joined_at) DO NOTHING
                """, (
                    task_id,
                    participation['jr_type'],
                    participation['joined_at'],
                    participation.get('handoff_from')
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[MAGRPO] Failed to persist participation: {e}")
        finally:
            if conn:
                conn.close()

    def _persist_handoff(self, handoff: Dict):
        """Persist handoff to database."""
        try:
            conn = self._get_db_connection()
            if not conn:
                return

            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE magrpo_task_participation
                    SET handoff_to = %s, context_preserved_score = %s
                    WHERE task_id = %s AND jr_type = %s
                    AND handoff_to IS NULL
                """, (
                    handoff['to_jr'],
                    handoff['context_preserved'],
                    handoff['task_id'],
                    handoff['from_jr']
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[MAGRPO] Failed to persist handoff: {e}")
        finally:
            if conn:
                conn.close()

    def _persist_rewards(self, task_id: str, success: bool, rewards: Dict[str, float]):
        """Persist reward computation to database."""
        try:
            conn = self._get_db_connection()
            if not conn:
                return

            with conn.cursor() as cur:
                for jr_type, reward in rewards.items():
                    cur.execute("""
                        UPDATE magrpo_task_participation
                        SET contribution_score = %s
                        WHERE task_id = %s AND jr_type = %s
                    """, (reward, task_id, jr_type))
                conn.commit()
        except Exception as e:
            logger.error(f"[MAGRPO] Failed to persist rewards: {e}")
        finally:
            if conn:
                conn.close()


# Singleton instance for global access
_tracker_instance: Optional[MAGRPOGroupTracker] = None


def get_magrpo_tracker() -> MAGRPOGroupTracker:
    """Get or create the global MAGRPO tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = MAGRPOGroupTracker()
    return _tracker_instance


if __name__ == '__main__':
    # Test the tracker
    import sys

    tracker = MAGRPOGroupTracker(persist_to_db=False)

    # Simulate multi-Jr task
    task_id = "test-task-001"

    # SE Jr starts the task
    tracker.register_participation(task_id, "Software Engineer Jr.")

    # SE Jr hands off to Research Jr.
    tracker.record_handoff("Software Engineer Jr.", "Research Jr.", task_id,
                          context_preserved=0.85)
    tracker.register_participation(task_id, "Research Jr.",
                                  handoff_from="Software Engineer Jr.")

    # Task completes successfully
    rewards = tracker.compute_group_reward(task_id, task_success=True)

    print(f"Rewards: {json.dumps(rewards, indent=2)}")

    # Get stats
    stats = tracker.get_jr_cooperation_stats("Software Engineer Jr.")
    print(f"Stats: {json.dumps(stats, indent=2, default=str)}")
