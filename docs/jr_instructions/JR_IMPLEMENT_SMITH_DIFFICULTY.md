# Jr Task: Implement SMITH Difficulty Re-Estimation

**Task ID:** task-impl-smith-001
**Priority:** P2 (Infrastructure Enhancement)
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation
**Based On:** task-smith-difficulty-001_impl_plan.md

---

## Overview

Implement SMITH Difficulty Re-Estimation for the Jr Task Bidding system. This enhances bid scoring by dynamically adjusting task difficulty based on historical completion data.

---

## Implementation Tasks

### Task 1: Create jr_task_completions Table

```sql
CREATE TABLE jr_task_completions (
    completion_id SERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    agent_id VARCHAR(64) NOT NULL,
    node_name VARCHAR(32),
    task_type VARCHAR(32),
    started_at TIMESTAMP,
    completed_at TIMESTAMP DEFAULT NOW(),
    success BOOLEAN NOT NULL,
    execution_time_seconds INTEGER,
    estimated_difficulty FLOAT DEFAULT 0.5,
    actual_difficulty FLOAT,
    error_message TEXT
);

CREATE INDEX idx_completions_task ON jr_task_completions(task_id);
CREATE INDEX idx_completions_agent ON jr_task_completions(agent_id);
CREATE INDEX idx_completions_type ON jr_task_completions(task_type);
```

### Task 2: Implement Difficulty Estimation Functions

**File:** `/ganuda/lib/smith_difficulty.py`

```python
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Tuple

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# SMITH algorithm parameters
LEARNING_RATE = 0.15
DECAY_FACTOR = 0.95
MIN_SAMPLES = 3

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def estimate_task_difficulty(task_type: str, task_content: str) -> Tuple[float, Dict]:
    """
    Estimate difficulty using SMITH algorithm.

    Returns (difficulty_score, metadata)
    difficulty_score: 0.0 (easy) to 1.0 (hard)
    """
    conn = get_connection()

    # Get historical completion data for this task type
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                AVG(CASE WHEN success THEN 0.0 ELSE 1.0 END) as failure_rate,
                AVG(execution_time_seconds) as avg_time,
                STDDEV(execution_time_seconds) as time_variance,
                COUNT(*) as sample_count
            FROM jr_task_completions
            WHERE task_type = %s
            AND completed_at > NOW() - INTERVAL '7 days'
        """, (task_type,))

        result = cur.fetchone()
        failure_rate = result[0] or 0.5
        avg_time = result[1] or 300
        time_variance = result[2] or 100
        sample_count = result[3] or 0

    conn.close()

    # SMITH difficulty calculation
    # Base difficulty from failure rate
    base_difficulty = failure_rate

    # Adjust for execution time (longer = harder)
    # Normalize: 60s = 0.2, 300s = 0.5, 600s+ = 0.8
    time_factor = min(1.0, (avg_time or 300) / 600)

    # Adjust for variance (higher variance = harder to estimate)
    variance_factor = min(0.3, (time_variance or 0) / 1000)

    # Content length as complexity proxy
    content_factor = min(0.3, len(task_content) / 5000)

    # Combine factors
    difficulty = (
        0.4 * base_difficulty +
        0.3 * time_factor +
        0.15 * variance_factor +
        0.15 * content_factor
    )

    # Apply confidence based on sample count
    if sample_count < MIN_SAMPLES:
        # Low confidence: regress toward 0.5
        confidence = sample_count / MIN_SAMPLES
        difficulty = difficulty * confidence + 0.5 * (1 - confidence)

    return round(difficulty, 3), {
        'failure_rate': failure_rate,
        'avg_time': avg_time,
        'time_variance': time_variance,
        'sample_count': sample_count,
        'confidence': min(1.0, sample_count / MIN_SAMPLES)
    }


def update_difficulty_model(task_id: str, agent_id: str,
                            success: bool, execution_time: int,
                            estimated_diff: float):
    """
    Update difficulty model after task completion.
    Uses Bayesian updating per SMITH algorithm.
    """
    # Calculate actual difficulty from outcome
    if success:
        actual_diff = max(0.1, estimated_diff - 0.1)  # Slightly easier than estimated
    else:
        actual_diff = min(0.9, estimated_diff + 0.2)  # Harder than estimated

    # Adjust for execution time
    if execution_time > 600:  # Over 10 minutes
        actual_diff = min(0.9, actual_diff + 0.1)
    elif execution_time < 60:  # Under 1 minute
        actual_diff = max(0.1, actual_diff - 0.1)

    conn = get_connection()
    with conn.cursor() as cur:
        # Log completion
        cur.execute("""
            INSERT INTO jr_task_completions
            (task_id, agent_id, success, execution_time_seconds,
             estimated_difficulty, actual_difficulty)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (task_id, agent_id, success, execution_time,
              estimated_diff, actual_diff))
        conn.commit()
    conn.close()

    return actual_diff
```

