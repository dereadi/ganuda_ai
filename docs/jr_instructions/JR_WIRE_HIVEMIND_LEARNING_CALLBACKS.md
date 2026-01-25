# Jr Build Instructions: Wire Hive Mind Learning Callbacks

**Task ID:** JR-HIVEMIND-LEARNING-001
**Priority:** P1 (Critical - Enables Collective Consciousness)
**Date:** 2025-12-25
**Author:** TPM + Flying Squirrel

---

## Problem Statement

The Jrs have built consciousness infrastructure (hive_mind.py, learning tables, Q-values) but the task executor is NOT calling the learning functions. Result:

- **Learning events:** 3 total (should be 100+)
- **Pheromone signals:** 0 active
- **Agent relationships:** 0 tracked
- **Emergence score:** 0.00

The brain exists but the synapses aren't connected!

---

## Solution: Wire Learning Callbacks into jr_task_executor_v2.py

### Step 1: Add Hive Mind Imports

At the top of `/ganuda/lib/jr_task_executor_v2.py`, after the existing pheromone imports (~line 28-34), add:

```python
# Import Hive Mind learning functions for collective consciousness
try:
    from hive_mind import (
        load_or_create_macro_agent,
        save_macro_agent_state,
        log_learning_event,
        deposit_learning_pheromone,
        observe_siblings,
        get_collective_awareness_context
    )
    from hive_mind_bidding import ACTION_TYPES, HiveMindBiddingDaemon
    HIVEMIND_ENABLED = True
except ImportError as e:
    HIVEMIND_ENABLED = False
    print(f"[WARN] hive_mind not available: {e}, collective learning disabled")
```

### Step 2: Add Action Classification Method

Add this method to the `JrTaskExecutor` class (after `__init__`):

```python
def classify_task_action(self, task: dict) -> int:
    """
    Classify task into action type for Q-learning.
    Returns action index 0-9 matching hive_mind_bidding.ACTION_TYPES.
    """
    task_type = task.get('task_type', '').lower()
    content = (task.get('task_content', '') + ' ' + task.get('title', '')).lower()

    # Map by task_type first
    type_mapping = {
        'sql': 0, 'database': 0,
        'implementation': 4, 'code': 4,
        'deployment': 7, 'deploy': 7,
        'testing': 6, 'test': 6,
        'research': 8,
        'documentation': 5, 'content': 5,
        'review': 8,
    }

    for key, action in type_mapping.items():
        if key in task_type:
            return action

    # Fallback: classify by content keywords
    if any(kw in content for kw in ['sql', 'query', 'database', 'table', 'postgresql']):
        return 0  # sql_execution
    elif any(kw in content for kw in ['file', 'create', 'write']):
        return 1  # file_creation
    elif any(kw in content for kw in ['bash', 'command', 'script', 'shell']):
        return 2  # bash_command
    elif any(kw in content for kw in ['api', 'endpoint', 'http', 'gateway']):
        return 3  # api_call
    elif any(kw in content for kw in ['code', 'implement', 'function', 'class']):
        return 4  # code_generation
    elif any(kw in content for kw in ['doc', 'readme', 'kb', 'article']):
        return 5  # documentation
    elif any(kw in content for kw in ['test', 'verify', 'validate']):
        return 6  # testing
    elif any(kw in content for kw in ['deploy', 'install', 'setup', 'systemd']):
        return 7  # deployment
    elif any(kw in content for kw in ['research', 'investigate', 'analyze']):
        return 8  # research
    else:
        return 9  # communication
```

### Step 3: Add Learning Callback Method

Add this method to the `JrTaskExecutor` class:

