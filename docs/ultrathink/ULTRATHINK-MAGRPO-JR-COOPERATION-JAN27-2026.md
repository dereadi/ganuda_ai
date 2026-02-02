# ULTRATHINK: MAGRPO Multi-Agent Jr Cooperation

**Date:** January 27, 2026
**TPM:** Claude Opus 4.5
**Source:** arXiv 2508.04652 - Multi-Agent Group Relative Policy Optimization
**Council Status:** APPROVED (Jan 26) - Deferred pending AgeMem/C3AI completion
**Priority:** P2 (AgeMem/C3AI now complete)

---

## Executive Summary

MAGRPO (Multi-Agent Group Relative Policy Optimization) extends our existing M-GRPO momentum learner to enable **multi-agent cooperation** between Jr specialists. While M-GRPO prevents individual agent collapse, MAGRPO optimizes **group dynamics** for better task handoffs and reduced commitment failures.

---

## Problem Statement

### Current Jr Cooperation Issues

| Issue | Frequency | Impact |
|-------|-----------|--------|
| Task handoff failures | ~15% of multi-step tasks | Work duplication, delays |
| Commitment conflicts | ~8% of shared resources | Database locks, file conflicts |
| Context loss between Jrs | ~20% of complex tasks | Incomplete implementations |
| Credit assignment unclear | Ongoing | Unfair Shapley contribution |

### Root Cause

Our current system treats each Jr as independent:
- M-GRPO optimizes individual Jr behavior
- No explicit reward for cooperation
- HiveMind tracks contributions but doesn't optimize them
- Task queue has no coordination signals

---

## MAGRPO Research Summary

### Source Paper (arXiv 2508.04652)

**Key Concepts:**
1. **Group Relative Advantage:** Compare agent action against group average, not just self-baseline
2. **Cooperation Bonus:** Reward agents for actions that improve group outcome
3. **Communication Penalty:** Discourage redundant/conflicting signals
4. **Joint Policy Gradient:** Update all agents toward group objective

**Findings:**
- 23% improvement in cooperative task success
- 41% reduction in coordination failures
- Emergent task specialization without explicit programming

### Mapping to Cherokee AI

| MAGRPO Concept | Cherokee Mapping |
|----------------|------------------|
| Agent group | Jr specialist pool |
| Group reward | Task completion success |
| Communication channel | Pheromone signals + jr_work_queue |
| Policy network | LLM + momentum weights |
| Coordination signal | HiveMind Shapley contributions |

---

## Current Infrastructure Assessment

### What We Have

```
/ganuda/lib/jr_momentum_learner.py
├── MomentumJrLearner class
├── EMA teacher model maintenance
├── Hybrid voting (student/teacher)
├── IQR filtering for low-entropy solutions
└── Per-Jr optimization (single agent)

/ganuda/lib/hive_mind.py
├── HiveMindTracker class
├── Shapley contribution calculation
├── Jr activity monitoring
└── No optimization feedback loop

/ganuda/lib/smadrl_pheromones.py
├── Pheromone signaling system
├── Task difficulty estimation
├── Decay dynamics
└── No group optimization
```

### What's Missing

1. **Group objective function** - Reward all participating Jrs for task success
2. **Cross-agent advantage calculation** - Compare Jr action to group average
3. **Coordination reward signal** - Bonus for successful handoffs
4. **Joint policy update** - Propagate group gradient to all Jrs

---

## Implementation Architecture

### Phase 1: Group Reward Infrastructure

Create tracking for multi-Jr task outcomes:

