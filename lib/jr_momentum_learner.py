#!/usr/bin/env python3
"""
Jr Momentum Learner
Based on M-GRPO: Momentum-Anchored Policy Optimization
Cherokee AI Federation - For Seven Generations

Prevents policy collapse in self-improving Jr agents by:
1. Maintaining EMA teacher model
2. Hybrid voting between student/teacher
3. IQR filtering of low-entropy solutions

Phase 5 of Learning Infrastructure
Created: January 17, 2026
"""

import copy
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# MAGRPO multi-agent cooperation (Phase 2)
try:
    from magrpo_tracker import get_magrpo_tracker, MAGRPOGroupTracker
    HAS_MAGRPO = True
except ImportError:
    HAS_MAGRPO = False
    logger.warning("MAGRPO tracker not available, using individual learning only")

# Database config - loaded from secrets
from lib.secrets_loader import get_db_config
DB_CONFIG = get_db_config()

# Try to import psycopg2
try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    logger.warning("psycopg2 not available, database persistence disabled")


class MomentumJrLearner:
    """Apply M-GRPO principles to Jr self-improvement."""

    def __init__(self, jr_type: str, momentum_decay: float = 0.999,
                 group_tracker: Optional['MAGRPOGroupTracker'] = None):
        """
        Initialize momentum learner.

        Args:
            jr_type: Type of Jr (e.g., 'it_triad_jr')
            momentum_decay: EMA decay rate (0.999 = slow teacher, 0.9 = faster)
            group_tracker: Optional MAGRPO tracker for multi-agent learning
        """
        self.jr_type = jr_type
        self.momentum_decay = momentum_decay
        self.student_state = self._init_state()
        self.teacher_state = None  # Initialized on first update
        self.learning_history = []

        # MAGRPO integration
        self.group_tracker = group_tracker
        if self.group_tracker is None and HAS_MAGRPO:
            try:
                self.group_tracker = get_magrpo_tracker()
                logger.info(f"[M-GRPO] Using shared MAGRPO tracker for {jr_type}")
            except Exception as e:
                logger.warning(f"[M-GRPO] Could not get MAGRPO tracker: {e}")

        # Try to load existing state
        self.load_state()

    def _init_state(self) -> Dict[str, Any]:
        """Initialize learner state."""
        return {
            'approach_weights': {
                'direct_code': 0.5,
                'search_first': 0.5,
                'read_docs': 0.5,
                'ask_council': 0.5,
                'use_rlm': 0.5  # Phase 4 - recursive decomposition
            },
            'task_type_preferences': {},
            'success_patterns': [],
            'failure_patterns': [],
            'last_updated': datetime.now().isoformat()
        }

    def update_teacher(self):
        """Update momentum teacher with EMA of student."""
        if self.teacher_state is None:
            self.teacher_state = copy.deepcopy(self.student_state)
            return

        # EMA update: teacher = decay * teacher + (1-decay) * student
        for key in self.student_state['approach_weights']:
            old = self.teacher_state['approach_weights'].get(key, 0.5)
            new = self.student_state['approach_weights'].get(key, 0.5)
            self.teacher_state['approach_weights'][key] = (
                self.momentum_decay * old + (1 - self.momentum_decay) * new
            )

        self.teacher_state['last_updated'] = datetime.now().isoformat()

    def score_approach(self, approach: str, use_teacher: bool = False) -> float:
        """Score an approach based on learned weights."""
        state = self.teacher_state if use_teacher else self.student_state
        if state is None:
            return 0.5
        return state['approach_weights'].get(approach, 0.5)

    def vote_on_approach(self, task: dict, approaches: List[str]) -> str:
        """
        Combined voting from student and teacher.

        Returns best approach using hybrid scoring.
        """
        results = []

        for approach in approaches:
            student_score = self.score_approach(approach, use_teacher=False)
            teacher_score = self.score_approach(approach, use_teacher=True)

            # Teacher has 40% weight to anchor student (prevent runaway)
            combined = 0.6 * student_score + 0.4 * teacher_score
            results.append((approach, combined))

        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        return results[0][0]

    def compute_solution_entropy(self, solution: dict) -> float:
        """
        Compute entropy of a solution approach.

        High entropy = exploratory, diverse
        Low entropy = overconfident, narrow
        """
        # Simplified entropy based on approach diversity
        approaches_used = solution.get('approaches_considered', [])
        if not approaches_used:
            return 0.0

        # More approaches considered = higher entropy
        base_entropy = min(len(approaches_used) / 4.0, 1.0)

        # Uniform distribution of consideration = higher entropy
        weights = solution.get('approach_weights', [1.0] * len(approaches_used))
        if len(weights) > 1:
            weights = np.array(weights) / sum(weights)
            dist_entropy = -np.sum(weights * np.log(weights + 1e-10))
            normalized = dist_entropy / np.log(len(weights))
        else:
            normalized = 0.0

        return (base_entropy + normalized) / 2.0

    def filter_low_entropy_solutions(self, solutions: List[dict]) -> List[dict]:
        """
        IQR pruning of overconfident solutions.

        Removes solutions with statistically low entropy.
        """
        if len(solutions) < 4:
            return solutions

        entropies = [self.compute_solution_entropy(s) for s in solutions]

        q1 = np.percentile(entropies, 25)
        q3 = np.percentile(entropies, 75)
        iqr = q3 - q1
        threshold = q1 - 1.5 * iqr

        return [s for s, e in zip(solutions, entropies) if e > threshold]

    def get_learning_report(self) -> dict:
        """Generate learning progress report including MAGRPO metrics."""
        if not self.learning_history:
            return {'status': 'no_data', 'jr_type': self.jr_type}

        successes = sum(1 for h in self.learning_history if h['success'])
        total = len(self.learning_history)

        report = {
            'jr_type': self.jr_type,
            'total_outcomes': total,
            'success_rate': round(successes / total, 3) if total > 0 else 0,
            'student_weights': self.student_state['approach_weights'],
            'teacher_weights': self.teacher_state['approach_weights'] if self.teacher_state else None,
            'momentum_decay': self.momentum_decay,
            'magrpo_enabled': self.group_tracker is not None
        }

        # Add MAGRPO cooperation stats if available
        if self.group_tracker:
            try:
                coop_stats = self.group_tracker.get_jr_cooperation_stats(self.jr_type)
                report['cooperation'] = {
                    'tasks_participated': coop_stats.get('tasks_participated', 0),
                    'handoffs_sent': coop_stats.get('handoffs_sent', 0),
                    'handoffs_received': coop_stats.get('handoffs_received', 0),
                    'avg_context_preservation': round(
                        coop_stats.get('avg_context_preservation', 0), 3
                    )
                }
            except Exception as e:
                report['cooperation'] = {'error': str(e)}

        return report

    def record_outcome(self, task: dict, approach: str, success: bool):
        """Record task outcome for learning."""
        outcome = {
            'task_type': task.get('type', task.get('task_type', 'unknown')),
            'approach': approach,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        self.learning_history.append(outcome)

        # Update student weights
        current = self.student_state['approach_weights'].get(approach, 0.5)
        delta = 0.05 if success else -0.05
        new_weight = max(0.1, min(0.9, current + delta))
        self.student_state['approach_weights'][approach] = new_weight

        # Update teacher (slow EMA)
        self.update_teacher()

        # Persist state periodically
        if len(self.learning_history) % 5 == 0:
            self.save_state()

    def record_group_outcome(self, task_id: str, task: dict, approach: str,
                              success: bool, context_preserved: float = 0.0):
        """
        Record task outcome with MAGRPO group learning.

        This extends record_outcome to:
        1. Register participation with group tracker
        2. Incorporate group rewards into learning
        3. Track cooperation quality

        Args:
            task_id: Unique task identifier
            task: Task details
            approach: Approach used
            success: Whether task succeeded
            context_preserved: Quality of context handoff (0-1)
        """
        # First, do individual learning
        self.record_outcome(task, approach, success)

        if not self.group_tracker:
            return

        try:
            # Register our participation
            self.group_tracker.register_participation(task_id, self.jr_type)

            # Get group rewards
            group_rewards = self.group_tracker.compute_group_reward(task_id, success)
            my_group_reward = group_rewards.get(self.jr_type, 0.0)

            # Apply group reward as additional learning signal
            if my_group_reward != 0:
                self._apply_group_reward(approach, my_group_reward)
                logger.info(f"[M-GRPO] Applied group reward {my_group_reward:.3f} "
                           f"to {self.jr_type} for approach '{approach}'")

        except Exception as e:
            logger.error(f"[M-GRPO] Failed to record group outcome: {e}")

    def _apply_group_reward(self, approach: str, reward: float):
        """
        Apply group reward to approach weights.

        Group rewards modify weights more gently than individual outcomes
        to encourage cooperation without destabilizing individual learning.
        """
        current = self.student_state['approach_weights'].get(approach, 0.5)

        # Group reward has 50% impact of individual (stability)
        delta = reward * 0.025  # Max ±0.025 per group outcome
        new_weight = max(0.1, min(0.9, current + delta))

        self.student_state['approach_weights'][approach] = new_weight

        # Update teacher with new student weights
        self.update_teacher()

    def record_handoff(self, task_id: str, to_jr: str, context_preserved: float):
        """
        Record handing off a task to another Jr.

        Args:
            task_id: Task being handed off
            to_jr: Jr type receiving the task
            context_preserved: Quality of context transfer (0-1)
        """
        if not self.group_tracker:
            logger.warning("[M-GRPO] Cannot record handoff - no group tracker")
            return

        try:
            self.group_tracker.record_handoff(
                from_jr=self.jr_type,
                to_jr=to_jr,
                task_id=task_id,
                context_preserved=context_preserved
            )
            logger.info(f"[M-GRPO] Recorded handoff: {self.jr_type} -> {to_jr} "
                       f"(context: {context_preserved:.2f})")
        except Exception as e:
            logger.error(f"[M-GRPO] Failed to record handoff: {e}")

    def get_learning_report(self) -> dict:
        """Generate learning progress report including MAGRPO metrics."""
        if not self.learning_history:
            return {'status': 'no_data', 'jr_type': self.jr_type}

        successes = sum(1 for h in self.learning_history if h['success'])
        total = len(self.learning_history)

        report = {
            'jr_type': self.jr_type,
            'total_outcomes': total,
            'success_rate': round(successes / total, 3) if total > 0 else 0,
            'student_weights': self.student_state['approach_weights'],
            'teacher_weights': self.teacher_state['approach_weights'] if self.teacher_state else None,
            'momentum_decay': self.momentum_decay,
            'magrpo_enabled': self.group_tracker is not None
        }

        # Add MAGRPO cooperation stats if available
        if self.group_tracker:
            try:
                coop_stats = self.group_tracker.get_jr_cooperation_stats(self.jr_type)
                report['cooperation'] = {
                    'tasks_participated': coop_stats.get('tasks_participated', 0),
                    'handoffs_sent': coop_stats.get('handoffs_sent', 0),
                    'handoffs_received': coop_stats.get('handoffs_received', 0),
                    'avg_context_preservation': round(
                        coop_stats.get('avg_context_preservation', 0), 3
                    )
                }
            except Exception as e:
                report['cooperation'] = {'error': str(e)}

        return report

    def save_state(self):
        """Persist learner state to database."""
        if not HAS_PSYCOPG2:
            return False

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            state_json = json.dumps({
                'student': self.student_state,
                'teacher': self.teacher_state,
                'history_count': len(self.learning_history)
            })

            cur.execute("""
                INSERT INTO jr_learning_state (jr_type, state_json, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (jr_type) DO UPDATE SET
                    state_json = EXCLUDED.state_json,
                    updated_at = NOW()
            """, (self.jr_type, state_json))

            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    def load_state(self) -> bool:
        """Load learner state from database."""
        if not HAS_PSYCOPG2:
            return False

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            cur.execute("""
                SELECT state_json FROM jr_learning_state
                WHERE jr_type = %s
            """, (self.jr_type,))

            row = cur.fetchone()
            cur.close()
            conn.close()

            if row:
                state = json.loads(row[0])
                self.student_state = state.get('student', self._init_state())
                self.teacher_state = state.get('teacher')
                logger.info(f"[M-GRPO] Loaded state for {self.jr_type}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Could not load state: {e}")
            return False


# Convenience function
def get_momentum_learner(jr_type: str = "it_triad_jr",
                         use_magrpo: bool = True) -> MomentumJrLearner:
    """
    Get momentum learner instance.

    Args:
        jr_type: Jr type identifier
        use_magrpo: Whether to enable MAGRPO group learning
    """
    group_tracker = None
    if use_magrpo and HAS_MAGRPO:
        try:
            group_tracker = get_magrpo_tracker()
        except Exception:
            pass
    return MomentumJrLearner(jr_type, group_tracker=group_tracker)


if __name__ == '__main__':
    # Test the momentum learner with MAGRPO
    print("=" * 60)
    print("M-GRPO + MAGRPO Momentum Learner - Test Suite")
    print("=" * 60)

    # Create learners for two Jrs
    learner1 = get_momentum_learner('Software Engineer Jr.', use_magrpo=True)
    learner2 = get_momentum_learner('Research Jr.', use_magrpo=True)

    print(f"\nMAGRPO enabled: {learner1.group_tracker is not None}")

    approaches = ['direct_code', 'search_first', 'read_docs', 'ask_council', 'use_rlm']
    task_id = f"test-magrpo-{datetime.now().strftime('%H%M%S')}"

    # Simulate collaborative task
    print(f"\nSimulating collaborative task: {task_id}")

    # Jr1 starts task
    task = {'type': 'code_implementation', 'task_id': task_id}
    chosen1 = learner1.vote_on_approach(task, approaches)
    print(f"  SE Jr. chose: {chosen1}")

    # Jr1 hands off to Jr2
    learner1.record_handoff(task_id, 'Research Jr.', context_preserved=0.85)

    # Jr2 continues
    chosen2 = learner2.vote_on_approach(task, approaches)
    print(f"  Research Jr. chose: {chosen2}")

    # Task succeeds
    learner1.record_group_outcome(task_id, task, chosen1, success=True, context_preserved=0.85)
    learner2.record_group_outcome(task_id, task, chosen2, success=True)

    print("\nLearning Reports:")
    print("\nSoftware Engineer Jr.:")
    print(json.dumps(learner1.get_learning_report(), indent=2))

    print("\nResearch Jr.:")
    print(json.dumps(learner2.get_learning_report(), indent=2))