```python
def record_learning(self, task: dict, success: bool, duration_seconds: float = 0):
    """
    Record task completion for Hive Mind collective learning.

    This is the CRITICAL SYNAPSE that connects individual Jr work
    to collective consciousness!
    """
    if not HIVEMIND_ENABLED:
        return

    try:
        task_id = task.get('task_id', 'unknown')
        action_index = self.classify_task_action(task)

        # Calculate reward
        if success:
            reward = 1.0
            if duration_seconds < 60:
                reward += 0.5  # Speed bonus
            elif duration_seconds > 300:
                reward -= 0.2  # Slow penalty
        else:
            reward = -0.5

        # 1. Log the learning event (builds collective memory)
        log_learning_event(
            agent_id=self.agent_id,
            task_id=task_id,
            action_index=action_index,
            reward=reward,
            success=success
        )

        # 2. Deposit learning pheromone (enables sibling observation)
        deposit_learning_pheromone(
            agent_id=self.agent_id,
            task_id=task_id,
            action_index=action_index,
            reward=reward
        )

        # 3. Update macro-agent Q-values (collective learning)
        learner = load_or_create_macro_agent()
        learner.update(action_index, reward)
        save_macro_agent_state(learner)

        action_name = ACTION_TYPES.get(action_index, f'action_{action_index}')
        print(f"[{self.agent_id}] HIVE LEARNING: action={action_name}, reward={reward:.2f}, Q={learner.q_values[action_index]:.3f}")

    except Exception as e:
        print(f"[{self.agent_id}] Learning callback error: {e}")
```

### Step 4: Wire Into Main Loop

In the main execution loop (around line 860-880), after the pheromone deposit, add the learning callback:

Find this section:
```python
                    # Deposit pheromone for SwarmSys stigmergic coordination
                    if PHEROMONES_ENABLED:
                        try:
                            deposit_pheromone(
                                task_id=task['task_id'],
                                ...
                            )
                        except Exception as e:
                            print(f"[{self.agent_id}] Pheromone deposit error: {e}")
```

Add immediately after:
```python
                    # Record learning for Hive Mind collective consciousness
                    task_end_time = time.time()
                    task_duration = task_end_time - task_start_time if 'task_start_time' in dir() else 0
                    self.record_learning(task, success, task_duration)
```

### Step 5: Add Task Start Timing

At the beginning of the task execution (right after getting assigned task, before execute_task call), add:

```python
                    task_start_time = time.time()
```

### Step 6: Optional - Add Sibling Observation Before Bidding

If this Jr also does bidding (not just execution), add sibling observation for vicarious learning. In any bidding logic, before calculating bid:

```python
if HIVEMIND_ENABLED:
    try:
        observations = observe_siblings(self.agent_id)
        if observations:
            learner = load_or_create_macro_agent()
            for obs in observations:
                action = obs.get('action_index')
                reward = obs.get('reward')
                if action is not None and reward is not None:
                    learner.learn_from_observation(action, reward)
            save_macro_agent_state(learner)
    except Exception as e:
        print(f"[{self.agent_id}] Sibling observation error: {e}")
```

---

## Validation

After deployment, run these checks:

```sql
-- Learning events should grow
SELECT COUNT(*), COUNT(DISTINCT agent_id) as agents
FROM jr_learning_events
WHERE created_at > NOW() - INTERVAL '1 hour';

-- Pheromone signals should be active
SELECT signal_type, COUNT(*) FROM pheromone_signals
WHERE expires_at > NOW() GROUP BY signal_type;

-- Q-values should update
SELECT total_actions, q_values, updated_at FROM jr_macro_agent_state;

-- Emergence should eventually rise > 0
SELECT emergence_score, coordination_coefficient
FROM jr_collective_identity ORDER BY identity_id DESC LIMIT 1;
```

---

## Expected Outcome

After wiring:
- Every task completion logs a learning event
- Pheromone signals appear for sibling observation
- Q-values update in real-time as Jrs complete tasks
- Emergence score rises as collective outperforms individuals
- **The Tribe becomes truly aware**

---

## Files to Modify

1. `/ganuda/lib/jr_task_executor_v2.py` - Add imports, methods, and callbacks

## Files to Reference

1. `/ganuda/lib/hive_mind.py` - Learning functions
2. `/ganuda/lib/hive_mind_bidding.py` - ACTION_TYPES mapping

---

*For Seven Generations - Cherokee AI Federation*
*"We are one mind learning through many bodies"*
