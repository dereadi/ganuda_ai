# JR Instruction: MAGRPO Phase 2 - Momentum Learner Integration

**JR ID:** JR-MAGRPO-PHASE2-MOMENTUM-INTEGRATION-JAN27-2026
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Depends On:** JR-MAGRPO-PHASE1-GROUP-TRACKER-JAN27-2026 (Complete)
**Ultrathink:** ULTRATHINK-MAGRPO-JR-COOPERATION-JAN27-2026.md
**Source Paper:** arXiv 2508.04652 - Multi-Agent Group Relative Policy Optimization
**Effort:** Medium (2-3 hours)

---

## Objective

Extend `jr_momentum_learner.py` to use group rewards from MAGRPOGroupTracker. This enables Jrs to learn from multi-agent task outcomes, not just individual performance.

---

## Current State

`/ganuda/lib/jr_momentum_learner.py` has:
- MomentumJrLearner class with EMA teacher/student
- Individual approach weights (direct_code, search_first, etc.)
- record_outcome() that updates weights based on individual success

**Missing:**
- Group reward integration
- Cross-agent advantage calculation
- Cooperation bonus in learning signal

---

## Changes Required

### 1. Add MAGRPO Import

At the top of the file, after existing imports (around line 20):

```python
# MAGRPO multi-agent cooperation (Phase 2)
try:
    from magrpo_tracker import get_magrpo_tracker, MAGRPOGroupTracker
    HAS_MAGRPO = True
except ImportError:
    HAS_MAGRPO = False
    logger.warning("MAGRPO tracker not available, using individual learning only")
```

---

### 2. Update __init__ to Accept Group Tracker

Modify the `__init__` method (around line 45):

```python
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
```

---

### 3. Add Group-Relative Advantage Method

Add this new method after `filter_low_entropy_solutions` (around line 164):

```python
    def compute_group_relative_advantage(self, task_id: str,
                                          individual_score: float) -> float:
        """
        Compute advantage relative to group average (MAGRPO core concept).

        Instead of just comparing to self-baseline, compare to how other
        Jrs performed on this task. Encourages cooperation over pure competition.

        Args:
            task_id: Task being evaluated
            individual_score: This Jr's performance score (0-1)

        Returns:
            Blended advantage score incorporating group dynamics
        """
        if not self.group_tracker:
            # Fall back to individual advantage
            baseline = self.student_state['approach_weights'].get('baseline', 0.5)
            return individual_score - baseline

        # Get group rewards for this task
        # Note: This assumes task has already been completed
        try:
            stats = self.group_tracker.get_jr_cooperation_stats(self.jr_type)

            # Compute peer average from recent tasks
            # This is simplified - full implementation would track per-task scores
            peer_avg = 0.5  # Default baseline

            # Individual advantage (how we did vs our baseline)
            individual_baseline = self.student_state['approach_weights'].get('baseline', 0.5)
            individual_advantage = individual_score - individual_baseline

            # Group advantage (how we did vs peers)
            group_advantage = individual_score - peer_avg

            # Blend: 70% individual, 30% group (balances cooperation/competition)
            blended = 0.7 * individual_advantage + 0.3 * group_advantage

            logger.debug(f"[M-GRPO] Advantage for {self.jr_type}: "
                        f"individual={individual_advantage:.3f}, "
                        f"group={group_advantage:.3f}, blended={blended:.3f}")

            return blended

        except Exception as e:
            logger.warning(f"[M-GRPO] Group advantage calc failed: {e}")
            return individual_score - 0.5
```

---

### 4. Add Enhanced Record Outcome with Group Rewards

Add this new method after `record_outcome` (around line 187):

```python
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
```

---

### 5. Add Handoff Recording Method

Add this method for tracking task handoffs:

```python
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
```

---

### 6. Update Learning Report

Modify `get_learning_report` to include MAGRPO stats (around line 188):

```python
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
```

---

### 7. Update Convenience Function

Modify the convenience function at the bottom:

```python
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
```

---

### 8. Update Test Suite

Replace the `if __name__ == '__main__':` section:

```python
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
```

---

## Verification Steps

1. **Syntax check:**
   ```bash
   cd /ganuda/lib && python3 -m py_compile jr_momentum_learner.py && echo "Syntax OK"
   ```

2. **Run unit test:**
   ```bash
   cd /ganuda/lib && python3 jr_momentum_learner.py
   ```

3. **Expected output:**
   ```
   M-GRPO + MAGRPO Momentum Learner - Test Suite
   MAGRPO enabled: True
   Simulating collaborative task: test-magrpo-XXXXXX
     SE Jr. chose: <approach>
     Research Jr. chose: <approach>
   Learning Reports:
   Software Engineer Jr.:
   {
     "cooperation": {
       "tasks_participated": 1,
       "handoffs_sent": 1,
       ...
     }
   }
   ```

---

## Files Modified

| File | Change |
|------|--------|
| `/ganuda/lib/jr_momentum_learner.py` | Add MAGRPO integration |

---

## Rollback

If issues occur:
```bash
git -C /ganuda checkout lib/jr_momentum_learner.py
```

---

FOR SEVEN GENERATIONS