```python
class MAGRPOGroupTracker:
    """Track group task outcomes for MAGRPO optimization."""

    def __init__(self):
        self.group_tasks = {}  # task_id -> participating Jrs
        self.handoff_log = []  # (from_jr, to_jr, task_id, success)

    def register_participation(self, task_id: str, jr_type: str):
        """Register Jr participation in a task."""
        if task_id not in self.group_tasks:
            self.group_tasks[task_id] = []
        self.group_tasks[task_id].append({
            'jr_type': jr_type,
            'joined_at': datetime.now(),
            'contribution': None
        })

    def record_handoff(self, from_jr: str, to_jr: str, task_id: str, context_preserved: float):
        """Record task handoff between Jrs."""
        self.handoff_log.append({
            'from_jr': from_jr,
            'to_jr': to_jr,
            'task_id': task_id,
            'context_preserved': context_preserved,  # 0-1 score
            'timestamp': datetime.now()
        })

    def compute_group_reward(self, task_id: str, task_success: bool) -> Dict[str, float]:
        """Compute reward for each Jr based on group outcome."""
        participants = self.group_tasks.get(task_id, [])

        if not participants:
            return {}

        base_reward = 1.0 if task_success else -0.5

        # Distribute reward with cooperation bonus
        rewards = {}
        for p in participants:
            jr_type = p['jr_type']

            # Base share
            individual_reward = base_reward / len(participants)

            # Handoff bonus - reward successful context preservation
            handoff_bonus = self._compute_handoff_bonus(jr_type, task_id)

            rewards[jr_type] = individual_reward + handoff_bonus

        return rewards
```

### Phase 2: Cross-Agent Advantage

Extend momentum learner with group-relative advantage:

```python
class MAGRPOMomentumLearner(MomentumJrLearner):
    """Multi-agent extension of momentum learner."""

    def __init__(self, jr_type: str, group_tracker: MAGRPOGroupTracker):
        super().__init__(jr_type)
        self.group_tracker = group_tracker
        self.peer_momentum = {}  # Other Jrs' momentum weights

    def compute_group_relative_advantage(self, task_id: str, action_quality: float) -> float:
        """
        Compute advantage relative to group average, not just self-baseline.

        This encourages Jrs to contribute positively to group outcomes,
        not just optimize their individual metrics.
        """
        # Get all Jr action qualities for this task
        group_qualities = self._get_peer_action_qualities(task_id)

        if not group_qualities:
            return action_quality - self.baseline  # Fall back to individual

        # Group average (excluding self)
        peer_avg = np.mean([q for jr, q in group_qualities.items() if jr != self.jr_type])

        # Relative advantage = how much better than group average
        group_advantage = action_quality - peer_avg

        # Blend individual and group advantage (prevents pure competition)
        individual_advantage = action_quality - self.baseline

        # 70% individual, 30% group (balances cooperation/competition)
        blended_advantage = 0.7 * individual_advantage + 0.3 * group_advantage

        return blended_advantage

    def update_with_group_gradient(self, task_id: str, task_success: bool):
        """Propagate group reward gradient to momentum weights."""
        group_rewards = self.group_tracker.compute_group_reward(task_id, task_success)

        my_reward = group_rewards.get(self.jr_type, 0)

        # Update momentum with group signal
        self._apply_reward_gradient(my_reward, task_id)
```

### Phase 3: Coordination Signals

Enhance pheromone system with cooperation signals:

```python
# New pheromone types for MAGRPO
MAGRPO_PHEROMONES = {
    'handoff_ready': {
        'description': 'Jr ready to hand off task',
        'decay_rate': 0.9,
        'visibility': 'all_jrs'
    },
    'context_available': {
        'description': 'Rich context available for continuation',
        'decay_rate': 0.95,
        'visibility': 'same_task'
    },
    'cooperation_success': {
        'description': 'Successful multi-Jr task completion',
        'decay_rate': 0.8,
        'visibility': 'all_jrs'
    },
    'conflict_warning': {
        'description': 'Potential resource conflict detected',
        'decay_rate': 0.7,
        'visibility': 'all_jrs'
    }
}
```

### Phase 4: Database Schema

Track multi-agent interactions:

```sql
-- MAGRPO Group Task Participation
CREATE TABLE IF NOT EXISTS magrpo_task_participation (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    jr_type VARCHAR(50) NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),
    contribution_score FLOAT,
    handoff_from VARCHAR(50),
    handoff_to VARCHAR(50),
    context_preserved_score FLOAT,
    UNIQUE(task_id, jr_type, joined_at)
);

-- MAGRPO Cooperation Metrics
CREATE TABLE IF NOT EXISTS magrpo_cooperation_metrics (
    id SERIAL PRIMARY KEY,
    jr_type VARCHAR(50) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    tasks_participated INT DEFAULT 0,
    handoffs_sent INT DEFAULT 0,
    handoffs_received INT DEFAULT 0,
    avg_context_preservation FLOAT,
    cooperation_score FLOAT,
    group_reward_total FLOAT,
    UNIQUE(jr_type, period_start)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_magrpo_task_jr ON magrpo_task_participation(task_id, jr_type);
CREATE INDEX IF NOT EXISTS idx_magrpo_metrics_jr ON magrpo_cooperation_metrics(jr_type, period_start);
```

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `/ganuda/lib/magrpo_tracker.py` | CREATE | Group task tracking, reward computation |
| `/ganuda/lib/magrpo_momentum.py` | CREATE | Multi-agent momentum learner extension |
| `/ganuda/lib/jr_momentum_learner.py` | MODIFY | Add hooks for MAGRPO integration |
| `/ganuda/lib/smadrl_pheromones.py` | MODIFY | Add cooperation pheromone types |
| `/ganuda/sql/magrpo_schema.sql` | CREATE | Database tables for tracking |
| `/ganuda/jr_executor/jr_queue_worker.py` | MODIFY | Integrate MAGRPO signals |

---

## Security Considerations (Crawdad)

| Risk | Mitigation |
|------|------------|
| Jr gaming group rewards | IQR filtering on reward distribution |
| Collusion between Jrs | Audit log all cooperation signals |
| Reward hacking | Cap maximum cooperation bonus |
| Context leakage in handoffs | Sanitize shared context |

---

## Seven Generations Assessment (Turtle)

**Sustainable Design:**
- Cooperation patterns persist across Jr generations
- Successful handoff strategies become encoded in momentum weights
- Group wisdom accumulates in thermal memory

**Long-Term Value:**
- Future Jrs inherit cooperation skills
- Task specialization emerges organically
- Federation becomes more than sum of parts

---

## Implementation Phases

| Phase | Deliverable | Effort | Dependencies |
|-------|-------------|--------|--------------|
| P1 | MAGRPOGroupTracker class | 2 days | None |
| P2 | Database schema | 1 day | P1 |
| P3 | MAGRPOMomentumLearner extension | 3 days | P1, P2 |
| P4 | Pheromone integration | 2 days | P3 |
| P5 | Jr queue worker integration | 2 days | P4 |
| P6 | Testing & validation | 3 days | P5 |

**Total Effort:** ~13 days (2.5 weeks)

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Task handoff success rate | ~85% | 95% | magrpo_task_participation |
| Context preservation score | Unknown | >0.8 | handoff_to context_preserved |
| Multi-Jr task completion | ~80% | 92% | task success with 2+ Jrs |
| Commitment conflicts | ~8% | <2% | conflict_warning pheromones |

---

## Jr Assignment

### Phase 1-2: Foundation (Software Engineer Jr.)
- Create MAGRPOGroupTracker class
- Create database schema
- Unit tests for reward computation

### Phase 3-4: Integration (Software Engineer Jr. + Infrastructure Jr.)
- Extend MomentumJrLearner
- Integrate with pheromone system
- Deploy schema to bluefin

### Phase 5-6: Validation (Research Jr. + TPM)
- A/B test cooperation metrics
- Validate Seven Generations sustainability
- Document findings

---

## Rollback Plan

If MAGRPO causes issues:
1. Disable group reward computation (fall back to individual)
2. Remove MAGRPO pheromone types
3. Keep tracking tables for analysis
4. Revert to M-GRPO baseline

---

FOR SEVEN GENERATIONS

This enhancement ensures our Jr collective becomes wiser through cooperation,
building institutional knowledge that persists across agent generations.