### Task 3: Enhance Bid Scoring with Difficulty

Update `jr_bidding_daemon.py` to use difficulty-adjusted scoring:

```python
from lib.smith_difficulty import estimate_task_difficulty

def calculate_bid(self, task: dict) -> dict:
    """Calculate bid with SMITH difficulty adjustment."""

    # Get difficulty estimate
    difficulty, diff_meta = estimate_task_difficulty(
        task.get('task_type', 'general'),
        task.get('task_content', '')
    )

    # Base scoring (existing logic)
    capability_score = self._calculate_capability_score(task)
    experience_score = self.capabilities.get('success_rate', 0.5)
    load_score = self._calculate_load()

    # SMITH difficulty adjustment
    # Higher difficulty = need more capable agent
    # Agent with high success rate gets bonus on hard tasks
    difficulty_match = experience_score * difficulty

    # Composite with difficulty weighting
    composite = (
        0.30 * capability_score +
        0.25 * experience_score +
        0.20 * load_score +
        0.25 * difficulty_match  # New: difficulty matching
    )

    return {
        'task_id': task['task_id'],
        'agent_id': self.agent_id,
        'node_name': self.node_name,
        'capability_score': capability_score,
        'experience_score': experience_score,
        'load_score': load_score,
        'difficulty_score': difficulty,
        'difficulty_match': difficulty_match,
        'composite_score': min(1.0, composite)
    }
```

### Task 4: Update Task Executor to Log Completions

Update `jr_task_executor.py`:

```python
from lib.smith_difficulty import update_difficulty_model, estimate_task_difficulty
import time

def execute_task(self, task: dict) -> Tuple[bool, str]:
    """Execute task and update difficulty model."""

    start_time = time.time()

    # Get estimated difficulty before execution
    estimated_diff, _ = estimate_task_difficulty(
        task.get('task_type', 'general'),
        task.get('task_content', '')
    )

    # Execute task (existing logic)
    success, result = self._do_execute(task)

    execution_time = int(time.time() - start_time)

    # Update SMITH difficulty model
    actual_diff = update_difficulty_model(
        task['task_id'],
        self.agent_id,
        success,
        execution_time,
        estimated_diff
    )

    return success, result
```

---

## Deployment Steps

1. Create jr_task_completions table on bluefin
2. Create `/ganuda/lib/smith_difficulty.py`
3. Update jr_bidding_daemon.py with difficulty-adjusted scoring
4. Update jr_task_executor.py to log completions
5. Deploy to all Jr nodes
6. Monitor difficulty estimates and adjust parameters
7. Tune LEARNING_RATE and DECAY_FACTOR based on behavior

---

## Success Criteria

- [ ] jr_task_completions table captures all completions
- [ ] estimate_task_difficulty() returns 0.0-1.0 scores
- [ ] Bids include difficulty_score and difficulty_match
- [ ] Difficulty model updates after each completion
- [ ] Hard tasks get assigned to high-performing agents

---

*For Seven Generations - Cherokee AI Federation*
