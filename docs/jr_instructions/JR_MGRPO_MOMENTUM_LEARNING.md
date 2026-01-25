# Jr Instructions: M-GRPO Momentum Learning for Jr Self-Improvement

**Priority**: 2
**Assigned Jr**: it_triad_jr
**Source**: M-GRPO Paper (Dec 15, 2025)
**Ultrathink**: ULTRATHINK-MGRPO-DEC20-2025.md

---

## OBJECTIVE

Implement momentum-anchored learning for Jr self-improvement, preventing policy collapse when Jrs learn from their own execution history. Based on M-GRPO principles.

---

### Task 1: Create Momentum Learner

Create `/ganuda/lib/jr_momentum_learner.py`:

```python
#!/usr/bin/env python3
"""
Jr Momentum Learner
Based on M-GRPO: Momentum-Anchored Policy Optimization
Cherokee AI Federation - For Seven Generations

Prevents policy collapse in self-improving Jr agents by:
1. Maintaining EMA teacher model
2. Hybrid voting between student/teacher
3. IQR filtering of low-entropy solutions
"""

import copy
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
import psycopg2

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}


class MomentumJrLearner:
    """Apply M-GRPO principles to Jr self-improvement."""

    def __init__(self, jr_type: str, momentum_decay: float = 0.999):
        """
        Initialize momentum learner.

        Args:
            jr_type: Type of Jr (e.g., 'it_triad_jr')
            momentum_decay: EMA decay rate (0.999 = slow teacher, 0.9 = faster)
        """
        self.jr_type = jr_type
        self.momentum_decay = momentum_decay
        self.student_state = self._init_state()
        self.teacher_state = None  # Initialized on first update
        self.learning_history = []

    def _init_state(self) -> Dict[str, Any]:
        """Initialize learner state."""
        return {
            'approach_weights': {
                'direct_code': 0.5,
                'search_first': 0.5,
                'read_docs': 0.5,
                'ask_council': 0.5
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

    def record_outcome(self, task: dict, approach: str, success: bool):
        """Record task outcome for learning."""
        outcome = {
            'task_type': task.get('type', 'unknown'),
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

    def get_learning_report(self) -> dict:
        """Generate learning progress report."""
        if not self.learning_history:
            return {'status': 'no_data'}

        successes = sum(1 for h in self.learning_history if h['success'])
        total = len(self.learning_history)

        return {
            'jr_type': self.jr_type,
            'total_outcomes': total,
            'success_rate': round(successes / total, 3) if total > 0 else 0,
            'student_weights': self.student_state['approach_weights'],
            'teacher_weights': self.teacher_state['approach_weights'] if self.teacher_state else None,
            'momentum_decay': self.momentum_decay
        }

    def save_state(self):
        """Persist learner state to database."""
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

    def load_state(self) -> bool:
        """Load learner state from database."""
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
            return True
        return False


if __name__ == '__main__':
    # Test the momentum learner
    learner = MomentumJrLearner('it_triad_jr')

    # Simulate learning
    approaches = ['direct_code', 'search_first', 'read_docs', 'ask_council']

    # Simulate some outcomes
    for i in range(10):
        task = {'type': 'code_fix'}
        chosen = learner.vote_on_approach(task, approaches)
        success = np.random.random() > 0.3 if chosen == 'search_first' else np.random.random() > 0.6
        learner.record_outcome(task, chosen, success)

    print(json.dumps(learner.get_learning_report(), indent=2))
```

---

### Task 2: Create Database Schema

Create `/ganuda/sql/jr_learning_state.sql`:

```sql
-- Jr Learning State Schema
-- For M-GRPO momentum learning

CREATE TABLE IF NOT EXISTS jr_learning_state (
    id SERIAL PRIMARY KEY,
    jr_type VARCHAR(64) UNIQUE NOT NULL,
    state_json JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jr_learning_type ON jr_learning_state(jr_type);
```

---

### Task 3: Create Integration Test

Create `/ganuda/tests/test_momentum_learner.py`:

```python
#!/usr/bin/env python3
"""Test M-GRPO Momentum Learner."""

import sys
sys.path.insert(0, '/ganuda/lib')

from jr_momentum_learner import MomentumJrLearner
import numpy as np

def test_ema_update():
    """Test that teacher updates slower than student."""
    learner = MomentumJrLearner('test_jr', momentum_decay=0.9)

    # Initial weights should be 0.5
    assert learner.student_state['approach_weights']['direct_code'] == 0.5

    # Record a success - student should update quickly
    learner.record_outcome({'type': 'test'}, 'direct_code', True)

    student_weight = learner.student_state['approach_weights']['direct_code']
    teacher_weight = learner.teacher_state['approach_weights']['direct_code']

    # Student should move faster (0.55 vs closer to 0.5)
    assert student_weight > teacher_weight
    print(f"Student: {student_weight}, Teacher: {teacher_weight}")


def test_entropy_filtering():
    """Test IQR entropy filtering."""
    learner = MomentumJrLearner('test_jr')

    solutions = [
        {'approaches_considered': ['a', 'b', 'c', 'd']},  # High entropy
        {'approaches_considered': ['a']},  # Low entropy
        {'approaches_considered': ['a', 'b']},  # Medium
        {'approaches_considered': ['a', 'b', 'c']},  # Medium-high
        {'approaches_considered': []},  # Zero entropy
    ]

    filtered = learner.filter_low_entropy_solutions(solutions)
    print(f"Filtered {len(solutions)} -> {len(filtered)} solutions")

    # Low/zero entropy should be removed
    assert len(filtered) < len(solutions)


def test_hybrid_voting():
    """Test student-teacher hybrid voting."""
    learner = MomentumJrLearner('test_jr')

    # Train student to prefer search_first
    for _ in range(5):
        learner.record_outcome({}, 'search_first', True)
        learner.record_outcome({}, 'direct_code', False)

    # Student should now prefer search_first
    # But teacher (EMA) should be more conservative
    approaches = ['direct_code', 'search_first']
    chosen = learner.vote_on_approach({}, approaches)

    print(f"Report: {learner.get_learning_report()}")
    print(f"Chosen approach: {chosen}")


if __name__ == '__main__':
    print("Testing EMA update...")
    test_ema_update()
    print()

    print("Testing entropy filtering...")
    test_entropy_filtering()
    print()

    print("Testing hybrid voting...")
    test_hybrid_voting()
    print()

    print("All tests passed!")
```

---

## SUCCESS CRITERIA

1. jr_momentum_learner.py created with MomentumJrLearner class
2. EMA teacher updates correctly (slower than student)
3. IQR filtering removes low-entropy solutions
4. Hybrid voting balances student exploration with teacher stability
5. State can be persisted and loaded from database
6. Tests pass

---

*For Seven Generations - Cherokee AI Federation*
